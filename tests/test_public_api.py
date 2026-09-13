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


def test_document_loader_accepts_fileprovider():
    """Verify Document.loader can accept a FileProvider."""
    from asciidoctrine.loader import MemoryLoader
    from asciidoctrine.nodes import Document

    doc = Document()
    loader = MemoryLoader({"a": "b"})
    doc.loader = loader
    assert doc.loader is loader
    doc.loader = None
    assert doc.loader is None
