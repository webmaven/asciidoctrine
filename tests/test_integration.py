from asciidoc_parser.lark_parser import parse_to_ast
from asciidoc_parser.resolver import ASGResolver


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
