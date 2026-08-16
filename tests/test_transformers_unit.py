import pytest
from lark import Token

from asciidoctrine.nodes import Document, Node, NodeTransformer, Paragraph, Span, Text
from asciidoctrine.transformers.block_transformer import BlockTransformer

pytestmark = pytest.mark.unit


class MockTransformer(BlockTransformer):
    pass


@pytest.fixture
def transformer():
    return MockTransformer()


def test_get_list_level_bullets(transformer):
    # * item
    token = Token("ULIST_MARKER", "* ")
    assert transformer._get_list_level(token) == 1

    # ** item
    token = Token("ULIST_MARKER", "** ")
    assert transformer._get_list_level(token) == 2

    #   * item (indented)
    token = Token("ULIST_MARKER", "  * ")
    assert transformer._get_list_level(token) == 2


def test_get_list_level_ordered(transformer):
    # . item
    token = Token("OLIST_MARKER", ". ")
    assert transformer._get_list_level(token) == 1

    # .. item
    token = Token("OLIST_MARKER", ".. ")
    assert transformer._get_list_level(token) == 2

    # 1. item
    token = Token("OLIST_MARKER", "1. ")
    assert transformer._get_list_level(token) == 1


def test_set_location_from_children(transformer):
    node = Node()
    child1 = Text("abc")
    child1.location = [{"line": 1, "col": 1}, {"line": 1, "col": 3}]

    child2 = Text("def")
    child2.location = [{"line": 1, "col": 5}, {"line": 1, "col": 7}]

    transformer._set_location_from_children(node, [child1, child2])

    assert node.location == [{"line": 1, "col": 1}, {"line": 1, "col": 7}]


def test_set_location_from_children_with_newline(transformer):
    node = Node()
    child1 = Text("abc")
    child1.location = [{"line": 1, "col": 1}, {"line": 1, "col": 3}]

    nl_token = Token("_NEWLINE", "\n")
    nl_token.line = 1
    nl_token.column = 4
    nl_token.end_line = 2
    nl_token.end_column = 1

    transformer._set_location_from_children(node, [child1, nl_token])

    # Should ignore NL token and only use child1
    assert node.location == [{"line": 1, "col": 1}, {"line": 1, "col": 3}]


# NodeTransformer TDD Tests (Issue #73)


class WordReplacer(NodeTransformer):
    """Replaces a specific word in Text nodes."""

    def visit_text(self, node: Text, **kwargs):
        if node.value == "apple":
            return Text("banana")
        return node


class TypeConverter(NodeTransformer):
    """Replaces Text nodes containing 'emphasize' with a Span node."""

    def visit_text(self, node: Text, **kwargs):
        if "emphasize" in node.value:
            # Replace Text node with a Span node of variant='emphasis'
            return Span(variant="emphasis", inlines=[Text(node.value)])
        return node


class CommentPruner(NodeTransformer):
    """Prunes out paragraphs whose content starts with 'Comment:'."""

    def visit_paragraph(self, node: Paragraph, **kwargs):
        # Inspect children of the paragraph
        if node.inlines and isinstance(node.inlines[0], Text):
            if node.inlines[0].value.startswith("Comment:"):
                return None  # Deletes this paragraph!
        return self.generic_visit(node, **kwargs)


class MultiParagraphExporter(NodeTransformer):
    """Expands a Paragraph containing 'split' into two Paragraphs."""

    def visit_paragraph(self, node: Paragraph, **kwargs):
        if (
            node.inlines
            and isinstance(node.inlines[0], Text)
            and "split" in node.inlines[0].value
        ):
            p1 = Paragraph(inlines=[Text("First part")])
            p2 = Paragraph(inlines=[Text("Second part")])
            return [p1, p2]  # Expands to list of nodes!
        return self.generic_visit(node, **kwargs)


def test_node_transformer_replace_same_type():
    doc = Document(blocks=[Paragraph(inlines=[Text("apple"), Text("cherry")])])
    WordReplacer().visit(doc)
    p = doc.blocks[0]
    assert p.inlines[0].value == "banana"
    assert p.inlines[1].value == "cherry"


def test_node_transformer_replace_different_type():
    doc = Document(blocks=[Paragraph(inlines=[Text("please emphasize me")])])
    TypeConverter().visit(doc)
    p = doc.blocks[0]
    assert isinstance(p.inlines[0], Span)
    assert p.inlines[0].variant == "emphasis"
    assert p.inlines[0].inlines[0].value == "please emphasize me"


def test_node_transformer_delete_node():
    doc = Document(
        blocks=[
            Paragraph(inlines=[Text("Comment: discard this")]),
            Paragraph(inlines=[Text("Keep this one")]),
        ]
    )
    CommentPruner().visit(doc)
    assert len(doc.blocks) == 1
    assert doc.blocks[0].inlines[0].value == "Keep this one"


def test_node_transformer_expand_node():
    doc = Document(blocks=[Paragraph(inlines=[Text("split this block")])])
    MultiParagraphExporter().visit(doc)
    assert len(doc.blocks) == 2
    assert doc.blocks[0].inlines[0].value == "First part"
    assert doc.blocks[1].inlines[0].value == "Second part"


def test_table_span_both(transformer):
    cols = Token("COLS", "3")
    rows = Token("ROWS", "2")
    assert transformer.span_both(cols, rows) == {"colspan": 3, "rowspan": 2}
    assert transformer.span_both(None, rows) == {"colspan": 1, "rowspan": 2}


def test_table_span_cols(transformer):
    cols = Token("COLS", "4")
    assert transformer.span_cols(cols) == {"colspan": 4}


def test_table_multiplier(transformer):
    mult = Token("MULTIPLIER", "5")
    assert transformer.multiplier(mult) == {"multiplier": 5}


def test_table_align_both(transformer):
    horiz = Token("ALIGN", "^")
    vert = Token("VALIGN", ".^")
    assert transformer.align_both(horiz, vert) == {
        "align": "center",
        "valign": "middle",
    }
    assert transformer.align_both(horiz, None) == {"align": "center"}


def test_table_align_vert(transformer):
    vert = Token("VALIGN", ".>")
    assert transformer.align_vert(vert) == {"valign": "bottom"}


def test_table_cell_spec(transformer):
    children = [
        {"colspan": 2, "rowspan": 3},
        {"align": "center", "valign": "middle"},
        Token("STYLE_SPEC", "s"),
    ]
    assert transformer.table_cell_spec(children) == {
        "colspan": 2,
        "rowspan": 3,
        "align": "center",
        "valign": "middle",
        "style": "s",
    }


def test_block_transformer_delimiters(transformer):
    from lark.tree import Meta

    from asciidoctrine.nodes import Paragraph, Text

    meta = Meta()

    # Quote variants (4, 5, 6)
    q4_delim = Token("QUOTE_DELIM_4", "____")
    q4 = transformer.quote_4(meta, [q4_delim, Paragraph(inlines=[Text("Quote text")])])
    assert q4.delimiter == "____"

    q5_delim = Token("QUOTE_DELIM_5", "_____")
    q5 = transformer.quote_5(meta, [q5_delim, Paragraph(inlines=[Text("Quote text")])])
    assert q5.delimiter == "_____"

    q6_delim = Token("QUOTE_DELIM_6", "______")
    q6 = transformer.quote_6(meta, [q6_delim, Paragraph(inlines=[Text("Quote text")])])
    assert q6.delimiter == "______"

    # Sidebar variants (5, 6)
    s5_delim = Token("SIDEBAR_DELIM_5", "*****")
    s5 = transformer.sidebar_5(
        meta, [s5_delim, Paragraph(inlines=[Text("Sidebar text")])]
    )
    assert s5.delimiter == "*****"

    s6_delim = Token("SIDEBAR_DELIM_6", "******")
    s6 = transformer.sidebar_6(
        meta, [s6_delim, Paragraph(inlines=[Text("Sidebar text")])]
    )
    assert s6.delimiter == "******"

    # Open block variants (4, 5, 6, long)
    o4_delim = Token("OPEN_BLOCK_DELIM_4", "~~~~")
    o4 = transformer.open_block_4(
        meta, [o4_delim, Paragraph(inlines=[Text("Open text")])]
    )
    assert o4.delimiter == "~~~~"

    o5_delim = Token("OPEN_BLOCK_DELIM_5", "~~~~~")
    o5 = transformer.open_block_5(
        meta, [o5_delim, Paragraph(inlines=[Text("Open text")])]
    )
    assert o5.delimiter == "~~~~~"

    o6_delim = Token("OPEN_BLOCK_DELIM_6", "~~~~~~")
    o6 = transformer.open_block_6(
        meta, [o6_delim, Paragraph(inlines=[Text("Open text")])]
    )
    assert o6.delimiter == "~~~~~~"

    olong_delim = Token("OPEN_BLOCK_DELIM_6", "~~~~~~~")
    olong = transformer.open_block_long(
        meta, [olong_delim, Paragraph(inlines=[Text("Open text")])]
    )
    assert olong.delimiter == "~~~~~~~"


def test_open_block_legacy_warning(transformer):
    import warnings

    from lark.tree import Meta

    from asciidoctrine.nodes import Paragraph, Text

    meta = Meta()
    delim = Token("OPEN_BLOCK_DELIM", "--")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ob = transformer.open_block_legacy(
            meta, [delim, Paragraph(inlines=[Text("Legacy open")])]
        )
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert "deprecated" in str(w[-1].message)
        assert ob.delimiter == "--"


def test_block_transformer_verbatim_blocks(transformer):
    from lark.tree import Meta

    meta = Meta()

    # literal_block
    lit_delim = Token("LITERAL_DELIM", "....")
    lit_content = Token("LITERAL_CONTENT", "literal text content")
    lit = transformer.literal_block(meta, [lit_delim, lit_content, lit_delim])
    assert lit.delimiter == "...."
    assert lit.inlines[0].value == "literal text content"

    # passthrough_block
    pass_delim = Token("PASSTHROUGH_BLOCK_DELIM", "++++")
    pass_content = Token("PASSTHROUGH_CONTENT", "pass text content")
    pas = transformer.passthrough_block(meta, [pass_delim, pass_content, pass_delim])
    assert pas.delimiter == "++++"
    assert pas.inlines[0].value == "pass text content"

    # outer_listing_block
    out_start = Token("OUTER_LISTING_START", "--ASCIIDOCTRINE_OUTER_LISTING_START_4--")
    out_content = Token("OUTER_LISTING_CONTENT", "outer listing content")
    out_end = Token("OUTER_LISTING_END", "--ASCIIDOCTRINE_OUTER_LISTING_END_4--")
    out_lis = transformer.outer_listing_block(meta, [out_start, out_content, out_end])
    assert out_lis.delimiter == "----"
    assert out_lis.inlines[0].value == "outer listing content"


def test_table_cell_fallback_and_spec(transformer):
    from lark.tree import Meta

    meta = Meta()
    spec_dict = {
        "colspan": 2,
        "rowspan": 3,
        "align": "center",
        "valign": "middle",
        "style": "s",
        "multiplier": 2,
    }
    cell_token = Token("TABLE_CELL", "| Invalid AsciiDoc ((( markup")

    cell = transformer.table_cell(meta, [spec_dict, cell_token])
    assert cell.colspan == 2
    assert cell.rowspan == 3
    assert cell.align == "center"
    assert cell.valign == "middle"
    assert cell.style == "s"
    assert cell.multiplier == 2
    assert len(cell.blocks) == 1
    assert cell.blocks[0].inlines[0].value == "Invalid AsciiDoc ((( markup"


# ---------------------------------------------------------------------------
# _merge_consecutive_lists
# ---------------------------------------------------------------------------


def test_merge_consecutive_lists_description_lists(transformer):
    from asciidoctrine.nodes import (
        DescriptionList,
        DescriptionListItem,
        DescriptionListTerm,
    )

    term = DescriptionListTerm(inlines=[Text("key")])
    item = DescriptionListItem(terms=[term], blocks=[])
    dl1 = DescriptionList(items=[item])
    dl2 = DescriptionList(items=[item])
    result = transformer._merge_consecutive_lists([dl1, dl2])
    assert len(result) == 1
    assert isinstance(result[0], DescriptionList)
    assert len(result[0].items) == 2


def test_merge_consecutive_lists_callout_lists(transformer):
    from asciidoctrine.nodes import CalloutList, CalloutListItem

    cli1 = CalloutListItem(number=1, principal=[Text("first")])
    cli2 = CalloutListItem(number=2, principal=[Text("second")])
    cl1 = CalloutList(items=[cli1])
    cl2 = CalloutList(items=[cli2])
    result = transformer._merge_consecutive_lists([cl1, cl2])
    assert len(result) == 1
    assert isinstance(result[0], CalloutList)
    assert len(result[0].items) == 2


def test_merge_consecutive_lists_different_types_not_merged(transformer):
    from asciidoctrine.nodes import List as ASTList, Paragraph

    ul = ASTList(variant="unordered", marker="*")
    para = Paragraph(inlines=[Text("para")])
    result = transformer._merge_consecutive_lists([ul, para])
    assert len(result) == 2


def test_merge_consecutive_lists_empty(transformer):
    assert transformer._merge_consecutive_lists([]) == []


# ---------------------------------------------------------------------------
# _get_list_level
# ---------------------------------------------------------------------------


def test_get_list_level_dash(transformer):
    token = Token("ULIST_MARKER", "- ")
    assert transformer._get_list_level(token) == 1


def test_get_list_level_numeric_fallback(transformer):
    # "1. " — starts with neither -, *, . so falls to else → level=1
    token = Token("OLIST_MARKER", "1. ")
    assert transformer._get_list_level(token) == 1


# ---------------------------------------------------------------------------
# _nest_list_items — deep nesting and edge cases
# ---------------------------------------------------------------------------


def test_nest_list_items_empty(transformer):
    assert transformer._nest_list_items([]) == []


def test_nest_list_items_deep_nesting(transformer):
    items = [
        {
            "level": 1,
            "item_type": "bullet",
            "marker": "*",
            "children": [Text("parent")],
            "raw_children": [],
        },
        {
            "level": 2,
            "item_type": "bullet",
            "marker": "**",
            "children": [Text("child")],
            "raw_children": [],
        },
    ]
    result = transformer._nest_list_items(items)
    assert len(result) == 1
    # The child should be nested under the parent
    parent = result[0]
    assert len(parent.blocks) == 1  # one nested ASTList


def test_nest_list_items_variant_change_same_level(transformer):
    """Switching from bullet to ordered at the same level must not crash."""
    items = [
        {
            "level": 1,
            "item_type": "bullet",
            "marker": "*",
            "children": [Text("a")],
            "raw_children": [],
        },
        {
            "level": 1,
            "item_type": "enumerated",
            "marker": ".",
            "children": [Text("b")],
            "raw_children": [],
        },
    ]
    result = transformer._nest_list_items(items)
    # Both end up in the same list (variant stays from first item per impl)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# _build_verbatim_inlines — CRLF, HTML callouts, auto-number, no-nl branch
# ---------------------------------------------------------------------------


def test_build_verbatim_inlines_empty(transformer):
    result = transformer._build_verbatim_inlines("", None)
    assert len(result) == 1
    assert result[0].value == ""


def test_build_verbatim_inlines_no_callouts(transformer):
    result = transformer._build_verbatim_inlines("just text", None)
    assert len(result) == 1
    assert result[0].value == "just text"


def test_build_verbatim_inlines_crlf_line(transformer):
    """Lines with CRLF endings must be handled without crashing."""
    content = "first line\r\nsecond line\r\n"
    result = transformer._build_verbatim_inlines(content, None)
    # No callouts — should return a single Text with the original content
    assert result[0].value == content


def test_build_verbatim_inlines_html_bare_callout(transformer):
    """The HTML_BARE_CALLOUT_RE branch (<!--1-->) must fire and produce a Callout."""
    from asciidoctrine.nodes import Callout

    content = "some code <!--1-->\n"
    result = transformer._build_verbatim_inlines(content, None)
    callout_nodes = [n for n in result if isinstance(n, Callout)]
    assert len(callout_nodes) == 1
    assert callout_nodes[0].value == 1


def test_build_verbatim_inlines_auto_numbered_callout(transformer):
    """'<.>' must auto-number starting at 1."""
    from asciidoctrine.nodes import Callout

    content = "line a <.>\nline b <.>\n"
    result = transformer._build_verbatim_inlines(content, None)
    callouts = [n for n in result if isinstance(n, Callout)]
    assert len(callouts) == 2
    assert callouts[0].value == 1
    assert callouts[1].value == 2


def test_build_verbatim_inlines_explicit_callout_no_trailing_nl(transformer):
    """Line without a trailing newline must still parse the callout."""
    from asciidoctrine.nodes import Callout

    content = "code <1>"  # no trailing newline
    result = transformer._build_verbatim_inlines(content, None)
    callouts = [n for n in result if isinstance(n, Callout)]
    assert callouts[0].value == 1


def test_build_verbatim_inlines_callout_increments_next_auto(transformer):
    """An explicit <3> must advance next_auto past 3."""
    from asciidoctrine.nodes import Callout

    content = "a <3>\nb <.>\n"
    result = transformer._build_verbatim_inlines(content, None)
    callouts = [n for n in result if isinstance(n, Callout)]
    assert callouts[0].value == 3
    assert callouts[1].value == 4  # next_auto advances past 3


# ---------------------------------------------------------------------------
# Outer block variants with non-default delimiters
# ---------------------------------------------------------------------------


def test_outer_listing_block_non_default_delimiter(transformer):
    from lark.tree import Meta

    meta = Meta()
    # Pattern: --ASCIIDOCTRINE_OUTER_LISTING_START_<N>-- where N controls dashes
    start = Token("OUTER_LISTING_START", "--ASCIIDOCTRINE_OUTER_LISTING_START_5--")
    content = Token("OUTER_LISTING_CONTENT", "code here")
    result = transformer.outer_listing_block(meta, [start, content])
    assert result.delimiter == "-----"
    assert result.inlines[0].value == "code here"


def test_outer_literal_block_non_default_delimiter(transformer):
    from lark.tree import Meta

    meta = Meta()
    start = Token("OUTER_LITERAL_START", "--ASCIIDOCTRINE_OUTER_LITERAL_START_5--")
    content = Token("OUTER_LITERAL_CONTENT", "literal here")
    result = transformer.outer_literal_block(meta, [start, content])
    assert result.delimiter == "....."
    assert result.inlines[0].value == "literal here"


def test_outer_passthrough_block_non_default_delimiter(transformer):
    from lark.tree import Meta

    meta = Meta()
    start = Token(
        "OUTER_PASSTHROUGH_START", "--ASCIIDOCTRINE_OUTER_PASSTHROUGH_START_5--"
    )
    content = Token("OUTER_PASSTHROUGH_CONTENT", "raw html")
    result = transformer.outer_passthrough_block(meta, [start, content])
    assert result.delimiter == "+++++"
    assert result.inlines[0].value == "raw html"


def test_outer_comment_block_non_default_delimiter(transformer):
    from lark.tree import Meta

    meta = Meta()
    start = Token("OUTER_COMMENT_START", "--ASCIIDOCTRINE_OUTER_COMMENT_START_5--")
    content = Token("OUTER_COMMENT_CONTENT", "a comment")
    result = transformer.outer_comment_block(meta, [start, content])
    assert result.delimiter == "/////"
    assert result.value == "a comment"


def test_outer_comment_block_default_delimiter(transformer):
    from lark.tree import Meta

    meta = Meta()
    content = Token("OUTER_COMMENT_CONTENT", "plain comment")
    result = transformer.outer_comment_block(meta, [content])
    assert result.delimiter == "////"


# ---------------------------------------------------------------------------
# shorthand_admonition
# ---------------------------------------------------------------------------


def test_shorthand_admonition(transformer):
    from lark.tree import Meta

    meta = Meta()
    adm_type = Token("ADMONITION_TYPE", "WARNING")
    content = [Text("Watch out")]
    result = transformer.shorthand_admonition(meta, [adm_type, content])
    assert result.variant == "warning"
    assert len(result.blocks) == 1
    assert isinstance(result.blocks[0], Paragraph)
    assert result.blocks[0].inlines[0].value == "Watch out"


def test_shorthand_admonition_default_note(transformer):
    """shorthand_admonition defaults to 'note' when no ADMONITION_TYPE token."""
    from lark.tree import Meta

    meta = Meta()
    content = [Text("FYI")]
    result = transformer.shorthand_admonition(meta, [content])
    assert result.variant == "note"


# ---------------------------------------------------------------------------
# admonition_4 / admonition_5 / admonition_6
# ---------------------------------------------------------------------------


def test_admonition_block_variants(transformer):
    from lark.tree import Meta

    meta = Meta()
    para = Paragraph(inlines=[Text("Admonition body")])

    # admonition_4
    start4 = Token("ADMONITION_START", "[NOTE]")
    delim4 = Token("ADMONITION_DELIM_4", "====")
    a4 = transformer.admonition_4(meta, [start4, para, delim4])
    assert a4.variant == "note"
    assert a4.delimiter == "===="
    assert len(a4.blocks) == 1

    # admonition_5
    start5 = Token("ADMONITION_START", "[TIP]")
    delim5 = Token("ADMONITION_DELIM_5", "=====")
    a5 = transformer.admonition_5(meta, [start5, para, delim5])
    assert a5.variant == "tip"

    # admonition_6
    start6 = Token("ADMONITION_START", "[CAUTION]")
    delim6 = Token("ADMONITION_DELIM_6", "======")
    a6 = transformer.admonition_6(meta, [start6, para, delim6])
    assert a6.variant == "caution"


# ---------------------------------------------------------------------------
# sidebar_4
# ---------------------------------------------------------------------------


def test_sidebar_4(transformer):
    from lark.tree import Meta

    meta = Meta()
    delim = Token("SIDEBAR_DELIM_4", "****")
    para = Paragraph(inlines=[Text("sidebar body")])
    result = transformer.sidebar_4(meta, [delim, para])
    assert result.delimiter == "****"
    assert len(result.blocks) == 1


# ---------------------------------------------------------------------------
# paragraph location consolidation
# ---------------------------------------------------------------------------


def test_paragraph_location_consolidation(transformer):
    """consecutive Text nodes with same attrs get merged; location is updated."""
    from lark.tree import Meta

    meta = Meta()
    # Build two text-content lists (simulating two lines)
    t1 = Text("Hello")
    t1.location = [{"line": 1, "col": 1}, {"line": 1, "col": 5}]
    t2 = Text(" world")
    t2.location = [{"line": 1, "col": 6}, {"line": 1, "col": 11}]
    # paragraph receives lists of nodes per line
    result = transformer.paragraph(meta, [[t1], [t2]])
    # Should have a newline Text(\n) inserted between lines and then consolidated
    assert isinstance(result, Paragraph)


# ---------------------------------------------------------------------------
# colist_item — whitespace token filtering
# ---------------------------------------------------------------------------


def test_colist_item_whitespace_filter(transformer):
    from lark.tree import Meta

    meta = Meta()
    num = Token("COLIST_NUM", "2")
    ws = Token("WHITESPACE", "  ")  # should be filtered out
    content = [Text("second callout")]
    result = transformer.colist_item(meta, [num, ws, content])
    assert result.value == 2
    assert result.principal[0].value == "second callout"


# ---------------------------------------------------------------------------
# dlist_item — BlockNode child branch
# ---------------------------------------------------------------------------


def test_dlist_item_with_block_node_child(transformer):
    from lark.tree import Meta

    from asciidoctrine.nodes import DescriptionListTerm

    meta = Meta()
    term = DescriptionListTerm(inlines=[Text("term")])
    body_para = Paragraph(inlines=[Text("definition body")])
    # Pass a BlockNode directly (not a list) as child
    result = transformer.dlist_item(meta, [term, body_para])
    assert len(result.terms) == 1
    assert len(result.blocks) == 1
    assert result.blocks[0].inlines[0].value == "definition body"


# ---------------------------------------------------------------------------
# table — multiplier expansion and rowspan/colspan grid
# ---------------------------------------------------------------------------


def test_table_multiplier_expansion(transformer):
    """A cell with multiplier=2 must be cloned into 2 cells in the table."""
    from lark.tree import Meta

    from asciidoctrine.nodes import TableCell, TableRow

    meta = Meta()
    cell = TableCell(blocks=[Paragraph(inlines=[Text("repeated")])])
    cell.colspan = 1
    cell.rowspan = 1
    cell.align = None
    cell.valign = None
    cell.style = None
    cell.multiplier = 2
    # Give both cells a location on the same line so num_cols is computed
    cell.location = [{"line": 1, "col": 1}, {"line": 1, "col": 10}]

    result = transformer.table(meta, [cell])
    # 2 cells on same line → num_cols=2, expanded into 1 row of 2 cells
    all_cells = [c for row in result.rows for c in row.cells]
    assert len(all_cells) == 2


def test_table_colspan_grid(transformer):
    """A cell spanning 2 cols must leave a 'spanned' marker in the grid."""
    from lark.tree import Meta

    from asciidoctrine.nodes import TableCell

    meta = Meta()

    def make_cell(line, col_end, colspan=1, rowspan=1):
        c = TableCell(blocks=[Paragraph(inlines=[Text("x")])])
        c.colspan = colspan
        c.rowspan = rowspan
        c.align = None
        c.valign = None
        c.style = None
        c.location = [{"line": line, "col": 1}, {"line": line, "col": col_end}]
        return c

    # Row 1: cell spanning 2 cols; Row 1 col 2 and 3 appear on same line → num_cols=2
    c1 = make_cell(1, 5, colspan=2)
    c2 = make_cell(2, 5)
    result = transformer.table(meta, [c1, c2])
    assert len(result.rows) >= 1


def test_table_empty_cells(transformer):
    from lark.tree import Meta

    meta = Meta()
    result = transformer.table(meta, [])
    assert result.rows == []


def test_table_num_cols_zero_guard(transformer):
    """When all cells have no location, num_cols must fall back to 1."""
    from lark.tree import Meta

    from asciidoctrine.nodes import TableCell

    meta = Meta()
    cell = TableCell(blocks=[])
    cell.colspan = 1
    cell.rowspan = 1
    cell.align = None
    cell.valign = None
    cell.style = None
    cell.location = None  # no location → first_line lookup returns 1, sum=0 → fallback
    result = transformer.table(meta, [cell])
    assert len(result.rows) == 1


# ---------------------------------------------------------------------------
# BlockTransformer._merge_consecutive_lists — location-update branches
# ---------------------------------------------------------------------------


def _loc(l1, c1, l2, c2):
    return [{"line": l1, "col": c1}, {"line": l2, "col": c2}]


def test_merge_consecutive_lists_ulist_updates_location(transformer):
    """Covers lines 59-60: end-location updated when merging adjacent unordered lists."""
    from asciidoctrine.nodes import List as ASTList, ListItem

    item1 = ListItem(marker="*", principal=[Text("A")])
    item2 = ListItem(marker="*", principal=[Text("B")])
    l1 = ASTList(variant="unordered", marker="*")
    l1.items.append(item1)
    l1.location = _loc(1, 1, 1, 5)
    l2 = ASTList(variant="unordered", marker="*")
    l2.items.append(item2)
    l2.location = _loc(2, 1, 2, 9)

    result = transformer._merge_consecutive_lists([l1, l2])
    assert len(result) == 1
    assert result[0].location[1] == {"line": 2, "col": 9}


def test_merge_consecutive_lists_dlist_updates_location(transformer):
    """Covers line 66: end-location updated when merging adjacent DescriptionLists."""
    from asciidoctrine.nodes import DescriptionList

    dl1 = DescriptionList()
    dl1.location = _loc(1, 1, 2, 10)
    dl2 = DescriptionList()
    dl2.location = _loc(4, 1, 5, 10)

    result = transformer._merge_consecutive_lists([dl1, dl2])
    assert len(result) == 1
    assert result[0].location[1] == {"line": 5, "col": 10}


def test_merge_consecutive_lists_callout_updates_location(transformer):
    """Covers line 72: end-location updated when merging adjacent CalloutLists."""
    from asciidoctrine.nodes import CalloutList

    cl1 = CalloutList()
    cl1.location = _loc(10, 1, 10, 5)
    cl2 = CalloutList()
    cl2.location = _loc(11, 1, 11, 5)

    result = transformer._merge_consecutive_lists([cl1, cl2])
    assert len(result) == 1
    assert result[0].location[1] == {"line": 11, "col": 5}


def test_nest_list_items_stack_pops_on_level_decrease(transformer):
    """Covers line 109: while-loop pops stack when nesting level drops."""
    from asciidoctrine.nodes import List as ASTList

    items = [
        {"level": 1, "item_type": "bullet", "marker": "*",
         "children": [Text("A")], "checked": None},
        {"level": 2, "item_type": "bullet", "marker": "**",
         "children": [Text("A.1")], "checked": None},
        {"level": 1, "item_type": "bullet", "marker": "*",
         "children": [Text("B")], "checked": None},
    ]
    result = transformer._nest_list_items(items)
    # Two top-level items; first has a nested child
    assert len(result) == 2
    assert len(result[0].blocks) == 1
    assert isinstance(result[0].blocks[0], ASTList)


# ---------------------------------------------------------------------------
# InlineTransformer.text_content — angle-bracket and backslash-escape paths
# ---------------------------------------------------------------------------

from asciidoctrine.transformers.inline_transformer import InlineTransformer


def _it():
    return InlineTransformer()


def test_text_content_plain_token():
    result = _it().text_content(None, [Token("TEXT", "hello")])
    assert len(result) == 1
    assert isinstance(result[0], Text)
    assert result[0].value == "hello"


def test_text_content_adjacent_tokens_merged():
    result = _it().text_content(None, [Token("TEXT", "foo"), Token("TEXT", "bar")])
    assert len(result) == 1
    assert result[0].value == "foobar"


def test_text_content_node_child_passthrough():
    node = Span(variant="strong", form="constrained", inlines=[Text("bold")])
    result = _it().text_content(None, [node])
    assert result[0] is node


def test_text_content_pending_attrs_applied_to_next_node():
    children = [{"role": "highlight"}, Token("TEXT", "marked")]
    result = _it().text_content(None, children)
    assert result[0].attributes.get("role") == "highlight"


def test_text_content_pending_attrs_no_following_node_emitted_as_text():
    """Trailing pending attrs with no subsequent node become a literal [attr=val] Text."""
    children = [{"role": "orphan"}]
    result = _it().text_content(None, children)
    assert len(result) == 1
    assert "[" in result[0].value


def test_text_content_bare_ref_escaped_with_backslash():
    """Backslash before a bare URL → Ref converted to plain Text of the target."""
    from asciidoctrine.nodes import Ref
    ref = Ref(variant="link", target="https://example.com")
    ref.attributes["role"] = "bare"
    # Text ending with backslash, then bare Ref
    children = [Token("TEXT", "Visit \\"), ref]
    result = _it().text_content(None, children)
    combined = "".join(n.value for n in result if isinstance(n, Text))
    assert "https://example.com" in combined
    assert not any(isinstance(n, Ref) for n in result)


def test_text_content_bare_ref_angle_brackets_stripped():
    """<URL> — angle brackets stripped when bare Ref surrounded by < and > tokens."""
    from asciidoctrine.nodes import Ref
    ref = Ref(variant="link", target="https://example.com")
    ref.attributes["role"] = "bare"
    # preceding text ends with '<', then bare Ref, then '>' token
    children = [Token("TEXT", "See <"), ref, Token("GT", ">")]
    result = _it().text_content(None, children)
    full_text = "".join(n.value for n in result if isinstance(n, Text))
    assert "<" not in full_text
    assert ">" not in full_text


def test_text_content_bare_ref_angle_bracket_next_is_text_node():
    """Next item after bare Ref is a Text node starting with '>' (lines 130-133, 144-149)."""
    from asciidoctrine.nodes import Ref
    ref = Ref(variant="link", target="https://example.com")
    ref.attributes["role"] = "bare"
    # Next child is a Text node starting with '>' instead of a '>' Token
    next_text = Text(">rest")
    children = [Token("TEXT", "See <"), ref, next_text]
    result = _it().text_content(None, children)
    full = "".join(n.value for n in result if isinstance(n, Text))
    # '<' stripped before ref, '>' stripped from start of next_text
    assert "<" not in full
    # "rest" should survive
    assert "rest" in full


def test_text_content_bare_ref_angle_bracket_next_text_only_gt():
    """Next Text node is exactly '>' — should be removed entirely (lines 147-149)."""
    from asciidoctrine.nodes import Ref
    ref = Ref(variant="link", target="https://example.com")
    ref.attributes["role"] = "bare"
    # Next item is Text(">"): stripping ">" leaves an empty string → node removed
    next_text = Text(">")
    children = [Token("TEXT", "Before <"), ref, next_text]
    result = _it().text_content(None, children)
    # The empty Text("") should be removed; no stray ">" in output
    full = "".join(n.value for n in result if isinstance(n, Text))
    assert ">" not in full
    assert "<" not in full


def test_text_content_backslash_only_preceding_text_popped():
    """Preceding text is exactly '\\' — after stripping it becomes empty and is popped (line 108)."""
    from asciidoctrine.nodes import Ref
    ref = Ref(variant="link", target="https://example.com")
    ref.attributes["role"] = "bare"
    # The ONLY content of the previous Text node is the backslash
    children = [Token("TEXT", "\\"), ref]
    result = _it().text_content(None, children)
    # The backslash Text should be popped; ref converted to plain text of target
    assert not any(n.value == "\\" for n in result if isinstance(n, Text))
    combined = "".join(n.value for n in result if isinstance(n, Text))
    assert "https://example.com" in combined


# ---------------------------------------------------------------------------
# inline_transformer L138 — nodes.pop() when preceding text is exactly "<"
# ---------------------------------------------------------------------------

def test_text_content_angle_bracket_only_preceding_text_popped():
    """Preceding text is exactly '<' — after stripping it becomes empty and is popped (line 138)."""
    from asciidoctrine.nodes import Ref
    ref = Ref(variant="link", target="https://example.com")
    ref.attributes["role"] = "bare"
    # The ONLY content of the previous Text node is "<"
    children = [Token("TEXT", "<"), ref, Token("GT", ">")]
    result = _it().text_content(None, children)
    # The "<" Text should be popped; no stray "<" in output
    full = "".join(n.value for n in result if isinstance(n, Text))
    assert "<" not in full


# ---------------------------------------------------------------------------
# BaseTransformer gaps — LocationDict.__init__ (L13-14) and Tree branch (L43-44)
# ---------------------------------------------------------------------------

def test_location_dict_init():
    """LocationDict.__init__ sets location to None (lines 13-14)."""
    from asciidoctrine.transformers.base_transformer import LocationDict
    d = LocationDict(a=1, b=2)
    assert d["a"] == 1
    assert d.location is None


def test_set_location_from_children_tree_branch(transformer):
    """_set_location_from_children handles lark.Tree children (lines 43-44)."""
    from lark import Tree
    from asciidoctrine.nodes import Paragraph, Text

    t = Token("TEXT", "hello")
    t.line = 5
    t.column = 3
    t.end_line = 5
    t.end_column = 8

    tree = Tree("some_rule", [t])
    node = Paragraph()
    transformer._set_location_from_children(node, [tree])
    assert node.location is not None
    assert node.location[0]["line"] == 5


# ---------------------------------------------------------------------------
# nodes.py — append() else-branch for typed list nodes (L448, L587, L631)
# ---------------------------------------------------------------------------

def test_callout_list_append_wrong_type_raises():
    """CalloutList.append with non-CalloutListItem falls to super() which raises AttributeError
    (BlockNode.append tries self.blocks but CalloutList never initialises it)."""
    import pytest
    from asciidoctrine.nodes import CalloutList, Paragraph
    cl = CalloutList()
    p = Paragraph()
    with pytest.raises(AttributeError):
        cl.append(p)


def test_list_append_wrong_type_raises():
    """List.append with non-ListItem falls to super().append which raises AttributeError."""
    import pytest
    from asciidoctrine.nodes import List as ASTList, Paragraph
    lst = ASTList(variant="unordered", marker="*")
    p = Paragraph()
    with pytest.raises(AttributeError):
        lst.append(p)


def test_description_list_append_wrong_type_raises():
    """DescriptionList.append with non-DescriptionListItem falls to super() which raises AttributeError."""
    import pytest
    from asciidoctrine.nodes import DescriptionList, Paragraph
    dl = DescriptionList()
    p = Paragraph()
    with pytest.raises(AttributeError):
        dl.append(p)
