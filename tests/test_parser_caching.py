import pytest

from asciidoctrine.lark_parser import (
    _DOCUMENT_PARSERS,
    clear_parser_cache,
    get_document_parser,
    get_inline_parser,
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

    # Should only be called once, because the subsequent 9 calls should use the cache.
    assert call_count == 1
    # Cache should only contain 1 entry for default grammar
    assert len(lp._DOCUMENT_PARSERS) == 1
