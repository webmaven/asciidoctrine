import pytest

from asciidoctrine.nodes import Document, Paragraph, Text
from asciidoctrine.resolver import ASGResolver

pytestmark = pytest.mark.unit


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



def test_resolver_block_attribute_cleaning_and_comment_removal():
    from asciidoctrine.nodes import Node, Paragraph, Text

    class MockComment(Node):
        def __init__(self):
            super().__init__()
            self.name = "comment"
            self.type = "block"

    doc = Document()
    doc.attributes = {}

    p_with_attrs = Paragraph(inlines=[Text("Some text")])
    p_with_attrs.attributes = {
        "style": "source",
        "1": "source",
        "positional": ["source"],
        "my-named-attr": "value",
    }

    p_with_only_positional = Paragraph(inlines=[Text("Other text")])
    p_with_only_positional.attributes = {
        "positional": ["some-style"],
        "style": "some-style",
    }

    comment_node = MockComment()

    doc.blocks.extend([p_with_attrs, p_with_only_positional, comment_node])

    resolver = ASGResolver(doc)
    asg = resolver.resolve(doc)

    # 1. Verify comment block is removed
    asg_block_names = [b["name"] for b in asg.get("blocks", [])]
    assert "comment" not in asg_block_names
    assert len(asg_block_names) == 2

    # 2. Verify p_with_attrs has had its positional/digit attributes removed, keeping my-named-attr and style
    cleaned_p = asg["blocks"][0]
    assert "attributes" in cleaned_p
    assert "my-named-attr" in cleaned_p["attributes"]
    assert "style" in cleaned_p["attributes"]
    assert "positional" not in cleaned_p["attributes"]
    assert "1" not in cleaned_p["attributes"]

    # 3. Verify p_with_only_positional keeps style in attributes
    empty_p = asg["blocks"][1]
    assert "attributes" in empty_p
    assert "style" in empty_p["attributes"]
    assert "positional" not in empty_p["attributes"]


