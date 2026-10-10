from httpx import Response

from model_verifier.providers import (
    ProviderCheck,
    calculate_usage_score,
    parse_anthropic_message_response,
    parse_anthropic_stream_response,
    parse_openai_chat_response,
    parse_openai_stream_response,
    select_effective_provider_mode,
    summarize_protocol_report,
)


def test_parse_openai_chat_response_extracts_protocol_and_usage_evidence():
    res = Response(200, json={
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "model": "gpt-4.1",
        "choices": [{"message": {"role": "assistant", "content": "ok"}}],
        "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
    })

    check = parse_openai_chat_response(res, "gpt-4.1")

    assert check.status == "pass"
    assert check.score == 100
    assert check.provider == "openai"
    assert check.observed_model == "gpt-4.1"
    assert check.usage == {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15}
    assert "choices_message_content" in check.signals


def test_parse_openai_stream_response_requires_data_chunks_and_done_marker():
    stream_text = "\n".join([
        'data: {"model":"gpt-4.1","choices":[{"delta":{"content":"he"}}]}',
        'data: {"choices":[{"delta":{"content":"llo"}}]}',
        "data: [DONE]",
    ])
    res = Response(200, content=stream_text.encode("utf-8"))

    check = parse_openai_stream_response(res, "gpt-4.1")

    assert check.status == "pass"
    assert check.score == 100
    assert check.observed_model == "gpt-4.1"
    assert check.text_sample == "hello"
    assert "stream_done" in check.signals


def test_parse_anthropic_message_response_extracts_content_and_usage():
    res = Response(200, json={
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "claude-3-5-sonnet",
        "content": [{"type": "text", "text": "ok"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 2},
    })

    check = parse_anthropic_message_response(res, "claude-3-5-sonnet")

    assert check.status == "pass"
    assert check.score == 100
    assert check.provider == "anthropic"
    assert check.observed_model == "claude-3-5-sonnet"
    assert check.usage == {"input_tokens": 10, "output_tokens": 2}
    assert "content_text_block" in check.signals


def test_parse_anthropic_stream_response_requires_message_events():
    events = [
        'event: message_start\ndata: {"type":"message_start","message":{"model":"claude-3-5-sonnet"}}',
        'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"hi"}}',
        'event: message_stop\ndata: {"type":"message_stop"}',
    ]
    res = Response(200, content=("\n\n".join(events)).encode("utf-8"))

    check = parse_anthropic_stream_response(res, "claude-3-5-sonnet")

    assert check.status == "pass"
    assert check.score == 100
    assert check.observed_model == "claude-3-5-sonnet"
    assert check.text_sample == "hi"
    assert "message_stop" in check.signals


def test_usage_score_flags_missing_and_invalid_usage():
    assert calculate_usage_score({"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}) == 100
    assert calculate_usage_score({}) == 50
    assert calculate_usage_score({"prompt_tokens": -1, "completion_tokens": 2}) == 0


def test_select_effective_provider_mode_prefers_user_choice_then_model_hint():
    assert select_effective_provider_mode("openai", "claude-3-5-sonnet") == "openai"
    assert select_effective_provider_mode("anthropic", "gpt-4.1") == "anthropic"
    assert select_effective_provider_mode("auto", "claude-3-5-sonnet") == "anthropic"
    assert select_effective_provider_mode("auto", "gpt-4.1") == "openai"
    assert select_effective_provider_mode("auto", "private-model") == "openai"


def test_summarize_protocol_report_averages_checks_and_risk_signals():
    report = summarize_protocol_report("openai", [
        ProviderCheck(
            name="non_stream",
            provider="openai",
            status="pass",
            score=100,
            signals=["choices_message_content"],
            warnings=[],
            observed_model="gpt-4.1",
            usage={"total_tokens": 10},
            text_sample="ok",
        ),
        ProviderCheck(
            name="stream",
            provider="openai",
            status="warn",
            score=60,
            signals=["data_chunks"],
            warnings=["缺少 stream_done"],
            observed_model="gpt-4.1",
            usage={},
            text_sample="ok",
        ),
    ])

    assert report["provider_guess"] == "openai"
    assert report["protocol_score"] == 80
    assert report["usage_score"] == 75
    assert report["observed_model"] == "gpt-4.1"
    assert report["risk_signals"] == ["缺少 stream_done"]
