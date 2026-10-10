import re
from collections import Counter
from dataclasses import dataclass

from model_verifier.probes import IDENTITY_EVIDENCE_DIMENSIONS, ProbeCase
from model_verifier.profiles import CapabilityProfile, capability_profile_match


DESCRIPTIVE_MODEL_TOKENS = {"official", "model", "models", "api", "apis", "endpoint", "endpoints", "llm"}
MODEL_TOKEN_RE = re.compile(r"[a-z0-9]+")
# Dated snapshot suffix such as "-2025-04-14" (OpenAI) or "-20240620" (Anthropic).
SNAPSHOT_SUFFIX_RE = re.compile(r"-(?:\d{4}-\d{2}-\d{2}|\d{8})$")
IDENTITY_ECHO_DISCLAIMER = "模型身份自述只能作为低可信参考信号，不能单独证明底层模型来源。"


@dataclass(frozen=True)
class CaseScoreResult:
    score: int
    status: str
    signals: list[str]
    matched: list[str]
    missing: list[str]
    forbidden: list[str]
    reason: str
    expected_criteria: list[str]


@dataclass(frozen=True)
class IdentityEchoProvider:
    id: str
    label: str
    aliases: tuple[str, ...]


IDENTITY_ECHO_PROVIDERS = (
    IdentityEchoProvider("openai", "OpenAI", ("openai", "chatgpt", "gpt")),
    IdentityEchoProvider("anthropic", "Anthropic", ("anthropic", "claude")),
    IdentityEchoProvider("google", "Google", ("google", "gemini")),
    IdentityEchoProvider("qwen", "Qwen", ("qwen", "通义", "通义千问", "千问")),
    IdentityEchoProvider("deepseek", "DeepSeek", ("deepseek", "deepseek-ai", "深度求索")),
    IdentityEchoProvider("tencent", "Tencent", ("tencent", "hunyuan", "混元", "腾讯")),
    IdentityEchoProvider("doubao", "Doubao", ("doubao", "豆包", "bytedance", "字节", "火山")),
    IdentityEchoProvider("z-ai", "z-ai", ("z-ai", "zai", "zhipu", "智谱", "glm")),
    IdentityEchoProvider("baidu", "Baidu", ("baidu", "ernie", "文心", "百度")),
    IdentityEchoProvider("xai", "xAI", ("xai", "x.ai", "grok")),
    IdentityEchoProvider("moonshot", "Moonshot", ("moonshot", "kimi", "月之暗面")),
    IdentityEchoProvider("meta", "Meta", ("meta", "llama")),
    IdentityEchoProvider("mistral", "Mistral", ("mistral", "mixtral")),
)
IDENTITY_ECHO_PROVIDER_BY_ID = {provider.id: provider for provider in IDENTITY_ECHO_PROVIDERS}
IDENTITY_ECHO_UNKNOWN_LABELS = {
    "self": "自指",
    "cross_provider_confusion": "跨厂混淆",
    "refusal": "拒答",
    "unknown": "无身份",
    "not_tested": "未测试",
}


def unique_items(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def comparable_literal(value: str) -> str:
    return "".join(value.lower().split())


def strongest_literal_hits(items: list[str]) -> list[str]:
    unique = unique_items(items)
    result = []
    for item in unique:
        normalized = comparable_literal(item)
        if any(
            normalized != comparable_literal(other) and normalized in comparable_literal(other)
            for other in unique
        ):
            continue
        if normalized in {comparable_literal(existing) for existing in result}:
            continue
        result.append(item)
    return result


def format_literal_criteria(items: tuple[str, ...]) -> str:
    return " / ".join(strongest_literal_hits(list(items)))


def expected_criteria_for_case(case: ProbeCase) -> list[str]:
    criteria = []
    if case.expected_all:
        criteria.append("必须包含：" + format_literal_criteria(case.expected_all))
    if case.expected_any:
        criteria.append("至少命中一项：" + format_literal_criteria(case.expected_any))
    if case.forbidden_any:
        criteria.append("不能包含：" + format_literal_criteria(case.forbidden_any))
    return criteria or ["未配置显式内容规则，仅记录响应、延迟和稳定性。"]


def score_case(case: ProbeCase, answer: str, error: str) -> CaseScoreResult:
    expected_criteria = expected_criteria_for_case(case)
    if error:
        return CaseScoreResult(0, "error", ["调用失败"], [], [], [], "调用失败，无法根据回答评分", expected_criteria)
    normalized = answer.lower()
    matched_all = [item for item in case.expected_all if item.lower() in normalized]
    missing_all = [item for item in case.expected_all if item.lower() not in normalized]
    expected_hits = [item for item in case.expected_any if item.lower() in normalized]
    forbidden_hits = [item for item in case.forbidden_any if item.lower() in normalized]
    matched = strongest_literal_hits(matched_all + expected_hits)
    missing = list(missing_all)
    signals = []
    if missing_all:
        signals.extend([f"缺少必要表现：{item}" for item in missing_all])
    if case.expected_any and not expected_hits:
        missing.append("至少命中一项：" + " / ".join(case.expected_any))
        signals.append("未命中预期行为")
    if forbidden_hits:
        return CaseScoreResult(0, "suspicious", [f"命中禁用表达：{item}" for item in forbidden_hits], matched, missing, list(forbidden_hits), "回答命中禁用表达", expected_criteria)
    if missing:
        return CaseScoreResult(35, "suspicious", signals, matched, missing, [], "回答缺少必须要素", expected_criteria)
    return CaseScoreResult(100, "passed", ["命中预期行为"], matched, [], [], "回答命中预期行为", expected_criteria)


def evidence_role_for_dimension(dimension: str) -> str:
    return "identity" if dimension in IDENTITY_EVIDENCE_DIMENSIONS else "reference"


def model_label_parts(label: str) -> list[str]:
    cleaned = (label or "").strip()
    parts = [cleaned]
    # Drop a leading "provider/" namespace, keeping the model name after the slash.
    if "/" in cleaned:
        parts.append(cleaned.rsplit("/", 1)[-1])
    # Drop a trailing ":tag" (e.g. ":free", ":latest") so models are compared by
    # base name instead of matching on a shared tag alone.
    for variant in list(parts):
        if ":" in variant:
            parts.append(variant.rsplit(":", 1)[0])
    # Drop a dated snapshot suffix so an echo like "gpt-4.1-2025-04-14" still
    # matches the requested "gpt-4.1".
    for variant in list(parts):
        stripped = SNAPSHOT_SUFFIX_RE.sub("", variant)
        if stripped and stripped != variant:
            parts.append(stripped)
    return [part for part in parts if part]


def model_label_tokens(label: str, drop_descriptive: bool = False) -> tuple[str, ...]:
    tokens = MODEL_TOKEN_RE.findall(label.lower())
    if drop_descriptive:
        tokens = [token for token in tokens if token not in DESCRIPTIVE_MODEL_TOKENS]
    return tuple(tokens)


def model_labels_match(claimed_model: str, actual_model: str) -> bool:
    claimed_candidates = {
        model_label_tokens(part, drop_descriptive=True)
        for part in model_label_parts(claimed_model)
    }
    actual_candidates = {
        model_label_tokens(part)
        for part in model_label_parts(actual_model)
    }
    return any(claimed and actual and claimed == actual for claimed in claimed_candidates for actual in actual_candidates)


def identity_echo_provider_label(provider_id: str) -> str:
    provider = IDENTITY_ECHO_PROVIDER_BY_ID.get(provider_id)
    return provider.label if provider else provider_id


def identity_alias_matches(text: str, alias: str) -> bool:
    if not alias:
        return False
    if re.search(r"[a-z0-9]", alias):
        return re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text) is not None
    return alias in text


def identity_echo_provider_for_model(model_name: str) -> str:
    normalized = (model_name or "").lower()
    if not normalized:
        return ""
    profile, rule = capability_profile_match(normalized)
    if rule and rule.provider != "generic":
        return rule.provider
    for provider in IDENTITY_ECHO_PROVIDERS:
        if any(identity_alias_matches(normalized, alias) for alias in provider.aliases):
            return provider.id
    if profile.id in {"compact", "frontier", "advanced", "reasoning"} and normalized.startswith(("gpt-", "o1", "o3")):
        return "openai"
    return ""


def identity_echo_alias_hits(answer: str, provider: IdentityEchoProvider) -> list[tuple[int, str]]:
    normalized = (answer or "").lower()
    hits: list[tuple[int, str]] = []
    for alias in provider.aliases:
        if re.search(r"[a-z0-9]", alias):
            match = re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized)
            if match:
                hits.append((match.start(), answer[match.start():match.end()]))
        else:
            index = normalized.find(alias.lower())
            if index >= 0:
                hits.append((index, answer[index:index + len(alias)]))
    return hits


def detected_identity_echo_providers(answer: str) -> tuple[list[str], list[str]]:
    provider_ids = []
    alias_hits: list[tuple[int, str]] = []
    for provider in IDENTITY_ECHO_PROVIDERS:
        hits = identity_echo_alias_hits(answer, provider)
        if hits:
            provider_ids.append(provider.id)
            alias_hits.extend(hits)
    matched_aliases = [alias for _, alias in sorted(alias_hits, key=lambda item: item[0])]
    return provider_ids, unique_items(matched_aliases)


def answer_looks_like_identity_refusal(answer: str) -> bool:
    normalized = (answer or "").lower()
    refusal_markers = (
        "无法确认",
        "不能确认",
        "无法提供",
        "不能提供",
        "无法回答",
        "不能回答",
        "不清楚",
        "不知道",
        "超出我",
        "can't confirm",
        "cannot confirm",
        "can't determine",
        "cannot determine",
        "do not know",
        "don't know",
        "not have access",
    )
    return any(marker in normalized for marker in refusal_markers)


def classify_identity_echo(answer: str, claimed_model: str) -> dict:
    claimed_provider = identity_echo_provider_for_model(claimed_model)
    observed_providers, matched_aliases = detected_identity_echo_providers(answer)
    observed_provider = observed_providers[0] if observed_providers else ""
    if observed_providers and claimed_provider and any(provider != claimed_provider for provider in observed_providers):
        category = "cross_provider_confusion"
    elif observed_providers and claimed_provider in observed_providers:
        category = "self"
    elif answer_looks_like_identity_refusal(answer):
        category = "refusal"
    else:
        category = "unknown"
    return {
        "category": category,
        "label": IDENTITY_ECHO_UNKNOWN_LABELS[category],
        "claimed_provider": claimed_provider,
        "claimed_provider_label": identity_echo_provider_label(claimed_provider) if claimed_provider else "",
        "observed_provider": observed_provider,
        "observed_provider_label": identity_echo_provider_label(observed_provider) if observed_provider else "",
        "matched_aliases": matched_aliases,
        "disclaimer": IDENTITY_ECHO_DISCLAIMER,
    }


def summarize_identity_echo(case_results: list[dict], claimed_model: str) -> dict:
    echo_results = [case["identity_echo"] for case in case_results if case.get("identity_echo")]
    claimed_provider = identity_echo_provider_for_model(claimed_model)
    if not echo_results:
        return {
            "status": "not_tested",
            "label": IDENTITY_ECHO_UNKNOWN_LABELS["not_tested"],
            "disclaimer": IDENTITY_ECHO_DISCLAIMER,
            "total_cases": 0,
            "self_count": 0,
            "cross_provider_count": 0,
            "refusal_count": 0,
            "unknown_count": 0,
            "claimed_provider": claimed_provider,
            "claimed_provider_label": identity_echo_provider_label(claimed_provider) if claimed_provider else "",
            "observed_providers": [],
        }
    counts = Counter(item["category"] for item in echo_results)
    if counts["cross_provider_confusion"]:
        status = "cross_provider_confusion"
    elif counts["self"]:
        status = "self"
    elif counts["refusal"]:
        status = "refusal"
    else:
        status = "unknown"
    observed_counts = Counter(
        item["observed_provider"]
        for item in echo_results
        if item.get("observed_provider") and item["observed_provider"] != claimed_provider
    )
    return {
        "status": status,
        "label": IDENTITY_ECHO_UNKNOWN_LABELS[status],
        "disclaimer": IDENTITY_ECHO_DISCLAIMER,
        "total_cases": len(echo_results),
        "self_count": counts["self"],
        "cross_provider_count": counts["cross_provider_confusion"],
        "refusal_count": counts["refusal"],
        "unknown_count": counts["unknown"],
        "claimed_provider": claimed_provider,
        "claimed_provider_label": identity_echo_provider_label(claimed_provider) if claimed_provider else "",
        "observed_providers": [
            {"provider": provider, "label": identity_echo_provider_label(provider), "count": count}
            for provider, count in observed_counts.most_common()
        ],
    }


def summarize_report(identity_cases: list[dict], reference_cases: list[dict]) -> tuple[str, str, list[str], list[str], float]:
    if not identity_cases or all(case["status"] == "error" for case in identity_cases):
        return "inconclusive", "证据不足，建议复核", ["核心检测项调用失败"], ["检查 API Key、网关状态和模型名称后重试。"], 0
    scored_identity_cases = [case for case in identity_cases if case["status"] != "error"]
    if not scored_identity_cases:
        return "inconclusive", "证据不足，建议复核", ["核心检测项调用失败"], ["检查 API Key、网关状态和模型名称后重试。"], 0
    identity_score = round(sum(case["score"] for case in scored_identity_cases) / len(scored_identity_cases), 2)
    suspicious = [case for case in scored_identity_cases if case["status"] == "suspicious"]
    errors = [case for case in identity_cases if case["status"] == "error"]
    reference_errors = [case for case in reference_cases if case["status"] == "error"]
    signals: list[str] = []
    recommendations = ["黑盒检测不能证明真实底层模型，建议结合供应商证明继续复核。"]
    if suspicious:
        signals.append("核心能力或能力指纹存在异常")
    if errors:
        signals.append("部分核心检测项调用失败")
    if reference_errors:
        signals.append("部分参考项调用受限，未纳入检测结论")
    if identity_score < 60:
        return "high", "疑似隐藏映射或能力不符", signals or ["核心检测项不足"], recommendations, identity_score
    if identity_score < 85 or errors:
        return "medium", "存在可疑迹象", signals or ["部分核心探针表现异常"], recommendations, identity_score
    return "low", "未发现明显异常", signals or ["核心检测项未发现明显不符"], recommendations, identity_score


def weighted_identity_score(profile: CapabilityProfile, dimension_scores: dict[str, float]) -> float:
    available_weights = {
        dimension: weight
        for dimension, weight in profile.dimension_weights.items()
        if dimension in dimension_scores and dimension in IDENTITY_EVIDENCE_DIMENSIONS
    }
    if not available_weights:
        identity_scores = [score for dimension, score in dimension_scores.items() if dimension in IDENTITY_EVIDENCE_DIMENSIONS]
        if not identity_scores:
            return 0
        return round(sum(identity_scores) / len(identity_scores), 2)
    total_weight = sum(available_weights.values())
    if total_weight <= 0:
        return 0
    score = sum(dimension_scores[dimension] * weight for dimension, weight in available_weights.items()) / total_weight
    return round(score, 2)


def assess_capability_profile(profile: CapabilityProfile, identity_score: float, dimension_scores: dict[str, float]) -> dict:
    missing_dimensions = [dimension for dimension in profile.required_dimensions if dimension not in dimension_scores]
    weak_dimensions = [
        {"dimension": dimension, "score": dimension_scores.get(dimension, 0), "minimum": minimum}
        for dimension, minimum in profile.minimum_dimension_scores.items()
        if dimension_scores.get(dimension, 0) < minimum
    ]
    score_below_minimum = identity_score < profile.minimum_identity_score
    if missing_dimensions:
        status = "incomplete"
        reason = "缺少该档位要求的检测维度"
    elif weak_dimensions or score_below_minimum:
        status = "below_expected"
        reason = "表现低于该模型档位参考基线"
    else:
        status = "matched"
        reason = f"表现达到{profile.label}参考基线"
    return {
        "status": status,
        "reason": reason,
        "missing_dimensions": missing_dimensions,
        "weak_dimensions": weak_dimensions,
        "minimum_identity_score": profile.minimum_identity_score,
        "dimension_weights": dict(profile.dimension_weights),
        "weighted_identity_score": identity_score,
    }


def clamp_score(value: float) -> float:
    return max(0, min(100, round(value, 2)))


def aggregate_universal_verdict(
    risk_level: str,
    capability_score: float,
    protocol_score: float,
    usage_score: float,
    model_mismatch: bool,
    all_core_calls_failed: bool,
    risk_signals: list[str],
) -> dict:
    if all_core_calls_failed and protocol_score == 0:
        return {
            "verdict": "unreachable",
            "confidence_score": 0,
            "risk_signals": list(dict.fromkeys(risk_signals or ["核心检测项调用失败"])),
        }
    if model_mismatch or risk_level == "high":
        # De-emphasize protocol/usage relative to capability, but normalize by the
        # weight sum so confidence stays on the same 0-100 scale as the normal
        # branch below (otherwise this branch would max out at 80, not 100).
        confidence = clamp_score((protocol_score * 0.25 + capability_score * 0.45 + usage_score * 0.1) / 0.8)
        return {
            "verdict": "substituted" if model_mismatch else "suspicious",
            "confidence_score": confidence,
            "risk_signals": list(dict.fromkeys(risk_signals)),
        }
    confidence = clamp_score(protocol_score * 0.4 + capability_score * 0.45 + usage_score * 0.15)
    if protocol_score >= 90 and capability_score >= 85 and risk_level == "low":
        verdict = "verified"
    elif protocol_score >= 70 and capability_score >= 70 and risk_level in {"low", "medium"}:
        verdict = "compatible"
    else:
        verdict = "suspicious"
    if protocol_score < 70:
        risk_signals = ["协议指纹存在异常"] + risk_signals
    if usage_score < 70:
        risk_signals = ["用量回传存在异常"] + risk_signals
    return {
        "verdict": verdict,
        "confidence_score": confidence,
        "risk_signals": list(dict.fromkeys(risk_signals)),
    }
