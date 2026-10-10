import json
import time

import httpx

from model_verifier.probes import (
    MODEL_VERIFICATION_MAX_OUTPUT_TOKENS,
    MODEL_VERIFICATION_SYSTEM_PROMPT,
    is_probably_chat_model_id,
)
from model_verifier.providers import (
    extract_openai_choice_text,
    extract_openai_reasoning_text,
    parse_anthropic_message_response,
    parse_anthropic_stream_response,
    parse_openai_chat_response,
    parse_openai_stream_response,
    select_effective_provider_mode,
    summarize_protocol_report,
)
from model_verifier.types import ModelCallResult, VerificationOptions, VerificationTarget
from model_verifier.url_safety import validate_public_base_url


def normalize_gateway_url(base_url: str, endpoint: str) -> str:
    clean_base = (base_url or "").strip().rstrip("/")
    if clean_base.endswith("/v1"):
        clean_base = clean_base[:-3].rstrip("/")
    clean_endpoint = "/" + endpoint.lstrip("/")
    return clean_base + clean_endpoint



def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 12:
        return "***"
    return value[:6] + "..." + value[-4:]


def auth_headers(api_key: str) -> dict[str, str]:
    return {"Authorization": "Bearer " + api_key}


def target_auth_headers(target: VerificationTarget) -> dict[str, str]:
    return auth_headers(target.api_key)


def anthropic_auth_headers(target: VerificationTarget) -> dict[str, str]:
    # Native Anthropic Messages API authenticates via `x-api-key`. Keep the
    # `Authorization: Bearer` header too so Anthropic-compatible gateways that
    # expect a bearer token continue to work.
    return {
        **target_auth_headers(target),
        "x-api-key": target.api_key,
        "anthropic-version": "2023-06-01",
    }


def build_chat_payload(model_name: str, prompt: str, stream: bool = False) -> dict:
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": MODEL_VERIFICATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": MODEL_VERIFICATION_MAX_OUTPUT_TOKENS,
        "stream": stream,
    }
    if stream:
        payload["stream_options"] = {"include_usage": True}
    return payload


def build_anthropic_payload(model_name: str, prompt: str, stream: bool = False) -> dict:
    return {
        "model": model_name,
        "system": MODEL_VERIFICATION_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": MODEL_VERIFICATION_MAX_OUTPUT_TOKENS,
        "stream": stream,
    }


def response_snippet(text: str, limit: int = 240) -> str:
    compact = " ".join((text or "").strip().split())
    if not compact:
        return ""
    return compact[:limit] + ("..." if len(compact) > limit else "")


def parse_streaming_chat_completion(text: str, status_code: int) -> tuple[str, str, bool, str]:
    data_lines = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("data:"):
            data_lines.append(stripped.removeprefix("data:").strip())
    if not data_lines:
        return "", "", False, ""
    chunks = []
    reasoning_chunks = []
    parsed_any = False
    upstream_model = ""
    for item in data_lines:
        if not item or item == "[DONE]":
            continue
        try:
            data = json.loads(item)
        except ValueError:
            continue
        parsed_any = True
        if not upstream_model and data.get("model"):
            upstream_model = str(data.get("model") or "")
        for choice in data.get("choices") or []:
            content = extract_openai_choice_text(choice)
            reasoning = extract_openai_reasoning_text(choice)
            if content and content != reasoning:
                chunks.append(content)
            elif content:
                reasoning_chunks.append(content)
            elif reasoning:
                reasoning_chunks.append(reasoning)
    if chunks:
        return "".join(chunks), "", True, upstream_model
    if reasoning_chunks:
        return "".join(reasoning_chunks), "", True, upstream_model
    detail = f"网关流式响应缺少模型输出（HTTP {status_code}）"
    snippet = response_snippet(text)
    if snippet:
        detail += f"：{snippet}"
    if not parsed_any:
        detail = f"网关返回不可解析的流式响应（HTTP {status_code}）"
        if snippet:
            detail += f"：{snippet}"
    return "", detail, True, upstream_model


def parse_chat_completion(res: httpx.Response) -> tuple[str, str, str]:
    snippet = response_snippet(res.text)
    try:
        data = res.json()
    except ValueError:
        answer, error, parsed_stream, upstream_model = parse_streaming_chat_completion(res.text, res.status_code)
        if parsed_stream:
            return answer, error, upstream_model
        detail = f"网关返回非 JSON 响应（HTTP {res.status_code}）"
        if snippet:
            detail += f"：{snippet}"
        return "", detail, ""
    choices = data.get("choices") or [{}]
    upstream_model = str(data.get("model") or "")
    answer = extract_openai_choice_text(choices[0])
    if not answer:
        detail = f"网关响应缺少模型输出（HTTP {res.status_code}）"
        if snippet:
            detail += f"：{snippet}"
        return "", detail, upstream_model
    return answer, "", upstream_model


def parse_anthropic_stream_completion(text: str, status_code: int) -> tuple[str, str, str]:
    chunks = []
    thinking_chunks = []
    upstream_model = ""
    for block in (text or "").split("\n\n"):
        payload = ""
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("data:"):
                payload = stripped.removeprefix("data:").strip()
        if not payload:
            continue
        try:
            data = json.loads(payload)
        except ValueError:
            continue
        if not upstream_model and isinstance(data.get("message"), dict):
            upstream_model = str(data["message"].get("model") or "")
        delta = data.get("delta")
        if isinstance(delta, dict):
            if delta.get("text"):
                chunks.append(str(delta.get("text") or ""))
            if delta.get("thinking"):
                thinking_chunks.append(str(delta.get("thinking") or ""))
    if chunks:
        return "".join(chunks), "", upstream_model
    if thinking_chunks:
        return "".join(thinking_chunks), "", upstream_model
    detail = f"网关流式响应缺少模型输出（HTTP {status_code}）"
    snippet = response_snippet(text)
    if snippet:
        detail += f"：{snippet}"
    return "", detail, upstream_model


def parse_anthropic_message_completion(res: httpx.Response) -> tuple[str, str, str]:
    snippet = response_snippet(res.text)
    try:
        data = res.json()
    except ValueError:
        return parse_anthropic_stream_completion(res.text, res.status_code)
    content = data.get("content") if isinstance(data, dict) else []
    answer = "".join(
        str(item.get("text", ""))
        for item in content
        if isinstance(item, dict) and item.get("type") == "text"
    )
    upstream_model = str(data.get("model") or "") if isinstance(data, dict) else ""
    if not answer:
        detail = f"网关响应缺少模型输出（HTTP {res.status_code}）"
        if snippet:
            detail += f"：{snippet}"
        return "", detail, upstream_model
    return answer, "", upstream_model


def should_retry_with_explicit_stream(error: str) -> bool:
    return error.startswith("网关流式响应缺少模型输出")


def call_model(target: VerificationTarget, prompt: str, options: VerificationOptions, provider_mode: str | None = None) -> ModelCallResult:
    effective_mode = provider_mode or select_effective_provider_mode(options.provider_mode, target.model)
    started = time.time()
    try:
        with httpx.Client(timeout=options.timeout_seconds) as client:
            if effective_mode == "anthropic":
                headers = anthropic_auth_headers(target)
                url = normalize_gateway_url(target.base_url, "/v1/messages")
                res = client.post(url, headers=headers, json=build_anthropic_payload(target.model, prompt))
                res.raise_for_status()
                answer, error, upstream_model = parse_anthropic_message_completion(res)
                if error and should_retry_with_explicit_stream(error):
                    res = client.post(url, headers=headers, json=build_anthropic_payload(target.model, prompt, stream=True))
                    res.raise_for_status()
                    answer, error, upstream_model = parse_anthropic_message_completion(res)
                return ModelCallResult(answer, int((time.time() - started) * 1000), error, upstream_model)
            url = normalize_gateway_url(target.base_url, "/v1/chat/completions")
            # Default to streaming mode for OpenAI-compatible gateways (including Router ByNara)
            # Streaming properly captures reasoning deltas (e.g. gpt-5.6-luna) and avoids gateway timeouts
            try:
                res = client.post(url, headers=target_auth_headers(target), json=build_chat_payload(target.model, prompt, stream=True))
                res.raise_for_status()
                answer, error, upstream_model = parse_chat_completion(res)
                if answer and not error:
                    return ModelCallResult(answer, int((time.time() - started) * 1000), "", upstream_model)
            except Exception:
                pass
            res = client.post(url, headers=target_auth_headers(target), json=build_chat_payload(target.model, prompt, stream=False))
            res.raise_for_status()
            answer, error, upstream_model = parse_chat_completion(res)
            if error and should_retry_with_explicit_stream(error):
                res = client.post(url, headers=target_auth_headers(target), json=build_chat_payload(target.model, prompt, stream=True))
                res.raise_for_status()
                answer, error, upstream_model = parse_chat_completion(res)
            return ModelCallResult(answer, int((time.time() - started) * 1000), error, upstream_model)
    except Exception as exc:
        return ModelCallResult("", int((time.time() - started) * 1000), str(exc), "")


def run_protocol_verification(target: VerificationTarget, options: VerificationOptions) -> dict:
    effective_mode = select_effective_provider_mode(options.provider_mode, target.model)
    checks = []
    prompt = '只输出 JSON：{"status":"ok","n":3}，不要输出其他文字。'
    try:
        with httpx.Client(timeout=options.timeout_seconds) as client:
            if effective_mode == "anthropic":
                headers = anthropic_auth_headers(target)
                url = normalize_gateway_url(target.base_url, "/v1/messages")
                non_stream = client.post(url, headers=headers, json=build_anthropic_payload(target.model, prompt))
                checks.append(parse_anthropic_message_response(non_stream, target.model))
                stream = client.post(url, headers=headers, json=build_anthropic_payload(target.model, prompt, stream=True))
                checks.append(parse_anthropic_stream_response(stream, target.model))
                return summarize_protocol_report("anthropic", checks)
            url = normalize_gateway_url(target.base_url, "/v1/chat/completions")
            non_stream = client.post(url, headers=target_auth_headers(target), json=build_chat_payload(target.model, prompt))
            checks.append(parse_openai_chat_response(non_stream, target.model))
            stream = client.post(url, headers=target_auth_headers(target), json=build_chat_payload(target.model, prompt, stream=True))
            checks.append(parse_openai_stream_response(stream, target.model))
            return summarize_protocol_report("openai", checks)
    except Exception as exc:
        return {
            "provider_guess": effective_mode,
            "protocol_score": 0,
            "usage_score": 0,
            "observed_model": "",
            "checks": [],
            "risk_signals": [f"协议探针调用失败：{exc}"],
        }


def fetch_model_ids(base_url: str, api_key: str, timeout_seconds: float = 30) -> dict:
    normalized = validate_public_base_url(base_url)
    url = normalize_gateway_url(normalized, "/v1/models")
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            res = client.get(url, headers=auth_headers(api_key))
            res.raise_for_status()
            data = res.json()
    except Exception as exc:
        raise ValueError(f"无法获取模型列表：{exc}") from exc
    models = data.get("data", [])
    if not isinstance(models, list):
        raise ValueError("无法获取模型列表：网关返回格式不是 OpenAI 兼容模型列表")
    model_ids = sorted({
        str(item.get("id")).strip()
        for item in models
        if isinstance(item, dict) and item.get("id") and is_probably_chat_model_id(str(item.get("id")))
    })
    if not model_ids:
        raise ValueError("无法获取模型列表：没有可用于模型验真的对话模型")
    return {
        "base_url": normalized,
        "api_key_masked": mask_secret(api_key.strip()),
        "items": model_ids,
    }

