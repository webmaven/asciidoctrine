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


if __name__ == "__main__":
    test_resolver()
