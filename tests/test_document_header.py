
import pytest
from asciidoc_parser import parse_to_ast

def test_document_title():
    source = "= My Document Title\n\n"
    ast = parse_to_ast(source)
    assert ast['type'] == 'document'
    assert 'header' in ast
    assert ast['header']['type'] == 'header'
    assert 'title' in ast['header']
    assert ast['header']['title']['children'][0]['text'] == 'My Document Title'
    assert 'children' not in ast or not ast['children']

def test_document_title_with_author():
    source = """= My Document Title
John Doe

"""
    ast = parse_to_ast(source)
    assert ast['type'] == 'document'
    assert 'header' in ast
    header = ast['header']
    assert header['type'] == 'header'
    assert header['title']['children'][0]['text'] == 'My Document Title'
    assert 'author' in header
    assert header['author']['children'][0]['text'] == 'John Doe'

def test_document_title_with_author_and_revision():
    source = """= My Document Title
John Doe
v1.0, 2023-01-01

"""
    ast = parse_to_ast(source)
    assert ast['type'] == 'document'
    assert 'header' in ast
    header = ast['header']
    assert header['type'] == 'header'
    assert header['title']['children'][0]['text'] == 'My Document Title'
    assert header['author']['children'][0]['text'] == 'John Doe'
    assert 'revision' in header
    assert header['revision']['children'][0]['text'] == 'v1.0, 2023-01-01'

def test_header_with_attributes():
    source = """= My Document Title
:my-attr: my-value
:another: another-value

This is a paragraph.
"""
    ast = parse_to_ast(source)
    assert ast['type'] == 'document'
    assert 'header' in ast
    header = ast['header']
    assert header['type'] == 'header'

    attributes = header['attributes']
    assert attributes['my-attr'][0]['text'] == 'my-value'
    assert attributes['another'][0]['text'] == 'another-value'

    assert 'children' in ast and len(ast['children']) == 1
    assert ast['children'][0]['type'] == 'paragraph'

def test_header_only_attributes():
    source = """:my-attr: my-value

This is a paragraph.
"""
    ast = parse_to_ast(source)
    assert ast['type'] == 'document'
    assert 'header' not in ast
    assert ast['children'][0]['type'] == 'attribute_entry'
    assert ast['children'][1]['type'] == 'paragraph'

def test_no_header():
    source = "Just a paragraph.\n"
    ast = parse_to_ast(source)
    assert ast['type'] == 'document'
    assert 'header' not in ast
    assert ast['children'][0]['type'] == 'paragraph'

def test_header_followed_by_section():
    source = """= My Document Title

== Section 1
"""
    ast = parse_to_ast(source)
    assert ast['type'] == 'document'
    assert 'header' in ast
    assert ast['header']['type'] == 'header'
    assert 'children' in ast and len(ast['children']) == 1
    assert ast['children'][0]['type'] == 'section'
    assert ast['children'][0]['title']['children'][0]['text'] == 'Section 1'
