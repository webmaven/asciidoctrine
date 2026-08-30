import pytest

from asciidoctrine.lark_parser import parse_to_ast

pytestmark = pytest.mark.unit


def test_block_title_attaches_after_paragraph():
    source = (
        "First paragraph.\n"
        ".Title for next\n"
        "[source,python]\n"
        "----\n"
        "print('hi')\n"
        "----\n"
    )

    doc = parse_to_ast(source, strict=False)

    # Expect two top-level blocks: a Paragraph and the Listing that follows
    assert len(doc.blocks) >= 2

    listing = doc.blocks[1]
    assert getattr(listing, "title", None) is not None, "Listing should have an attached title"

    title = listing.title
    title_text = "".join(getattr(n, "value", "") for n in title.inlines)
    assert title_text == "Title for next"
