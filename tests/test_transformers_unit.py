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
