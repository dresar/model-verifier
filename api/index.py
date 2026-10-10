import http.client
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Add root src directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(root_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from model_verifier.demo import dispatch_demo_request_with_headers


def resolve_request_path(raw_path: str, headers: dict) -> str:
    """Resolve the real request path accounting for Vercel serverless rewrites and proxy headers."""
    # Check Vercel routing headers first
    for header_name in (
        "x-forwarded-uri",
        "x-original-uri",
        "x-invoke-path",
        "x-matched-path",
        "X-Forwarded-Uri",
        "X-Original-Uri",
        "X-Invoke-Path",
        "X-Matched-Path",
    ):
        header_val = headers.get(header_name)
        if header_val and not header_val.endswith("index.py"):
            return header_val

    parsed = urlparse(raw_path)
    qs = parse_qs(parsed.query)
    if "path" in qs and qs["path"]:
        param_path = qs["path"][0]
        if not param_path.startswith("/"):
            param_path = f"/api/{param_path}"
        return param_path

    # Fallback: if raw_path is just /api/index.py or /index.py, default to /api/health
    if parsed.path.endswith("index.py") or parsed.path in {"", "/"}:
        return "/api/health"

    return raw_path


class handler(BaseHTTPRequestHandler):
    def _handle(self, method: str):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""
        req_headers = {key: self.headers[key] for key in self.headers}

        target_path = resolve_request_path(self.path, req_headers)
        response = dispatch_demo_request_with_headers(method, target_path, body, req_headers)

        self.send_response(response.status)
        for name, value in response.headers.items():
            self.send_header(name, value)
        for name, value in response.multi_headers:
            self.send_header(name, value)

        if "Access-Control-Allow-Origin" not in response.headers:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Locale")

        self.end_headers()
        self.wfile.write(response.body)

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Locale")
        self.end_headers()


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    if method == "OPTIONS":
        headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
            ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Locale"),
        ]
        start_response("204 No Content", headers)
        return [b""]

    raw_path = environ.get("PATH_INFO", "/")
    query = environ.get("QUERY_STRING", "")
    full_path = raw_path + (f"?{query}" if query else "")
    content_length = int(environ.get("CONTENT_LENGTH") or 0)
    body = environ["wsgi.input"].read(content_length) if content_length > 0 else b""

    headers = {}
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            header_name = key[5:].replace("_", "-").title()
            headers[header_name] = value
        elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
            headers[key.replace("_", "-").title()] = value

    effective_path = resolve_request_path(full_path, headers)
    response = dispatch_demo_request_with_headers(method, effective_path, body, headers)
    response_headers = list(response.headers.items())
    for name, value in response.multi_headers:
        response_headers.append((name, value))

    response_headers.append(("Access-Control-Allow-Origin", "*"))
    response_headers.append(("Access-Control-Allow-Methods", "GET, POST, OPTIONS"))
    response_headers.append(("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Locale"))

    reason_phrase = http.client.responses.get(response.status, "OK")
    status_str = f"{response.status} {reason_phrase}"
    start_response(status_str, response_headers)
    return [response.body]
