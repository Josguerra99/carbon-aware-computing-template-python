#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

bash "$(dirname "$0")/../ensure-env.sh"

if [[ ! -x .venv/bin/python ]]; then
  echo ".venv missing — running setup..."
  bash "$(dirname "$0")/setup.sh"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PORT="${PORT:-3916}"
echo "Starting forecast server (uvicorn) on port ${PORT}..."
exec python -m uvicorn src.server.index:app --host 0.0.0.0 --port "$PORT"
