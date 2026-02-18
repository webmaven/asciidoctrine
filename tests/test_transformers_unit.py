import pytest
from lark import Token

from asciidoctrine.nodes import Node, Text
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
