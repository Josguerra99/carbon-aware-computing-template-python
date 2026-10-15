#!/usr/bin/env bash
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Carbon-aware Python template — WSL + TensorFlow"
echo "    $ROOT"

if ! grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  echo "ERROR: Run inside WSL. From Windows: npm run setup:wsl"
  exit 1
fi

PY=python3
if ! command -v "$PY" >/dev/null; then
  echo "ERROR: python3 not found. sudo apt install -y python3 python3-venv python3-pip"
  exit 1
fi

PY_VER="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "==> Python $PY_VER"

if command -v nvidia-smi >/dev/null 2>&1; then
  echo "==> GPU:"
  nvidia-smi -L || true
else
  echo "WARN: nvidia-smi not found in WSL. Install NVIDIA WSL drivers on Windows first."
fi

if ! "$PY" -m venv /tmp/cac-venv-probe >/dev/null 2>&1; then
  echo "==> Installing python venv (sudo may prompt)..."
  sudo apt-get update -qq
  sudo apt-get install -y python3 python3-pip python3-venv "python${PY_VER}-venv" || \
    sudo apt-get install -y python3 python3-pip python3-venv
fi
rm -rf /tmp/cac-venv-probe 2>/dev/null || true

echo "==> Project venv + requirements.txt..."
"$PY" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if command -v nvidia-smi >/dev/null 2>&1; then
  echo "==> NVIDIA visible — installing tensorflow[and-cuda] (requirements-tf-gpu.txt)..."
  python -m pip uninstall -y tensorflow tensorflow-intel 2>/dev/null || true
  python -m pip install -r requirements-tf-gpu.txt
  TF_MODE=gpu
else
  TF_MODE=cpu
fi

if [[ ! -f .env ]]; then
  cp .env.example .env 2>/dev/null || bash scripts/ensure-env.sh
fi

MAIN_URL="$(bash scripts/wsl-resolve-main-url.sh 2>/dev/null || echo "http://127.0.0.1:3915")"
export MAIN_SERVER_URL="$MAIN_URL"
export TF_MODE

python <<'PY'
from pathlib import Path
import os

path = Path(".env")
text = path.read_text(encoding="utf-8") if path.exists() else ""
main_url = os.environ.get("MAIN_SERVER_URL", "http://127.0.0.1:3915")
tf_mode = os.environ.get("TF_MODE", "cpu")

def set_line(key: str, value: str) -> None:
    global text
    line = f"{key}={value}"
    lines = text.splitlines()
    out = []
    found = False
    for row in lines:
        if row.startswith(f"{key}="):
            out.append(line)
            found = True
        else:
            out.append(row)
    if not found:
        out.append(line)
    text = "\n".join(out).rstrip() + "\n"

set_line("PORT", "3916")
set_line("MAIN_SERVER_URL", main_url)
set_line("TF_BACKEND", tf_mode)
path.write_text(text, encoding="utf-8")
print(f"==> .env updated (MAIN_SERVER_URL={main_url}, TF_BACKEND={tf_mode})")
PY

echo "==> Smoke test TensorFlow..."
if ! bash scripts/smoke-tf-gpu.sh 2>&1 | tee /tmp/tf-smoke.log; then
  echo "WARN: TensorFlow smoke test failed (see log)."
fi

cat <<EOF

==> Setup complete.

From WSL (uvicorn --reload):
  cd "$ROOT"
  source .venv/bin/activate
  bash scripts/start-wsl-tf.sh

From Windows (website on :3915 + proxy + WSL):
  npm run start:wsl

Do not pip install TensorFlow on Windows if you train in WSL — use the Linux .venv only.

EOF
