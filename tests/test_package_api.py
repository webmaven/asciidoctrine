"""
Unit tests for the asciidoctrine public package API (__init__.py).

Verifies that all symbols in __all__ are importable from the package root,
that __version__ exists and is a valid string, and that the most
commonly-used public functions work end-to-end from the top-level import.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


class TestPackageImports:
    """All symbols in __all__ must be importable from the package root."""

    def test_parse_to_ast_importable(self) -> None:
        from asciidoctrine import parse_to_ast  # noqa: F401

        assert callable(parse_to_ast)

    def test_ascii_doc_syntax_error_importable(self) -> None:
        from asciidoctrine import AsciiDocSyntaxError  # noqa: F401

        assert issubclass(AsciiDocSyntaxError, Exception)

    def test_serialize_to_asciidoc_importable(self) -> None:
        from asciidoctrine import serialize_to_asciidoc  # noqa: F401

        assert callable(serialize_to_asciidoc)

    def test_node_importable(self) -> None:
        from asciidoctrine import Node  # noqa: F401

        assert Node is not None

    def test_docinfo_importable(self) -> None:
        from asciidoctrine import Docinfo  # noqa: F401

        assert Docinfo is not None

    def test_document_importable(self) -> None:
        from asciidoctrine import Document  # noqa: F401

        assert Document is not None

    def test_section_importable(self) -> None:
        from asciidoctrine import Section  # noqa: F401

        assert Section is not None

    def test_paragraph_importable(self) -> None:
        from asciidoctrine import Paragraph  # noqa: F401

        assert Paragraph is not None

    def test_text_importable(self) -> None:
        from asciidoctrine import Text  # noqa: F401

        assert Text is not None

    def test_node_visitor_importable(self) -> None:
        from asciidoctrine import NodeVisitor  # noqa: F401

        assert NodeVisitor is not None

    def test_node_transformer_importable(self) -> None:
        from asciidoctrine import NodeTransformer  # noqa: F401

        assert NodeTransformer is not None

    def test_asg_resolver_importable(self) -> None:
        from asciidoctrine import ASGResolver  # noqa: F401

        assert ASGResolver is not None

    def test_workspace_catalog_importable(self) -> None:
        from asciidoctrine import WorkspaceCatalog  # noqa: F401

        assert WorkspaceCatalog is not None

    def test_workspace_builder_importable(self) -> None:
        from asciidoctrine import WorkspaceBuilder  # noqa: F401

        assert WorkspaceBuilder is not None


class TestPackageMetadata:
    def test_version_exists(self) -> None:
        import asciidoctrine

        assert hasattr(asciidoctrine, "__version__")

    def test_version_is_string(self) -> None:
        import asciidoctrine

        assert isinstance(asciidoctrine.__version__, str)

    def test_version_not_empty(self) -> None:
        import asciidoctrine

        assert len(asciidoctrine.__version__) > 0

    def test_all_defined(self) -> None:
        import asciidoctrine

        assert hasattr(asciidoctrine, "__all__")
        assert isinstance(asciidoctrine.__all__, list)

    def test_all_symbols_importable(self) -> None:
        """Every name in __all__ must be a real attribute on the module."""
        import asciidoctrine

        for name in asciidoctrine.__all__:
            assert hasattr(asciidoctrine, name), f"__all__ contains {name!r} but it is not importable"


class TestPackageEndToEnd:
    """Light end-to-end smoke tests exercising the public API."""

    def test_parse_to_ast_returns_document(self) -> None:
        from asciidoctrine import Document, parse_to_ast

        doc = parse_to_ast("= Hello\n\nWorld.")
        assert isinstance(doc, Document)

    def test_asg_resolver_round_trip(self) -> None:
        from asciidoctrine import ASGResolver, parse_to_ast

        doc = parse_to_ast("= Title\n\nParagraph text.")
        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)
        assert asg["name"] == "document"

    def test_serialize_to_asciidoc_round_trip(self) -> None:
        from asciidoctrine import parse_to_ast, serialize_to_asciidoc

        src = "= Simple\n\nA paragraph.\n"
        doc = parse_to_ast(src)
        out = serialize_to_asciidoc(doc)
        assert isinstance(out, str)
        assert len(out) > 0

    def test_workspace_catalog_basic(self) -> None:
        from asciidoctrine import WorkspaceCatalog, parse_to_ast

        catalog = WorkspaceCatalog()
        doc = parse_to_ast("= Doc\n\nContent.")
        catalog.index_document("doc.adoc", doc)
        assert "doc.adoc#" in catalog.by_fqid
