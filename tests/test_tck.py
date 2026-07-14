import glob
import json
import os
import subprocess
import sys
import time

import pytest


@pytest.fixture(scope="session")
def tck_output():
    """Runs the TCK once per session and caches output in a temporary file for xdist workers."""
    cache_file = os.path.join("tests", ".tck_cache.json")
    lock_file = os.path.join("tests", ".tck_cache.lock")

    # 1. Check if cache already exists (subsequent workers or runs)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
                return data["stdout"], data["stderr"], data["returncode"]
        except Exception:
            pass

    # 2. Try to acquire the exclusive creation lock
    acquired_lock = False
    try:
        with open(lock_file, "x") as f:
            f.write(str(os.getpid()))
        acquired_lock = True
    except FileExistsError:
        # Another worker is running the TCK. Wait for the cache file to be written.
        for _ in range(600):  # Wait up to 60 seconds
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r") as f:
                        data = json.load(f)
                        return data["stdout"], data["stderr"], data["returncode"]
                except Exception:
                    pass
            time.sleep(0.1)

    # 3. If we acquired the lock (or wait timed out), we run the TCK
    try:
        tck_dir = os.path.join("vendor", "asciidoc-tck")
        node_modules = os.path.join(tck_dir, "node_modules")

        # Ensure TCK is initialized
        if not os.path.exists(node_modules):
            subprocess.run(["npm", "ci"], cwd=tck_dir, check=True)

        # Run TCK via our custom native JSON runner
        run_tck_script = os.path.join("bin", "run-tck-json.mjs")
        if "COV_CORE_SOURCE" in os.environ or "COVERAGE_RUN" in os.environ:
            adapter_cmd = "coverage run --parallel-mode --source=src/asciidoctrine bin/tck-adapter.py"
        else:
            adapter_cmd = f"{sys.executable} bin/tck-adapter.py"

        cmd = ["node", run_tck_script, adapter_cmd]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

        # Save cache atomically
        temp_cache_file = cache_file + f".tmp.{os.getpid()}"
        with open(temp_cache_file, "w") as f:
            json.dump(
                {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode,
                },
                f,
            )
        os.replace(temp_cache_file, cache_file)

        return result.stdout, result.stderr, result.returncode

    finally:
        # 4. Clean up lock file if we were the owner
        if acquired_lock:
            try:
                os.remove(lock_file)
            except Exception:
                pass


def get_tck_tests():
    tck_tests_dir = os.path.join("vendor", "asciidoc-tck", "tests")
    pattern = os.path.join(tck_tests_dir, "**", "*-input.adoc")
    adoc_files = glob.glob(pattern, recursive=True)
    return sorted([os.path.relpath(f, tck_tests_dir) for f in adoc_files])


def get_known_failures():
    failures_file = os.path.join("tests", "tck_failures.txt")
    if not os.path.exists(failures_file):
        return set()
    with open(failures_file, "r") as f:
        return {line.strip() for line in f if line.strip()}


def get_parametrized_tests():
    tests = get_tck_tests()
    failures = get_known_failures()
    params = []
    for t in tests:
        if t in failures:
            params.append(
                pytest.param(
                    t,
                    marks=pytest.mark.xfail(reason=f"Known failure: {t}", strict=True),
                )
            )
        else:
            params.append(t)
    return params


@pytest.fixture(scope="session")
def tck_failures(tck_output):
    """Loads the TCK JSON output once per session and returns a set of failed test names."""
    stdout, stderr, returncode = tck_output
    try:
        data = json.loads(stdout)
        return {f["name"] for f in data.get("failures", [])}
    except Exception:
        # Fallback to empty set in case of loading error
        return set()


@pytest.mark.parametrize("adoc_path", get_parametrized_tests())
def test_tck(adoc_path, tck_failures):
    tck_name = adoc_path.replace("-input.adoc", "").replace("\\", "/")
    assert tck_name not in tck_failures, f"TCK test failed: {adoc_path}"
