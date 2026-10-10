import respx
from httpx import Response

from model_verifier.client import (
    build_anthropic_payload,
    build_chat_payload,
    call_model,
    fetch_model_ids,
    run_protocol_verification,
)
from model_verifier.types import VerificationOptions, VerificationTarget


def target() -> VerificationTarget:
    return VerificationTarget(
        source="temporary",
        base_url="https://gateway.example.test",
        model="gpt-4.1",
        api_key="sk-test-secret",
        api_key_masked="sk-tes...cret",
        site_name="临时接入",
    )


def test_build_chat_payload_uses_system_prompt_and_stream_options():
    payload = build_chat_payload("gpt-4.1", "hello", stream=True)

    assert payload["model"] == "gpt-4.1"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1] == {"role": "user", "content": "hello"}
    assert payload["temperature"] == 0
    assert payload["max_tokens"] == 512
    assert payload["stream"] is True
    assert payload["stream_options"] == {"include_usage": True}


def test_build_anthropic_payload_uses_messages_protocol():
    payload = build_anthropic_payload("claude-3-5-sonnet", "hello")

    assert payload["model"] == "claude-3-5-sonnet"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert payload["temperature"] == 0
    assert payload["max_tokens"] == 512
    assert payload["stream"] is False


def test_fetch_model_ids_filters_non_chat_models():
    with respx.mock:
        route = respx.get("https://gateway.example.test/v1/models").mock(return_value=Response(200, json={
            "data": [
                {"id": "gpt-4.1"},
                {"id": "text-embedding-3-small"},
                {"id": "whisper-1"},
                {"id": "private-chat"},
            ],
        }))

        result = fetch_model_ids("https://gateway.example.test", "sk-test-secret")

    assert route.calls.last.request.headers["authorization"] == "Bearer sk-test-secret"
    assert result["items"] == ["gpt-4.1", "private-chat"]
    assert result["api_key_masked"] == "sk-tes...cret"


def test_call_model_openai_returns_answer_and_upstream_model():
    with respx.mock:
        respx.post("https://gateway.example.test/v1/chat/completions").mock(return_value=Response(200, json={
            "model": "gpt-4.1",
            "choices": [{"message": {"content": "ok"}}],
        }))

        result = call_model(target(), "hello", VerificationOptions(claimed_model="gpt-4.1"))

    assert result.answer == "ok"
    assert result.error == ""
    assert result.upstream_model == "gpt-4.1"
    assert result.latency_ms >= 0


def test_call_model_openai_joins_list_content_parts():
    with respx.mock:
        respx.post("https://gateway.example.test/v1/chat/completions").mock(return_value=Response(200, json={
            "model": "gpt-4.1",
            "choices": [{"message": {"content": [{"type": "text", "text": "1"}, {"type": "text", "text": "72 元"}]}}],
        }))

        result = call_model(target(), "hello", VerificationOptions(claimed_model="gpt-4.1"))

    # content-parts arrays must be joined into text, not stringified as a repr
    assert result.answer == "172 元"
    assert result.error == ""


def test_run_protocol_verification_openai_reports_scores():
    with respx.mock:
        respx.post("https://gateway.example.test/v1/chat/completions").mock(side_effect=[
            Response(200, json={
                "model": "gpt-4.1",
                "choices": [{"message": {"content": '{"status":"ok","n":3}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 4, "total_tokens": 14},
            }),
            Response(200, content="\n".join([
                'data: {"model":"gpt-4.1","choices":[{"delta":{"content":"ok"}}]}',
                "data: [DONE]",
            ]).encode("utf-8")),
        ])

        report = run_protocol_verification(target(), VerificationOptions(claimed_model="gpt-4.1"))

    assert report["provider_guess"] == "openai"
    assert report["protocol_score"] >= 90
    assert report["usage_score"] == 75
    assert report["observed_model"] == "gpt-4.1"


def test_call_model_anthropic_sends_x_api_key_header():
    anthropic_target = VerificationTarget(
        source="temporary",
        base_url="https://gateway.example.test",
        model="claude-3-5-sonnet",
        api_key="sk-ant-secret",
        api_key_masked="sk-ant...cret",
        site_name="临时接入",
    )
    with respx.mock:
        route = respx.post("https://gateway.example.test/v1/messages").mock(return_value=Response(200, json={
            "model": "claude-3-5-sonnet",
            "content": [{"type": "text", "text": "ok"}],
        }))

        result = call_model(
            anthropic_target,
            "hello",
            VerificationOptions(claimed_model="claude-3-5-sonnet", provider_mode="anthropic"),
        )

    request = route.calls.last.request
    assert request.headers["x-api-key"] == "sk-ant-secret"
    assert request.headers["authorization"] == "Bearer sk-ant-secret"
    assert request.headers["anthropic-version"] == "2023-06-01"
    assert result.answer == "ok"
    assert result.upstream_model == "claude-3-5-sonnet"


def test_normalize_gateway_url_handles_v1_and_trailing_slashes():
    from model_verifier.client import normalize_gateway_url

    assert normalize_gateway_url("https://router.bynara.id", "/v1/chat/completions") == "https://router.bynara.id/v1/chat/completions"
    assert normalize_gateway_url("https://router.bynara.id/", "/v1/chat/completions") == "https://router.bynara.id/v1/chat/completions"
    assert normalize_gateway_url("https://router.bynara.id/v1", "/v1/chat/completions") == "https://router.bynara.id/v1/chat/completions"
    assert normalize_gateway_url("https://router.bynara.id/v1/", "/v1/models") == "https://router.bynara.id/v1/models"


def test_call_model_openai_streaming_reasoning_deltas_luna():
    bynara_target = VerificationTarget(
        source="temporary",
        base_url="https://router.bynara.id/v1",
        model="gpt-5.6-luna",
        api_key="sk-bynara-secret",
        api_key_masked="sk-byn...cret",
        site_name="Router ByNara",
    )
    # Simulates streaming response from Router ByNara with reasoning_content deltas followed by content
    stream_content = "\n".join([
        'data: {"id":"chatcmpl-1","model":"gpt-5.6-luna","choices":[{"index":0,"delta":{"reasoning_content":"Thinking deeply..."}}]}',
        'data: {"id":"chatcmpl-1","model":"gpt-5.6-luna","choices":[{"index":0,"delta":{"content":"Jawaban "}}]}',
        'data: {"id":"chatcmpl-1","model":"gpt-5.6-luna","choices":[{"index":0,"delta":{"content":"Otentik."}}]}',
        "data: [DONE]",
    ]).encode("utf-8")

    with respx.mock:
        respx.post("https://router.bynara.id/v1/chat/completions").mock(return_value=Response(
            200,
            content=stream_content,
            headers={"Content-Type": "text/event-stream"},
        ))

        result = call_model(bynara_target, "test prompt", VerificationOptions(claimed_model="gpt-5.6-luna"))

    assert result.answer == "Jawaban Otentik."
    assert result.error == ""
    assert result.upstream_model == "gpt-5.6-luna"

