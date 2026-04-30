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
NETWORK_ERROR_MARKERS = (
    "could not fetch url",
    "failed to establish a new connection",
    "temporary failure in name resolution",
    "name or service not known",
    "connection timed out",
    "read timed out",
    "connection aborted",
    "network is unreachable",
    "proxy error",
    "remote end closed connection",
)


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


def run_command(command: list[str]) -> tuple[bool, str]:
    print(f"[bootstrap] Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    combined_output = f"{result.stdout or ''}\n{result.stderr or ''}"
    return result.returncode == 0, combined_output


def has_network_issue(pip_output: str) -> bool:
    output = pip_output.lower()
    return any(marker in output for marker in NETWORK_ERROR_MARKERS)


def recreate_virtualenv() -> bool:
    if VENV_DIR.exists():
        print(f"[bootstrap] Removing failed environment: {VENV_DIR}")
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    ok, _ = run_command([sys.executable, "-m", "venv", str(VENV_DIR)])
    return ok


def read_packages_from_requirements() -> list[str]:
    packages: list[str] = []
    for raw in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            continue
        packages.append(line)
    return packages


def install_with_default_index(python_bin: Path) -> tuple[bool, bool]:
    ok, output = run_command([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
    if not ok:
        return False, has_network_issue(output)

    ok, output = run_command([str(python_bin), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
    if ok:
        return True, False
    return False, has_network_issue(output)


def install_with_national_mirror(python_bin: Path) -> bool:
    print(f"[bootstrap] Switching to national mirror: {MIRROR_INDEX_URL}")
    ok, _ = run_command(
        [str(python_bin), "-m", "pip", "install", "--upgrade", "pip", "-i", MIRROR_INDEX_URL]
    )
    if not ok:
        return False

    packages = read_packages_from_requirements()
    if not packages:
        ok, _ = run_command(
            [str(python_bin), "-m", "pip", "install", "-i", MIRROR_INDEX_URL, "-r", str(REQUIREMENTS_FILE)]
        )
        return ok

    for package in packages:
        ok, _ = run_command([str(python_bin), "-m", "pip", "install", "-i", MIRROR_INDEX_URL, package])
        if not ok:
            return False
    return True


def install_dependencies(python_bin: Path) -> bool:
    ok, had_network_issue = install_with_default_index(python_bin)
    if ok:
        return True

    if had_network_issue:
        print("[bootstrap] Warning: Cannot reach the default PyPI server.")
        return install_with_national_mirror(python_bin)

    return False


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
