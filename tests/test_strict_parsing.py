"""
Integration tests for strict vs. permissive parsing behaviour.

Each case in STRICT_CASES verifies:
  - strict=True raises AsciiDocSyntaxError containing the expected message fragment
  - strict=False succeeds and produces the expected top-level block name(s)

Special cases that don't fit the generic pattern are tested individually below.
"""

import warnings

import pytest

from asciidoctrine import AsciiDocSyntaxError, parse_to_ast

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Parametrized cases: (id, source, strict_msg, permissive_names)
# ---------------------------------------------------------------------------
STRICT_CASES = [
    (
        "unclosed_listing",
        "[source,python]\n----\nprint('hello')\n",
        "Unclosed verbatim block",
        ["paragraph"],
    ),
    (
        "unclosed_sidebar",
        "****\nSome sidebar content without closing\n",
        "Unclosed block delimiter",
        ["paragraph"],
    ),
    (
        "malformed_attribute_list",
        "[source,python\n----\nprint('hello')\n----",
        "Malformed block attribute list",
        ["paragraph", "listing"],  # permissive splits into two blocks
    ),
    (
        "malformed_anchor",
        "[[my_anchor\nSome content",
        "Unclosed inline anchor",
        ["paragraph"],
    ),
    (
        "malformed_block_macro",
        "image::logo.png\n",
        "Malformed block macro",
        ["image"],
    ),
    (
        "malformed_description_list_marker",
        ":: invalid\n",
        "Malformed description list marker",
        ["paragraph"],
    ),
    (
        "bullet_prefixed_bold_description_list_term",
        "* **Incremental Compilation**:: Tracks dependencies via a DAG cache.\n",
        "Malformed description list term",
        ["descriptionList"],
    ),
    (
        "bullet_prefixed_description_list_term",
        "* Term:: definition\n",
        "Malformed description list term",
        ["descriptionList"],
    ),

    (
        "broken_table_unclosed",
        "|===\n| Cell 1 | Cell 2\n",
        "Unclosed block delimiter",
        ["paragraph"],
    ),
    (
        "malformed_table_cell_specifier",
        "|===\n|2.. Cell\n|===\n",
        "Malformed table cell specifier",
        ["table"],
    ),
    (
        "malformed_bracket_in_bold",
        "[This is *bold with [unbalanced* bracket\n",
        "Malformed block attribute list",
        None,  # permissive result not checked beyond no-raise
    ),
]


@pytest.mark.parametrize(
    "source,strict_msg,permissive_names",
    [(s, m, p) for _, s, m, p in STRICT_CASES],
    ids=[id_ for id_, *_ in STRICT_CASES],
)
def test_strict_raises_permissive_succeeds(source, strict_msg, permissive_names):
    """strict=True raises AsciiDocSyntaxError; strict=False parses successfully."""
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert strict_msg in str(exc_info.value)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        doc = parse_to_ast(source, strict=False)
    if permissive_names is not None:
        assert [b.name for b in doc.blocks] == permissive_names


# ---------------------------------------------------------------------------
# Special cases that don't follow the strict-raises / permissive-succeeds pattern
# ---------------------------------------------------------------------------


def test_valid_description_list_term_level3():
    """A valid triple-colon term is a dlist even in strict mode."""
    source = "term:::\n"
    doc = parse_to_ast(source, strict=True)
    assert doc.blocks[0].name == "descriptionList"


def test_unclosed_inline_footnote_always_raises():
    """An unclosed footnote:[ is a hard grammar error in both strict and permissive mode.

    Since `footnote:` is now a proper grammar terminal (not raw text), the Earley
    parser fails to match the closing `]` and raises a parse error before the AST
    is even built.  Both strict=True and strict=False must raise AsciiDocSyntaxError
    with the friendly 'Unclosed inline footnote' diagnostic.
    """
    source = "This is a footnote:[some footnote text"
    for strict in (True, False):
        with pytest.raises(AsciiDocSyntaxError) as exc_info:
            parse_to_ast(source, strict=strict)
        assert "Unclosed inline footnote" in str(exc_info.value), (
            f"Expected 'Unclosed inline footnote' in error (strict={strict}), "
            f"got: {exc_info.value}"
        )


@pytest.mark.parametrize(
    "source",
    [
        "* **Incremental Compilation**:: Tracks dependencies via a DAG cache.\n",
        "* Term:: definition\n",
    ],
    ids=["bold_term", "plain_term"],
)
def test_bullet_prefixed_description_list_term_has_actionable_diagnostics(source):
    """Both recovery and strict errors must explain how to fix either form."""
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast(source, strict=True)
    assert "Remove the leading bullet" in str(exc_info.value)
    assert "list continuation (+)" in str(exc_info.value)

    with pytest.warns(SyntaxWarning) as caught:
        doc = parse_to_ast(source, strict=False)
    assert doc.blocks[0].name == "descriptionList"
    assert "Remove the leading bullet" in str(caught[0].message)
    assert "list continuation (+)" in str(caught[0].message)


def test_strict_default_behavior():
    """parse_to_ast() defaults to strict=True."""
    source = "image::logo.png\n"
    with pytest.raises(AsciiDocSyntaxError):
        parse_to_ast(source)


def test_legacy_open_block_strict_mode_never_errors():
    """The '--' open block is deprecated but must never raise in strict mode.

    It is too widespread to ever become a hard error, so strict=True must
    NOT raise AsciiDocSyntaxError for it. Instead, it must always emit a
    DeprecationWarning regardless of the strict flag.
    """
    source = "--\nSome content.\n--\n"

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


def test_syntax_error_formatted_diagnostic():
    """AsciiDocSyntaxError formats line, column, snippet context, and filepath cleanly."""
    err = AsciiDocSyntaxError(
        "Parsing failed",
        line=14,
        column=7,
        context="invalid syntax here\n      ^",
        filepath="/path/to/chapter1.adoc",
    )
    formatted = str(err)
    assert "Syntax error in 'chapter1.adoc' at line 14, column 7." in formatted
    assert "invalid syntax here\n      ^" in formatted

    # When filepath is None or '<root>'
    err_root = AsciiDocSyntaxError(
        "Parsing failed",
        line=2,
        column=5,
        context="bad inline *bold\n    ^",
        filepath="<root>",
    )
    formatted_root = str(err_root)
    assert "Syntax error at line 2, column 5." in formatted_root
    assert "bad inline *bold\n    ^" in formatted_root

    # When context is None, falls back to message
    err_no_context = AsciiDocSyntaxError("Plain syntax error message")
    assert str(err_no_context) == "Plain syntax error message"
