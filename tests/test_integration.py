import pytest
from asciidoctrine.lark_parser import parse_to_ast
from asciidoctrine.resolver import ASGResolver


pytestmark = pytest.mark.integration


def test_full_pipeline_with_locations():
    """End-to-end: attribute substitution + location coordinates survive parse→resolve."""
    source = """= Title
:name: World

Hello {name}!
"""
    ast = parse_to_ast(source)
    resolver = ASGResolver(ast)
    resolved = resolver.resolve(ast)

    assert resolved["name"] == "document"
    assert resolved["header"]["title"][0]["value"] == "Title"
    assert resolved["header"]["title"][0]["location"] == [
        {"line": 1, "col": 3},
        {"line": 1, "col": 7},
    ]

    para = resolved["blocks"][0]
    assert para["name"] == "paragraph"
    assert para["inlines"][0]["value"] == "Hello World!"
    assert para["inlines"][0]["location"] == [
        {"line": 4, "col": 1},
        {"line": 4, "col": 13},
    ]
    assert para["location"] == [{"line": 4, "col": 1}, {"line": 4, "col": 13}]


def test_resolver_non_destructive():
    """Resolving an AST to ASG must not mutate the original AST."""
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
