import pytest
from asciidoctrine.lark_parser import parse_to_ast
from asciidoctrine.nodes import Listing, Literal, Text



pytestmark = pytest.mark.integration
def test_listing_block_coordinates_without_attributes():
    source = '----\nimport os\nprint("hello")\n----\n'
    ast = parse_to_ast(source)
    node = ast.blocks[0]

    assert isinstance(node, Listing)
    # The block starts at line 1 (the first delimiter) and ends at line 4 (the second delimiter)
    assert node.location is not None
    assert node.location[0]["line"] == 1
    assert node.location[1]["line"] == 4

    # The text node inside should span line 2 to line 3
    text_node = node.inlines[0]
    assert isinstance(text_node, Text)
    assert text_node.location is not None
    assert text_node.location[0]["line"] == 2
    assert text_node.location[1]["line"] == 3


def test_listing_block_coordinates_with_attributes():
    source = '[source,python]\n----\nimport os\nprint("hello")\n----\n'
    ast = parse_to_ast(source)
    node = ast.blocks[0]

    assert isinstance(node, Listing)
    # The block includes block_metadata, so it starts at line 1 (attributes) and ends at line 5 (second delimiter)
    assert node.location is not None
    assert node.location[0]["line"] == 1
    assert node.location[1]["line"] == 5

    # The text node inside should span line 3 to line 4
    text_node = node.inlines[0]
    assert isinstance(text_node, Text)
    assert text_node.location is not None
    assert text_node.location[0]["line"] == 3
    assert text_node.location[1]["line"] == 4


def test_literal_block_coordinates():
    source = "....\nliteral content\n....\n"
    ast = parse_to_ast(source)
    node = ast.blocks[0]

    assert isinstance(node, Literal)
    # The literal block starts at line 1 and ends at line 3
    assert node.location is not None
    assert node.location[0]["line"] == 1
    assert node.location[1]["line"] == 3

    # The text node inside is on line 2
    text_node = node.inlines[0]
    assert isinstance(text_node, Text)
    assert text_node.location is not None
    assert text_node.location[0]["line"] == 2
    assert text_node.location[1]["line"] == 2


def test_indented_literal_block_coordinates():
    source = "  indented literal\n"
    ast = parse_to_ast(source)
    node = ast.blocks[0]

    assert isinstance(node, Literal)
    # The indented literal is on line 1
    assert node.location is not None
    assert node.location[0]["line"] == 1
    assert node.location[1]["line"] == 1

    # The text node inside is also on line 1
    text_node = node.inlines[0]
    assert isinstance(text_node, Text)
    assert text_node.location is not None
    assert text_node.location[0]["line"] == 1
    assert text_node.location[1]["line"] == 1
