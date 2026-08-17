import pytest

from asciidoctrine import parse_to_ast

pytestmark = pytest.mark.integration


def _strip_locations(node):
    """Recursively strip 'location' from ASG dict."""
    if isinstance(node, dict):
        node.pop("location", None)
        for key, value in node.items():
            _strip_locations(value)
    elif isinstance(node, list):
        for item in node:
            _strip_locations(item)
    return node


def test_document_title():
    source = "= My Document Title\n\n"
    ast = _strip_locations(parse_to_ast(source).to_dict())
    assert ast["name"] == "document"
    assert "header" in ast
    assert ast["header"]["title"][0]["value"] == "My Document Title"
    assert "blocks" not in ast or not ast["blocks"]


def test_document_title_with_author():
    source = """= My Document Title
John Doe

"""
    ast = _strip_locations(parse_to_ast(source).to_dict())
    assert ast["name"] == "document"
    assert "header" in ast
    header = ast["header"]
    assert header["title"][0]["value"] == "My Document Title"
    assert "authors" in header
    assert header["authors"][0]["fullname"] == "John Doe"


def test_document_title_with_author_and_revision():
    source = """= My Document Title
John Doe
v1.0, 2023-01-01

"""
    ast = _strip_locations(parse_to_ast(source).to_dict())
    assert ast["name"] == "document"
    assert "header" in ast
    header = ast["header"]
    assert header["title"][0]["value"] == "My Document Title"
    assert header["authors"][0]["fullname"] == "John Doe"
    assert "revision" in header
    assert header["revision"]["value"] == "v1.0, 2023-01-01"


def test_header_with_attributes():
    source = """= My Document Title
:my-attr: my-value
:another: another-value

This is a paragraph.
"""
    ast = _strip_locations(parse_to_ast(source).to_dict())
    assert ast["name"] == "document"
    assert "header" in ast

    attributes = ast["attributes"]
    assert attributes["my-attr"] == "my-value"
    assert attributes["another"] == "another-value"

    assert "blocks" in ast and len(ast["blocks"]) == 1
    assert ast["blocks"][0]["name"] == "paragraph"


def test_header_only_attributes():
    source = """:my-attr: my-value

This is a paragraph.
"""
    ast = _strip_locations(parse_to_ast(source).to_dict())
    assert ast["name"] == "document"
    assert "header" not in ast
    assert ast["blocks"][0]["name"] == "attribute_entry"
    assert ast["blocks"][1]["name"] == "paragraph"


def test_no_header():
    source = "Just a paragraph.\n"
    ast = _strip_locations(parse_to_ast(source).to_dict())
    assert ast["name"] == "document"
    assert "header" not in ast
    assert ast["blocks"][0]["name"] == "paragraph"


def test_header_followed_by_section():
    source = """= My Document Title

== Section 1
"""
    ast = _strip_locations(parse_to_ast(source).to_dict())
    assert ast["name"] == "document"
    assert "header" in ast
    assert "blocks" in ast and len(ast["blocks"]) == 1
    assert ast["blocks"][0]["name"] == "section"
    # Concatenate all title inlines for verification
    actual_title = "".join([n["value"] for n in ast["blocks"][0]["title"]])
    assert actual_title == "Section 1"
