# Plan: Fix Pyodide Functional Tests

## Objective
Get the functional tests in `tests/test_functional.py` working by resolving the `FileNotFoundError` for the Pyodide distribution directory and ensuring all dependencies (wheels) are correctly provided to the Pyodide environment.

## Current Failures
The tests fail because `pytest-pyodide` defaults to searching for a `pyodide/` directory containing the Pyodide runtime.
```
FileNotFoundError: [Errno 2] No such file or directory: '/home/webmaven/Code/GitHub/asciidoctrine/pyodide'
```

## Key Components
-   **Pyodide Distribution**: Needs to be present in a directory served by `pytest-pyodide`.
-   **Wheels**: `lark` and `asciidoctrine` must be available as wheels for installation within Pyodide.
-   **Runner**: `selenium` is used, so a compatible browser driver (e.g. geckodriver or chromedriver) must be available.

## Proposed Solution

### Step 1: Bootstrap Pyodide Environment
Create a `pyodide` directory and populate it with a Pyodide release.
-   Download Pyodide v0.26.4 (latest stable as of this plan).
-   Extract to `pyodide/`.

### Step 2: Prepare Dependency Wheels
-   **Asciidoctrine**: Rebuild the wheel to ensure it includes the latest changes.
    ```bash
    venv/bin/python3 -m pip install build
    venv/bin/python3 -m build
    ```
-   **Lark**: Download the specific version of Lark wheel required.
    ```bash
    venv/bin/python3 -m pip download "lark>=1.1.0" --dest pyodide/ --only-binary=:all: --python-version 3.10 --platform any
    ```
    *Note: The test expects `lark-1.3.1-py3-none-any.whl`, so we should ensure that specific version is downloaded.*

### Step 3: Configure Pytest
Update `pyproject.toml` or add a `pytest.ini` to properly configure `pytest-pyodide`.
-   Set `--dist-dir` to `pyodide`.
-   Set `--browser` (defaulting to `firefox` or `chrome` depending on environment availability).

### Step 4: Refactor Functional Tests
Update `tests/test_functional.py` to be more robust:
-   Ensure `run_if_pyodide` can correctly find wheels even if they are in `dist/` or `pyodide/`.
-   Use `@copy_files_to_pyodide` if appropriate to simplify wheel management.
-   Improve error reporting if `selenium` or browser drivers are missing.

## Implementation Steps

### Phase 1: Preparation (Manual/Scripted)
1.  Create `pyodide/` directory.
2.  Download Pyodide artifacts (e.g. from CDN or GitHub releases).
3.  Build current project wheel and copy it to `pyodide/`.
4.  Download `lark` wheel to `pyodide/`.

### Phase 2: Configuration
1.  Modify `pyproject.toml` to include:
    ```toml
    [tool.pytest.ini_options]
    addopts = "--dist-dir=pyodide --browser=firefox"
    ```

### Phase 3: Test Refactoring
1.  Update `tests/test_functional.py` to use relative paths for wheels or ensure they match what's in `pyodide/`.

## Verification
1.  Run `venv/bin/pytest tests/test_functional.py`.
2.  Confirm that a browser opens (or runs headlessly) and the three tests pass.

## Alternatives Considered
-   **Skip tests**: Just disable them if the environment isn't set up. (Rejected: The user explicitly asked to get them working).
-   **Use CDN**: Configure `pytest-pyodide` to load from a CDN. (Rejected: `pytest-pyodide`'s `selenium` fixture is designed to serve local files for performance and reliability in CI).
