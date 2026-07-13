import pytest
from lark import Token

from asciidoctrine.nodes import Document, Node, NodeTransformer, Paragraph, Span, Text
from asciidoctrine.transformers.block_transformer import BlockTransformer


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
