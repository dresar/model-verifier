import hashlib
from collections.abc import Callable

from model_verifier.client import call_model, run_protocol_verification
from model_verifier.probes import DIMENSIONS, ProbeCase
from model_verifier.providers import select_effective_provider_mode
from model_verifier.profiles import (
    capability_profile_match,
    capability_profile_summary,
    model_verification_probe_cases_for_profile,
)
from model_verifier.scoring import (
    aggregate_universal_verdict,
    assess_capability_profile,
    classify_identity_echo,
    evidence_role_for_dimension,
    model_labels_match,
    score_case,
    summarize_identity_echo,
    summarize_report,
    weighted_identity_score,
)
from model_verifier.types import ModelCallResult, VerificationOptions, VerificationTarget
from model_verifier.url_safety import validate_public_base_url


ProtocolRunner = Callable[[VerificationTarget, VerificationOptions], dict]
ModelCaller = Callable[[VerificationTarget, str, VerificationOptions, str], ModelCallResult]


def probe_prompt_for_call(case: ProbeCase, repeat_index: int) -> str:
    if case.dimension != "identity_claim":
        return case.prompt
    digest = hashlib.sha1(f"{case.id}:{repeat_index}:{case.prompt}".encode("utf-8")).hexdigest()[:8]
    return f"{case.prompt}\n\n[Verifier nonce: {digest}]"



def run_verification(target: VerificationTarget, options: VerificationOptions) -> dict:
    # Enforce the SSRF guard on the public entry point so direct API/CLI callers
    # cannot reach localhost/private/metadata addresses via target.base_url.
    validate_public_base_url(target.base_url)
    return run_verification_with_caller(
        target,
        options,
        protocol_runner=run_protocol_verification,
        model_caller=call_model,
    )


def run_verification_with_caller(
    target: VerificationTarget,
    options: VerificationOptions,
    protocol_runner: ProtocolRunner,
    model_caller: ModelCaller,
) -> dict:
    claimed_model_clean = options.claimed_model.strip()
    capability_profile, profile_rule = capability_profile_match(claimed_model_clean)
    case_results = []
    dimension_totals = {dimension: [] for dimension in DIMENSIONS}
    upstream_models = []
    protocol_report = protocol_runner(target, options)
    effective_provider_mode = protocol_report.get("provider_guess") or select_effective_provider_mode(options.provider_mode, target.model)
    if protocol_report.get("observed_model"):
        upstream_models.append(str(protocol_report["observed_model"]))
    probe_cases = model_verification_probe_cases_for_profile(capability_profile)
    for case in probe_cases:
        repeat_answers = []
        repeat_errors = []
        total_latency = 0
        for repeat_index in range(case.repeat):
            result = model_caller(target, probe_prompt_for_call(case, repeat_index), options, effective_provider_mode)
            repeat_answers.append(result.answer)
            repeat_errors.append(result.error)
            if result.upstream_model:
                upstream_models.append(result.upstream_model)
            total_latency += result.latency_ms
        answer = repeat_answers[-1] if repeat_answers else ""
        error = next((item for item in repeat_errors if item), "")
        score_result = score_case(case, answer, error)
        if case.dimension == "stability" and not error and len(set(repeat_answers)) > 1:
            score_result = score_result.__class__(
                score=min(score_result.score, 60),
                status="suspicious",
                signals=["重复调用结果不一致"],
                matched=score_result.matched,
                missing=score_result.missing,
                forbidden=score_result.forbidden,
                reason="重复调用结果不一致",
                expected_criteria=score_result.expected_criteria,
            )
        evidence_role = evidence_role_for_dimension(case.dimension)
        dimension_totals.setdefault(case.dimension, []).append(score_result.score)
        case_result = {
            "id": case.id,
            "title": case.title,
            "dimension": case.dimension,
            "evidence_role": evidence_role,
            "status": score_result.status,
            "score": score_result.score,
            "latency_ms": total_latency,
            "signals": score_result.signals,
            "matched": score_result.matched,
            "missing": score_result.missing,
            "forbidden": score_result.forbidden,
            "reason": score_result.reason,
            "expected_criteria": score_result.expected_criteria,
            "prompt": case.prompt,
            "answer_preview": answer[:500],
            "error": error,
        }
        if case.dimension == "identity_claim" and not error:
            identity_echo = classify_identity_echo(answer, claimed_model_clean)
            case_result["identity_echo"] = identity_echo
            if identity_echo["category"] == "cross_provider_confusion":
                case_result["signals"] = [f"身份自述出现跨厂混淆：{identity_echo['observed_provider_label']}"] + case_result["signals"]
            elif identity_echo["category"] == "refusal":
                case_result["signals"] = ["身份自述拒答"] + case_result["signals"]
            elif identity_echo["category"] == "unknown":
                case_result["signals"] = ["身份自述未给出明确厂商"] + case_result["signals"]
        case_results.append(case_result)
    identity_cases = [case for case in case_results if case["evidence_role"] == "identity"]
    reference_cases = [case for case in case_results if case["evidence_role"] == "reference"]
    risk_level, conclusion, signals, recommendations, identity_score = summarize_report(identity_cases, reference_cases)
    identity_echo_summary = summarize_identity_echo(case_results, claimed_model_clean)
    all_core_calls_failed = bool(identity_cases) and all(case["status"] == "error" for case in identity_cases)
    dimension_scores = {
        dimension: round(sum(scores) / len(scores), 2)
        for dimension, scores in dimension_totals.items()
        if scores
    }
    if identity_score:
        identity_score = weighted_identity_score(capability_profile, dimension_scores)
    upstream_model = next((item for item in upstream_models if item), "")
    model_mismatch = False
    if upstream_model and not model_labels_match(target.model, upstream_model):
        model_mismatch = True
        risk_level = "high"
        conclusion = "上游响应模型与选择模型不一致"
        identity_score = 0
        dimension_scores["identity_claim"] = 0
        signals = [f"选择模型 {target.model} 与上游响应模型 {upstream_model} 不一致"] + signals
        recommendations = ["请确认所选模型、网关映射和供应商返回的模型名称。"] + recommendations
    elif not model_labels_match(claimed_model_clean, target.model):
        model_mismatch = True
        risk_level = "high"
        conclusion = "选择模型与实际调用模型不一致"
        identity_score = 0
        dimension_scores["identity_claim"] = 0
        signals = [f"选择模型 {claimed_model_clean} 与实际调用模型 {target.model} 不一致"] + signals
        recommendations = ["请确认所选模型、上游模型映射和供应商提供的实际模型名称。"] + recommendations
    profile_assessment = assess_capability_profile(capability_profile, identity_score, dimension_scores)
    if profile_assessment["status"] == "below_expected" and risk_level not in {"high", "inconclusive"}:
        risk_level = "medium"
        conclusion = "存在可疑迹象"
        signals = [profile_assessment["reason"]] + signals
        recommendations = ["建议按该模型档位补充能力基线或使用供应商证明复核。"] + recommendations
    protocol_score = float(protocol_report.get("protocol_score", 0) or 0)
    usage_score = float(protocol_report.get("usage_score", 0) or 0)
    capability_score = float(identity_score or 0)
    universal_result = aggregate_universal_verdict(
        risk_level,
        capability_score,
        protocol_score,
        usage_score,
        model_mismatch,
        all_core_calls_failed,
        list(protocol_report.get("risk_signals", [])) + signals,
    )
    return {
        "claimed_model": claimed_model_clean,
        "capability_profile": capability_profile_summary(capability_profile, profile_rule, probe_cases),
        "profile_assessment": profile_assessment,
        "actual_model": target.model,
        "upstream_model": upstream_model,
        "risk_level": risk_level,
        "conclusion": conclusion,
        "identity_score": identity_score,
        "dimension_scores": dimension_scores,
        "signals": signals,
        "recommendations": recommendations,
        "identity_echo_summary": identity_echo_summary,
        "verdict": universal_result["verdict"],
        "confidence_score": universal_result["confidence_score"],
        "provider_guess": protocol_report.get("provider_guess", "generic"),
        "protocol_score": protocol_score,
        "capability_score": capability_score,
        "usage_score": usage_score,
        "protocol_evidence": protocol_report,
        "usage_evidence": {
            "score": usage_score,
            "checks": [
                {"name": check.get("name"), "usage": check.get("usage", {})}
                for check in protocol_report.get("checks", [])
            ],
        },
        "risk_signals": universal_result["risk_signals"],
        "cases": case_results,
    }
