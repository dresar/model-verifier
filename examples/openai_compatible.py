import os

from model_verifier.report import run_verification
from model_verifier.types import VerificationOptions, VerificationTarget


report = run_verification(
    VerificationTarget(
        source="example",
        base_url=os.environ["OPENAI_COMPATIBLE_BASE_URL"],
        model=os.environ["MODEL_NAME"],
        api_key=os.environ["API_KEY"],
        api_key_masked="***",
        site_name="OpenAI-compatible example",
    ),
    VerificationOptions(claimed_model=os.environ["CLAIMED_MODEL"], provider_mode="openai"),
)

print(report["verdict"], report["confidence_score"])
