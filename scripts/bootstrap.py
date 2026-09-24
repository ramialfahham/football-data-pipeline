"""Set up a fresh clone of this repo with one command, and prove it works with a second.

    python scripts/bootstrap.py            # set up everything that needs no credentials
    python scripts/bootstrap.py --verify   # tests, pre-commit on all files, site build
    python scripts/bootstrap.py --fetch-key  # API key from Secret Manager into .env (you run it)

Every step skips itself when its work is already done, and no existing local file is overwritten.
Standard library only: it runs before any dependency is installed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_VERSION = (3, 11)
NODE_MAJOR = 24
REQUIREMENTS = ("requirements.txt", "requirements-dev.txt", "requirements-ui.txt")
LOCAL_COPIES = ((".env.example", ".env"), ("dbt_project/profiles.example.yml", "profiles.yml"))
GCP_PROJECT = "football-data-pipeline-gcp"
API_KEY_SECRET_NAME = "api-football-key"
API_KEY_VAR = "API_FOOTBALL_API_KEY"

# The deepest file an install writes is 150 characters below the repo root
# (.venv\Lib\site-packages\google\cloud\bigquery_storage_v1alpha\...). Windows refuses paths over
# 259 characters unless long paths are enabled, so 80 leaves room for dependencies to grow.
MAX_ROOT_CHARS_WITHOUT_LONG_PATHS = 80


class SetupError(Exception):
    pass


def say(status: str, message: str) -> None:
    print(f"[{status}] {message}", flush=True)


def run(cmd: list[str], cwd: Path = ROOT) -> None:
    say("run", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise SetupError(f"`{' '.join(cmd)}` failed with exit code {result.returncode}")


def tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise SetupError(f"`{name}` is not installed or not on PATH. See README 'Getting started'.")
    return found


def venv_tool(name: str, root: Path = ROOT) -> Path:
    if os.name == "nt":
        return root / ".venv" / "Scripts" / f"{name}.exe"
    return root / ".venv" / "bin" / name


def venv_python(root: Path = ROOT) -> Path:
    return venv_tool("python", root)


def path_too_long(root: Path, is_windows: bool, long_paths_enabled: bool) -> bool:
    return is_windows and not long_paths_enabled and len(str(root)) > MAX_ROOT_CHARS_WITHOUT_LONG_PATHS


def windows_long_paths_enabled() -> bool:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
            return winreg.QueryValueEx(key, "LongPathsEnabled")[0] == 1
    except OSError:
        return False


def remote_rename_needed(remotes: dict[str, str]) -> bool:
    return "gitlab" not in remotes and "gitlab.com" in remotes.get("origin", "")


def copy_if_missing(source: Path, target: Path) -> bool:
    if target.exists():
        return False
    shutil.copyfile(source, target)
    return True


def npm_install_needed(site: Path) -> bool:
    installed = site / "node_modules" / ".package-lock.json"
    lock = site / "package-lock.json"
    return not installed.exists() or lock.stat().st_mtime > installed.stat().st_mtime


def write_api_key(env_file: Path, key: str) -> None:
    lines = env_file.read_text(encoding="utf-8").splitlines(keepends=True)
    prefix = f"{API_KEY_VAR}="
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            if line[len(prefix):].strip():
                raise SetupError(f"{API_KEY_VAR} already has a value in .env; it is not overwritten.")
            lines[index] = f"{prefix}{key}\n"
            break
    else:
        lines.append(f"{prefix}{key}\n")
    env_file.write_text("".join(lines), encoding="utf-8")


def check_prerequisites() -> None:
    if sys.version_info[:2] != PYTHON_VERSION:
        raise SetupError(
            f"Run this with Python {PYTHON_VERSION[0]}.{PYTHON_VERSION[1]} (found "
            f"{sys.version_info[0]}.{sys.version_info[1]}). On Windows: py -3.11 scripts/bootstrap.py"
        )
    if os.name == "nt" and path_too_long(ROOT, True, windows_long_paths_enabled()):
        raise SetupError(
            f"The repo folder path is {len(str(ROOT))} characters long and Windows long paths are off, "
            "so the install would fail with 'file name too long'. Clone into a short folder "
            r"(for example C:\src\football-data-pipeline), or turn on long paths as described in "
            "the README."
        )
    node = subprocess.run([tool("node"), "--version"], capture_output=True, text=True).stdout.strip()
    if not node.startswith(f"v{NODE_MAJOR}."):
        raise SetupError(f"Node {NODE_MAJOR} is required (found {node or 'none'}).")
    tool("npm")
    tool("git")


def check_hooks_path() -> None:
    result = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"], cwd=ROOT, capture_output=True, text=True
    )
    if result.stdout.strip():
        raise SetupError(
            "git's core.hooksPath is set, so pre-commit cannot install its hooks. "
            "Remove it with: git config --unset-all core.hooksPath (then run this again)."
        )


def set_up_remote() -> None:
    names = subprocess.run(["git", "remote"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    remotes = {
        name: subprocess.run(
            ["git", "remote", "get-url", name], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
        for name in names
    }
    if remote_rename_needed(remotes):
        run(["git", "remote", "rename", "origin", "gitlab"])
    else:
        say("skip", "git remote: nothing to rename")


def set_up_python() -> Path:
    python = venv_python()
    if python.exists():
        say("skip", ".venv exists")
    else:
        run([sys.executable, "-m", "venv", ".venv"])
    version = subprocess.run(
        [str(python), "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
        capture_output=True,
        text=True,
    ).stdout.split()
    if tuple(int(part) for part in version) != PYTHON_VERSION:
        raise SetupError(
            f".venv uses Python {'.'.join(version)}, not {PYTHON_VERSION[0]}.{PYTHON_VERSION[1]}. "
            "Delete .venv and run this again."
        )
    run([str(python), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    install = [str(python), "-m", "pip", "install", "--quiet"]
    for requirements in REQUIREMENTS:
        install += ["-r", requirements]
    run(install)
    return python


def set_up_local_files() -> None:
    for source, target in LOCAL_COPIES:
        if copy_if_missing(ROOT / source, ROOT / target):
            say("ok", f"created {target} from {source}")
        else:
            say("skip", f"{target} exists, left unchanged")


def set_up(python: Path) -> None:
    run([str(python), "-m", "pre_commit", "install", "--install-hooks"])
    site = ROOT / "site_v2"
    if npm_install_needed(site):
        run([tool("npm"), "ci", "--no-audit", "--no-fund"], cwd=site)
    else:
        say("skip", "site_v2/node_modules is up to date")
    run([str(venv_tool("dbt")), "deps", "--project-dir", "dbt_project", "--quiet"])
    run([str(python), "-m", "playwright", "install", "chromium"])


def verify(python: Path) -> None:
    run([str(python), "-m", "pytest", "tests", "-q", "--no-header"])
    run([str(python), "-m", "pre_commit", "run", "--all-files", "--show-diff-on-failure"])
    run([tool("npm"), "run", "build"], cwd=ROOT / "site_v2")


def fetch_key() -> None:
    env_file = ROOT / ".env"
    copy_if_missing(ROOT / ".env.example", env_file)
    result = subprocess.run(
        [
            tool("gcloud"),
            "secrets",
            "versions",
            "access",
            "latest",
            f"--secret={API_KEY_SECRET_NAME}",
            f"--project={GCP_PROJECT}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SetupError(f"gcloud could not read the secret: {result.stderr.strip()}")
    key = result.stdout.strip()
    if not key:
        raise SetupError("the secret is empty")
    write_api_key(env_file, key)
    say("ok", f"{API_KEY_VAR} written to .env")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="prove the setup works (no credentials)")
    mode.add_argument("--fetch-key", action="store_true", help="API key from Secret Manager into .env")
    args = parser.parse_args(argv)
    try:
        if args.fetch_key:
            fetch_key()
            return 0
        if args.verify:
            python = venv_python()
            if not python.exists():
                raise SetupError("no .venv yet: run `python scripts/bootstrap.py` first")
            verify(python)
            say("ok", "verified: tests, pre-commit and the site build pass")
            return 0
        check_prerequisites()
        check_hooks_path()
        set_up_remote()
        python = set_up_python()
        set_up_local_files()
        set_up(python)
        say("ok", "setup complete. Prove it with: python scripts/bootstrap.py --verify")
        return 0
    except SetupError as error:
        say("stop", str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
