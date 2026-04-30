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
MIRROR_INDEX_URL = "https://mirror-pypi.runflare.com/simple"


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


def run_command(command: list[str], extra_env: dict[str, str] | None = None) -> tuple[bool, str]:
    print(f"[bootstrap] Running: {' '.join(command)}")
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, env=env)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    combined_output = f"{result.stdout or ''}\n{result.stderr or ''}"
    return result.returncode == 0, combined_output


def recreate_virtualenv() -> bool:
    if VENV_DIR.exists():
        print(f"[bootstrap] Removing failed environment: {VENV_DIR}")
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    ok, _ = run_command([sys.executable, "-m", "venv", str(VENV_DIR)])
    return ok


def pip_mirror_env() -> dict[str, str]:
    return {
        # Disable all pip config files to avoid silently falling back to other indexes.
        "PIP_CONFIG_FILE": os.devnull,
        "PIP_INDEX_URL": MIRROR_INDEX_URL,
    }


def should_upgrade_pip() -> bool:
    if not sys.stdin or not sys.stdin.isatty():
        print("[bootstrap] Non-interactive mode detected. pip upgrade is skipped.")
        return False

    while True:
        try:
            choice = input(
                "[bootstrap] Do you want to upgrade pip from the mirror before installing dependencies? [y/N]: "
            )
        except EOFError:
            print("\n[bootstrap] No input received. pip upgrade is skipped.")
            return False

        answer = choice.strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"", "n", "no"}:
            return False
        print("[bootstrap] Please answer with 'y' or 'n'.")


def install_dependencies(python_bin: Path, upgrade_pip: bool) -> bool:
    mirror_env = pip_mirror_env()
    print(f"[bootstrap] Installing dependencies only from mirror: {MIRROR_INDEX_URL}")

    if upgrade_pip:
        ok, _ = run_command(
            [str(python_bin), "-m", "pip", "install", "--upgrade", "pip", "-i", MIRROR_INDEX_URL],
            extra_env=mirror_env,
        )
        if not ok:
            return False
    else:
        print("[bootstrap] Skipping pip upgrade by user choice.")

    ok, _ = run_command(
        [str(python_bin), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE), "-i", MIRROR_INDEX_URL],
        extra_env=mirror_env,
    )
    return ok


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

    upgrade_pip = should_upgrade_pip()
    limit = retry_limit()
    attempt = 1

    while limit == 0 or attempt <= limit:
        print(f"\n[bootstrap] Setup attempt {attempt}")

        if recreate_virtualenv():
            python_bin = venv_python()
            if python_bin.exists() and install_dependencies(python_bin, upgrade_pip):
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
