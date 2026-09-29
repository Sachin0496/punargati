#!/usr/bin/env bash
# macOS / Linux / x64 Windows-WSL: CPU fallback so anyone can try PunarGati.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m punargati.models download
.venv/bin/python -m punargati.doctor
echo "Run with: scripts/run.sh"
