#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
ENTRYPOINT_FILE = PROJECT_ROOT / "sms_panel_desktop.py"
VENV_DIR = PROJECT_ROOT / ".venv"
RETRY_ENV_VAR = "SMS_PANEL_BOOTSTRAP_RETRIES"
DEFAULT_RETRY_LIMIT = 3
RETRY_DELAY_SECONDS = 2


def retry_limit() -> int:
    raw = os.environ.get(RETRY_ENV_VAR, "").strip()
    if not raw:
        return DEFAULT_RETRY_LIMIT
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_RETRY_LIMIT
    return max(0, value)


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run_command(command: list[str]) -> bool:
    print(f"[bootstrap] Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=PROJECT_ROOT)
    return result.returncode == 0


def recreate_virtualenv() -> bool:
    if VENV_DIR.exists():
        print(f"[bootstrap] Removing failed environment: {VENV_DIR}")
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    return run_command([sys.executable, "-m", "venv", str(VENV_DIR)])


def install_dependencies(python_bin: Path) -> bool:
    return run_command([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"]) and run_command(
        [str(python_bin), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
    )


def launch_app(python_bin: Path) -> int:
    print("[bootstrap] Dependencies installed successfully. Launching app...")
    return subprocess.call([str(python_bin), str(ENTRYPOINT_FILE)], cwd=PROJECT_ROOT)


def main() -> int:
    if not REQUIREMENTS_FILE.exists():
        print(f"[bootstrap] Missing file: {REQUIREMENTS_FILE}")
        return 1
    if not ENTRYPOINT_FILE.exists():
        print(f"[bootstrap] Missing file: {ENTRYPOINT_FILE}")
        return 1

    limit = retry_limit()
    attempt = 1

    while limit == 0 or attempt <= limit:
        print(f"\n[bootstrap] Setup attempt {attempt}")

        if recreate_virtualenv():
            python_bin = venv_python()
            if python_bin.exists() and install_dependencies(python_bin):
                return launch_app(python_bin)

        print("[bootstrap] Setup failed. Restarting from scratch...")
        attempt += 1
        time.sleep(RETRY_DELAY_SECONDS)

    print(f"[bootstrap] Setup failed after {limit} attempts.")
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[bootstrap] Cancelled by user.")
        raise SystemExit(130)
