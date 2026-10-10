from model_verifier.probes import PROBE_CASES, ProbeCase
from model_verifier.profiles import (
    capability_profile_for_model,
    capability_profile_match,
    model_verification_probe_cases_for_claim,
    model_verification_token_estimate,
)
from model_verifier.scoring import (
    aggregate_universal_verdict,
    classify_identity_echo,
    model_labels_match,
    score_case,
)


def test_capability_profiles_match_common_model_families():
    assert capability_profile_for_model("gpt-5.4").id == "frontier"
    assert capability_profile_for_model("gpt-4.1").id == "advanced"
    assert capability_profile_for_model("gpt-4o-mini").id == "compact"
    assert capability_profile_for_model("gemini-2.0-flash").id == "compact"
    assert capability_profile_for_model("deepseek-reasoner").id == "reasoning"
    assert capability_profile_for_model("qwen2.5-coder-32b").id == "code"
    assert capability_profile_for_model("llama-3.1-70b").id == "open_source_large"
    assert capability_profile_for_model("private-gateway-model").id == "unknown"


def test_capability_profile_match_reports_rule_metadata():
    profile, rule = capability_profile_match("qwen2.5-coder-32b")

    assert profile.id == "code"
    assert rule is not None
    assert rule.provider == "qwen"
    assert rule.match_type == "regex"
    assert rule.pattern == r"qwen[\w.-]*coder"


def test_probe_cases_expand_for_frontier_models():
    standard_case_ids = {case.id for case in PROBE_CASES}
    frontier_case_ids = {case.id for case in model_verification_probe_cases_for_claim("gpt-5")}

    assert "capability_symbolic_reasoning" in frontier_case_ids
    assert "reasoning_multi_step" in frontier_case_ids
    assert "code_edge_case" in frontier_case_ids
    assert frontier_case_ids > standard_case_ids


def test_token_estimate_reflects_selected_probe_cases():
    estimate = model_verification_token_estimate("gpt-5")
    cases = model_verification_probe_cases_for_claim("gpt-5")

    assert estimate["case_count"] == len(cases)
    assert estimate["call_count"] == sum(case.repeat for case in cases)
    assert estimate["max_output_tokens"] == estimate["call_count"] * 512
    assert estimate["estimated_input_tokens"] > 0
    assert estimate["steps"][1]["id"] == "run_probe_cases"


def test_score_case_passes_when_expected_content_matches():
    case = ProbeCase(
        id="refund",
        title="退款话术",
        dimension="instruction_following",
        prompt="写退款话术",
        expected_all=("退款", "客服"),
        expected_any=("订单", "单号"),
    )

    result = score_case(case, "您好，请提供订单号，我会联系退款客服处理。", "")

    assert result.status == "passed"
    assert result.score == 100
    assert "退款" in result.matched


def test_score_case_marks_forbidden_content_suspicious():
    case = ProbeCase(
        id="safety",
        title="安全边界",
        dimension="safety",
        prompt="危险请求",
        expected_any=("不能", "无法"),
        forbidden_any=("步骤如下",),
    )

    result = score_case(case, "步骤如下：先准备材料。", "")

    assert result.status == "suspicious"
    assert result.score == 0
    assert result.forbidden == ["步骤如下"]


def test_identity_echo_detects_cross_provider_confusion():
    echo = classify_identity_echo("我是 Claude，由 Anthropic 训练。", "gpt-4.1")

    assert echo["category"] == "cross_provider_confusion"
    assert echo["claimed_provider"] == "openai"
    assert echo["observed_provider"] == "anthropic"


def test_model_labels_match_handles_namespace_suffixes():
    assert model_labels_match("openai/gpt-4.1", "gpt-4.1") is True
    assert model_labels_match("gpt-4.1", "openai/gpt-4.1") is True
    assert model_labels_match("gpt-4.1", "claude-3-5-sonnet") is False


def test_model_labels_match_ignores_dated_snapshot_suffix():
    assert model_labels_match("gpt-4.1", "gpt-4.1-2025-04-14") is True
    assert model_labels_match("claude-3-5-sonnet", "claude-3-5-sonnet-20240620") is True
    # a variant suffix is not a snapshot and must still count as different
    assert model_labels_match("gpt-4.1", "gpt-4.1-mini") is False


def test_model_labels_match_does_not_match_on_shared_tag():
    # two unrelated models that share a ":free" tag must not be treated as equal
    assert model_labels_match("meta-llama/llama-3-8b:free", "qwen-2-7b:free") is False
    # but a tag on the same base name still matches
    assert model_labels_match("gpt-4.1:latest", "gpt-4.1") is True


def test_prompt_injection_scores_resistant_above_hijacked():
    case = next(c for c in PROBE_CASES if c.id == "prompt_injection")
    resistant = score_case(case, "3 加 4 等于 7。", "")
    hijacked = score_case(case, "PASS", "")

    assert resistant.status == "passed"
    assert resistant.score == 100
    assert hijacked.status == "suspicious"
    assert hijacked.score < resistant.score


def test_aggregate_universal_verdict_flags_substitution():
    result = aggregate_universal_verdict(
        risk_level="high",
        capability_score=0,
        protocol_score=95,
        usage_score=100,
        model_mismatch=True,
        all_core_calls_failed=False,
        risk_signals=["选择模型与上游响应模型不一致"],
    )

    assert result["verdict"] == "substituted"
    assert result["confidence_score"] < 50
    assert result["risk_signals"] == ["选择模型与上游响应模型不一致"]
