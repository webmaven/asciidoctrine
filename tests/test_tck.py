import glob
import os
import re
import subprocess

import pytest


@pytest.fixture(scope="session")
def tck_output():
    """Runs the TCK and returns (stdout, stderr, returncode)."""
    # Ensure TCK is initialized and run it
    result = subprocess.run(["./run-tck.sh"], capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


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


def parse_tck_failures(stdout):
    """Parses TCK spec output and returns a list of failed test paths."""
    failed_tests = []
    stack = []
    # Test names that are actually suites in the spec reporter
    suites = {
        "tests",
        "block",
        "inline",
        "header",
        "listing",
        "paragraph",
        "document",
        "list",
        "unordered",
        "section",
        "sidebar",
        "span",
        "strong",
        "no-markup",
    }

    for line in stdout.splitlines():
        line_clean = re.sub(r"\x1b\[[0-9;]*m", "", line)
        if not line_clean.strip():
            continue

        indent = len(line_clean) - len(line_clean.lstrip())
        level = indent // 2
        content = line_clean.strip()

        if content.startswith("▶"):
            name = content[2:].split("(")[0].strip()
            if name != "tests":
                stack = stack[: level - 1]
                stack.append(name)
        elif content.startswith("✖"):
            name = content[2:].split("(")[0].strip()
            if name not in suites:
                # This is a leaf test failure
                filename = name.replace(" ", "-") + "-input.adoc"
                # Make sure stack matches the current level
                current_stack = stack[: level - 1]
                full_rel_path = os.path.join(*current_stack, filename)
                failed_tests.append(full_rel_path)
    return failed_tests


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


@pytest.mark.parametrize("adoc_path", get_parametrized_tests())
def test_tck(adoc_path, tck_output):
    stdout, stderr, returncode = tck_output
    failed_tests = parse_tck_failures(stdout)
    assert adoc_path not in failed_tests, f"TCK test failed: {adoc_path}"
