#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if command -v python3 >/dev/null 2>&1; then
  exec python3 run_sms_panel.py
fi

if command -v python >/dev/null 2>&1; then
  exec python run_sms_panel.py
fi

echo "Python 3 is required but was not found in PATH."
exit 1
