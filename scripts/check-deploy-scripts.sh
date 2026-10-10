#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

bash -n scripts/dev-local.sh
bash -n scripts/start.sh
bash -n scripts/deploy.sh

grep -q 'REMOTE="${REMOTE:-}"' scripts/deploy.sh
grep -q 'DEPLOY_DIR="${DEPLOY_DIR:-/opt/model-verifier}"' scripts/deploy.sh
grep -q 'APP_PORT="${APP_PORT:-2004}"' scripts/deploy.sh
grep -q 'PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-http://127.0.0.1:$APP_PORT/verify}"' scripts/deploy.sh
grep -q 'MODEL_VERIFIER_HOST_API_BASE_URL="${MODEL_VERIFIER_HOST_API_BASE_URL:-}"' scripts/deploy.sh
grep -q 'MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL="${MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL:-}"' scripts/deploy.sh
grep -q 'MODEL_VERIFIER_HOST_API_NETWORK="${MODEL_VERIFIER_HOST_API_NETWORK:-}"' scripts/deploy.sh
grep -q 'REMOTE is required' scripts/deploy.sh
grep -q 'set_env_var APP_PORT "$APP_PORT"' scripts/deploy.sh
grep -q 'COPY --from=build /app/apps/web/dist /usr/share/nginx/html/verify' scripts/deploy.sh
grep -q 'location = /verify' scripts/deploy.sh
grep -q 'http://127.0.0.1:$APP_PORT/verify/api/health' scripts/deploy.sh
grep -q 'ops/nginx-verify-location.conf' scripts/deploy.sh
grep -q 'MODEL_VERIFIER_HOST_API_BASE_URL="${MODEL_VERIFIER_HOST_API_BASE_URL:-http://127.0.0.1:8000}"' scripts/dev-local.sh
grep -q 'MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL="${MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL:-$MODEL_VERIFIER_HOST_API_BASE_URL}"' scripts/dev-local.sh

echo "deploy scripts contract ok"
