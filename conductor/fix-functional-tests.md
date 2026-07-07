# Plan: Fix Pyodide Functional Tests

## Objective
Get the functional tests in `tests/test_functional.py` working by resolving the `FileNotFoundError` for the Pyodide distribution directory, ensuring all dependencies (wheels) are correctly provided to the Pyodide environment, and establishing Python 3.14 and Pyodide 314.0.2 as the baseline.

## Key Decisions Implemented
1. **Directory Standard**: Adhere to project standards and use `dist/` instead of `pyodide/`.
2. **Pyodide Stable Release**: Use **Pyodide 314.0.2** as the current stable release.
3. **Driver & Automation**: Use **Playwright** with its **auto-browser downloader** running in **headless mode**. Selenium is not needed and will not be installed.
4. **Baseline Platform**: Declare **Python 3.14** and **Pyodide 314.0.2** as the minimum supported baseline environments. Since `asciidoctrine` has no existing users or released packages, this change has no backward compatibility impact.

---

## Key Components
- **Pyodide Distribution**: Pyodide 314.0.2 release artifacts must be present in the `dist/` directory, served locally by the runner.
- **Wheels**: `lark` and `asciidoctrine` must be built as wheels and placed in `dist/` for installation within Pyodide.
- **Browser & Driver**: Playwright's native Chromium browser running headlessly via Playwright's automated browser manager.

---

## Proposed Solution

### Step 1: Update Project Dependencies & Metadata
1. Edit `pyproject.toml` to:
   - Declare `requires-python = ">=3.14"` (setting Python 3.14 as the baseline).
   - Add `pytest-pyodide` and `playwright` to `[project.optional-dependencies]` under the `test` group.
2. Install the updated test dependencies in the virtual environment:
   ```bash
   venv/bin/pip install -e ".[test]"
   ```
3. Use Playwright's auto-browser downloader to install the hermetic Chromium browser:
   ```bash
   venv/bin/playwright install chromium
   ```

### Step 2: Bootstrap Pyodide 314.0.2 Environment
1. Create the `dist/` directory:
   ```bash
   mkdir -p dist
   ```
2. Download and extract the Pyodide 314.0.2 release tarball to `dist/`:
   ```bash
   curl -L https://github.com/pyodide/pyodide/releases/download/314.0.2/pyodide-314.0.2.tar.bz2 | tar -xjf - -C dist --strip-components=1
   ```

### Step 3: Prepare Dependency Wheels in `dist/`
1. Rebuild the `asciidoctrine` wheel targeting the Python 3.14 baseline:
   ```bash
   venv/bin/python3 -m build --wheel --outdir dist/
   ```
2. Download the `lark` wheel into `dist/` for Python 3.14 compatibility:
   ```bash
   venv/bin/python3 -m pip download "lark==1.3.1" --dest dist/ --only-binary=:all: --python-version 3.14 --platform any
   ```

### Step 4: Configure Pytest Options
Update the `pyproject.toml` `[tool.pytest.ini_options]` block to configure the Pyodide test options to use Playwright Chrome headlessly:
```toml
addopts = "--dist-dir=dist --browser=playwright-chrome --headless"
```

### Step 5: Refactor Functional Tests
Update `tests/test_functional.py` to:
1. Reference the updated wheel version patterns.
2. Robustly check for `pytest-pyodide` installation before running, falling back to a clean skip if required.

---

## Verification Plan
1. Run the functional tests:
   ```bash
   venv/bin/pytest tests/test_functional.py
   ```
2. Confirm that tests execute headlessly inside Chromium via Playwright / Pyodide 314.0.2 and all three test cases pass successfully.
