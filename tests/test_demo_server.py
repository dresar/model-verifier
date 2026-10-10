import json

import respx
from httpx import Response

from model_verifier import demo
from model_verifier.demo import demo_report, dispatch_demo_request


def decode_json(body: bytes) -> dict:
    return json.loads(body.decode("utf-8"))


def clear_verification_jobs():
    with demo.MODEL_VERIFICATION_JOBS_LOCK:
        demo.MODEL_VERIFICATION_JOBS.clear()


def wait_for_verification_job(job_id: str):
    for _ in range(50):
        response = dispatch_demo_request("GET", f"/api/model-verification/runs/{job_id}", b"")
        if response.status != 202:
            return response
    return dispatch_demo_request("GET", f"/api/model-verification/runs/{job_id}", b"")


def test_demo_health_endpoint_returns_json():
    response = dispatch_demo_request("GET", "/api/health", b"")

    assert response.status == 200
    assert response.headers["Content-Type"] == "application/json; charset=utf-8"
    assert decode_json(response.body) == {"ok": True}


def test_verify_prefixed_health_endpoint_returns_json():
    response = dispatch_demo_request("GET", "/verify/api/health", b"")

    assert response.status == 200
    assert decode_json(response.body) == {"ok": True}


def test_demo_report_uses_core_verification_shape():
    report = demo_report()

    assert report["claimed_model"] == "gpt-4.1"
    assert report["actual_model"] == "gpt-4.1"
    assert report["verdict"] == "verified"
    assert report["risk_level"] == "low"
    assert report["confidence_score"] >= 90
    assert report["cases"]


def test_demo_report_endpoint_returns_verification_report():
    response = dispatch_demo_request("POST", "/api/demo-report", b"{}")
    data = decode_json(response.body)

    assert response.status == 200
    assert data["verdict"] == "verified"
    assert data["case_count"] == len(data["cases"])


def test_model_verification_settings_endpoint_matches_frontend_contract():
    response = dispatch_demo_request("GET", "/api/model-verification/settings?claimed_model=gpt-4.1", b"")
    data = decode_json(response.body)

    assert response.status == 200
    assert data["quota_cost"] == 0
    assert data["daily_limit"] == 20
    assert data["authenticated"] is False
    assert data["token_estimate"]["case_count"] > 0


def test_temporary_models_endpoint_returns_model_list():
    response = dispatch_demo_request(
        "POST",
        "/api/model-verification/temporary-models",
        json.dumps({"base_url": "https://gateway.example.test", "api_key": "sk-test-secret"}).encode("utf-8"),
    )
    data = decode_json(response.body)

    assert response.status == 200
    assert data["base_url"] == "https://gateway.example.test"
    assert data["api_key_masked"] == "sk-tes...cret"
    assert "gpt-4.1" in data["items"]


def test_model_verification_runs_endpoint_accepts_temporary_payload():
    response = dispatch_demo_request(
        "POST",
        "/api/model-verification/runs",
        json.dumps(
            {
                "source": "temporary",
                "base_url": "https://gateway.example.test",
                "api_key": "sk-test-secret",
                "claimed_model": "gpt-4.1",
                "provider_mode": "openai",
            }
        ).encode("utf-8"),
    )
    data = decode_json(response.body)

    assert response.status == 200
    assert data["source"] == "temporary"
    assert data["base_url"] == "https://gateway.example.test"
    assert data["api_key_masked"] == "sk-tes...cret"
    assert data["verdict"] == "verified"


def test_demo_run_does_not_flag_advertised_models_as_substituted():
    # All three advertised demo models must echo the selected model, so none of
    # them is reported as a model substitution just for being selected.
    for model in ("gpt-4.1-mini", "claude-3-5-sonnet"):

        response = dispatch_demo_request(
            "POST",
            "/api/model-verification/runs",
            json.dumps(
                {
                    "source": "temporary",
                    "base_url": "https://gateway.example.test",
                    "api_key": "sk-test-secret",
                    "claimed_model": model,
                    "provider_mode": "openai",
                }
            ).encode("utf-8"),
        )
        data = decode_json(response.body)

        assert response.status == 200, model
        assert data["verdict"] != "substituted", model
        assert data["actual_model"] == model
        assert data["upstream_model"] == model


def test_temporary_live_run_defaults_model_to_claimed_model(monkeypatch):
    # The temporary flow posts only `claimed_model` (no `model`); a live gateway
    # run must default the upstream request model to it instead of failing 400.
    monkeypatch.setattr(demo, "validate_public_base_url", lambda url: url)
    with respx.mock:
        respx.post("https://live.example.test/v1/chat/completions").mock(return_value=Response(200, json={
            "model": "gpt-4.1",
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
        }))
        response = dispatch_demo_request(
            "POST",
            "/api/model-verification/runs",
            json.dumps(
                {
                    "source": "temporary",
                    "base_url": "https://live.example.test",
                    "api_key": "sk-test-secret",
                    "claimed_model": "gpt-4.1",
                    "provider_mode": "openai",
                }
            ).encode("utf-8"),
        )
    data = decode_json(response.body)

    assert response.status == 200
    assert data["claimed_model"] == "gpt-4.1"
    assert data["actual_model"] == "gpt-4.1"


def test_sites_endpoint_is_empty_for_open_source_demo():
    response = dispatch_demo_request("GET", "/api/sites", b"")
    data = decode_json(response.body)

    assert response.status == 200
    assert data == {"items": []}


def test_me_endpoint_returns_anonymous_without_host_api():
    response = dispatch_demo_request("GET", "/api/me?scope=user", b"")
    data = decode_json(response.body)

    assert response.status == 200
    assert data == {"authenticated": False, "kind": None, "user": None}


def test_login_endpoint_redirects_to_host_api_when_configured(monkeypatch):
    monkeypatch.setattr(demo, "HOST_API_BASE_URL", "https://modelscan.example")

    response = dispatch_demo_request("GET", "/api/auth/github?next=/model/verification", b"")

    assert response.status == 302
    assert response.headers["Location"] == "https://modelscan.example/api/auth/github?next=/model/verification"


def test_verify_prefixed_login_redirect_strips_verify_prefix_for_host_api(monkeypatch):
    monkeypatch.setattr(demo, "HOST_API_BASE_URL", "https://modelscan.example")

    response = dispatch_demo_request("GET", "/verify/api/auth/github?next=/verify/", b"")

    assert response.status == 302
    assert response.headers["Location"] == "https://modelscan.example/api/auth/github?next=/verify/"


def test_host_api_proxy_forwards_cookie_and_returns_json(monkeypatch):
    captured = {}

    class FakeResponse:
        status_code = 200
        content = b'{"items":[{"id":1,"name":"Demo","base_url":"https://gateway.example.test","api_key_count":1,"api_keys":[],"note":"","enabled":true,"last_sync_at":null,"last_sync_error":""}]}'
        headers = {"content-type": "application/json; charset=utf-8"}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def request(self, method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["headers"] = kwargs["headers"]
            return FakeResponse()

    monkeypatch.setattr(demo, "HOST_API_BASE_URL", "https://modelscan.example")
    monkeypatch.setattr(demo.httpx, "Client", FakeClient)

    response = demo.dispatch_demo_request_with_headers(
        "GET",
        "/api/sites",
        b"",
        headers={"Cookie": "modelscan_user_session=session-token"},
    )
    data = decode_json(response.body)

    assert response.status == 200
    assert data["items"][0]["name"] == "Demo"
    assert captured["method"] == "GET"
    assert captured["url"] == "https://modelscan.example/api/sites"
    assert captured["headers"]["Cookie"] == "modelscan_user_session=session-token"
    assert captured["client_kwargs"]["trust_env"] is False


def test_saved_model_verification_run_is_queued_and_polled_from_host_api(monkeypatch):
    captured = {}
    clear_verification_jobs()

    class FakeResponse:
        status_code = 200
        content = b'{"source":"saved","verdict":"verified"}'
        headers = {"content-type": "application/json; charset=utf-8"}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client_kwargs"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def request(self, method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["body"] = kwargs["content"]
            captured["headers"] = kwargs["headers"]
            return FakeResponse()

    payload = json.dumps({"source": "saved", "site_model_id": 42, "claimed_model": "gpt-5.4"}).encode("utf-8")
    monkeypatch.setattr(demo, "HOST_API_BASE_URL", "https://modelscan.example")
    monkeypatch.setattr(demo, "HOST_API_INTERNAL_BASE_URL", "http://modelscan-api-1:8000")
    monkeypatch.setattr(demo.httpx, "Client", FakeClient)

    response = demo.dispatch_demo_request_with_headers(
        "POST",
        "/verify/api/model-verification/runs",
        payload,
        headers={"Cookie": "modelscan_user_session=session-token", "Content-Type": "application/json"},
    )
    queued = decode_json(response.body)

    assert response.status == 202
    assert queued["status"] == "running"
    assert queued["job_id"]

    completed = wait_for_verification_job(queued["job_id"])
    data = decode_json(completed.body)

    assert completed.status == 200
    assert data == {"source": "saved", "verdict": "verified"}
    assert captured["method"] == "POST"
    assert captured["url"] == "http://modelscan-api-1:8000/api/model-verification/runs"
    assert captured["body"] == payload
    assert captured["headers"]["Cookie"] == "modelscan_user_session=session-token"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["client_kwargs"]["timeout"] == 600
    assert captured["client_kwargs"]["trust_env"] is False
    clear_verification_jobs()


def test_host_api_proxy_preserves_multiple_set_cookie_headers(monkeypatch):
    class FakeHeaders:
        def get(self, name, default=None):
            if name.lower() == "content-type":
                return "application/json"
            return default

        def get_list(self, name):
            if name.lower() == "set-cookie":
                return [
                    'modelscan_user_session=""; Max-Age=0; Path=/; SameSite=lax',
                    'ping_mddb_user_session=""; Max-Age=0; Path=/; SameSite=lax',
                ]
            return []

    class FakeResponse:
        status_code = 200
        content = b'{"ok":true}'
        headers = FakeHeaders()

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def request(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr(demo, "HOST_API_BASE_URL", "https://modelscan.example")
    monkeypatch.setattr(demo.httpx, "Client", FakeClient)

    response = demo.dispatch_demo_request_with_headers("POST", "/api/auth/logout?scope=user", b"", headers={})

    assert response.status == 200
    assert response.multi_headers == (
        ("Set-Cookie", 'modelscan_user_session=""; Max-Age=0; Path=/; SameSite=lax'),
        ("Set-Cookie", 'ping_mddb_user_session=""; Max-Age=0; Path=/; SameSite=lax'),
    )


def test_verify_endpoint_rejects_missing_required_fields():
    response = dispatch_demo_request("POST", "/api/verify", b"{}")
    data = decode_json(response.body)

    assert response.status == 400
    assert "base_url" in data["error"]


def test_root_serves_demo_page():
    response = dispatch_demo_request("GET", "/", b"")
    html = response.body.decode("utf-8")

    assert response.status == 200
    assert "Model Verifier" in html
    assert "Vite" in html


def test_verify_root_serves_demo_page():
    response = dispatch_demo_request("GET", "/verify/", b"")
    html = response.body.decode("utf-8")

    assert response.status == 200
    assert "/verify/" in html
