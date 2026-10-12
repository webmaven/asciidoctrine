#!/usr/bin/env python3
"""Cross-platform development helper for asciidoctrine.

AGENTS.md documents the development workflow using POSIX paths
(``venv/bin/pytest``, ``./run-tck.sh``). Those do not exist on Windows, where
the interpreter lives at ``venv\\Scripts\\python.exe`` and the shell scripts
require Git Bash. This wrapper resolves the correct interpreter and entry
points on both platforms so contributors never have to translate by hand.

Usage::

    python bin/dev.py setup          # create venv and install .[test]
    python bin/dev.py verify         # core tests + ruff + mypy
    python bin/dev.py all            # verify + doctest corpus
    python bin/dev.py tck            # run the upstream TCK suite
    python bin/dev.py tck-coverage   # run the TCK and print a coverage summary
    python bin/dev.py fmt            # auto-format with ruff
    python bin/dev.py pytest [args]  # run pytest with forwarded arguments

The equivalent POSIX workflow (Linux/macOS) is unchanged -- this script is a
convenience wrapper, not a replacement.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / "venv"

# Windows keeps the interpreter and scripts under Scripts\, POSIX under bin/.
SCRIPTS = "Scripts" if os.name == "nt" else "bin"
PYTHON = VENV / SCRIPTS / ("python.exe" if os.name == "nt" else "python3")

USAGE = """\
Commands:
  setup          Create venv/ and install the test extras
  verify         Core tests + ruff format/lint + mypy  (Tier 2 pre-commit)
  all            verify + the real-world doctest corpus
  tck            Run the upstream Node.js TCK suite
  tck-coverage   Run the TCK and print a coverage summary
  fmt            Auto-format and lint-fix with ruff
  pytest [args]  Run pytest, forwarding any extra arguments
"""


def die(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def venv_python() -> Path:
    if not PYTHON.exists():
        raise SystemExit(
            die(
                f"no virtual environment at {VENV}.\n"
                "Create one first:  python bin/dev.py setup"
            )
        )
    return PYTHON


def tool(name: str) -> str:
    """Resolve an entry-point script inside the venv, e.g. 'pytest' -> pytest.exe."""
    candidate = VENV / SCRIPTS / name
    if os.name == "nt":
        candidate = candidate.with_suffix(".exe")
    if not candidate.exists():
        # Fall back to invoking it as a module, which always works.
        return str(venv_python())
    return str(candidate)


def run(cmd: list[str], *, env_extra: dict[str, str] | None = None) -> int:
    """Run a command from the repository root, streaming output."""
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    print(f"+ {' '.join(cmd)}", file=sys.stderr)
    return subprocess.run(cmd, cwd=ROOT, env=env).returncode


def cmd_setup() -> int:
    import venv

    if VENV.exists():
        print(f"venv/ already present at {VENV}; installing into it.")
    else:
        print(f"Creating virtual environment at {VENV} ...")
        venv.EnvBuilder(with_pip=True, clear=False).create(VENV)

    rc = run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"])
    if rc:
        return rc
    # Installing the project with its test extra is what makes `asciidoctrine`
    # importable in editable mode, resolving back to src/.
    return run([str(PYTHON), "-m", "pip", "install", "-e", ".[test]"])


def cmd_verify() -> int:
    steps = [
        [tool("pytest"), "-n0", "-k", "not functional", "-q", "--tb=short"],
        [tool("ruff"), "format", "--check", "."],
        [tool("ruff"), "check", "."],
        [tool("mypy"), "src/asciidoctrine"],
    ]
    for step in steps:
        rc = run(step)
        if rc:
            return rc
    return 0


def cmd_all() -> int:
    rc = cmd_verify()
    if rc:
        return rc
    # The doctest corpus is gated behind RUN_DOCTESTS to keep the default run fast.
    return run(
        [tool("pytest"), "-n0", "tests/test_doctest_parsing.py", "-q", "--tb=short"],
        env_extra={"RUN_DOCTESTS": "1"},
    )


def _shell_script(name: str, *extra: str) -> int:
    """Run a repository shell script via bash (Git Bash on Windows)."""
    if os.name == "nt":
        bash = "bash"
        # Confirm Git Bash (or WSL bash) is actually available before running.
        if subprocess.run(["where", "bash"], capture_output=True).returncode:
            raise SystemExit(
                die(
                    f"{name} requires bash, which was not found on PATH.\n"
                    "Install Git for Windows (https://git-scm.com/download/win) "
                    "and re-run from Git Bash."
                )
            )
    else:
        bash = "bash"
    return run([bash, name, *extra])


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0 if argv else 2

    command, rest = argv[0], argv[1:]

    if command == "setup":
        return cmd_setup()
    if command == "verify":
        return cmd_verify()
    if command == "all":
        return cmd_all()
    if command == "fmt":
        return run([tool("ruff"), "format", "."])
    if command == "tck":
        return _shell_script("./run-tck.sh")
    if command == "tck-coverage":
        return _shell_script("./run-tck-coverage.sh")
    if command == "pytest":
        return run([tool("pytest"), *rest])

    print(f"error: unknown command {command!r}\n", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
