from typing import Any
from unittest.mock import MagicMock

import pytest
from lark.exceptions import UnexpectedInput, UnexpectedToken

from asciidoctrine.lark_parser import (
    _TERMINAL_NAMES,
    AsciiDocSyntaxError,
    _format_expected_terminals,
    parse_inlines,
    parse_to_ast,
)
from asciidoctrine.loader import MemoryLoader
from asciidoctrine.nodes import Document, Paragraph, Ref
from asciidoctrine.resolver import ASGResolver, WorkspaceBuilder, WorkspaceCatalog


def test_terminal_names_mapping() -> None:
    """Verify _TERMINAL_NAMES contains user-friendly descriptions for key grammar terminals."""
    assert "_NEWLINE" in _TERMINAL_NAMES
    assert _TERMINAL_NAMES["_NEWLINE"] == "newline"
    assert _TERMINAL_NAMES["DLIST_MARKER_2"] == ":: (description list marker)"
    assert _TERMINAL_NAMES["SECTION_TITLE_LEAD"] == "section title marker (=)"
    assert _TERMINAL_NAMES["ATTR_LIST_CONTENT"] == "attribute list content"
    assert _TERMINAL_NAMES["EQUALS"] == "="
    assert _TERMINAL_NAMES["LISTING_DELIM"] == "listing block delimiter (----)"
    assert _TERMINAL_NAMES["TABLE_DELIM"] == "table delimiter (|===)"


def test_format_expected_terminals_translates_internal_tokens() -> None:
    """Verify _format_expected_terminals converts internal tokens to friendly names and ignores anonymous ones."""
    mock_exc = MagicMock(spec=UnexpectedInput)
    mock_exc.expected = [
        "_NEWLINE",
        "DLIST_MARKER_2",
        "ATTR_LIST_CONTENT",
        "EQUALS",
        "__ANON_12",
        "CUSTOM_RULE",
    ]
    mock_exc.accepts = None
    mock_exc.allowed = None

    formatted = _format_expected_terminals(mock_exc)
    assert "_NEWLINE" not in formatted
    assert "newline" in formatted
    assert ":: (description list marker)" in formatted
    assert "attribute list content" in formatted
    assert "=" in formatted
    assert "__ANON_12" not in formatted
    assert "CUSTOM_RULE" in formatted


def test_syntax_error_human_readable_tokens() -> None:
    """Verify that AsciiDocSyntaxError diagnostic messages contain friendly names instead of raw Lark terminal names."""
    # parse_inlines with a newline triggers UnexpectedCharacters from Lark
    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_inlines("hello\nworld")

    err_msg = str(exc_info.value)
    # Ensure raw internal terminal names are translated or not exposed
    assert "_NEWLINE" not in err_msg
    # Ensure translated / friendly names are present
    assert "Expected one of:" in err_msg


def test_parse_to_ast_unexpected_token_translation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify parse_to_ast formats UnexpectedToken with human-readable expected terminals."""
    from asciidoctrine import lark_parser

    # Create a mock UnexpectedToken exception
    mock_token = MagicMock()
    mock_token.line = 1
    mock_token.column = 5
    mock_token.start_pos = 5
    exc = UnexpectedToken(
        mock_token, expected={"_NEWLINE", "DLIST_MARKER_2", "ATTR_LIST_CONTENT"}
    )
    exc.line = 1
    exc.column = 5
    exc.pos_in_stream = 5

    def fake_parse(_text: str, *args: Any, **kwargs: Any) -> None:
        raise exc

    # Patch parser.parse in get_document_parser
    parser_instance = lark_parser.get_document_parser()
    monkeypatch.setattr(parser_instance, "parse", fake_parse)

    with pytest.raises(AsciiDocSyntaxError) as exc_info:
        parse_to_ast("dummy content")

    err = exc_info.value
    err_str = str(err)
    assert "_NEWLINE" not in err_str
    assert "newline" in err_str
    assert ":: (description list marker)" in err_str
    assert "attribute list content" in err_str
    assert "Expected one of:" in err_str


def test_unresolved_cross_reference_graceful_handling() -> None:
    """Verify ASGResolver records a warning and sets unresolved strategy instead of raising KeyError."""
    catalog = WorkspaceCatalog()
    doc = Document()
    catalog.index_document("main.adoc", doc)

    xref1 = Ref(variant="xref", target="missing.adoc#missing_anchor")
    xref2 = Ref(variant="xref", target="another_missing#local")
    doc2 = Document()
    doc2.blocks.append(Paragraph(inlines=[xref1, xref2]))

    resolver = ASGResolver(doc2, catalog=catalog, current_file_id="main.adoc")
    # Must not raise KeyError!
    asg = resolver.resolve(doc2)

    # Check warnings were recorded in resolver.warnings
    assert len(resolver.warnings) == 2
    w1 = resolver.warnings[0]
    assert w1["type"] == "unresolved_xref"
    assert w1["target"] == "missing.adoc#missing_anchor"
    assert "Unresolved cross-reference" in w1["message"]

    w2 = resolver.warnings[1]
    assert w2["type"] == "unresolved_xref"
    assert w2["target"] == "another_missing#local"
    assert "Unresolved cross-reference" in w2["message"]

    # Check that in the resolved ASG, both ref nodes are marked as unresolved
    para = asg["blocks"][0]
    ref_node1 = para["inlines"][0]
    ref_node2 = para["inlines"][1]
    assert ref_node1["resolved_strategy"] == "unresolved"
    assert ref_node2["resolved_strategy"] == "unresolved"


def test_workspace_builder_unresolved_xref_graceful() -> None:
    """Verify WorkspaceBuilder resolves projects containing unresolved xrefs without crashing."""
    loader = MemoryLoader(
        {
            "intro.adoc": "= Intro\n\nSee xref:nonexistent.adoc#intro[Missing Doc].",
        }
    )
    builder = WorkspaceBuilder("/workspace", loader=loader)
    graphs = builder.build()
    assert "intro.adoc" in graphs
    intro_asg = graphs["intro.adoc"]
    para = intro_asg["blocks"][0]
    ref_node = para["inlines"][1]  # index 1 after "See "
    assert ref_node["resolved_strategy"] == "unresolved"

    # Verify builder accumulated the warning
    assert len(builder.warnings) == 1
    assert builder.warnings[0]["type"] == "unresolved_xref"
    assert builder.warnings[0]["target"] == "nonexistent.adoc#intro"
