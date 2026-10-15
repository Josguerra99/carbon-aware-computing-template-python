#!/usr/bin/env bash
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

WORKSHOP_PORT="${WORKSHOP_PORT:-3915}"

if ! grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  echo "ERROR: Run inside WSL, or use npm run start:wsl from Windows."
  exit 1
fi

if [[ ! -f .venv/bin/activate ]]; then
  echo "ERROR: .venv missing. Run: npm run setup:wsl"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

set -a
if [[ -f .env ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line//$'\r'/}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    export "$line"
  done < .env
fi
set +a

export TF_BACKEND="${TF_BACKEND:-gpu}"

check_health() {
  local base="$1"
  base="${base%/}"
  curl -4 -sf --connect-timeout 2 --max-time 4 "${base}/api/health" >/dev/null
}

MAIN_RESOLVED=""
env_base="${MAIN_SERVER_URL:-}"
env_base="${env_base%/}"
if [[ -n "$env_base" ]] && check_health "$env_base"; then
  MAIN_RESOLVED="$env_base"
  echo "Workshop site OK at MAIN_SERVER_URL from .env ($MAIN_RESOLVED)"
fi

if [[ -z "$MAIN_RESOLVED" ]]; then
  for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if candidate="$(bash scripts/wsl-resolve-main-url.sh)" && check_health "$candidate"; then
      MAIN_RESOLVED="$candidate"
      break
    fi
    if [[ "$attempt" -lt 10 ]]; then
      echo "Waiting for workshop site on port ${WORKSHOP_PORT} (attempt ${attempt}/10)..."
      sleep 2
    fi
  done
fi

if [[ -z "$MAIN_RESOLVED" ]]; then
  echo "ERROR: Workshop site not reachable from WSL."
  exit 1
fi

export MAIN_SERVER_URL="$MAIN_RESOLVED"

if [[ "${WIN_PROXY:-}" == "1" ]]; then
  PORT=3917
  echo "WSL team server on port ${PORT} (Windows proxy publishes :3916)"
else
  PORT="${PORT:-3916}"
fi
export PORT

UVICORN_RELOAD="${UVICORN_RELOAD:-${NODEMON_RELOAD:-1}}"
echo "TF_BACKEND=${TF_BACKEND} | MAIN_SERVER_URL=${MAIN_SERVER_URL}"
echo "Forecast server on http://0.0.0.0:${PORT}"

if [[ "$UVICORN_RELOAD" == "1" || "$UVICORN_RELOAD" == "true" ]]; then
  echo "Uvicorn reload: edits under src/ restart server and retrain."
  exec python -m uvicorn src.server.index:app --host 0.0.0.0 --port "$PORT" --reload
fi

exec python -m uvicorn src.server.index:app --host 0.0.0.0 --port "$PORT"
