#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-7860}"
WEB_HOST="${WEB_HOST:-127.0.0.1}"
WEB_PORT="${WEB_PORT:-5174}"
MODEL_VERIFIER_HOST_API_BASE_URL="${MODEL_VERIFIER_HOST_API_BASE_URL:-http://127.0.0.1:8000}"
MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL="${MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL:-$MODEL_VERIFIER_HOST_API_BASE_URL}"

if [[ ! -d .venv ]]; then
  "$PYTHON_BIN" -m venv .venv
fi

VENV_PYTHON="$ROOT/.venv/bin/python"
"$VENV_PYTHON" -m pip install -e '.[test]'

if [[ ! -d apps/web/node_modules ]]; then
  npm --prefix apps/web install
fi

cleanup() {
  jobs -p | xargs -r kill >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "Model verifier API: http://$API_HOST:$API_PORT/verify/api/health"
echo "Model verifier Web: http://$WEB_HOST:$WEB_PORT/verify/"
echo "Host API proxy:     $MODEL_VERIFIER_HOST_API_BASE_URL"
echo "Host API internal:  $MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL"
echo

MODEL_VERIFIER_HOST_API_BASE_URL="$MODEL_VERIFIER_HOST_API_BASE_URL" \
MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL="$MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL" \
  "$ROOT/.venv/bin/model-verifier-demo" --host "$API_HOST" --port "$API_PORT" &

npm --prefix apps/web run dev -- --host "$WEB_HOST" --port "$WEB_PORT" --strictPort
