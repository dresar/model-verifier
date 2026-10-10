import re
from dataclasses import dataclass

from model_verifier.probes import (
    CAPABILITY_FINGERPRINT_CASES,
    MODEL_VERIFICATION_MAX_OUTPUT_TOKENS,
    MODEL_VERIFICATION_SYSTEM_PROMPT,
    PROBE_CASES,
    PROFILE_EXTRA_CASES,
    ProbeCase,
)


@dataclass(frozen=True)
class CapabilityProfile:
    id: str
    label: str
    description: str
    model_markers: tuple[str, ...]
    required_dimensions: tuple[str, ...]
    minimum_identity_score: int
    minimum_dimension_scores: dict[str, int]
    dimension_weights: dict[str, float]
    extra_probe_case_ids: tuple[str, ...] = ()
    requires_fingerprint: bool = False


@dataclass(frozen=True)
class ModelProfileRule:
    profile_id: str
    provider: str
    match_type: str
    pattern: str
    label: str
    priority: int


FRONTIER_MODEL_MARKERS = (
    "gpt-5",
    "gpt-4.5",
    "claude-3-5-sonnet",
    "claude-3.5-sonnet",
    "claude-3-7-sonnet",
    "claude-3.7-sonnet",
    "claude-4",
    "deepseek-reasoner",
    "o1",
    "o3",
)

CAPABILITY_PROFILES = (
    CapabilityProfile(
        id="compact",
        label="轻量模型",
        description="面向低成本或小参数量对话的模型，允许部分高阶能力波动。",
        model_markers=("mini", "small", "lite", "flash", "haiku", "turbo", "fast"),
        required_dimensions=("instruction_following", "reasoning"),
        minimum_identity_score=65,
        minimum_dimension_scores={"instruction_following": 65, "reasoning": 55},
        dimension_weights={"instruction_following": 0.55, "reasoning": 0.25, "stability": 0.2},
    ),
    CapabilityProfile(
        id="frontier",
        label="高阶旗舰模型",
        description="面向高阶推理、代码和复杂指令的模型，需要通过能力指纹核验。",
        model_markers=FRONTIER_MODEL_MARKERS,
        required_dimensions=("instruction_following", "reasoning", "code", "capability_fingerprint"),
        minimum_identity_score=85,
        minimum_dimension_scores={"instruction_following": 85, "reasoning": 80, "code": 75, "capability_fingerprint": 70},
        dimension_weights={"instruction_following": 0.22, "reasoning": 0.28, "code": 0.2, "capability_fingerprint": 0.3},
        extra_probe_case_ids=("reasoning_multi_step", "code_edge_case"),
        requires_fingerprint=True,
    ),
    CapabilityProfile(
        id="reasoning",
        label="推理模型",
        description="面向复杂推理和多步问题的模型，重点评估推理稳定性和能力指纹。",
        model_markers=("deepseek-reasoner", "o1", "o3", "reasoner", "reasoning"),
        required_dimensions=("instruction_following", "reasoning", "capability_fingerprint"),
        minimum_identity_score=82,
        minimum_dimension_scores={"instruction_following": 75, "reasoning": 82, "capability_fingerprint": 65},
        dimension_weights={"instruction_following": 0.16, "reasoning": 0.48, "code": 0.12, "capability_fingerprint": 0.24},
        extra_probe_case_ids=("reasoning_multi_step",),
        requires_fingerprint=True,
    ),
    CapabilityProfile(
        id="code",
        label="代码模型",
        description="面向代码生成、修复和边界条件处理的模型，重点评估代码能力。",
        model_markers=("coder", "code", "codestral", "devstral"),
        required_dimensions=("instruction_following", "reasoning", "code"),
        minimum_identity_score=78,
        minimum_dimension_scores={"instruction_following": 70, "reasoning": 65, "code": 78},
        dimension_weights={"instruction_following": 0.18, "reasoning": 0.18, "code": 0.54, "stability": 0.1},
        extra_probe_case_ids=("code_edge_case",),
    ),
    CapabilityProfile(
        id="advanced",
        label="强通用模型",
        description="面向常规推理、代码和多语言指令的模型，需要稳定通过核心能力探针。",
        model_markers=("gpt-4", "claude-3", "gemini-1.5", "gemini-2", "deepseek-chat", "qwen-max", "qwen-plus"),
        required_dimensions=("instruction_following", "reasoning", "code"),
        minimum_identity_score=80,
        minimum_dimension_scores={"instruction_following": 80, "reasoning": 70, "code": 65},
        dimension_weights={"instruction_following": 0.34, "reasoning": 0.28, "code": 0.22, "stability": 0.16},
    ),
    CapabilityProfile(
        id="standard",
        label="标准通用模型",
        description="面向常规聊天、文本处理和基础推理的模型，按通用能力基线评估。",
        model_markers=("qwen", "kimi", "moonshot", "doubao", "glm", "ernie", "hunyuan", "yi", "baichuan"),
        required_dimensions=("instruction_following", "reasoning"),
        minimum_identity_score=72,
        minimum_dimension_scores={"instruction_following": 70, "reasoning": 60},
        dimension_weights={"instruction_following": 0.44, "reasoning": 0.28, "code": 0.12, "stability": 0.16},
    ),
    CapabilityProfile(
        id="open_source_large",
        label="开源大模型",
        description="面向开源或开放权重的大参数模型，重点评估通用指令、推理和稳定性。",
        model_markers=("llama", "mistral", "mixtral", "command-r", "nemotron"),
        required_dimensions=("instruction_following", "reasoning", "code"),
        minimum_identity_score=74,
        minimum_dimension_scores={"instruction_following": 70, "reasoning": 65, "code": 55},
        dimension_weights={"instruction_following": 0.36, "reasoning": 0.32, "code": 0.16, "stability": 0.16},
    ),
    CapabilityProfile(
        id="unknown",
        label="未知模型",
        description="未匹配到明确能力档位，仅按基础黑盒行为抽检给出参考结果。",
        model_markers=(),
        required_dimensions=(),
        minimum_identity_score=50,
        minimum_dimension_scores={},
        dimension_weights={},
    ),
)
CAPABILITY_PROFILE_BY_ID = {profile.id: profile for profile in CAPABILITY_PROFILES}

MODEL_PROFILE_RULES = (
    ModelProfileRule("compact", "openai", "regex", r"gpt-[\w.-]*mini", "OpenAI mini 系列", 120),
    ModelProfileRule("frontier", "openai", "prefix", "gpt-5", "OpenAI GPT-5 系列", 110),
    ModelProfileRule("frontier", "openai", "prefix", "gpt-4.5", "OpenAI GPT-4.5 系列", 108),
    ModelProfileRule("reasoning", "openai", "regex", r"^o[13]([\w.-]*)?$", "OpenAI 推理系列", 106),
    ModelProfileRule("advanced", "openai", "prefix", "gpt-4", "OpenAI GPT-4 系列", 90),
    ModelProfileRule("compact", "anthropic", "contains", "haiku", "Claude Haiku 轻量系列", 120),
    ModelProfileRule("frontier", "anthropic", "contains", "claude-4", "Claude 4 系列", 110),
    ModelProfileRule("frontier", "anthropic", "regex", r"claude-3[.-][57]-sonnet", "Claude 3.5/3.7 Sonnet 系列", 108),
    ModelProfileRule("advanced", "anthropic", "contains", "claude-3", "Claude 3 系列", 88),
    ModelProfileRule("compact", "google", "contains", "flash", "Gemini Flash 系列", 116),
    ModelProfileRule("advanced", "google", "regex", r"gemini-(1\.5|2)([\w.-]*)?", "Gemini 1.5/2 系列", 86),
    ModelProfileRule("reasoning", "deepseek", "contains", "deepseek-reasoner", "DeepSeek Reasoner", 112),
    ModelProfileRule("advanced", "deepseek", "contains", "deepseek-chat", "DeepSeek Chat", 84),
    ModelProfileRule("code", "qwen", "regex", r"qwen[\w.-]*coder", "Qwen Coder 系列", 118),
    ModelProfileRule("standard", "qwen", "contains", "qwen", "Qwen 通用系列", 78),
    ModelProfileRule("standard", "moonshot", "contains", "kimi", "Kimi 系列", 78),
    ModelProfileRule("standard", "moonshot", "contains", "moonshot", "Moonshot 系列", 78),
    ModelProfileRule("standard", "bytedance", "contains", "doubao", "豆包系列", 78),
    ModelProfileRule("standard", "zhipu", "contains", "glm", "GLM 系列", 76),
    ModelProfileRule("standard", "baidu", "contains", "ernie", "文心 ERNIE 系列", 76),
    ModelProfileRule("standard", "tencent", "contains", "hunyuan", "混元系列", 76),
    ModelProfileRule("standard", "01-ai", "regex", r"(^|[-_.])yi([-.]|$)", "Yi 系列", 74),
    ModelProfileRule("standard", "baichuan", "contains", "baichuan", "百川系列", 74),
    ModelProfileRule("open_source_large", "meta", "contains", "llama", "Llama 系列", 82),
    ModelProfileRule("open_source_large", "mistral", "contains", "mistral", "Mistral 系列", 82),
    ModelProfileRule("open_source_large", "mistral", "contains", "mixtral", "Mixtral 系列", 82),
    ModelProfileRule("open_source_large", "cohere", "contains", "command-r", "Command R 系列", 78),
    ModelProfileRule("open_source_large", "nvidia", "contains", "nemotron", "Nemotron 系列", 78),
    ModelProfileRule("code", "mistral", "contains", "codestral", "Codestral 系列", 116),
    ModelProfileRule("code", "mistral", "contains", "devstral", "Devstral 系列", 116),
    ModelProfileRule("compact", "generic", "regex", r"(^|[-_.])(mini|small|lite|fast|turbo)([-_.]|$)", "通用轻量命名", 70),
    ModelProfileRule("reasoning", "generic", "regex", r"(reasoner|reasoning)", "通用推理命名", 68),
    ModelProfileRule("code", "generic", "regex", r"(^|[-_.])(code|coder)([-_.]|$)", "通用代码命名", 66),
)


def estimate_text_tokens(text: str) -> int:
    compact = (text or "").strip()
    if not compact:
        return 0
    ascii_words = re.findall(r"[A-Za-z0-9_]+", compact)
    non_ascii_chars = len(re.findall(r"[^\x00-\x7F\s]", compact))
    punctuation = len(re.findall(r"[^\w\s]", compact, flags=re.UNICODE))
    return max(1, len(ascii_words) + non_ascii_chars + max(0, punctuation // 2))


def model_profile_rule_matches(rule: ModelProfileRule, model_name: str) -> bool:
    if rule.match_type == "exact":
        return model_name == rule.pattern
    if rule.match_type == "prefix":
        return model_name.startswith(rule.pattern)
    if rule.match_type == "contains":
        return rule.pattern in model_name
    if rule.match_type == "regex":
        return re.search(rule.pattern, model_name) is not None
    return False


def capability_profile_match(model_name: str) -> tuple[CapabilityProfile, ModelProfileRule | None]:
    normalized = (model_name or "").strip().lower()
    if not normalized:
        return CAPABILITY_PROFILE_BY_ID["unknown"], None
    matched_rule = next(
        (
            rule
            for rule in sorted(MODEL_PROFILE_RULES, key=lambda item: item.priority, reverse=True)
            if model_profile_rule_matches(rule, normalized)
        ),
        None,
    )
    if matched_rule:
        return CAPABILITY_PROFILE_BY_ID[matched_rule.profile_id], matched_rule
    return CAPABILITY_PROFILE_BY_ID["unknown"], None


def capability_profile_for_model(model_name: str) -> CapabilityProfile:
    return capability_profile_match(model_name)[0]


def model_profile_rule_summary(rule: ModelProfileRule | None) -> dict | None:
    if rule is None:
        return None
    return {
        "profile_id": rule.profile_id,
        "provider": rule.provider,
        "match_type": rule.match_type,
        "pattern": rule.pattern,
        "label": rule.label,
        "priority": rule.priority,
    }


def model_verification_probe_cases_for_profile(profile: CapabilityProfile) -> list[ProbeCase]:
    probe_cases = list(PROBE_CASES)
    if profile.requires_fingerprint:
        probe_cases.extend(CAPABILITY_FINGERPRINT_CASES)
    for case_id in profile.extra_probe_case_ids:
        case = PROFILE_EXTRA_CASES.get(case_id)
        if case and all(existing.id != case.id for existing in probe_cases):
            probe_cases.append(case)
    return probe_cases


def model_verification_probe_cases_for_claim(claimed_model: str) -> list[ProbeCase]:
    profile = capability_profile_for_model(claimed_model)
    return model_verification_probe_cases_for_profile(profile)


def profile_probe_case_ids(profile: CapabilityProfile, probe_cases: list[ProbeCase] | None = None) -> list[str]:
    cases = probe_cases if probe_cases is not None else model_verification_probe_cases_for_profile(profile)
    return [case.id for case in cases]


def capability_profile_summary(profile: CapabilityProfile, rule: ModelProfileRule | None = None, probe_cases: list[ProbeCase] | None = None) -> dict:
    return {
        "id": profile.id,
        "label": profile.label,
        "description": profile.description,
        "required_dimensions": list(profile.required_dimensions),
        "minimum_identity_score": profile.minimum_identity_score,
        "minimum_dimension_scores": dict(profile.minimum_dimension_scores),
        "dimension_weights": dict(profile.dimension_weights),
        "probe_case_ids": profile_probe_case_ids(profile, probe_cases),
        "requires_fingerprint": profile.requires_fingerprint,
        "match_rule": model_profile_rule_summary(rule),
    }


def estimate_case_input_tokens(case: ProbeCase) -> int:
    return estimate_text_tokens(MODEL_VERIFICATION_SYSTEM_PROMPT) + estimate_text_tokens(case.prompt)


def model_verification_token_estimate(claimed_model: str = "") -> dict:
    probe_cases = model_verification_probe_cases_for_claim((claimed_model or "").strip())
    call_count = sum(case.repeat for case in probe_cases)
    estimated_input_tokens = sum(estimate_case_input_tokens(case) * case.repeat for case in probe_cases)
    max_output_tokens = call_count * MODEL_VERIFICATION_MAX_OUTPUT_TOKENS
    return {
        "disclaimer": "实际 token 消耗取决于模型输出，以下为点击前预估。",
        "case_count": len(probe_cases),
        "call_count": call_count,
        "estimated_input_tokens": estimated_input_tokens,
        "max_output_tokens": max_output_tokens,
        "steps": [
            {"id": "prepare_request", "call_count": 0, "estimated_input_tokens": 0, "max_output_tokens": 0},
            {
                "id": "run_probe_cases",
                "call_count": call_count,
                "estimated_input_tokens": estimated_input_tokens,
                "max_output_tokens": max_output_tokens,
            },
            {"id": "summarize_report", "call_count": 0, "estimated_input_tokens": 0, "max_output_tokens": 0},
        ],
    }

