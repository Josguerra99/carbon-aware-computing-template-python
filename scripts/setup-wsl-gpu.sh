#!/usr/bin/env bash
# Reinstall TensorFlow GPU wheel in the project .venv (WSL only).
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  echo "ERROR: Run inside WSL."
  exit 1
fi

if [[ ! -f .venv/bin/activate ]]; then
  echo "ERROR: .venv missing. Run: npm run setup:wsl"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip uninstall -y tensorflow tensorflow-intel 2>/dev/null || true
python -m pip install -r requirements-tf-gpu.txt

if grep -q '^TF_BACKEND=' .env 2>/dev/null; then
  sed -i 's/^TF_BACKEND=.*/TF_BACKEND=gpu/' .env
else
  echo "TF_BACKEND=gpu" >> .env
fi

echo "==> GPU TensorFlow installed. Smoke test:"
bash scripts/smoke-tf-gpu.sh
