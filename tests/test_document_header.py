from asciidoc_parser import parse_to_ast


def test_document_title():
    source = "= My Document Title\n\n"
    ast = parse_to_ast(source).to_dict()
    assert ast["name"] == "document"
    assert "header" in ast
    assert ast["header"]["title"][0]["value"] == "My Document Title"
    assert "blocks" not in ast or not ast["blocks"]


def test_document_title_with_author():
    source = """= My Document Title
John Doe

"""
    ast = parse_to_ast(source).to_dict()
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
    ast = parse_to_ast(source).to_dict()
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
    ast = parse_to_ast(source).to_dict()
    assert ast["name"] == "document"
    assert "header" in ast

    attributes = ast["attributes"]
    # In my resolved ASG it's simple strings
    # But wait, to_dict() returns rich objects if not resolved.
    # The unit test calls to_dict() directly on AST.
    # Header nodes in to_dict() return header metadata.
    # Let's check what Header.to_dict() does.
    # It returns header_data which has attributes if present.
    # Wait, I didn't include attributes in Header.to_dict()!
    # But document has them.

    assert attributes["my-attr"] == "my-value"
    assert attributes["another"] == "another-value"

    assert "blocks" in ast and len(ast["blocks"]) == 1
    assert ast["blocks"][0]["name"] == "paragraph"


def test_header_only_attributes():
    source = """:my-attr: my-value

This is a paragraph.
"""
    ast = parse_to_ast(source).to_dict()
    assert ast["name"] == "document"
    assert "header" not in ast
    assert ast["blocks"][0]["name"] == "attribute_entry"
    assert ast["blocks"][1]["name"] == "paragraph"


def test_no_header():
    source = "Just a paragraph.\n"
    ast = parse_to_ast(source).to_dict()
    assert ast["name"] == "document"
    assert "header" not in ast
    assert ast["blocks"][0]["name"] == "paragraph"


def test_header_followed_by_section():
    source = """= My Document Title

== Section 1
"""
    ast = parse_to_ast(source).to_dict()
    assert ast["name"] == "document"
    assert "header" in ast
    assert "blocks" in ast and len(ast["blocks"]) == 1
    assert ast["blocks"][0]["name"] == "section"
    assert ast["blocks"][0]["title"][0]["value"] == "Section 1"
