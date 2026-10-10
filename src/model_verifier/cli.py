import argparse
import json

from model_verifier.client import mask_secret
from model_verifier.report import run_verification
from model_verifier.types import VerificationOptions, VerificationTarget
from model_verifier.url_safety import validate_public_base_url


def main() -> None:
    parser = argparse.ArgumentParser(description="Run black-box model verification against a compatible model gateway.")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--claimed-model", required=True)
    parser.add_argument("--provider-mode", choices=["auto", "openai", "anthropic"], default="auto")
    parser.add_argument("--timeout-seconds", type=float, default=90)
    args = parser.parse_args()

    target = VerificationTarget(
        source="cli",
        base_url=validate_public_base_url(args.base_url),
        model=args.model.strip(),
        api_key=args.api_key.strip(),
        api_key_masked=mask_secret(args.api_key.strip()),
        site_name="CLI",
    )
    options = VerificationOptions(
        claimed_model=args.claimed_model.strip(),
        provider_mode=args.provider_mode,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(run_verification(target, options), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
