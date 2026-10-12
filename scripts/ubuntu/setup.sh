#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== Carbon-aware template (Python) — Ubuntu setup ==="
echo "Installs: python3-venv, pip packages from requirements.txt."
echo "Before run: set MAIN_SERVER_URL in .env to the URL from your facilitator."
echo ""

bash "$(dirname "$0")/../ensure-env.sh"

ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c "import sys; assert sys.version_info >= (3, 10)"
    echo "Python: $(python3 --version)"
    return
  fi
  echo "Installing python3, python3-venv, python3-pip..."
  sudo apt-get update -qq
  sudo apt-get install -y python3 python3-venv python3-pip
  echo "Python: $(python3 --version)"
}

ensure_python

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo ""
echo "Setup complete. Run: bash scripts/ubuntu/run.sh"
