#!/usr/bin/env bash
set -euo pipefail

# Deploy Model Verifier AI by Eka Syarif Maulana to a Docker host reachable over SSH.
#
# Usage:
#   scripts/deploy.sh
#
# Optional overrides:
#   REMOTE=your-server
#   DEPLOY_DIR=/opt/model-verifier
#   APP_PORT=2004
#   PUBLIC_WEB_URL=https://example.com/verify
#   MODEL_VERIFIER_HOST_API_BASE_URL=https://example.com
#   MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL=http://host-api:8000
#   MODEL_VERIFIER_HOST_API_NETWORK=host_api_network
#   COMPOSE_PROJECT=model-verifier
#   LOCAL_ENV_FILE=/absolute/path/to/.env.production

REMOTE="${REMOTE:-}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/model-verifier}"
APP_PORT="${APP_PORT:-2004}"
PUBLIC_WEB_URL="${PUBLIC_WEB_URL:-http://127.0.0.1:$APP_PORT/verify}"
MODEL_VERIFIER_HOST_API_BASE_URL="${MODEL_VERIFIER_HOST_API_BASE_URL:-}"
MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL="${MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL:-}"
MODEL_VERIFIER_HOST_API_NETWORK="${MODEL_VERIFIER_HOST_API_NETWORK:-}"
COMPOSE_PROJECT="${COMPOSE_PROJECT:-model-verifier}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

LOCAL_ENV_FILE="${LOCAL_ENV_FILE:-}"
if [[ -z "$LOCAL_ENV_FILE" && -f "$REPO_ROOT/.env.production" ]]; then
  LOCAL_ENV_FILE="$REPO_ROOT/.env.production"
fi

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

shell_quote() {
  printf "%q" "$1"
}

require_cmd ssh
require_cmd rsync

if [[ -z "$REMOTE" ]]; then
  echo "REMOTE is required. Example:" >&2
  echo "  REMOTE=your-server PUBLIC_WEB_URL=https://example.com/verify scripts/deploy.sh" >&2
  exit 1
fi

echo "==> Deploy target: $REMOTE:$DEPLOY_DIR"
echo "==> Public URL: $PUBLIC_WEB_URL"
echo "==> Host API: ${MODEL_VERIFIER_HOST_API_BASE_URL:-disabled}"
echo "==> Host API internal: ${MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL:-disabled}"
echo "==> App port on server localhost: $APP_PORT"

ssh "$REMOTE" "DEPLOY_DIR=$(shell_quote "$DEPLOY_DIR") bash -s" <<'REMOTE_PREPARE'
set -euo pipefail

command -v rsync >/dev/null 2>&1 || {
  echo "Missing required command on remote server: rsync" >&2
  exit 1
}
command -v docker >/dev/null 2>&1 || {
  echo "Missing required command on remote server: docker" >&2
  exit 1
}
docker compose version >/dev/null 2>&1 || {
  echo "Missing required command on remote server: docker compose" >&2
  exit 1
}

if [[ ! -d "$DEPLOY_DIR" ]]; then
  sudo mkdir -p "$DEPLOY_DIR"
  sudo chown "$(id -un):$(id -gn)" "$DEPLOY_DIR"
fi
mkdir -p "$DEPLOY_DIR/current"
REMOTE_PREPARE

echo "==> Syncing project files"
rsync -az --delete \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude 'node_modules/' \
  --exclude 'apps/web/node_modules/' \
  --exclude 'apps/web/dist/' \
  --exclude 'apps/web/tsconfig.tsbuildinfo' \
  --exclude '*.egg-info/' \
  --exclude '.pytest_cache/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.DS_Store' \
  --exclude '.env' \
  --exclude '.env.*' \
  --exclude 'runtime/' \
  "$REPO_ROOT/" "$REMOTE:$DEPLOY_DIR/current/"

if [[ -n "$LOCAL_ENV_FILE" ]]; then
  if [[ ! -f "$LOCAL_ENV_FILE" ]]; then
    echo "LOCAL_ENV_FILE does not exist: $LOCAL_ENV_FILE" >&2
    exit 1
  fi
  echo "==> Uploading env file: $LOCAL_ENV_FILE"
  rsync -az "$LOCAL_ENV_FILE" "$REMOTE:$DEPLOY_DIR/current/.env"
else
  echo "==> No local env file provided; remote .env will be created only if missing"
fi

echo "==> Preparing remote runtime files"
ssh "$REMOTE" \
  "DEPLOY_DIR=$(shell_quote "$DEPLOY_DIR") APP_PORT=$(shell_quote "$APP_PORT") PUBLIC_WEB_URL=$(shell_quote "$PUBLIC_WEB_URL") MODEL_VERIFIER_HOST_API_BASE_URL=$(shell_quote "$MODEL_VERIFIER_HOST_API_BASE_URL") MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL=$(shell_quote "$MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL") MODEL_VERIFIER_HOST_API_NETWORK=$(shell_quote "$MODEL_VERIFIER_HOST_API_NETWORK") COMPOSE_PROJECT=$(shell_quote "$COMPOSE_PROJECT") bash -s" <<'REMOTE_BOOTSTRAP'
set -euo pipefail

cd "$DEPLOY_DIR/current"
mkdir -p ops

set_env_var() {
  local key="$1"
  local value="$2"
  local tmp
  tmp="$(mktemp)"
  if [[ -f .env ]]; then
    awk -v key="$key" -v value="$value" '
      BEGIN { done = 0 }
      $0 ~ "^" key "=" { print key "=" value; done = 1; next }
      { print }
      END { if (!done) print key "=" value }
    ' .env > "$tmp"
  else
    printf '%s=%s\n' "$key" "$value" > "$tmp"
  fi
  mv "$tmp" .env
}

set_env_var PUBLIC_WEB_URL "$PUBLIC_WEB_URL"
set_env_var APP_PORT "$APP_PORT"
set_env_var MODEL_VERIFIER_HOST_API_BASE_URL "$MODEL_VERIFIER_HOST_API_BASE_URL"
set_env_var MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL "$MODEL_VERIFIER_HOST_API_INTERNAL_BASE_URL"
set_env_var MODEL_VERIFIER_HOST_API_NETWORK "$MODEL_VERIFIER_HOST_API_NETWORK"

cat > ops/web-nginx.conf <<'NGINX'
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    client_max_body_size 20m;
    resolver 127.0.0.11 ipv6=off valid=30s;

    location = /verify {
        return 301 /verify/;
    }

    location /verify/api/ {
        set $api_upstream api:7860;
        proxy_pass http://$api_upstream;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 60s;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }

    location /verify/ {
        try_files $uri $uri/ /verify/index.html;
    }
}
NGINX

cat > ops/nginx-verify-location.conf <<'NGINX'
# Add this location block to your HTTPS server.
# It routes /verify and /verify/* to this verifier service.
location = /verify {
    return 301 /verify/;
}

location /verify/ {
    proxy_pass http://127.0.0.1:__APP_PORT__;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_connect_timeout 60s;
    proxy_read_timeout 600s;
    proxy_send_timeout 600s;
}
NGINX
sed -i "s/__APP_PORT__/$APP_PORT/g" ops/nginx-verify-location.conf

cat > ops/Dockerfile.api.prod <<'DOCKERFILE'
FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src
RUN pip install --no-cache-dir -e /app

EXPOSE 7860
CMD ["model-verifier-demo", "--host", "0.0.0.0", "--port", "7860"]
DOCKERFILE

cat > ops/Dockerfile.web.prod <<'DOCKERFILE'
FROM node:23-alpine AS build

WORKDIR /app/apps/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

FROM nginx:1.30.2-alpine
COPY ops/web-nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/web/dist /usr/share/nginx/html/verify
DOCKERFILE

cat > docker-compose.prod.yml <<'COMPOSE'
services:
  api:
    build:
      context: .
      dockerfile: ops/Dockerfile.api.prod
    restart: unless-stopped
    env_file: .env
    expose:
      - "7860"

  web:
    build:
      context: .
      dockerfile: ops/Dockerfile.web.prod
    restart: unless-stopped
    ports:
      - "127.0.0.1:${APP_PORT:-2004}:80"
    depends_on:
      - api
COMPOSE

if [[ -n "$MODEL_VERIFIER_HOST_API_NETWORK" ]]; then
  cat >> docker-compose.prod.yml <<'COMPOSE'

networks:
  host-api:
    external: true
    name: ${MODEL_VERIFIER_HOST_API_NETWORK}
COMPOSE
  awk '
    { print }
    /^    expose:$/ { in_api = 1 }
    in_api && /^      - "7860"$/ {
      print "    networks:"
      print "      - default"
      print "      - host-api"
      in_api = 0
    }
  ' docker-compose.prod.yml > docker-compose.prod.yml.tmp
  mv docker-compose.prod.yml.tmp docker-compose.prod.yml
fi

docker compose -p "$COMPOSE_PROJECT" -f docker-compose.prod.yml down --remove-orphans || true

if command -v lsof >/dev/null 2>&1; then
  busy_pids="$(lsof -tiTCP:"$APP_PORT" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$busy_pids" ]]; then
    echo "Port $APP_PORT is still in use on the server:" >&2
    ps -fp $busy_pids >&2 || true
    exit 1
  fi
fi

docker compose -p "$COMPOSE_PROJECT" -f docker-compose.prod.yml build --pull api web
docker compose -p "$COMPOSE_PROJECT" -f docker-compose.prod.yml up -d --remove-orphans

echo "Waiting for health check..."
for attempt in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:$APP_PORT/verify/api/health" >/dev/null; then
    echo "Health check passed."
    exit 0
  fi
  sleep 2
done

echo "Health check failed. Recent container status:" >&2
docker compose -p "$COMPOSE_PROJECT" -f docker-compose.prod.yml ps >&2 || true
docker compose -p "$COMPOSE_PROJECT" -f docker-compose.prod.yml logs --tail=120 api web >&2 || true
exit 1
REMOTE_BOOTSTRAP

echo "==> Deploy finished"
echo "Open: $PUBLIC_WEB_URL"
echo "Health: $PUBLIC_WEB_URL/api/health"
