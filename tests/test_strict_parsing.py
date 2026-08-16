import pytest

from asciidoctrine import AsciiDocSyntaxError, parse_to_ast



pytestmark = pytest.mark.integration
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


def test_malformed_bracket_inside_bold_paragraph():
    # Syntax errors inside inline formatting should be correctly detected in strict mode
    source = "[This is *bold with [unbalanced* bracket\n"
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Malformed block attribute list" in str(exc_info.value)


def test_legacy_open_block_strict_mode_never_errors():
    """Regression guard: the '--' open block delimiter is deprecated in perpetuity.

    It is too widespread to ever become a hard error, so strict=True must
    NOT raise AsciiDocSyntaxError for it.  Instead, it must always emit a
    DeprecationWarning regardless of the strict flag.
    """
    import warnings

    source = "--\nSome content.\n--\n"

    # strict=True: parses successfully, emits DeprecationWarning, does not raise
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc = parse_to_ast(source, strict=True)
    assert doc.blocks[0].name == "open"
    assert doc.blocks[0].delimiter == "--"
    deprecation_warnings = [
        w for w in caught if issubclass(w.category, DeprecationWarning)
    ]
    assert deprecation_warnings, "Expected a DeprecationWarning for '--' delimiter"
    assert "deprecated" in str(deprecation_warnings[0].message).lower()

    # strict=False: same warning, same successful parse
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        doc_permissive = parse_to_ast(source, strict=False)
    assert doc_permissive.blocks[0].name == "open"
    deprecation_warnings_permissive = [
        w for w in caught if issubclass(w.category, DeprecationWarning)
    ]
    assert deprecation_warnings_permissive, (
        "Expected a DeprecationWarning for '--' delimiter in permissive mode too"
    )
