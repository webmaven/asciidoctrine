from asciidoctrine.nodes import Document, Paragraph, Text
from asciidoctrine.resolver import ASGResolver


def test_resolver():
    doc = Document()
    doc.attributes = {"name": "World"}

    p = Paragraph(inlines=[Text("Hello {name}!")])
    doc.blocks.append(p)

    resolver = ASGResolver(doc)
    resolved = resolver.resolve(doc)

    expected_text = "Hello World!"
    actual_text = resolved["blocks"][0]["inlines"][0]["value"]

    print(f"Actual text: {actual_text}")
    assert actual_text == expected_text
    print("Test passed!")


def test_resolver_filters_attributes_and_comments():
    from asciidoctrine.lark_parser import parse_to_ast
    
    source = """:my-attr: my-value

This is a paragraph.
"""
    ast = parse_to_ast(source)
    
    # 1. Verify attribute_entry is present in AST blocks list
    ast_dict = ast.to_dict()
    ast_block_names = [b["name"] for b in ast_dict.get("blocks", [])]
    assert "attribute_entry" in ast_block_names
    
    # 2. Resolve to ASG and verify attribute_entry is NOT present, but 'attributes' block IS present
    resolver = ASGResolver(ast)
    asg = resolver.resolve(ast)
    
    asg_block_names = [b["name"] for b in asg.get("blocks", [])]
    assert "attribute_entry" not in asg_block_names
    assert "attributes" in asg_block_names
    assert "paragraph" in asg_block_names
    
    # 3. Verify the details of the 'attributes' block
    attr_block = [b for b in asg["blocks"] if b["name"] == "attributes"][0]
    assert "my-attr" in attr_block["attributes"]
    assert attr_block["attributes"]["my-attr"]["value"] == "my-value"
    assert "location" in attr_block["attributes"]["my-attr"]



if __name__ == "__main__":
    test_resolver()
    test_resolver_filters_attributes_and_comments()

