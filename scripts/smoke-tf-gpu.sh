#!/usr/bin/env bash
set -eu
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
sed -i 's/\r$//' scripts/*.sh 2>/dev/null || true

if [[ ! -f .venv/bin/activate ]]; then
  echo "ERROR: .venv missing"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
export TF_BACKEND="${TF_BACKEND:-gpu}"
exec python -c "from src.core.tf_backend import ensure_tf_backend; ensure_tf_backend()"
