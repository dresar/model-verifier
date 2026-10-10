import pytest

from model_verifier.report import run_verification, run_verification_with_caller
from model_verifier.types import ModelCallResult, VerificationOptions, VerificationTarget


def target(model: str = "gpt-4.1") -> VerificationTarget:
    return VerificationTarget(
        source="temporary",
        base_url="https://gateway.example.test",
        model=model,
        api_key="sk-test-secret",
        api_key_masked="sk-tes...cret",
        site_name="临时接入",
    )


def successful_protocol_report() -> dict:
    return {
        "provider_guess": "openai",
        "protocol_score": 100,
        "usage_score": 100,
        "observed_model": "gpt-4.1",
        "checks": [
            {"name": "non_stream", "usage": {"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12}},
            {"name": "stream", "usage": {}},
        ],
        "risk_signals": [],
    }


def matching_answer(prompt: str) -> ModelCallResult:
    if "status" in prompt and '"n":3' in prompt:
        return ModelCallResult('{"status":"ok","n":3}', 10, "", "gpt-4.1")
    if "退款不到账" in prompt:
        return ModelCallResult("退款订单请联系官方客服处理。", 10, "", "gpt-4.1")
    if "password reset" in prompt:
        return ModelCallResult("- password reset link\n- password reset support", 10, "", "gpt-4.1")
    if "原价 240" in prompt:
        return ModelCallResult("172 元", 10, "", "gpt-4.1")
    if "所有 A 都是 B" in prompt:
        return ModelCallResult("不能，因为无法推出部分 A 是 C。", 10, "", "gpt-4.1")
    if "def last" in prompt:
        return ModelCallResult("使用 xs[-1]，原写法会触发 IndexError。", 10, "", "gpt-4.1")
    if "伪造" in prompt:
        return ModelCallResult("不能帮助伪造证件，这违法且不安全。", 10, "", "gpt-4.1")
    if "退款进度查询" in prompt:
        return ModelCallResult("您好，请问退款进度如何，感谢协助。", 10, "", "gpt-4.1")
    if "3 加 4" in prompt:
        return ModelCallResult("3 加 4 等于 7。", 10, "", "gpt-4.1")
    if "你是什么模型" in prompt:
        return ModelCallResult("我是 AI 模型，无法确认底层来源。", 10, "", "gpt-4.1")
    if "19+23" in prompt:
        return ModelCallResult("42", 10, "", "gpt-4.1")
    return ModelCallResult("ok", 10, "", "gpt-4.1")


def test_run_verification_with_caller_returns_core_report():
    report = run_verification_with_caller(
        target(),
        VerificationOptions(claimed_model="gpt-4.1"),
        protocol_runner=lambda _target, _options: successful_protocol_report(),
        model_caller=lambda _target, prompt, _options, _mode: matching_answer(prompt),
    )

    assert report["claimed_model"] == "gpt-4.1"
    assert report["actual_model"] == "gpt-4.1"
    assert report["upstream_model"] == "gpt-4.1"
    assert report["risk_level"] == "low"
    assert report["verdict"] == "verified"
    assert report["confidence_score"] >= 90
    assert report["protocol_score"] == 100
    assert report["usage_score"] == 100
    assert report["cases"]


def test_run_verification_with_caller_reports_unreachable_when_core_calls_fail():
    def failing_call(_target, _prompt, _options, _mode):
        return ModelCallResult("", 5, "timeout", "")

    report = run_verification_with_caller(
        target(),
        VerificationOptions(claimed_model="gpt-4.1"),
        protocol_runner=lambda _target, _options: {
            "provider_guess": "openai",
            "protocol_score": 0,
            "usage_score": 0,
            "observed_model": "",
            "checks": [],
            "risk_signals": ["协议探针调用失败：timeout"],
        },
        model_caller=failing_call,
    )

    assert report["verdict"] == "unreachable"
    assert report["confidence_score"] == 0
    assert report["risk_level"] == "inconclusive"


def test_run_verification_with_caller_reports_substituted_for_model_mismatch():
    report = run_verification_with_caller(
        target(model="gpt-4.1"),
        VerificationOptions(claimed_model="claude-3-5-sonnet"),
        protocol_runner=lambda _target, _options: successful_protocol_report(),
        model_caller=lambda _target, prompt, _options, _mode: matching_answer(prompt),
    )

    assert report["verdict"] == "substituted"
    assert report["risk_level"] == "high"
    assert report["identity_score"] == 0
    assert any("不一致" in signal for signal in report["signals"])


def test_run_verification_rejects_private_base_url():
    private_target = VerificationTarget(
        source="temporary",
        base_url="http://127.0.0.1:8000",
        model="gpt-4.1",
        api_key="sk-test-secret",
        api_key_masked="sk-tes...cret",
        site_name="临时接入",
    )

    with pytest.raises(ValueError):
        run_verification(private_target, VerificationOptions(claimed_model="gpt-4.1"))
