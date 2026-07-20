import pytest

from asciidoctrine import AsciiDocSyntaxError, parse_to_ast


def test_unclosed_listing_block():
    source = "[source,python]\n----\nprint('hello')\n"
    # Strict should raise exception
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Unclosed verbatim block" in str(exc_info.value)

    # Permissive should succeed
    doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "paragraph"


def test_unclosed_sidebar_block():
    source = "****\nSome sidebar content without closing\n"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Unclosed block delimiter" in str(exc_info.value)

    doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "paragraph"


def test_malformed_attribute_list():
    source = "[source,python\n----\nprint('hello')\n----"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Malformed block attribute list" in str(exc_info.value)

    doc = parse_to_ast(source, strict=False)
    # Under permissive, split into a paragraph and a listing block
    assert len(doc.blocks) == 2
    assert doc.blocks[0].name == "paragraph"
    assert doc.blocks[1].name == "listing"


def test_malformed_anchor():
    source = "[[my_anchor\nSome content"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Unclosed inline anchor" in str(exc_info.value)

    doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "paragraph"


def test_malformed_block_macro():
    source = "image::logo.png\n"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Malformed block macro" in str(exc_info.value)

    doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "image"


def test_malformed_description_list_marker():
    source = ":: invalid\n"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Malformed description list marker" in str(exc_info.value)

    doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "paragraph"


def test_valid_description_list_term_level3():
    source = "term:::\n"
    doc = parse_to_ast(source, strict=True)
    # Under both strict and permissive, this is now correctly a description list (dlist),
    # not a block macro with a colon target.
    assert doc.blocks[0].name == "descriptionList"


def test_unclosed_inline_footnote():
    source = "This is a footnote:[some footnote text"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Unclosed inline footnote" in str(exc_info.value)

    doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "paragraph"


def test_broken_table_structure():
    source = "|===\n| Cell 1 | Cell 2\n"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Unclosed block delimiter" in str(exc_info.value)

    doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "paragraph"


def test_malformed_table_cell_specifier():
    source = "|===\n|2.. Cell\n|===\n"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Malformed table cell specifier" in str(exc_info.value)

    doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "table"


def test_strict_default_behavior():
    # Verify that parse_to_ast defaults to strict=True
    source = "image::logo.png\n"
    with pytest.raises(AsciiDocSyntaxError):
        parse_to_ast(source)
