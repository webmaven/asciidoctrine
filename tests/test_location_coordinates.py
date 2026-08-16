"""
Integration tests for AST location coordinate tracking.

Each LOCATION_CASES entry verifies the start/end line of a verbatim block
and the text node it contains.
"""

import pytest

from asciidoctrine.lark_parser import parse_to_ast
from asciidoctrine.nodes import Listing, Literal

pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# (id, source, node_type, block_start, block_end, text_start, text_end)
# ---------------------------------------------------------------------------
LOCATION_CASES = [
    (
        "listing_no_attributes",
        '----\nimport os\nprint("hello")\n----\n',
        Listing,
        1, 4,   # block delimiter lines
        2, 3,   # content lines
    ),
    (
        "listing_with_attributes",
        '[source,python]\n----\nimport os\nprint("hello")\n----\n',
        Listing,
        1, 5,   # attribute line counts as block start
        3, 4,
    ),
    (
        "literal_delimited",
        "....\nliteral content\n....\n",
        Literal,
        1, 3,
        2, 2,
    ),
    (
        "literal_indented",
        "  indented literal\n",
        Literal,
        1, 1,
        1, 1,
    ),
]


@pytest.mark.parametrize(
    "source,node_type,block_start,block_end,text_start,text_end",
    [(s, t, bs, be, ts, te) for _, s, t, bs, be, ts, te in LOCATION_CASES],
    ids=[id_ for id_, *_ in LOCATION_CASES],
)
def test_verbatim_block_coordinates(
    source, node_type, block_start, block_end, text_start, text_end
):
    ast = parse_to_ast(source)
    node = ast.blocks[0]

    assert isinstance(node, node_type)
    assert node.location is not None
    assert node.location[0]["line"] == block_start
    assert node.location[1]["line"] == block_end

    text_node = node.inlines[0]
    assert text_node.location is not None
    assert text_node.location[0]["line"] == text_start
    assert text_node.location[1]["line"] == text_end
