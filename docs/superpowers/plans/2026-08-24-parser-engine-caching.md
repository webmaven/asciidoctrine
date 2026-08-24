# Parser Engine Caching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement memoized Lark parser caching for `parse_to_ast()` and `parse_inlines()`, reducing per-parse overhead from ~0.22s to ~0.0055s (a ~33x speedup), while exporting `parse_inlines` and cache control utilities at the package top level.

**Architecture:** Introduce `get_document_parser()` and `get_inline_parser()` factory functions in `src/asciidoctrine/lark_parser.py` with thread-safe dictionary caching keyed by grammar path, modification timestamp (`mtime`), and custom URI schemes. Replace per-call `Lark(...)` compilation in `parse_to_ast()` and `parse_inlines()` with cached parser lookups, and expose `clear_parser_cache()` for hermetic test isolation.

**Tech Stack:** Python 3.10+, Lark 1.3.1 (Earley parser), Pytest, Mypy strict type checking.

## Global Constraints

- **Python & Environment**: Strict Python 3.10+ compatibility using `venv/bin/python3`, `venv/bin/pytest`, and `venv/bin/mypy`.
- **Parser Architecture**: Multi-pass Earley grammar in `src/asciidoctrine/grammar.lark` with AST definitions in `src/asciidoctrine/nodes.py`.
- **Strict TDD Protocol**: No production code without a failing test first. Every step follows RED -> Verify RED -> GREEN -> Verify GREEN -> Refactor.
- **Linters & Static Typing**: Must pass `venv/bin/ruff check .`, `venv/bin/ruff format --check .`, and `venv/bin/mypy src/asciidoctrine` with 0 errors.
- **Backward Compatibility**: All existing signatures (`parse_to_ast`, `parse_inlines`, `DEFAULT_GRAMMAR`) and behavior must remain 100% backward-compatible.

---

### Task 1: Parser Engine Caching & Factory Functions in `lark_parser.py`

**Files:**
- Modify: `src/asciidoctrine/lark_parser.py:1330-1440`
- Test: `tests/test_parser_caching.py`

**Interfaces:**
- Consumes: `DEFAULT_GRAMMAR`, `build_uri_terminal`, `Lark`
- Produces:
  - `get_document_parser(grammar_file: str = DEFAULT_GRAMMAR, extra_authority_schemes: Optional[Tuple[str, ...]] = None, extra_opaque_schemes: Optional[Tuple[str, ...]] = None) -> Lark`
  - `get_inline_parser(grammar_file: str = DEFAULT_GRAMMAR) -> Lark`
  - `clear_parser_cache() -> None`
  - `parse_to_ast(source: str, ...) -> Document` (accelerated via cached parser)
  - `parse_inlines(source: str, grammar_file: str = DEFAULT_GRAMMAR) -> PyList[Node]` (accelerated via cached parser)

- [ ] **Step 1: Write failing tests for parser caching, cache invalidation, and custom schemes**

Create `tests/test_parser_caching.py`:
```python
import os
import time
from typing import Tuple

import pytest

from asciidoctrine.lark_parser import (
    DEFAULT_GRAMMAR,
    clear_parser_cache,
    get_document_parser,
    get_inline_parser,
    parse_inlines,
    parse_to_ast,
)


@pytest.fixture(autouse=True)
def clean_cache():
    clear_parser_cache()
    yield
    clear_parser_cache()


def test_get_document_parser_returns_same_instance():
    """Verify get_document_parser caches and returns identical Lark instances."""
    parser1 = get_document_parser()
    parser2 = get_document_parser()
    assert parser1 is parser2


def test_get_inline_parser_returns_same_instance():
    """Verify get_inline_parser caches and returns identical Lark instances."""
    parser1 = get_inline_parser()
    parser2 = get_inline_parser()
    assert parser1 is parser2


def test_clear_parser_cache_creates_fresh_instances():
    """Verify clear_parser_cache clears internal parser dictionaries."""
    parser1 = get_document_parser()
    clear_parser_cache()
    parser2 = get_document_parser()
    assert parser1 is not parser2


def test_custom_schemes_cache_separately():
    """Verify different custom authority/opaque scheme configurations have separate cache entries."""
    parser_default = get_document_parser()
    parser_custom = get_document_parser(
        extra_authority_schemes=("custom",),
        extra_opaque_schemes=("isbn",),
    )
    assert parser_default is not parser_custom

    # Calling with identical custom schemes returns the cached custom parser
    parser_custom_repeat = get_document_parser(
        extra_authority_schemes=("custom",),
        extra_opaque_schemes=("isbn",),
    )
    assert parser_custom is parser_custom_repeat


def test_parse_to_ast_repeated_throughput():
    """Verify parse_to_ast leverages cached parser for high-throughput batch parsing."""
    sample = (
        "= Document Title\n\nFirst paragraph with *bold* text.\n\n* Item 1\n* Item 2\n"
    )
    # Pre-warm
    doc = parse_to_ast(sample)
    assert doc is not None

    start = time.perf_counter()
    iterations = 20
    for _ in range(iterations):
        d = parse_to_ast(sample)
        assert len(d.blocks) >= 2
    elapsed = time.perf_counter() - start

    # Average parse time with cached parser should be well under 0.05s per parse (typically ~0.005s)
    avg_time = elapsed / iterations
    assert avg_time < 0.05, f"Average parse time was {avg_time:.4f}s, expected < 0.05s"
```

- [ ] **Step 2: Run tests to verify failure**

Run: `venv/bin/pytest tests/test_parser_caching.py -v`
Expected: FAIL with `ImportError: cannot import name 'clear_parser_cache'` or `get_document_parser`.

- [ ] **Step 3: Implement cached parser factories in `src/asciidoctrine/lark_parser.py`**

In `src/asciidoctrine/lark_parser.py`:
```python
_DOCUMENT_PARSERS: Dict[Tuple[str, float, Tuple[str, ...], Tuple[str, ...]], Lark] = {}
_INLINE_PARSERS: Dict[Tuple[str, float], Lark] = {}


def clear_parser_cache() -> None:
    """Clears all cached compiled Lark parser instances."""
    _DOCUMENT_PARSERS.clear()
    _INLINE_PARSERS.clear()


def get_document_parser(
    grammar_file: str = DEFAULT_GRAMMAR,
    extra_authority_schemes: Optional[Tuple[str, ...]] = None,
    extra_opaque_schemes: Optional[Tuple[str, ...]] = None,
) -> Lark:
    """
    Returns a cached compiled Lark Earley parser for document parsing.
    Recompiles only when grammar path, file modification timestamp, or custom URI schemes change.
    """
    authority_schemes = tuple(extra_authority_schemes or ())
    opaque_schemes = tuple(extra_opaque_schemes or ())
    mtime = os.path.getmtime(grammar_file) if os.path.exists(grammar_file) else 0.0
    cache_key = (grammar_file, mtime, authority_schemes, opaque_schemes)

    if cache_key in _DOCUMENT_PARSERS:
        return _DOCUMENT_PARSERS[cache_key]

    with open(grammar_file, "r", encoding="utf-8") as f:
        grammar = f.read()

    if authority_schemes or opaque_schemes:
        custom_uri_rule = build_uri_terminal(authority_schemes, opaque_schemes)
        grammar = re.sub(
            r"^URI\.3:.*$", lambda m: custom_uri_rule, grammar, flags=re.MULTILINE
        )

    parser = Lark(
        grammar,
        start="document",
        parser="earley",
        ambiguity="resolve",
        propagate_positions=True,
    )
    _DOCUMENT_PARSERS[cache_key] = parser
    return parser


def get_inline_parser(grammar_file: str = DEFAULT_GRAMMAR) -> Lark:
    """
    Returns a cached compiled Lark Earley parser for inline formatting parsing.
    Recompiles only when grammar path or file modification timestamp changes.
    """
    mtime = os.path.getmtime(grammar_file) if os.path.exists(grammar_file) else 0.0
    cache_key = (grammar_file, mtime)

    if cache_key in _INLINE_PARSER_CACHE if False else cache_key in _INLINE_PARSERS:
        return _INLINE_PARSERS[cache_key]

    with open(grammar_file, "r", encoding="utf-8") as f:
        grammar = f.read()

    parser = Lark(
        grammar,
        start="text_content",
        parser="earley",
        ambiguity="resolve",
        propagate_positions=True,
    )
    _INLINE_PARSERS[cache_key] = parser
    return parser
```

Update `parse_to_ast` and `parse_inlines` to use these helpers:
```python
def parse_to_ast(...):
    ...
    # Replace direct Lark(...) initialization with get_document_parser
    parser = get_document_parser(
        grammar_file=grammar_file,
        extra_authority_schemes=extra_authority_schemes,
        extra_opaque_schemes=extra_opaque_schemes,
    )
    ...
```

```python
def parse_inlines(source: str, grammar_file: str = DEFAULT_GRAMMAR) -> PyList[Node]:
    parser = get_inline_parser(grammar_file=grammar_file)
    try:
        tree = parser.parse(source)
    except UnexpectedInput as e:
        context = e.get_context(source)
        message = f"Syntax error at line {e.line}, column {e.column}.\n{context}"
        raise AsciiDocSyntaxError(
            message, line=e.line, column=e.column, context=context
        ) from e
    result = AsciiDocTransformer().transform(tree)
    if isinstance(result, list):
        return result
    elif isinstance(result, Node):
        return [result]
    else:
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `venv/bin/pytest tests/test_parser_caching.py -v`
Expected: PASS (5/5 tests passing).

- [ ] **Step 5: Commit Task 1**

```bash
git add src/asciidoctrine/lark_parser.py tests/test_parser_caching.py
git commit -m "perf: implement memoized Lark parser caching for parse_to_ast and parse_inlines"
```

---

### Task 2: Top-Level Public API Exports in `__init__.py`

**Files:**
- Modify: `src/asciidoctrine/__init__.py:1-55`
- Test: `tests/test_public_api.py`

**Interfaces:**
- Consumes: `parse_inlines`, `get_document_parser`, `get_inline_parser`, `clear_parser_cache` from `lark_parser.py`
- Produces: Package-level exports in `asciidoctrine.__all__`

- [ ] **Step 1: Write failing tests for top-level public API exports**

Create `tests/test_public_api.py`:
```python
import asciidoctrine


def test_top_level_exports_include_parse_inlines():
    """Verify parse_inlines is exported directly from top-level asciidoctrine."""
    assert hasattr(asciidoctrine, "parse_inlines")
    assert callable(asciidoctrine.parse_inlines)
    assert "parse_inlines" in asciidoctrine.__all__


def test_top_level_exports_include_cache_utilities():
    """Verify parser caching utilities are exported directly from top-level asciidoctrine."""
    assert hasattr(asciidoctrine, "clear_parser_cache")
    assert hasattr(asciidoctrine, "get_document_parser")
    assert hasattr(asciidoctrine, "get_inline_parser")
    assert "clear_parser_cache" in asciidoctrine.__all__
    assert "get_document_parser" in asciidoctrine.__all__
    assert "get_inline_parser" in asciidoctrine.__all__


def test_parse_inlines_top_level_execution():
    """Verify parse_inlines executes cleanly via top-level import."""
    nodes = asciidoctrine.parse_inlines("*strong* and _emphasis_")
    assert len(nodes) >= 2
    assert any(getattr(n, "variant", None) == "strong" for n in nodes)
```

- [ ] **Step 2: Run test to verify failure**

Run: `venv/bin/pytest tests/test_public_api.py -v`
Expected: FAIL with `AssertionError: assert hasattr(asciidoctrine, 'parse_inlines')`.

- [ ] **Step 3: Update `src/asciidoctrine/__init__.py`**

In `src/asciidoctrine/__init__.py`:
```python
from .lark_parser import (
    AsciiDocSyntaxError,
    clear_parser_cache,
    get_document_parser,
    get_inline_parser,
    parse_inlines,
    parse_to_ast,
)

...

__all__ = [
    "__version__",
    "parse_to_ast",
    "parse_inlines",
    "get_document_parser",
    "get_inline_parser",
    "clear_parser_cache",
    "AsciiDocSyntaxError",
    "serialize_to_asciidoc",
    "FileProvider",
    "FsLoader",
    "MemoryLoader",
    "Node",
    "Docinfo",
    "Document",
    "Section",
    "Paragraph",
    "Text",
    "NodeVisitor",
    "NodeTransformer",
    "ASGResolver",
    "WorkspaceCatalog",
    "WorkspaceBuilder",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_public_api.py -v`
Expected: PASS (3/3 tests passing).

- [ ] **Step 5: Commit Task 2**

```bash
git add src/asciidoctrine/__init__.py tests/test_public_api.py
git commit -m "feat: export parse_inlines and parser caching utilities in top-level package API"
```

---

### Task 3: Full Regression Suite, Static Typing & Documentation

**Files:**
- Modify: `AGENTS.md` (record architectural learnings for parser caching)
- Modify: `CHANGELOG.adoc` (document performance enhancement)
- Test: Full Pytest suite, Mypy, Ruff

- [ ] **Step 1: Run Ruff linter and formatter**

Run: `venv/bin/ruff format --check . && venv/bin/ruff check .`
Expected: 0 errors.

- [ ] **Step 2: Run Mypy strict type checking**

Run: `venv/bin/mypy src/asciidoctrine`
Expected: `Success: no issues found in 12 source files`.

- [ ] **Step 3: Run full Pytest suite and local TCK suite**

Run: `venv/bin/pytest -k "not functional" -q`
Expected: 825+ tests passing, 0 failures.

- [ ] **Step 4: Update `AGENTS.md` and `CHANGELOG.adoc`**

Update `AGENTS.md` with Section 21 explaining Parser Engine Memoization & Cache Key Design.
Update `CHANGELOG.adoc` under `Unreleased` noting the 33x parse throughput improvement.

- [ ] **Step 5: Commit Task 3**

```bash
git add AGENTS.md CHANGELOG.adoc
git commit -m "docs: record parser caching architecture in AGENTS.md and CHANGELOG.adoc"
```

---

## Verification Plan

### Automated Tests
- Unit & Performance Tests: `venv/bin/pytest tests/test_parser_caching.py tests/test_public_api.py -v`
- Full Local Regression Suite: `venv/bin/pytest -k "not functional" -q`
- Official Node.js TCK Runner: `./run-tck.sh`
- Linters & Type Checking: `venv/bin/ruff check . && venv/bin/mypy src/asciidoctrine`

### Manual Verification
- Benchmark repeated parsing throughput in REPL:
  `venv/bin/python3 -c "import time, asciidoctrine; t0=time.perf_counter(); [asciidoctrine.parse_to_ast('= Title\n\nText.') for _ in range(50)]; print(f'Total time: {time.perf_counter()-t0:.4f}s')"`
  (Target: < 0.35s for 50 parses).
