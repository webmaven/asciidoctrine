import pytest
from asciidoctrine.lark_parser import parse_to_ast
from asciidoctrine.resolver import ASGResolver



pytestmark = pytest.mark.integration
def test_full_pipeline_with_locations():
    source = """= Title
:name: World

Hello {name}!
"""
    # 1. Parse
    ast = parse_to_ast(source)

    # 2. Resolve
    resolver = ASGResolver(ast)
    resolved = resolver.resolve(ast)

    # 3. Verify structure and locations
    assert resolved["name"] == "document"
    assert resolved["header"]["title"][0]["value"] == "Title"
    assert resolved["header"]["title"][0]["location"] == [
        {"line": 1, "col": 3},
        {"line": 1, "col": 7},
    ]

    # Body paragraph
    para = resolved["blocks"][0]
    assert para["name"] == "paragraph"
    assert para["inlines"][0]["value"] == "Hello World!"
    # "Hello World!" starts at 4:1 and ends at 4:13
    assert para["inlines"][0]["location"] == [
        {"line": 4, "col": 1},
        {"line": 4, "col": 13},
    ]
    assert para["location"] == [{"line": 4, "col": 1}, {"line": 4, "col": 13}]


def test_nested_list_integration():
    source = """* Level 1
** Level 2
* Back to 1
"""
    ast = parse_to_ast(source)
    resolver = ASGResolver(ast)
    resolved = resolver.resolve(ast)

    list_node = resolved["blocks"][0]
    assert len(list_node["items"]) == 2

    item1 = list_node["items"][0]
    assert item1["principal"][0]["value"] == "Level 1"
    assert len(item1["blocks"]) == 1
    assert item1["blocks"][0]["name"] == "list"
    assert item1["blocks"][0]["items"][0]["principal"][0]["value"] == "Level 2"

    item2 = list_node["items"][1]
    assert item2["principal"][0]["value"] == "Back to 1"


def test_resolver_filters_attributes_and_comments():
    """parse + resolve: attribute_entry nodes are consumed; ASG gains an 'attributes' block."""
    from asciidoctrine.lark_parser import parse_to_ast

    source = """:my-attr: my-value

This is a paragraph.
"""
    ast = parse_to_ast(source)

    ast_dict = ast.to_dict()
    ast_block_names = [b["name"] for b in ast_dict.get("blocks", [])]
    assert "attribute_entry" in ast_block_names

    resolver = ASGResolver(ast)
    asg = resolver.resolve(ast)

    asg_block_names = [b["name"] for b in asg.get("blocks", [])]
    assert "attribute_entry" not in asg_block_names
    assert "attributes" in asg_block_names
    assert "paragraph" in asg_block_names

    attr_block = [b for b in asg["blocks"] if b["name"] == "attributes"][0]
    assert "my-attr" in attr_block["attributes"]
    assert attr_block["attributes"]["my-attr"]["value"] == "my-value"
    assert "location" in attr_block["attributes"]["my-attr"]


def test_resolver_non_destructive():
    """Resolving an AST to ASG must not mutate the original AST."""
    from asciidoctrine.lark_parser import parse_to_ast

    source = ":my-attr: my-value\n\n[my-block-attribute=my-val]\nThis is a paragraph.\n"
    ast = parse_to_ast(source)

    ast_blocks_before = [b.name for b in ast.blocks]
    assert "attribute_entry" in ast_blocks_before

    resolver = ASGResolver(ast)
    asg = resolver.resolve(ast)
    assert asg.get("name") == "document"

    ast_blocks_after = [b.name for b in ast.blocks]
    assert "attribute_entry" in ast_blocks_after

    p_node = [b for b in ast.blocks if b.name == "paragraph"][0]
    assert p_node.attributes.get("my-block-attribute") == "my-val"
