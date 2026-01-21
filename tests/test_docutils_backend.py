from docutils import nodes

from asciidoc_parser.docutils_backend import asciidoc_to_docutils


def test_basic_conversion():
    source = "== Hello\nTesting *bold* and _italic_.\n"
    document = asciidoc_to_docutils(source)

    assert isinstance(document, nodes.document)
    if len(document) == 0:
        print("\nDocument children:", document.children)

    # Check section
    section = document[0]
    assert isinstance(section, nodes.section)
    assert isinstance(section[0], nodes.title)
    assert section[0].astext() == "Hello"

    # Check paragraph
    para = section[1]
    assert isinstance(para, nodes.paragraph)
    assert "Testing " in para.astext()

    # Check inline nodes
    inline_nodes = para.children
    # Expected: [Text('Testing '), strong(Text('bold')), Text(' and '),
    # emphasis(Text('italic')), Text('.')]
    types = [type(c) for c in inline_nodes]
    assert nodes.strong in types
    assert nodes.emphasis in types


def test_list_conversion():
    source = "* Item 1\n* Item 2\n** Nested\n"
    document = asciidoc_to_docutils(source)
    blist = document[0]
    assert isinstance(blist, nodes.bullet_list)
    assert len(blist) == 2

    item2 = blist[1]
    assert isinstance(item2, nodes.list_item)
    # The new nested item will be in item2.blocks (which maps to item2[1] in docutils)
    assert "Item 2" in item2[0].astext()

    nested_list = item2[1]
    assert isinstance(nested_list, nodes.bullet_list)
    assert "Nested" in nested_list[0].astext()


def test_admonition_conversion():
    source = """
[NOTE]
====
This is a note.
====
"""
    document = asciidoc_to_docutils(source)
    note = document[0]
    assert isinstance(note, nodes.note)
    assert note[0].astext() == "This is a note."


def test_listing_conversion():
    source = """
[source,python]
----
print("hello")
----
"""
    document = asciidoc_to_docutils(source)
    listing = document[0]
    assert isinstance(listing, nodes.literal_block)
    assert 'print("hello")' in listing.astext()
    assert "python" in listing["classes"]
