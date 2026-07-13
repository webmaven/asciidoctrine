from docutils import nodes

from asciidoctrine.docutils_backend import asciidoc_to_docutils


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


def test_nested_dlist_conversion():
    source = """
Operating Systems::
  Linux:::
    Fedora:: Desktop
"""
    document = asciidoc_to_docutils(source)
    # The root should be a definition_list in docutils
    dlist = document[0]
    assert isinstance(dlist, nodes.definition_list)

    # Check "Operating Systems" term and definition
    item = dlist[0]
    assert isinstance(item, nodes.definition_list_item)
    assert item[0].astext() == "Operating Systems"

    # Check nested definition_list for "Linux"
    nested_dlist = item[1][0]
    assert isinstance(nested_dlist, nodes.definition_list)
    nested_item = nested_dlist[0]
    assert nested_item[0].astext() == "Linux"

    # Check doubly-nested definition_list for "Fedora"
    doubly_nested = nested_item[1][0]
    assert isinstance(doubly_nested, nodes.definition_list)
    final_item = doubly_nested[0]
    assert final_item[0].astext() == "Fedora"
    assert final_item[1].astext() == "Desktop"


def test_table_rendering_conversion():
    source = """
[cols="1,1"]
|===
| cell 1 | cell 2
2+^s| merged bold
|===
"""
    document = asciidoc_to_docutils(source)
    table = document[0]
    assert isinstance(table, nodes.table)

    # Check colspecs and tgroup
    tgroup = table[0]
    assert isinstance(tgroup, nodes.tgroup)

    tbody = tgroup[-1]
    assert isinstance(tbody, nodes.tbody)
    assert len(tbody) == 2

    # Row 1
    row1 = tbody[0]
    assert len(row1) == 2
    assert row1[0].astext() == "cell 1"
    assert row1[1].astext() == "cell 2"

    # Row 2 (merged cell)
    row2 = tbody[1]
    assert len(row2) == 1
    merged_cell = row2[0]
    assert isinstance(merged_cell, nodes.entry)
    assert merged_cell.get("morecols") == 1
    # Check that text is wrapped in strong node because of style 's'
    assert isinstance(merged_cell[0][0], nodes.strong)
    assert merged_cell.astext() == "merged bold"


def test_document_title_wrapping():
    source = """= Document Title

Preamble text.

== Section 1
Section 1 content.
"""
    document = asciidoc_to_docutils(source)
    assert isinstance(document, nodes.document)

    # There should be exactly one top-level node: the root section
    assert len(document) == 1
    root_section = document[0]
    assert isinstance(root_section, nodes.section)

    # First child of root section is the title
    assert isinstance(root_section[0], nodes.title)
    assert root_section[0].astext() == "Document Title"

    # Second child is the preamble paragraph
    assert isinstance(root_section[1], nodes.paragraph)
    assert root_section[1].astext() == "Preamble text."

    # Third child is Section 1
    sec1 = root_section[2]
    assert isinstance(sec1, nodes.section)
    assert sec1[0].astext() == "Section 1"
    assert sec1[1].astext() == "Section 1 content."


def test_footnote_rendering_conversion():
    # 1. Test auto-numbered footnote
    source_auto = "This is a paragraph with footnote:[Auto-numbered footnote content]."
    doc_auto = asciidoc_to_docutils(source_auto)

    # The paragraph should have a footnote reference
    para = doc_auto[0]
    assert isinstance(para, nodes.paragraph)
    assert len(para.children) == 3  # Text, footnote_reference, Text (trailing period)
    assert isinstance(para.children[1], nodes.footnote_reference)
    ref = para.children[1]
    assert ref["refid"] == "fn-1"
    assert ref.astext() == "1"

    # The footnote body should be appended to the document root
    assert len(doc_auto) == 2  # Paragraph and the footnote body
    fn_body = doc_auto[1]
    assert isinstance(fn_body, nodes.footnote)
    assert fn_body["ids"] == ["fn-1"]
    assert isinstance(fn_body[0], nodes.label)
    assert fn_body[0].astext() == "1"
    assert isinstance(fn_body[1], nodes.paragraph)
    assert fn_body[1].astext() == "Auto-numbered footnote content"

    # 2. Test named footnoteref definition and subsequent reference
    source_named = "Define here footnoteref:[my-custom-id, Named footnote content], and reference again footnoteref:[my-custom-id]."
    doc_named = asciidoc_to_docutils(source_named)

    para_named = doc_named[0]
    assert isinstance(para_named, nodes.paragraph)
    # Inline children: [Text, footnote_ref1, Text, footnote_ref2, Text (trailing period)]
    assert len(para_named.children) == 5

    ref1 = para_named.children[1]
    assert isinstance(ref1, nodes.footnote_reference)
    assert ref1["refid"] == "fn-my-custom-id"
    assert ref1.astext() == "1"

    ref2 = para_named.children[3]
    assert isinstance(ref2, nodes.footnote_reference)
    assert ref2["refid"] == "fn-my-custom-id"
    assert ref2.astext() == "1"

    # Footnote body appended to document root
    assert len(doc_named) == 2
    fn_body_named = doc_named[1]
    assert isinstance(fn_body_named, nodes.footnote)
    assert fn_body_named["ids"] == ["fn-my-custom-id"]
    assert fn_body_named[0].astext() == "1"
    assert fn_body_named[1].astext() == "Named footnote content"
