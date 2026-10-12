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
    python bin/dev.py functional     # Pyodide functional tests (needs dist/)
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
  functional     Run the Pyodide functional tests (requires dist/ to be built)
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


def _pyodide_runtime() -> str:
    """Pick the pytest-pyodide runtime for this platform.

    CI uses ``--runtime node`` on Linux, but that runtime shells out through
    ``/bin/bash`` and ``pexpect.spawn``, neither of which works on Windows.
    The browser runtimes are driven over Selenium instead, so on Windows we
    fall back to the browser that is actually available.

    Note the runtime name is a pytest-pyodide identifier, not a browser name:
    the supported set is ``chrome``, ``firefox``, ``safari``, ``node``. There
    is deliberately no ``edge`` -- Edge is not one of the harness runtimes, and
    passing it fails configuration with "Invalid runtime: edge".
    """
    override = os.environ.get("ASCIIDOCTRINE_PYODIDE_RUNTIME")
    if override:
        return override
    if os.name != "nt":
        return "node"
    # Windows: prefer Chrome, then Firefox. Safari is macOS-only.
    for browser in ("chrome", "firefox"):
        paths = {
            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ],
            "firefox": [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
        }[browser]
        if any(Path(p).exists() for p in paths):
            return browser
    return "chrome"


def _pyodide_dist_ready() -> bool:
    """The functional tests need a built wheel plus the Pyodide distribution."""
    dist = ROOT / "dist"
    if not dist.is_dir():
        return False
    if not list(dist.glob("asciidoctrine-*.whl")):
        return False
    # pyodide.js (legacy) or pyodide.mjs (current) marks an extracted distribution.
    return (dist / "pyodide.js").exists() or (dist / "pyodide.mjs").exists()


def cmd_functional() -> int:
    """Run the Pyodide functional tests against the locally built dist/."""
    if not _pyodide_dist_ready():
        raise SystemExit(
            die(
                "dist/ is not ready. Build it first:\n"
                "    python -m build --wheel\n"
                "    pip download lark platformdirs -d dist/\n"
                "    curl -L <pyodide tarball> -o pyodide.tar.bz2\n"
                "    tar -xjf pyodide.tar.bz2 && cp -r pyodide/* dist/\n"
                "See the test-pyodide job in .github/workflows/ci.yml."
            )
        )

    runtime = _pyodide_runtime()

    # On Windows the ES-module MIME shim must reach the server subprocess that
    # pytest-pyodide spawns. sitecustomize on PYTHONPATH is inherited across
    # multiprocessing spawn, which is why this works where a conftest would not.
    env_extra: dict[str, str] = {}
    if os.name == "nt":
        shim_dir = ROOT / "tools" / "windows-shims"
        existing = os.environ.get("PYTHONPATH", "")
        env_extra["PYTHONPATH"] = (
            f"{shim_dir}{os.pathsep}{existing}" if existing else str(shim_dir)
        )

    # `-o addopts=` clears the project's `-n auto`, which xdist cannot use with
    # the Pyodide runtime.
    return run(
        [
            tool("pytest"),
            "-o",
            "addopts=",
            "--runtime",
            runtime,
            "--dist-dir",
            "dist",
            "tests/test_functional.py",
        ],
        env_extra=env_extra,
    )


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
    if command == "functional":
        return cmd_functional()
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
