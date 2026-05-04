#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
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
BOOTSTRAP_STATE_FILE = VENV_DIR / ".bootstrap_state.json"
READY_CHECK_FLAG = "--is-bootstrap-ready"


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
    print(f"[bootstrap] Running: {' '.join(command)}", flush=True)
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    try:
        process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            bufsize=1,
        )
    except OSError as exc:
        message = f"[bootstrap] Failed to start command: {exc}\n"
        print(message, end="", file=sys.stderr, flush=True)
        return False, message

    output_lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        output_lines.append(line)
        print(line, end="", flush=True)

    return_code = process.wait()
    combined_output = "".join(output_lines)
    return return_code == 0, combined_output


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


def requirements_hash() -> str:
    digest = hashlib.sha256()
    digest.update(REQUIREMENTS_FILE.read_bytes())
    return digest.hexdigest()


def expected_bootstrap_state() -> dict[str, str]:
    return {
        "requirements_sha256": requirements_hash(),
        "mirror_index_url": MIRROR_INDEX_URL,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
    }


def load_bootstrap_state() -> dict[str, str] | None:
    if not BOOTSTRAP_STATE_FILE.exists():
        return None
    try:
        data = json.loads(BOOTSTRAP_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    return {str(key): str(value) for key, value in data.items()}


def save_bootstrap_state() -> None:
    try:
        BOOTSTRAP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BOOTSTRAP_STATE_FILE.write_text(
            json.dumps(expected_bootstrap_state(), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"[bootstrap] Warning: Could not save bootstrap state file: {exc}")


def is_bootstrap_ready(python_bin: Path) -> bool:
    if not VENV_DIR.exists() or not python_bin.exists():
        return False
    state = load_bootstrap_state()
    if not state:
        return False
    expected = expected_bootstrap_state()
    for key, value in expected.items():
        if state.get(key) != value:
            return False
    return True


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
    print("[bootstrap] Launching app...")
    if os.name != "nt":
        return subprocess.call([str(python_bin), str(ENTRYPOINT_FILE)], cwd=PROJECT_ROOT)

    scripts_dir = python_bin.parent
    pythonw_bin = scripts_dir / "pythonw.exe"
    if not pythonw_bin.exists():
        pythonw_bin = scripts_dir / "venvwlauncher.exe"

    launch_bin = pythonw_bin if pythonw_bin.exists() else python_bin
    creationflags = 0
    if launch_bin == python_bin:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    try:
        subprocess.Popen(
            [str(launch_bin), str(ENTRYPOINT_FILE)],
            cwd=PROJECT_ROOT,
            close_fds=True,
            creationflags=creationflags,
        )
    except OSError as exc:
        print(f"[bootstrap] Failed to start app process: {exc}")
        return 1

    print("[bootstrap] App started. Closing bootstrap console.")
    return 0


def main() -> int:
    if not REQUIREMENTS_FILE.exists():
        print(f"[bootstrap] Missing file: {REQUIREMENTS_FILE}")
        return 1
    if not ENTRYPOINT_FILE.exists():
        print(f"[bootstrap] Missing file: {ENTRYPOINT_FILE}")
        return 1

    python_bin = venv_python()
    if READY_CHECK_FLAG in sys.argv[1:]:
        return 0 if is_bootstrap_ready(python_bin) else 1

    if is_bootstrap_ready(python_bin):
        print("[bootstrap] Existing environment is ready. Skipping bootstrap steps.")
        return launch_app(python_bin)

    upgrade_pip = should_upgrade_pip()
    limit = retry_limit()
    attempt = 1

    while limit == 0 or attempt <= limit:
        print(f"\n[bootstrap] Setup attempt {attempt}")

        if recreate_virtualenv():
            python_bin = venv_python()
            if python_bin.exists() and install_dependencies(python_bin, upgrade_pip):
                app_exit_code = launch_app(python_bin)
                if app_exit_code == 0:
                    save_bootstrap_state()
                return app_exit_code

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
