#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  echo "[ERROR] .venv not found. Please run the setup in SETUP_LOCAL.md first."
  exit 1
fi
source .venv/bin/activate
python server_main.py --port 6400 --reload
