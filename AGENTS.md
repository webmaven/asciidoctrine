# Agent Development & Testing Guide

This document provides a technical overview of the local development environment, project structure, and testing protocols for the `asciidoctrine` project. It is designed to help agents quickly onboard and contribute to the parser.

## 🏗 Project Architecture

`asciidoctrine` is a multi-pass AsciiDoc parser built on the **Lark** engine (Earley algorithm).

*   **Grammar**: `src/asciidoctrine/grammar.lark` (EBNF)
*   **AST Nodes**: `src/asciidoctrine/nodes.py` (Converged with ASG schema)
*   **Transformer**: `src/asciidoctrine/lark_parser.py` (CST to AST)
*   **Semantic Resolver**: `src/asciidoctrine/resolver.py` (Resolves attributes)
*   **Backend**: `src/asciidoctrine/docutils_backend.py` (Docutils/Sphinx integration)

## 🛠 Local Setup

### Python Environment
The project uses a standard Python 3.10+ virtual environment.

```bash
# Activation not strictly required if using absolute paths
# pip install -e ".[test,docs]"
```

*   **Python Path**: `venv/bin/python3`
*   **Pip Path**: `venv/bin/pip`
*   **Pytest Path**: `venv/bin/pytest`

### Pyodide Setup (for Functional Tests)
To run functional tests, you need a local Pyodide environment and built wheels in the `dist/` directory.

```bash
# 1. Create and populate dist/ directory
mkdir -p dist
curl -L https://github.com/pyodide/pyodide/releases/download/0.27.2/pyodide-0.27.2.tar.bz2 | tar -xjf - -C dist --strip-components=1

# 2. Build project wheel
venv/bin/python3 -m build --wheel

# 3. Download dependencies for Pyodide
venv/bin/python3 -m pip download lark -d dist/
```

### TCK Dependencies
The Technology Compatibility Kit (TCK) requires Node.js (>= 20) and npm.

```bash
cd vendor/asciidoc-tck
npm ci
```
*Note: `run-tck.sh` handles `npm ci` automatically if `node_modules` is missing.*

## 🧪 Testing Protocols

The project uses a multi-tiered testing strategy.

### 1. Standard Pytest Suite
Runs unit, integration, and doctest-based examples.

```bash
# Run all stable tests
venv/bin/pytest -k "not functional"

# Functional tests (Pyodide) currently require a 'pyodide/' dist directory
# and are known to fail in standard environments.
```

### 2. Official TCK Suite
Authoritative tests for AsciiDoc specification compliance.

```bash
./run-tck.sh
```
*   **Adapter**: `bin/tck-adapter.py` (Bridge between TCK runner and parser)
*   **TCK Location**: `vendor/asciidoc-tck/`

### 3. TCK Coverage Report
To see a summary of passed/failed TCK categories:

```bash
./run-tck-coverage.sh
```

## 📋 New Feature Checklist

When adding support for a new AsciiDoc element:

1.  **Grammar**: Add the rule to `src/asciidoctrine/grammar.lark`.
2.  **Node**: Define a new `Node` subclass in `src/asciidoctrine/nodes.py` that matches the [ASG schema](https://gitlab.eclipse.org/eclipse/asciidoc-lang/asciidoc-lang/-/blob/main/asg/schema.json).
3.  **Transformer**: Implement a corresponding method in `BlockTransformer` or `InlineTransformer`.
4.  **Resolver**: If the element contains text that supports attribute substitution, ensure it's handled in `src/asciidoctrine/resolver.py`.
5.  **Backend**: Add a `visit_<name>` method to `DocutilsRenderer` in `src/asciidoctrine/docutils_backend.py`.
6.  **Tests**:
    *   Add a unit test in `tests/test_blocks_parsing.py` or `tests/test_inlines_parsing.py`.
    *   Add a functional test or TCK-style test in `tests/tck_harness/`.

## 📁 Key File Paths

| Path | Description |
| :--- | :--- |
| `src/asciidoctrine/` | Core package source code |
| `src/asciidoctrine/grammar.lark` | Authority for the parser's syntax rules |
| `src/asciidoctrine/nodes.py` | AST definitions (Follows ASG schema naming) |
| `src/asciidoctrine/transformers/` | CST-to-AST transformation logic |
| `tests/` | Pytest directory |
| `tests/tck_harness/` | Local TCK test additions |
| `vendor/asciidoc-tck/` | Official TCK (Submodule) |
| `vendor/asciidoctor-doctest/` | External example corpus (Submodule) |
| `bin/tck-adapter.py` | CLI entry point for the TCK runner |

## 💡 Troubleshooting & Patterns

*   **Earley Ambiguity**: If the grammar becomes ambiguous, Lark will raise a `VisitError` or `AmbiguityError`. Use `?rule` in the grammar to compress simple wrappers.
*   **Location Tracking**: The parser uses inclusive locations (`end_column - 1`). Use `_set_location_from_children()` in the transformer to ensure accuracy.
*   **Attribute Resolution**: Rich attributes (nodes) are resolved to strings in `attributes.py`.
*   **Git Submodules**: If submodules are missing or empty, run `git submodule update --init --recursive`.
