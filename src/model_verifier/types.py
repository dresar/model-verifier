from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationTarget:
    source: str
    base_url: str
    model: str
    api_key: str
    api_key_masked: str = ""
    site_name: str = ""


@dataclass(frozen=True)
class VerificationOptions:
    claimed_model: str
    provider_mode: str = "auto"
    timeout_seconds: float = 90


@dataclass(frozen=True)
class ModelCallResult:
    answer: str
    latency_ms: int
    error: str
    upstream_model: str = ""

