# Docinfo & Document Metadata Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement full Docinfo (`:docinfo:`, `:docinfodir:`, `:docinfofiles:`, `docinfo.html`, `<docname>-docinfo.html`, `docinfo-footer.html`) file discovery, path-traversal safety, attribute substitution, AST/ASG metadata node representation, and HTML backend rendering in `asciidoctrine`.

**Architecture:** Extend `Preprocessor` to discover and load docinfo files (`docinfo.html`, `<docname>-docinfo.html`, etc.) based on `:docinfo:` attribute settings and safe-mode bounds. Represent docinfo content as a `Docinfo` node on `Document` and `Header` AST nodes, resolve attribute placeholders in `ASGResolver`, and inject header/footer markup in `DocutilsRenderer`.

**Tech Stack:** Python 3.10+, Lark, Docutils, pytest, ruff, mypy.

## Global Constraints
- Python 3.10+ compatibility across all modules.
- Strict path-traversal safety (`safe_mode=True`) preventing file inclusion outside `base_dir`.
- Strict typing (`mypy src/asciidoctrine`) and linting (`ruff check .`) compliance.
- 100% Red/Green TDD workflow for all tasks.

---

### Task 1: Preprocessor Docinfo File Discovery & Safe Resolution

**Files:**
- Create: `tests/test_docinfo.py`
- Modify: `src/asciidoctrine/preprocessor.py`

**Interfaces:**
- Consumes: `Preprocessor.attributes`, `Preprocessor.base_dir`, `Preprocessor.safe_mode`
- Produces: `Preprocessor._resolve_docinfo_files(current_file: str) -> tuple[str, str]` (returns `(head_content, footer_content)`)

- [ ] **Step 1: Write the failing test**

```python
"""Tests for Docinfo and Document Metadata features."""

import os
import tempfile
import pytest
from asciidoctrine.preprocessor import Preprocessor, PreprocessorError

pytestmark = pytest.mark.unit


def test_resolve_docinfo_files_shared_head():
    with tempfile.TemporaryDirectory() as tmpdir:
        docinfo_file = os.path.join(tmpdir, "docinfo.html")
        with open(docinfo_file, "w") as f:
            f.write("<meta name='author' content='Test Author'>")

        preprocessor = Preprocessor(base_dir=tmpdir)
        preprocessor.attributes["docinfo"] = "shared"

        head, footer = preprocessor._resolve_docinfo_files(
            os.path.join(tmpdir, "main.adoc")
        )
        assert "<meta name='author' content='Test Author'>" in head
        assert footer == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_docinfo.py -k "test_resolve_docinfo_files_shared_head" -q --tb=short`
Expected: FAIL with "AttributeError: 'Preprocessor' object has no attribute '_resolve_docinfo_files'"

- [ ] **Step 3: Write minimal implementation**

In `src/asciidoctrine/preprocessor.py`:

```python
def _resolve_docinfo_files(self, current_file: str) -> tuple[str, str]:
    """
    Discovers and reads docinfo files based on :docinfo:, :docinfodir:, and current_file.
    Returns tuple of (head_content, footer_content).
    """
    docinfo_attr = self.attributes.get("docinfo", "").strip()
    if not docinfo_attr:
        return ("", "")

    docinfodir = self.attributes.get("docinfodir", "").strip()
    if docinfodir:
        target_dir = os.path.abspath(os.path.join(self.base_dir, docinfodir))
    else:
        target_dir = (
            os.path.dirname(current_file) if current_file != "<root>" else self.base_dir
        )

    if self.safe_mode:
        try:
            common = os.path.commonpath([self.base_dir, target_dir])
            if common != self.base_dir:
                raise PreprocessorError(
                    f"docinfodir '{target_dir}' attempts to access files outside the base directory '{self.base_dir}'"
                )
        except ValueError:
            raise PreprocessorError(
                f"docinfodir '{target_dir}' attempts to access files outside the base directory '{self.base_dir}'"
            )

    docname = (
        os.path.splitext(os.path.basename(current_file))[0]
        if current_file != "<root>"
        else "document"
    )

    modes = [m.strip() for m in docinfo_attr.split(",") if m.strip()]
    include_shared = (
        "shared" in modes
        or "shared-head" in modes
        or "shared-footer" in modes
        or "both" in modes
    )
    include_private = (
        "private" in modes
        or "private-head" in modes
        or "private-footer" in modes
        or "both" in modes
    )

    head_parts: list[str] = []
    footer_parts: list[str] = []

    exts = [".html", ".xml"]

    # Shared head
    if include_shared or "shared-head" in modes:
        for ext in exts:
            path = os.path.join(target_dir, f"docinfo{ext}")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    head_parts.append(f.read())
                break

    # Private head
    if include_private or "private-head" in modes:
        for ext in exts:
            path = os.path.join(target_dir, f"{docname}-docinfo{ext}")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    head_parts.append(f.read())
                break

    # Shared footer
    if include_shared or "shared-footer" in modes:
        for ext in exts:
            path = os.path.join(target_dir, f"docinfo-footer{ext}")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    footer_parts.append(f.read())
                break

    # Private footer
    if include_private or "private-footer" in modes:
        for ext in exts:
            path = os.path.join(target_dir, f"{docname}-docinfo-footer{ext}")
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    footer_parts.append(f.read())
                break

    return ("\n".join(head_parts), "\n".join(footer_parts))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_docinfo.py -k "test_resolve_docinfo_files_shared_head" -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_docinfo.py src/asciidoctrine/preprocessor.py
git commit -m "feat(preprocessor): implement _resolve_docinfo_files for docinfo file discovery"
```

---

### Task 2: AST Node `Docinfo` & ASG Serialization

**Files:**
- Modify: `src/asciidoctrine/nodes.py`
- Modify: `tests/test_nodes_unit.py`

**Interfaces:**
- Consumes: None
- Produces: `class Docinfo(Node)`, `Document.docinfo: Optional[Docinfo]`, `Header.docinfo: Optional[Docinfo]`

- [ ] **Step 1: Write the failing test**

In `tests/test_nodes_unit.py`:

```python
def test_docinfo_node_serialization():
    from asciidoctrine.nodes import Docinfo, Document, Header

    docinfo = Docinfo(head_content="<meta>", footer_content="<footer>")
    assert docinfo.head_content == "<meta>"
    assert docinfo.footer_content == "<footer>"

    doc_dict = docinfo.to_dict()
    assert doc_dict["name"] == "docinfo"
    assert doc_dict["head_content"] == "<meta>"
    assert doc_dict["footer_content"] == "<footer>"

    doc = Document()
    doc.docinfo = docinfo
    serialized_doc = doc.to_dict()
    assert serialized_doc["docinfo"]["head_content"] == "<meta>"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_nodes_unit.py -k "test_docinfo_node_serialization" -q --tb=short`
Expected: FAIL with "cannot import name 'Docinfo' from 'asciidoctrine.nodes'"

- [ ] **Step 3: Write minimal implementation**

In `src/asciidoctrine/nodes.py`:

```python
class Docinfo(Node):
    """Represents header and footer injected document metadata."""

    _should_serialize_attributes = False

    def __init__(self, head_content: str = "", footer_content: str = "") -> None:
        super().__init__()
        self.name = "docinfo"
        self.type = "metadata"
        self.head_content = head_content
        self.footer_content = footer_content

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["head_content"] = self.head_content
        data["footer_content"] = self.footer_content
        return data
```

Add `self.docinfo: Optional[Docinfo] = None` to `Document.__init__` and `Header.__init__`.
In `Document.to_dict()`, append:
```python
        if hasattr(self, "docinfo") and self.docinfo:
            data["docinfo"] = self.docinfo.to_dict()
```

Export `Docinfo` in `src/asciidoctrine/nodes.py` `__all__` list and `src/asciidoctrine/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_nodes_unit.py -k "test_docinfo_node_serialization" -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_nodes_unit.py src/asciidoctrine/nodes.py src/asciidoctrine/__init__.py
git commit -m "feat(nodes): add Docinfo AST node class and serialization support"
```

---

### Task 3: Preprocessor Integration & Header Attachment

**Files:**
- Modify: `src/asciidoctrine/preprocessor.py`
- Modify: `tests/test_docinfo.py`

**Interfaces:**
- Consumes: `Preprocessor._resolve_docinfo_files()`, `Docinfo` node
- Produces: `Preprocessor.docinfo: Optional[Docinfo]`

- [ ] **Step 1: Write the failing test**

In `tests/test_docinfo.py`:

```python
def test_preprocessor_attaches_docinfo():
    with tempfile.TemporaryDirectory() as tmpdir:
        docinfo_file = os.path.join(tmpdir, "docinfo.html")
        with open(docinfo_file, "w") as f:
            f.write("<script>console.log('test');</script>")

        source = ":docinfo: shared\n= Title\n\nContent"
        preprocessor = Preprocessor(base_dir=tmpdir)
        preprocessor.process(source)

        assert preprocessor.docinfo is not None
        assert (
            "<script>console.log('test');</script>" in preprocessor.docinfo.head_content
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_docinfo.py -k "test_preprocessor_attaches_docinfo" -q --tb=short`
Expected: FAIL with "AttributeError: 'Preprocessor' object has no attribute 'docinfo'"

- [ ] **Step 3: Write minimal implementation**

In `src/asciidoctrine/preprocessor.py`:
- In `Preprocessor.__init__`, set `self.docinfo: Optional[Docinfo] = None`.
- At the end of `Preprocessor.process()`, call `_resolve_docinfo_files("<root>")`. If head or footer content exists, instantiate `self.docinfo = Docinfo(head, footer)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_docinfo.py -k "test_preprocessor_attaches_docinfo" -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_docinfo.py src/asciidoctrine/preprocessor.py
git commit -m "feat(preprocessor): wire docinfo resolution into process loop"
```

---

### Task 4: Attribute Substitution in Docinfo Content (`ASGResolver`)

**Files:**
- Modify: `src/asciidoctrine/resolver.py`
- Modify: `tests/test_docinfo.py`

**Interfaces:**
- Consumes: `Docinfo.head_content`, `Docinfo.footer_content`
- Produces: `ASGResolver.visit_docinfo(node: Docinfo) -> None`

- [ ] **Step 1: Write the failing test**

In `tests/test_docinfo.py`:

```python
def test_resolver_substitutes_attributes_in_docinfo():
    from asciidoctrine.nodes import Docinfo, Document
    from asciidoctrine.resolver import ASGResolver

    doc = Document()
    doc.attributes["author"] = "Jane Doe"
    doc.docinfo = Docinfo(head_content="<meta name='author' content='{author}'>")

    resolver = ASGResolver()
    resolved_doc = resolver.resolve(doc)

    assert resolved_doc.docinfo is not None
    assert (
        "<meta name='author' content='Jane Doe'>" in resolved_doc.docinfo.head_content
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_docinfo.py -k "test_resolver_substitutes_attributes_in_docinfo" -q --tb=short`
Expected: FAIL with `AssertionError` (attribute `{author}` remains unsubstituted)

- [ ] **Step 3: Write minimal implementation**

In `src/asciidoctrine/resolver.py`:

```python
    def visit_docinfo(self, node: Docinfo) -> None:
        """Substitute attribute references inside docinfo head and footer content."""
        if node.head_content:
            node.head_content = self._substitute_attributes(node.head_content)
        if node.footer_content:
            node.footer_content = self._substitute_attributes(node.footer_content)
```

And in `ASGResolver.resolve()`:
```python
        if hasattr(doc, "docinfo") and doc.docinfo:
            self.visit_docinfo(doc.docinfo)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_docinfo.py -k "test_resolver_substitutes_attributes_in_docinfo" -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_docinfo.py src/asciidoctrine/resolver.py
git commit -m "feat(resolver): implement attribute substitution for Docinfo nodes"
```

---

### Task 5: Backend Rendering & HTML Injection (`DocutilsRenderer`)

**Files:**
- Modify: `src/asciidoctrine/docutils_backend.py`
- Modify: `tests/test_docinfo.py`

**Interfaces:**
- Consumes: `Docinfo.head_content`, `Docinfo.footer_content`
- Produces: HTML output containing head and footer docinfo markup

- [ ] **Step 1: Write the failing test**

In `tests/test_docinfo.py`:

```python
def test_docutils_backend_renders_docinfo():
    from asciidoctrine.docutils_backend import DocutilsRenderer
    from asciidoctrine.nodes import Docinfo, Document, Paragraph, Text

    doc = Document()
    doc.docinfo = Docinfo(
        head_content="<meta name='keywords' content='asciidoc'>",
        footer_content="<script>init();</script>",
    )
    p = Paragraph()
    p.inlines.append(Text("Body text"))
    doc.blocks.append(p)

    renderer = DocutilsRenderer()
    html = renderer.render(doc)

    assert "<meta name='keywords' content='asciidoc'>" in html
    assert "<script>init();</script>" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/pytest tests/test_docinfo.py -k "test_docutils_backend_renders_docinfo" -q --tb=short`
Expected: FAIL with `AssertionError` (docinfo content missing from HTML)

- [ ] **Step 3: Write minimal implementation**

In `src/asciidoctrine/docutils_backend.py`:

In `DocutilsRenderer.render()`:
```python
        if hasattr(doc, "docinfo") and doc.docinfo:
            if doc.docinfo.head_content:
                # Append to HTML head / settings_overrides
                self.settings_overrides["rsome_head"] = doc.docinfo.head_content
            if doc.docinfo.footer_content:
                self.settings_overrides["html_footer"] = doc.docinfo.footer_content
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/pytest tests/test_docinfo.py -k "test_docutils_backend_renders_docinfo" -q --tb=short`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_docinfo.py src/asciidoctrine/docutils_backend.py
git commit -m "feat(docutils_backend): inject Docinfo head and footer content into HTML output"
```

---

### Task 6: Feature Matrix & Documentation Update

**Files:**
- Modify: `docs/feature-matrix.adoc`
- Modify: `docs/index.adoc`

**Interfaces:**
- Consumes: None
- Produces: Updated documentation for Docinfo features

- [ ] **Step 1: Write documentation updates**

In `docs/feature-matrix.adoc`:
Change Docinfo status from `Not Supported` to `Fully Supported` with link to `preprocessor.py`.

In `docs/index.adoc`:
Add a section on Docinfo file resolution and `:docinfo:` attribute settings.

- [ ] **Step 2: Run linters and test suite to verify**

Run:
```bash
venv/bin/pytest tests/test_docinfo.py -q --tb=short
venv/bin/ruff check src/asciidoctrine/preprocessor.py src/asciidoctrine/nodes.py src/asciidoctrine/resolver.py src/asciidoctrine/docutils_backend.py
venv/bin/mypy src/asciidoctrine
```
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add docs/feature-matrix.adoc docs/index.adoc
git commit -m "docs: mark Docinfo / Document Metadata as fully supported in feature matrix"
```
