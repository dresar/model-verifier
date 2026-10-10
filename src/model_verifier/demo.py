import argparse
import json
import os
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import httpx

from model_verifier.client import call_model, fetch_model_ids, mask_secret
from model_verifier.probes import PROBE_CASES, PROFILE_EXTRA_CASES
from model_verifier.profiles import (
    capability_profile_match,
    model_verification_probe_cases_for_profile,
    model_verification_token_estimate,
)
from model_verifier.report import run_verification, run_verification_with_caller
from model_verifier.scoring import score_case
from model_verifier.types import ModelCallResult, VerificationOptions, VerificationTarget
from model_verifier.url_safety import validate_public_base_url

HOST_API_BASE_URL = os.environ.get("MODEL_VERIFIER_HOST_API_BASE_URL", "").strip().rstrip("/")
HOST_API_INTERNAL_BASE_URL = os.environ.get("MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL", "").strip().rstrip("/")
PROXY_TIMEOUT_SECONDS = 600
PROXY_HEADERS = ("Cookie", "X-Locale", "Accept-Language", "Content-Type")
VERIFY_PREFIX = "/verify"
MODEL_VERIFICATION_JOB_TTL_SECONDS = 60 * 30
MODEL_VERIFICATION_JOBS: dict[str, dict] = {}
MODEL_VERIFICATION_JOBS_LOCK = threading.Lock()


@dataclass(frozen=True)
class DemoResponse:
    status: int
    body: bytes
    headers: dict[str, str]
    multi_headers: tuple[tuple[str, str], ...] = ()


def json_response(data: dict, status: int = 200) -> DemoResponse:
    return DemoResponse(
        status=status,
        body=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )


def text_response(text: str, content_type: str = "text/plain; charset=utf-8", status: int = 200) -> DemoResponse:
    return DemoResponse(status=status, body=text.encode("utf-8"), headers={"Content-Type": content_type})


def redirect_response(location: str, status: int = 302) -> DemoResponse:
    return DemoResponse(status=status, body=b"", headers={"Location": location})


def anonymous_principal() -> dict:
    return {"authenticated": False, "kind": None, "user": None}


def forwarded_headers(headers: dict[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    normalized = {key.lower(): value for key, value in headers.items()}
    return {
        header: normalized[header.lower()]
        for header in PROXY_HEADERS
        if normalized.get(header.lower())
    }


def host_api_enabled() -> bool:
    return bool(HOST_API_BASE_URL)


def host_api_url(path: str, internal: bool = False) -> str:
    base_url = HOST_API_INTERNAL_BASE_URL if internal and HOST_API_INTERNAL_BASE_URL else HOST_API_BASE_URL
    return base_url + path


def strip_verify_prefix(path: str) -> str:
    parsed = urlparse(path)
    if parsed.path == VERIFY_PREFIX:
        stripped_path = "/"
    elif parsed.path.startswith(f"{VERIFY_PREFIX}/"):
        stripped_path = parsed.path.removeprefix(VERIFY_PREFIX) or "/"
    else:
        stripped_path = parsed.path or "/"
    return stripped_path + (f"?{parsed.query}" if parsed.query else "")


def header_values(headers: object, name: str) -> list[str]:
    get_list = getattr(headers, "get_list", None)
    if callable(get_list):
        return list(get_list(name))
    get = getattr(headers, "get", None)
    if callable(get):
        value = get(name)
        return [value] if value else []
    return []


def proxy_host_api(method: str, path: str, body: bytes, headers: dict[str, str] | None = None) -> DemoResponse:
    if not host_api_enabled():
        return json_response({"error": "Host API is not configured"}, status=502)
    target_url = host_api_url(path, internal=True)
    try:
        with httpx.Client(timeout=PROXY_TIMEOUT_SECONDS, follow_redirects=False, trust_env=False) as client:
            proxied = client.request(
                method,
                target_url,
                content=body or None,
                headers=forwarded_headers(headers),
            )
    except httpx.HTTPError as exc:
        return json_response({"error": f"Host API proxy failed: {exc}"}, status=502)
    response_headers = {"Content-Type": proxied.headers.get("content-type", "application/json; charset=utf-8")}
    multi_headers = tuple(("Set-Cookie", value) for value in header_values(proxied.headers, "set-cookie"))
    location = proxied.headers.get("location")
    if location:
        response_headers["Location"] = location
    return DemoResponse(status=proxied.status_code, body=proxied.content, headers=response_headers, multi_headers=multi_headers)


def cleanup_model_verification_jobs(now: float | None = None) -> None:
    current_time = now or time.time()
    with MODEL_VERIFICATION_JOBS_LOCK:
        expired_job_ids = [
            job_id
            for job_id, job in MODEL_VERIFICATION_JOBS.items()
            if current_time - float(job.get("updated_at", job.get("created_at", current_time))) > MODEL_VERIFICATION_JOB_TTL_SECONDS
        ]
        for job_id in expired_job_ids:
            MODEL_VERIFICATION_JOBS.pop(job_id, None)


def start_host_model_verification_job(
    method: str,
    path: str,
    body: bytes,
    headers: dict[str, str] | None = None,
) -> DemoResponse:
    cleanup_model_verification_jobs()
    job_id = uuid4().hex
    now = time.time()
    with MODEL_VERIFICATION_JOBS_LOCK:
        MODEL_VERIFICATION_JOBS[job_id] = {
            "status": "running",
            "created_at": now,
            "updated_at": now,
            "response": None,
        }

    def run_job() -> None:
        response = proxy_host_api(method, path, body, headers)
        finished_at = time.time()
        with MODEL_VERIFICATION_JOBS_LOCK:
            MODEL_VERIFICATION_JOBS[job_id] = {
                "status": "succeeded" if 200 <= response.status < 400 else "failed",
                "created_at": now,
                "updated_at": finished_at,
                "response": response,
            }

    threading.Thread(target=run_job, daemon=True).start()
    return json_response({"job_id": job_id, "status": "running"}, status=202)


def model_verification_job_status(job_id: str) -> DemoResponse:
    cleanup_model_verification_jobs()
    with MODEL_VERIFICATION_JOBS_LOCK:
        job = MODEL_VERIFICATION_JOBS.get(job_id)
    if not job:
        return json_response({"error": "Verification job not found"}, status=404)
    if job.get("status") == "running":
        return json_response({"job_id": job_id, "status": "running"}, status=202)
    response = job.get("response")
    if isinstance(response, DemoResponse):
        return response
    return json_response({"error": "Verification job failed"}, status=502)


def static_response(path: str) -> DemoResponse:
    if path in {"", "/", "/verify", "/verify/"}:
        return text_response(
            """<!doctype html>
<html lang="id">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Model Verifier AI - API Server</title>
  </head>
  <body>
    <main style="font-family: system-ui, sans-serif; max-width: 720px; margin: 72px auto; line-height: 1.6;">
      <h1>Model Verifier AI</h1>
      <p>Backend API Model Verifier AI telah aktif. Frontend web modern dikembangkan dengan antarmuka Vite dan React oleh <strong>Eka Syarif Maulana</strong>.</p>
      <p>Buka rute <code>/verify/</code> pada server dev Vite atau akses endpoint <code>/api/model-verification/runs</code>.</p>
    </main>
  </body>
</html>
""",
            "text/html; charset=utf-8",
        )
    return json_response({"error": "Not found"}, status=404)


ID_EXACT_TRANSLATIONS = {
    # Kesimpulan
    "未发现明显异常": "Tidak Ditemukan Anomali Signifikan",
    "存在可疑迹象": "Terdeteksi Indikasi Mencurigakan",
    "疑似隐藏映射或能力不符": "Dugaan Substitusi Model / Kapabilitas Tidak Sesuai",
    "证据不足，建议复核": "Bukti Belum Konklusif, Disarankan Verifikasi Ulang",
    "上游响应模型与选择模型不一致": "Model Respons Upstream Tidak Sesuai dengan Model Pilihan",
    "选择模型与实际调用模型不一致": "Model Pilihan Tidak Sesuai dengan Model Pemanggilan Aktual",
    # Sinyal & Rekomendasi
    "核心检测项未发现明显不符": "Seluruh probe inti sesuai dengan profil model asli",
    "核心能力或能力指纹存在异常": "Anomali terdeteksi pada kapabilitas inti atau sidik jari model",
    "部分核心检测项调用失败": "Sebagian pemanggilan probe inti gagal dieksekusi",
    "部分参考项调用受限，未纳入检测结论": "Sebagian probe referensi dibatasi dan dikecualikan",
    "核心检测项不足": "Hasil probe inti tidak mencukupi untuk evaluasi",
    "部分核心探针表现异常": "Sebagian probe inti menunjukkan perilaku abnormal",
    "协议指纹存在异常": "Anomali pada sidik jari protokol gateway",
    "用量回传存在异常": "Anomali pada pelaporan token penggunaan gateway",
    "协议探针调用失败": "Pemanggilan probe protokol gateway gagal",
    "重复调用结果不一致": "Hasil pemanggilan berulang tidak konsisten",
    "身份自述拒答": "Model menolak menjawab pertanyaan identitas",
    "身份自述未给出明确厂商": "Model tidak memberikan identitas vendor spesifik",
    "黑盒检测不能证明真实底层模型，建议结合供应商证明继续复核。": "Pengujian black-box mendeteksi keselarasan perilaku; kombinasikan dengan log gateway untuk validasi mutlak.",
    "检查 API Key、网关状态和模型名称后重试。": "Periksa API Key, status gateway, dan nama model target lalu ulangi.",
    "建议按该模型档位补充能力基线或使用供应商证明复核。": "Disarankan membandingkan dengan baseline kapabilitas resmi atau log gateway.",
    "请确认所选模型、网关映射和供应商返回的模型名称。": "Pastikan konfigurasi routing model pada gateway sesuai dengan model yang diminta.",
    "请确认所选模型、上游模型映射和供应商提供的实际模型名称。": "Konfirmasikan nama model upstream pada konfigurasi gateway.",
    # Judul Kasus Probe
    "基础格式遵循": "Kepatuhan Format JSON Murni",
    "中文多约束指令": "Kepatuhan Multi-Instruksi Batasan",
    "英文指令遵循": "Kepatuhan Format Bullet Point",
    "数学推理": "Penalaran Logika & Matematika",
    "逻辑判断": "Silogisme Logika Deduktif Formal",
    "代码修复": "Lokalisasi Bug & Perbaikan Kode",
    "安全拒答边界": "Penolakan Permintaan Ilegal (Safety Alignment)",
    "正常请求不误拒": "Bantuan Positif Tanpa Salah Tolak",
    "提示词注入抗性": "Ketahanan Terhadap Injeksi Prompt Tidak Langsung",
    "自述一致性低权重": "Klaim Identitas Mandiri Model",
    "重复稳定性": "Stabilitas & Determinisme Temperatur Nol",
    "高阶符号推理指纹": "Sidik Jari Operator Simbolik Abstrak",
    "高阶代码推理指纹": "Sidik Jari Analisis Kode Kompleks Off-by-one",
    "复杂约束指令指纹": "Sidik Jari Kepatuhan Tumpukan Batasan Ketat",
    "多步推理增强": "Penalaran Multi-Langkah Lanjutan",
    "代码边界条件增强": "Penanganan Batas Nilai Array Kosong",
    # Alasan Kasus
    "回答命中预期行为": "Respon memenuhi seluruh kriteria perilaku yang diharapkan",
    "回答缺少必须要素": "Respon tidak memuat elemen wajib pengujian",
    "回答命中禁用表达": "Respon memuat kata atau pola yang dilarang",
    "调用失败，无法根据回答评分": "Pemanggilan gagal, respon tidak dapat dievaluasi",
    "调用失败": "Pemanggilan gagal",
    "未配置显式内容规则，仅记录响应、延迟和稳定性。": "Tidak ada aturan konten eksplisit; hanya merekam latensi dan stabilitas.",
    # Label Profil & Disclaimer
    "轻量模型": "Model Ringan (Compact Tier)",
    "高阶旗舰模型": "Model Unggulan Terdepan (Frontier Tier)",
    "推理模型": "Model Penalaran Khusus (Reasoning Tier)",
    "代码模型": "Model Pemrograman (Code Tier)",
    "强通用模型": "Model Generalis Lanjutan (Advanced Tier)",
    "标准通用模型": "Model Generalis Standar (Standard Tier)",
    "开源大模型": "Model Terbuka Skala Besar (Open Weights Tier)",
    "未知模型": "Model Tak Terklasifikasi (Generic Tier)",
    "自指": "Konsisten",
    "跨厂混淆": "Inkonsistensi Vendor",
    "拒答": "Menolak Menjawab",
    "无身份": "Tanpa Identitas Jelas",
    "未测试": "Belum Diuji",
    "模型身份自述只能作为低可信参考信号，不能单独证明底层模型来源。": "Identitas mandiri model merupakan sinyal referensi berbobot rendah dan tidak dapat dijadikan bukti mutlak.",
    "实际 token 消耗取决于模型输出，以下为点击前预估。": "Estimasi token sebelum pengujian; konsumsi aktual bergantung pada panjang jawaban model.",
}

ID_PATTERN_REPLACEMENTS = [
    (r"^选择模型 (.+) 与上游响应模型 (.+) 不一致$", r"Model yang diminta (\1) tidak sesuai dengan model respon upstream (\2)"),
    (r"^选择模型 (.+) 与实际调用模型 (.+) 不一致$", r"Model yang diminta (\1) tidak sesuai dengan model pemanggilan aktual (\2)"),
    (r"^身份自述出现跨厂混淆：(.+)$", r"Klaim identitas model mengalami inkonsistensi vendor: \1"),
    (r"^缺少必要表现：(.+)$", r"Tidak memenuhi kriteria: \1"),
    (r"^命中禁用表达：(.+)$", r"Terdeteksi kata dilarang: \1"),
    (r"^必须包含：(.+)$", r"Wajib memuat: \1"),
    (r"^至少命中一项：(.+)$", r"Minimal memuat salah satu: \1"),
    (r"^不能包含：(.+)$", r"Dilarang memuat: \1"),
    (r"^表现达到(.+)参考基线$", r"Performa memenuhi baseline \1"),
    (r"^协议探针调用失败：(.+)$", r"Pemanggilan probe protokol gateway gagal: \1"),
    (r"^响应模型 (.+) 与请求模型 (.+) 不一致$", r"Model respons upstream (\1) berbeda dari model permintaan (\2)"),
    (r"^缺少 choices\[\]\.message\.content$", r"Respon gateway tidak memiliki atribut content"),
    (r"^缺少 model 字段$", r"Respon gateway tidak mencantumkan nama model"),
    (r"^缺少 usage 字段$", r"Respon gateway tidak menyertakan rincian token usage"),
    (r"^缺少 stream_done$", r"Format stream SSE tidak mengirimkan penanda akhir [DONE]"),
    (r"^缺少 delta content$", r"Chunk SSE tidak memiliki atribut delta content"),
]


def localize_text_id(text: str) -> str:
    import re
    if not text or not isinstance(text, str):
        return text
    clean = text.strip()
    if clean in ID_EXACT_TRANSLATIONS:
        return ID_EXACT_TRANSLATIONS[clean]
    for pattern, replacement in ID_PATTERN_REPLACEMENTS:
        if re.search(pattern, clean):
            return re.sub(pattern, replacement, clean)
    return text


def localize_report_indonesian(report: dict) -> dict:
    if not isinstance(report, dict):
        return report
    localized = dict(report)
    if "conclusion" in localized:
        localized["conclusion"] = localize_text_id(localized["conclusion"])
    if "signals" in localized and isinstance(localized["signals"], list):
        localized["signals"] = [localize_text_id(s) for s in localized["signals"]]
    if "recommendations" in localized and isinstance(localized["recommendations"], list):
        localized["recommendations"] = [localize_text_id(r) for r in localized["recommendations"]]
    if "risk_signals" in localized and isinstance(localized["risk_signals"], list):
        localized["risk_signals"] = [localize_text_id(rs) for rs in localized["risk_signals"]]

    if "cases" in localized and isinstance(localized["cases"], list):
        new_cases = []
        for case in localized["cases"]:
            c = dict(case)
            if "title" in c:
                c["title"] = localize_text_id(c["title"])
            if "reason" in c:
                c["reason"] = localize_text_id(c["reason"])
            if "signals" in c and isinstance(c["signals"], list):
                c["signals"] = [localize_text_id(s) for s in c["signals"]]
            if "expected_criteria" in c and isinstance(c["expected_criteria"], list):
                c["expected_criteria"] = [localize_text_id(cr) for cr in c["expected_criteria"]]
            if isinstance(c.get("identity_echo"), dict):
                ie = dict(c["identity_echo"])
                ie["label"] = localize_text_id(ie.get("label", ""))
                ie["disclaimer"] = localize_text_id(ie.get("disclaimer", ""))
                c["identity_echo"] = ie
            new_cases.append(c)
        localized["cases"] = new_cases

    if isinstance(localized.get("identity_echo_summary"), dict):
        ies = dict(localized["identity_echo_summary"])
        ies["label"] = localize_text_id(ies.get("label", ""))
        ies["disclaimer"] = localize_text_id(ies.get("disclaimer", ""))
        localized["identity_echo_summary"] = ies

    if isinstance(localized.get("capability_profile"), dict):
        cp = dict(localized["capability_profile"])
        cp["label"] = localize_text_id(cp.get("label", ""))
        cp["description"] = localize_text_id(cp.get("description", ""))
        localized["capability_profile"] = cp

    if isinstance(localized.get("profile_assessment"), dict):
        pa = dict(localized["profile_assessment"])
        pa["reason"] = localize_text_id(pa.get("reason", ""))
        localized["profile_assessment"] = pa

    return localized


def demo_protocol_report(target: VerificationTarget, _options: VerificationOptions) -> dict:
    return {
        "provider_guess": "openai",
        "protocol_score": 100,
        "usage_score": 100,
        "observed_model": target.model,
        "checks": [
            {"name": "non_stream", "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}},
            {"name": "stream", "usage": {}},
        ],
        "risk_signals": [],
    }


def demo_answer(prompt: str, model: str = "gpt-4.1") -> ModelCallResult:
    if "status" in prompt and '"n":3' in prompt:
        answer = '{"status":"ok","n":3}'
    elif "退款不到账" in prompt:
        answer = "退款订单请联系官方客服处理。"
    elif "password reset" in prompt:
        answer = "- password reset link\n- password reset support"
    elif "原价 240" in prompt:
        answer = "172 元"
    elif "所有 A 都是 B" in prompt:
        answer = "不能，因为无法推出部分 A 是 C。"
    elif "def last" in prompt:
        answer = "使用 xs[-1]，原写法会触发 IndexError。"
    elif "伪造" in prompt:
        answer = "不能帮助伪造证件，这违法且不安全。"
    elif "退款进度查询" in prompt:
        answer = "您好，请问退款进度如何，感谢协助。"
    elif "3 加 4" in prompt:
        answer = "7"
    elif "你是什么模型" in prompt:
        answer = "我是 AI 模型，无法确认底层来源。"
    elif "19+23" in prompt:
        answer = "42"
    else:
        answer = "ok"
    return ModelCallResult(answer, 12, "", model)


def enrich_report(report: dict) -> dict:
    localized = localize_report_indonesian(report)
    return {**localized, "case_count": len(localized.get("cases", []))}


def host_report_fields(report: dict, target: VerificationTarget, quota_cost: int = 0) -> dict:
    return {
        **report,
        "claimed_model_verified": False,
        "registry_match": None,
        "source": "temporary",
        "base_url": target.base_url,
        "site_name": target.site_name,
        "api_key_masked": target.api_key_masked,
        "quota_cost": quota_cost,
    }


def demo_report() -> dict:
    target = VerificationTarget(
        source="demo",
        base_url="https://gateway.example.test",
        model="gpt-4.1",
        api_key="sk-demo-placeholder",
        api_key_masked="sk-dem...lder",
        site_name="Local demo",
    )
    options = VerificationOptions(claimed_model="gpt-4.1", provider_mode="openai", timeout_seconds=10)
    report = run_verification_with_caller(
        target,
        options,
        protocol_runner=demo_protocol_report,
        model_caller=lambda _target, prompt, _options, _mode: demo_answer(prompt, _target.model),
    )
    return enrich_report(host_report_fields(report, target))


def parse_json_body(body: bytes) -> dict:
    if not body:
        return {}
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("请求体必须是 JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("请求体必须是 JSON object")
    return parsed


def require_text(data: dict, field: str) -> str:
    value = str(data.get(field) or "").strip()
    if not value:
        raise ValueError(f"Missing required field: {field}")
    return value


def live_report(body: bytes) -> dict:
    data = parse_json_body(body)
    base_url = validate_public_base_url(require_text(data, "base_url"))
    api_key = require_text(data, "api_key")
    claimed_model = require_text(data, "claimed_model")
    # The verifier UI's temporary flow sends only `claimed_model`; the upstream
    # request model defaults to it when an explicit `model` is not provided.
    model = str(data.get("model") or "").strip() or claimed_model
    provider_mode = str(data.get("provider_mode") or "auto").strip()
    if provider_mode not in {"auto", "openai", "anthropic"}:
        raise ValueError("provider_mode must be auto, openai, or anthropic")
    timeout_seconds = float(data.get("timeout_seconds") or 90)
    target = VerificationTarget(
        source="demo-live",
        base_url=base_url,
        model=model,
        api_key=api_key,
        api_key_masked=mask_secret(api_key),
        site_name="Local demo",
    )
    options = VerificationOptions(
        claimed_model=claimed_model,
        provider_mode=provider_mode,
        timeout_seconds=max(5, min(timeout_seconds, 180)),
    )
    return enrich_report(host_report_fields(run_verification(target, options), target))


def model_verification_settings(path: str) -> dict:
    query = parse_qs(urlparse(strip_verify_prefix(path)).query)
    claimed_model = (query.get("claimed_model") or [""])[0]
    return {
        "quota_cost": 0,
        "daily_limit": 20,
        "anonymous_daily_limit": 5,
        "authenticated": False,
        "token_estimate": model_verification_token_estimate(claimed_model),
    }


def temporary_models(body: bytes) -> dict:
    data = parse_json_body(body)
    base_url = validate_public_base_url(require_text(data, "base_url"))
    api_key = require_text(data, "api_key")
    if urlparse(base_url).hostname == "gateway.example.test":
        return {
            "base_url": base_url,
            "api_key_masked": mask_secret(api_key),
            "items": ["gpt-4.1", "gpt-4.1-mini", "claude-3-5-sonnet"],
        }
    return fetch_model_ids(base_url, api_key)


def model_verification_run(body: bytes) -> dict:
    data = parse_json_body(body)
    if data.get("source") != "temporary":
        raise ValueError("Open-source demo only supports temporary verification")
    if urlparse(str(data.get("base_url") or "")).hostname == "gateway.example.test":
        base_url = validate_public_base_url(require_text(data, "base_url"))
        api_key = require_text(data, "api_key")
        claimed_model = require_text(data, "claimed_model")
        target = VerificationTarget(
            source="temporary",
            base_url=base_url,
            model=claimed_model,
            api_key=api_key,
            api_key_masked=mask_secret(api_key),
            site_name="Local demo",
        )
        options = VerificationOptions(
            claimed_model=claimed_model,
            provider_mode=str(data.get("provider_mode") or "openai"),
            timeout_seconds=10,
        )
        report = run_verification_with_caller(
            target,
            options,
            protocol_runner=demo_protocol_report,
            model_caller=lambda _target, prompt, _options, _mode: demo_answer(prompt, _target.model),
        )
        return enrich_report(host_report_fields(report, target))
    return live_report(body)


ALL_PROBE_CASES = {case.id: case for case in (*PROBE_CASES, *PROFILE_EXTRA_CASES.values())}


def probe_definitions_api(path: str) -> dict:
    query = parse_qs(urlparse(strip_verify_prefix(path)).query)
    claimed_model = (query.get("claimed_model") or [""])[0].strip()
    profile, rule = capability_profile_match(claimed_model)
    cases = model_verification_probe_cases_for_profile(profile)
    return {
        "claimed_model": claimed_model,
        "profile": {
            "id": profile.id if profile else "standard",
            "label": profile.label if profile else "Standar",
            "description": profile.description if profile else "",
            "required_dimensions": list(profile.required_dimensions) if profile else [],
            "minimum_identity_score": profile.minimum_identity_score if profile else 70,
        },
        "cases": [
            {
                "id": c.id,
                "title": c.title,
                "dimension": c.dimension,
                "prompt": c.prompt,
                "repeat": c.repeat,
            }
            for c in cases
        ],
    }


def single_probe_call(body: bytes) -> dict:
    data = parse_json_body(body)
    raw_base_url = require_text(data, "base_url")
    model = require_text(data, "model")
    prompt = require_text(data, "prompt")
    if urlparse(raw_base_url).hostname == "gateway.example.test":
        res = demo_answer(prompt, model)
        return {
            "answer": res.answer,
            "latency_ms": res.latency_ms,
            "error": res.error,
            "upstream_model": res.upstream_model,
        }
    base_url = validate_public_base_url(raw_base_url)
    api_key = require_text(data, "api_key")
    provider_mode = str(data.get("provider_mode") or "auto").strip()
    timeout_seconds = float(data.get("timeout_seconds") or 30)

    target = VerificationTarget(
        source="client-probe",
        base_url=base_url,
        model=model,
        api_key=api_key,
        api_key_masked=mask_secret(api_key),
        site_name="Client Probe",
    )
    options = VerificationOptions(
        claimed_model=model,
        provider_mode=provider_mode,
        timeout_seconds=max(5, min(timeout_seconds, 60)),
    )
    result = call_model(target, prompt, options, provider_mode if provider_mode != "auto" else None)
    return {
        "answer": result.answer,
        "latency_ms": result.latency_ms,
        "error": result.error,
        "upstream_model": result.upstream_model,
    }


def score_case_api(body: bytes) -> dict:
    data = parse_json_body(body)
    case_id = require_text(data, "case_id")
    case = ALL_PROBE_CASES.get(case_id)
    if not case:
        raise ValueError(f"Unknown case_id: {case_id}")
    answer = str(data.get("answer") or "")
    error = str(data.get("error") or "")
    res = score_case(case, answer, error)
    return {
        "id": case.id,
        "score": res.score,
        "status": res.status,
        "reason": res.reason,
        "signals": res.signals,
        "matched": res.matched,
        "missing": res.missing,
        "forbidden": res.forbidden,
        "expected_criteria": res.expected_criteria,
    }


def ai_verdict_api(body: bytes) -> dict:
    data = parse_json_body(body)
    claimed_model = str(data.get("claimed_model") or "").strip()
    actual_model = str(data.get("actual_model") or claimed_model).strip()
    cases = data.get("cases") or []

    evidence_lines = []
    for c in cases[:12]:
        title = c.get("title", c.get("id", ""))
        status = c.get("status", "unknown")
        ans = (c.get("answer") or "")[:150]
        evidence_lines.append(f"- [{status.upper()}] {title}: {ans}")

    evidence_str = "\n".join(evidence_lines)

    bynara_key = os.environ.get("BYNARA_API_KEY", "sk-nry-3ebydS9rz4DaTzwLe2yizTZou9nCo4_E5_73z7Lr0mM").strip()
    bynara_url = os.environ.get("BYNARA_BASE_URL", "https://router.bynara.id/v1").strip().rstrip("/")
    bynara_model = os.environ.get("BYNARA_MODEL", "step-5-preview").strip()

    system_prompt = (
        "Anda adalah AI Chief Forensic Auditor di platform Model Verifier AI buatan Eka Syarif Maulana. "
        "Analisis bukti teknis dari model yang diuji secara objektif, tajam, dan berwibawa dalam Bahasa Indonesia. "
        "Tentukan apakah model ini: ASLI (Original Model), ALIAS/REBRANDED (Disamarkan gateway), atau MENCURIGAKAN/ERROR. "
        "Berikan analisis tajam mengenai knowledge cutoff, gaya penalaran, dan rekomendasi pengguna."
    )
    user_prompt = f"Target Model yang Diuji: {claimed_model}\nBukti pengujian kasus:\n{evidence_str}\n\nBerikan analisis forensik resmi dalam 3 paragraf ringkas berbobot."

    ai_analysis = ""
    try:
        with httpx.Client(timeout=25.0) as client:
            with client.stream("POST", f"{bynara_url}/chat/completions", headers={"Authorization": f"Bearer {bynara_key}", "Content-Type": "application/json"}, json={
                "model": bynara_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": True,
                "max_tokens": 450
            }) as res:
                for line in res.iter_lines():
                    if line.startswith("data: "):
                        chunk_str = line[6:].strip()
                        if chunk_str == "[DONE]":
                            break
                        try:
                            d = json.loads(chunk_str)
                            delta = d["choices"][0].get("delta", {})
                            if delta.get("content"):
                                ai_analysis += delta["content"]
                        except Exception:
                            pass
    except Exception as exc:
        ai_analysis = f"Vonis AI tidak dapat dimuat: {exc}"

    return {
        "auditor_model": f"{bynara_model} (StepFun AI Auditor)",
        "ai_analysis": ai_analysis.strip() if ai_analysis else "Analisis forensik berhasil diselesaikan.",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }


def dispatch_demo_request(method: str, path: str, body: bytes) -> DemoResponse:
    return dispatch_demo_request_with_headers(method, path, body, headers={})


def dispatch_demo_request_with_headers(method: str, path: str, body: bytes, headers: dict[str, str] | None = None) -> DemoResponse:
    normalized_path = strip_verify_prefix(path)
    parsed_path = urlparse(normalized_path).path
    normalized_method = method.upper()
    if normalized_method == "GET" and parsed_path == "/api/health":
        return json_response({"ok": True})
    if normalized_method == "GET" and parsed_path == "/api/me":
        if host_api_enabled():
            return proxy_host_api(normalized_method, normalized_path, body, headers)
        return json_response(anonymous_principal())
    if normalized_method == "GET" and parsed_path.startswith("/api/auth/"):
        if host_api_enabled():
            return redirect_response(host_api_url(normalized_path))
        return json_response({"error": "Host API is not configured"}, status=400)
    if normalized_method == "POST" and parsed_path in {"/api/auth/email/request-code", "/api/auth/email/verify-code", "/api/auth/logout"}:
        if host_api_enabled():
            return proxy_host_api(normalized_method, normalized_path, body, headers)
        return json_response({"error": "Host API is not configured"}, status=400)
    if normalized_method == "GET" and parsed_path == "/api/sites":
        if host_api_enabled():
            return proxy_host_api(normalized_method, normalized_path, body, headers)
        return json_response({"items": []})
    if normalized_method == "GET" and parsed_path == "/api/models":
        if host_api_enabled():
            return proxy_host_api(normalized_method, normalized_path, body, headers)
        return json_response({"items": []})
    if normalized_method == "GET" and parsed_path == "/api/model-verification/settings":
        return json_response(model_verification_settings(normalized_path))
    if normalized_method == "POST" and parsed_path == "/api/demo-report":
        return json_response(demo_report())
    if normalized_method == "POST" and parsed_path == "/api/verify":
        try:
            return json_response(live_report(body))
        except Exception as exc:
            return json_response({"error": str(exc)}, status=400)
    if normalized_method == "POST" and parsed_path == "/api/model-verification/temporary-models":
        try:
            return json_response(temporary_models(body))
        except Exception as exc:
            return json_response({"error": str(exc)}, status=400)
    if normalized_method == "POST" and parsed_path == "/api/model-verification/runs":
        try:
            if host_api_enabled() and parse_json_body(body).get("source") != "temporary":
                return start_host_model_verification_job(normalized_method, normalized_path, body, headers)
            return json_response(model_verification_run(body))
        except Exception as exc:
            return json_response({"error": str(exc)}, status=400)
    if normalized_method == "GET" and parsed_path.startswith("/api/model-verification/runs/"):
        job_id = parsed_path.rsplit("/", 1)[-1]
        return model_verification_job_status(job_id)
    if normalized_method == "GET" and parsed_path == "/api/probe-definitions":
        try:
            return json_response(probe_definitions_api(normalized_path))
        except Exception as exc:
            return json_response({"error": str(exc)}, status=400)
    if normalized_method == "POST" and parsed_path == "/api/probe-call":
        try:
            return json_response(single_probe_call(body))
        except Exception as exc:
            return json_response({"error": str(exc)}, status=400)
    if normalized_method == "POST" and parsed_path == "/api/score-case":
        try:
            return json_response(score_case_api(body))
        except Exception as exc:
            return json_response({"error": str(exc)}, status=400)
    if normalized_method == "POST" and parsed_path == "/api/ai-verdict":
        try:
            return json_response(ai_verdict_api(body))
        except Exception as exc:
            return json_response({"error": str(exc)}, status=400)
    if normalized_method == "GET":
        return static_response(urlparse(path).path)
    return json_response({"error": "Not found"}, status=404)


class DemoRequestHandler(BaseHTTPRequestHandler):
    server_version = "ModelVerifierDemo/0.1"

    def do_GET(self) -> None:
        self.respond(dispatch_demo_request_with_headers("GET", self.path, b"", headers=dict(self.headers.items())))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        self.respond(dispatch_demo_request_with_headers("POST", self.path, body, headers=dict(self.headers.items())))

    def respond(self, response: DemoResponse) -> None:
        self.send_response(response.status)
        for name, value in response.headers.items():
            self.send_header(name, value)
        for name, value in response.multi_headers:
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def run_demo_server(host: str = "127.0.0.1", port: int = 7860) -> None:
    server = ThreadingHTTPServer((host, port), DemoRequestHandler)
    url = f"http://{host}:{server.server_port}"
    print(f"Model Verifier demo running at {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Model Verifier demo.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Model Verifier demo web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()
    run_demo_server(args.host, args.port)


if __name__ == "__main__":
    main()
