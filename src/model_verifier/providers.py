import json
from dataclasses import dataclass


PROVIDER_MODES = {"auto", "openai", "anthropic"}


@dataclass(frozen=True)
class ProviderCheck:
    name: str
    provider: str
    status: str
    score: int
    signals: list[str]
    warnings: list[str]
    observed_model: str = ""
    usage: dict | None = None
    text_sample: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "status": self.status,
            "score": self.score,
            "signals": self.signals,
            "warnings": self.warnings,
            "observed_model": self.observed_model,
            "usage": self.usage or {},
            "text_sample": self.text_sample,
        }


def response_snippet(text: str, limit: int = 240) -> str:
    compact = " ".join((text or "").strip().split())
    return compact[:limit] + ("..." if len(compact) > limit else "")


def json_from_response(res) -> tuple[dict, str]:
    try:
        data = res.json()
    except ValueError:
        return {}, f"非 JSON 响应：{response_snippet(res.text)}"
    if not isinstance(data, dict):
        return {}, "JSON 响应不是对象"
    return data, ""


def status_from_score(score: int) -> str:
    if score >= 90:
        return "pass"
    if score > 0:
        return "warn"
    return "fail"


def normalize_usage(usage) -> dict:
    if not isinstance(usage, dict):
        return {}
    return {
        str(key): value
        for key, value in usage.items()
        if isinstance(value, int | float)
    }


def calculate_usage_score(usage: dict) -> int:
    if not usage:
        return 50
    numeric_values = [value for value in usage.values() if isinstance(value, int | float)]
    if not numeric_values:
        return 50
    if any(value < 0 for value in numeric_values):
        return 0
    total = usage.get("total_tokens")
    if total is not None:
        parts = [usage.get("prompt_tokens"), usage.get("completion_tokens")]
        if all(isinstance(item, int | float) for item in parts) and total < sum(parts):
            return 40
    return 100


def select_effective_provider_mode(provider_mode: str, model_name: str) -> str:
    if provider_mode in {"openai", "anthropic"}:
        return provider_mode
    normalized = (model_name or "").lower()
    if "claude" in normalized:
        return "anthropic"
    return "openai"


def extract_openai_reasoning_text(choice: dict) -> str:
    if not isinstance(choice, dict):
        return ""
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    delta = choice.get("delta") if isinstance(choice.get("delta"), dict) else {}
    reasoning = (
        message.get("reasoning_content")
        or delta.get("reasoning_content")
        or message.get("reasoning")
        or delta.get("reasoning")
        or message.get("thought")
        or delta.get("thought")
        or ""
    )
    if isinstance(reasoning, list):
        return "".join(str(item.get("text", "")) for item in reasoning if isinstance(item, dict))
    return str(reasoning or "")


def extract_openai_choice_text(choice: dict) -> str:
    if not isinstance(choice, dict):
        return ""
    message = choice.get("message") if isinstance(choice.get("message"), dict) else {}
    delta = choice.get("delta") if isinstance(choice.get("delta"), dict) else {}
    content = message.get("content") or delta.get("content") or choice.get("text") or ""
    if isinstance(content, list):
        joined = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
        if joined:
            return joined
    if str(content or "").strip():
        return str(content)
    # Fallback to reasoning/thought if no standard content is available
    return extract_openai_reasoning_text(choice)



def model_matches(claimed_model: str, observed_model: str) -> bool:
    return bool(claimed_model and observed_model and claimed_model.lower() == observed_model.lower())


def parse_openai_chat_response(res, claimed_model: str) -> ProviderCheck:
    data, error = json_from_response(res)
    if error:
        return ProviderCheck("non_stream", "openai", "fail", 0, [], [error])
    choices = data.get("choices") if isinstance(data.get("choices"), list) else []
    text = extract_openai_choice_text(choices[0]) if choices else ""
    usage = normalize_usage(data.get("usage"))
    observed_model = str(data.get("model") or "")
    signals = []
    warnings = []
    score = 0
    if text:
        signals.append("choices_message_content")
        score += 45
    else:
        warnings.append("缺少 choices[].message.content")
    if observed_model:
        signals.append("model_echo")
        score += 20 if model_matches(claimed_model, observed_model) else 10
        if not model_matches(claimed_model, observed_model):
            warnings.append(f"响应模型 {observed_model} 与请求模型 {claimed_model} 不一致")
    else:
        warnings.append("缺少 model 字段")
    usage_score = calculate_usage_score(usage)
    if usage:
        signals.append("usage")
        score += 35 if usage_score == 100 else 15
    else:
        warnings.append("缺少 usage 字段")
        score += 10
    score = min(100, score)
    return ProviderCheck("non_stream", "openai", status_from_score(score), score, signals, warnings, observed_model, usage, text)


def parse_openai_stream_response(res, claimed_model: str) -> ProviderCheck:
    data_lines = []
    for line in (res.text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("data:"):
            data_lines.append(stripped.removeprefix("data:").strip())
    if not data_lines:
        return ProviderCheck("stream", "openai", "fail", 0, [], ["缺少 data: SSE 分块"])
    chunks = []
    usage = {}
    observed_model = ""
    saw_done = False
    parsed_count = 0
    saw_reasoning = False
    for item in data_lines:
        if item == "[DONE]":
            saw_done = True
            continue
        if not item:
            continue
        try:
            data = json.loads(item)
        except ValueError:
            continue
        parsed_count += 1
        if not observed_model and data.get("model"):
            observed_model = str(data.get("model") or "")
        usage = normalize_usage(data.get("usage")) or usage
        for choice in data.get("choices") or []:
            text = extract_openai_choice_text(choice)
            reasoning = extract_openai_reasoning_text(choice)
            if reasoning:
                saw_reasoning = True
            if text:
                chunks.append(text)
    signals = []
    warnings = []
    score = 0
    if parsed_count:
        signals.append("data_chunks")
        score += 30
    if chunks:
        signals.append("delta_content")
        score += 35
    else:
        warnings.append("缺少 delta content")
    if saw_reasoning:
        signals.append("reasoning_delta")
        score += 10
    if saw_done:
        signals.append("stream_done")
        score += 25
    else:
        warnings.append("缺少 stream_done")
    if observed_model:
        signals.append("model_echo")
        score += 10 if model_matches(claimed_model, observed_model) else 5
        if not model_matches(claimed_model, observed_model):
            warnings.append(f"响应模型 {observed_model} 与请求模型 {claimed_model} 不一致")
    return ProviderCheck("stream", "openai", status_from_score(score), min(100, score), signals, warnings, observed_model, usage, "".join(chunks))


def anthropic_text_from_content(content) -> str:
    if not isinstance(content, list):
        return ""
    return "".join(
        str(item.get("text", ""))
        for item in content
        if isinstance(item, dict) and item.get("type") == "text"
    )


def parse_anthropic_message_response(res, claimed_model: str) -> ProviderCheck:
    data, error = json_from_response(res)
    if error:
        return ProviderCheck("non_stream", "anthropic", "fail", 0, [], [error])
    text = anthropic_text_from_content(data.get("content"))
    usage = normalize_usage(data.get("usage"))
    observed_model = str(data.get("model") or "")
    signals = []
    warnings = []
    score = 0
    if text:
        signals.append("content_text_block")
        score += 45
    else:
        warnings.append("缺少 content[] text block")
    if data.get("stop_reason"):
        signals.append("stop_reason")
        score += 10
    if observed_model:
        signals.append("model_echo")
        score += 20 if model_matches(claimed_model, observed_model) else 10
        if not model_matches(claimed_model, observed_model):
            warnings.append(f"响应模型 {observed_model} 与请求模型 {claimed_model} 不一致")
    else:
        warnings.append("缺少 model 字段")
    usage_score = calculate_usage_score(usage)
    if usage:
        signals.append("usage")
        score += 25 if usage_score == 100 else 10
    else:
        warnings.append("缺少 usage 字段")
    score = min(100, score)
    return ProviderCheck("non_stream", "anthropic", status_from_score(score), score, signals, warnings, observed_model, usage, text)


def parse_sse_events(text: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in (text or "").split("\n\n"):
        event_name = ""
        payload = ""
        for line in block.splitlines():
            stripped = line.strip()
            if stripped.startswith("event:"):
                event_name = stripped.removeprefix("event:").strip()
            elif stripped.startswith("data:"):
                payload = stripped.removeprefix("data:").strip()
        if not payload:
            continue
        try:
            data = json.loads(payload)
        except ValueError:
            continue
        events.append((event_name or str(data.get("type") or ""), data))
    return events


def parse_anthropic_stream_response(res, claimed_model: str) -> ProviderCheck:
    events = parse_sse_events(res.text)
    if not events:
        return ProviderCheck("stream", "anthropic", "fail", 0, [], ["缺少 Anthropic SSE 事件"])
    event_names = [name for name, _ in events]
    chunks = []
    observed_model = ""
    usage = {}
    for _, data in events:
        if not observed_model and isinstance(data.get("message"), dict):
            observed_model = str(data["message"].get("model") or "")
        delta = data.get("delta")
        if isinstance(delta, dict) and delta.get("text"):
            chunks.append(str(delta.get("text") or ""))
        if isinstance(data.get("usage"), dict):
            usage = normalize_usage(data.get("usage"))
    signals = []
    warnings = []
    score = 0
    for expected in ("message_start", "content_block_delta", "message_stop"):
        if expected in event_names:
            signals.append(expected)
            score += 25
        else:
            warnings.append(f"缺少 {expected}")
    if chunks:
        signals.append("text_delta")
        score += 15
    else:
        warnings.append("缺少 text_delta")
    if observed_model:
        signals.append("model_echo")
        score += 10 if model_matches(claimed_model, observed_model) else 5
        if not model_matches(claimed_model, observed_model):
            warnings.append(f"响应模型 {observed_model} 与请求模型 {claimed_model} 不一致")
    return ProviderCheck("stream", "anthropic", status_from_score(score), min(100, score), signals, warnings, observed_model, usage, "".join(chunks))


def summarize_protocol_report(provider_guess: str, checks: list[ProviderCheck]) -> dict:
    if not checks:
        return {
            "provider_guess": provider_guess,
            "protocol_score": 0,
            "usage_score": 50,
            "observed_model": "",
            "checks": [],
            "risk_signals": ["协议检测未执行"],
        }
    protocol_score = round(sum(check.score for check in checks) / len(checks), 2)
    usage_score = round(sum(calculate_usage_score(check.usage or {}) for check in checks) / len(checks), 2)
    observed_model = next((check.observed_model for check in checks if check.observed_model), "")
    risk_signals = []
    for check in checks:
        risk_signals.extend(check.warnings)
    return {
        "provider_guess": provider_guess,
        "protocol_score": protocol_score,
        "usage_score": usage_score,
        "observed_model": observed_model,
        "checks": [check.as_dict() for check in checks],
        "risk_signals": risk_signals,
    }
