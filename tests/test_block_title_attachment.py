import pytest

from asciidoctrine.lark_parser import parse_to_ast

pytestmark = pytest.mark.unit


def test_block_title_attaches_after_paragraph():
    source = (
        "First paragraph.\n\n"
        ".Title for next\n"
        "[source,python]\n"
        "----\n"
        "print('hi')\n"
        "----\n"
    )

    doc = parse_to_ast(source, strict=False)

    # Expect two top-level blocks: a Paragraph and the Listing that follows.
    # Note: the bug occurred when the following block had no title if the previous
    # block (or any preceding block) itself had a title — ensure separation with a blank line.
    assert len(doc.blocks) >= 2

    listing = doc.blocks[1]
    assert getattr(listing, "title", None) is not None, "Listing should have an attached title"

    title = listing.title
    title_text = "".join(getattr(n, "value", "") for n in title.inlines)
    assert title_text == "Title for next"


def test_block_title_attaches_when_preceded_by_titled_block():
    # Reproduce the regression: a block with a title directly followed by another
    # block that also has a title. The second block must receive its title.
    source = (
        ".Prev Title\n"
        "[source,python]\n"
        "----\n"
        "print('first')\n"
        "----\n"
        ".Title for next\n"
        "[source,python]\n"
        "----\n"
        "print('second')\n"
        "----\n"
    )

    doc = parse_to_ast(source, strict=False)

    # Expect two listings; both should have titles attached
    listings = [b for b in doc.blocks if getattr(b, 'name', '') == 'listing' or b.__class__.__name__ == 'Listing']
    assert len(listings) >= 2

    first_title = listings[0].title
    second_title = listings[1].title
    assert first_title is not None, "First listing should have a title"
    assert second_title is not None, "Second listing should have a title"

    first_text = "".join(getattr(n, 'value', '') for n in first_title.inlines)
    second_text = "".join(getattr(n, 'value', '') for n in second_title.inlines)
    assert first_text.strip() == "Prev Title"
    assert second_text.strip() == "Title for next"
