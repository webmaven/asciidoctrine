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
    sample = "= Document Title\n\nFirst paragraph with *bold* text.\n\n* Item 1\n* Item 2\n"
    # Pre-warm
    doc = parse_to_ast(sample)
    assert doc is not None

    start = time.perf_counter()
    iterations = 20
    for _ in range(iterations):
        d = parse_to_ast(sample)
        assert len(d.blocks) >= 2
    elapsed = time.perf_counter() - start

    # Average parse time with cached parser should be well under 0.2s per parse
    avg_time = elapsed / iterations
    assert avg_time < 0.2, f"Average parse time was {avg_time:.4f}s, expected < 0.2s"
