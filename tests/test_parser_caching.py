import pytest

from asciidoctrine.lark_parser import (
    _get_cache_dir,
    clear_ast_cache,
    clear_parser_cache,
    get_document_parser,
    get_inline_parser,
    parse_to_ast,
)


@pytest.fixture(autouse=True)
def clean_cache():
    clear_parser_cache()
    clear_ast_cache()
    yield
    clear_parser_cache()
    clear_ast_cache()


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


def test_parse_to_ast_uses_cached_parser(monkeypatch):
    """Verify parse_to_ast leverages cached parser and does not recompile."""
    import asciidoctrine.lark_parser as lp

    sample = (
        "= Document Title\n\nFirst paragraph with *bold* text.\n\n* Item 1\n* Item 2\n"
    )
    # First call populates cache
    doc1 = parse_to_ast(sample)
    assert doc1 is not None

    call_count = 0
    original_get_document_parser = lp.get_document_parser

    def spy_get_document_parser(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_get_document_parser(*args, **kwargs)

    monkeypatch.setattr(lp, "get_document_parser", spy_get_document_parser)

    # 10 calls to parse_to_ast
    for _ in range(10):
        d = parse_to_ast(sample)
        assert len(d.blocks) >= 2

    assert call_count == 10
    # Cache should only contain 1 entry for default grammar
    assert len(lp._DOCUMENT_PARSERS) == 1


def test_parse_to_ast_use_cache_hit_returns_equivalent_not_identical_ast():
    """Verify use_cache=True returns equivalent AST (deep copy) avoiding mutation hazard."""
    sample = "= Snippet Title\n\nSome *bold* content."
    doc1 = parse_to_ast(sample, use_cache=True)
    doc2 = parse_to_ast(sample, use_cache=True)

    assert doc1 is not doc2
    assert doc1.to_dict() == doc2.to_dict()

    # Mutation hazard check: mutate doc1 and ensure cached doc is untouched
    doc1.blocks.clear()
    doc3 = parse_to_ast(sample, use_cache=True)
    assert doc3 is not doc1
    assert len(doc3.blocks) > 0


def test_clear_ast_cache_forces_reparse():
    """Verify clear_ast_cache clears the LRU AST cache so next call re-parses."""
    import asciidoctrine.lark_parser as lp

    sample = "= Snippet For Clear\n\nParagraph text."
    doc1 = parse_to_ast(sample, use_cache=True)
    assert doc1 is not None

    hits_before = lp._cached_parse_to_ast.cache_info().hits

    # Second call should be a cache hit
    doc2 = parse_to_ast(sample, use_cache=True)
    assert doc2 is not None
    assert lp._cached_parse_to_ast.cache_info().hits == hits_before + 1

    # Clear cache (resets hits and misses to 0)
    clear_ast_cache()
    assert lp._cached_parse_to_ast.cache_info().currsize == 0

    # Third call should be a cache miss
    doc3 = parse_to_ast(sample, use_cache=True)
    assert doc3 is not None
    assert lp._cached_parse_to_ast.cache_info().misses == 1


def test_no_cross_contamination_between_distinct_sources():
    """Verify different source snippets do not cross-contaminate in the AST cache."""
    sample_a = "= Document A\n\nContent for document A."
    sample_b = "= Document B\n\nContent for document B."

    doc_a = parse_to_ast(sample_a, use_cache=True)
    doc_b = parse_to_ast(sample_b, use_cache=True)

    assert doc_a.to_dict() != doc_b.to_dict()
    assert (
        doc_a.header is not None and doc_a.header.title.inlines[0].value == "Document A"
    )
    assert (
        doc_b.header is not None and doc_b.header.title.inlines[0].value == "Document B"
    )

    # Repeat call for sample_a returns Document A
    doc_a2 = parse_to_ast(sample_a, use_cache=True)
    assert (
        doc_a2.header is not None
        and doc_a2.header.title.inlines[0].value == "Document A"
    )
    assert doc_a2 is not doc_a


def test_ast_cache_bypassed_when_use_cache_false():
    """Verify use_cache=False bypasses the AST cache completely."""
    import asciidoctrine.lark_parser as lp

    sample = "= No Cache\n\nThis snippet does not use cache."
    doc1 = parse_to_ast(sample, use_cache=False)
    assert doc1 is not None
    assert lp._cached_parse_to_ast.cache_info().currsize == 0


def test_ast_cache_bypassed_for_large_sources():
    """Verify sources >= 4096 characters bypass the AST cache even if use_cache=True."""
    import asciidoctrine.lark_parser as lp

    large_sample = "= Large Document\n\n" + ("Paragraph with some text.\n\n" * 200)
    assert len(large_sample) >= 4096

    doc1 = parse_to_ast(large_sample, use_cache=True)
    assert doc1 is not None
    assert lp._cached_parse_to_ast.cache_info().currsize == 0


def test_custom_schemes_cache_separately_in_ast_cache():
    """Verify custom authority and opaque schemes are part of the AST cache key."""
    import asciidoctrine.lark_parser as lp

    sample = "custom://example.com/path"
    doc_default = parse_to_ast(sample, use_cache=True)
    doc_custom = parse_to_ast(
        sample,
        extra_authority_schemes=["custom"],
        use_cache=True,
    )
    assert doc_default is not None
    assert doc_custom is not None
    # Different cache entries
    assert lp._cached_parse_to_ast.cache_info().currsize == 2


def test_clear_ast_cache_exported_in_init():
    """Verify clear_ast_cache is exported in asciidoctrine package and __all__."""
    import asciidoctrine

    assert hasattr(asciidoctrine, "clear_ast_cache")
    assert "clear_ast_cache" in asciidoctrine.__all__
    assert callable(asciidoctrine.clear_ast_cache)


def test_get_cache_dir_returns_writable_path():
    """Verify _get_cache_dir returns an existing, writable Path."""
    import os

    cache_dir = _get_cache_dir()
    assert cache_dir.exists()
    assert cache_dir.is_dir()
    assert os.access(cache_dir, os.W_OK)


def test_get_cache_dir_fallback_on_unwritable(monkeypatch, tmp_path):
    """Verify _get_cache_dir falls back to tempfile.gettempdir() when user cache dir fails."""
    import tempfile
    from pathlib import Path

    import asciidoctrine.lark_parser as lp

    def fail_user_cache_dir(*args, **kwargs):
        return str(tmp_path / "nonexistent" / "deep" / "\x00invalid")

    monkeypatch.setattr("platformdirs.user_cache_dir", fail_user_cache_dir)
    cache_dir = lp._get_cache_dir()
    assert cache_dir == Path(tempfile.gettempdir())
