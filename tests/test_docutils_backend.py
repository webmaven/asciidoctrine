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


def test_floating_title_and_break_conversion():
    # Floating title
    from docutils.utils import new_document

    from asciidoctrine.docutils_backend import DocutilsRenderer
    from asciidoctrine.nodes import FloatingTitle, Text, Title

    doc = new_document("<string>")
    renderer = DocutilsRenderer(doc)
    node = FloatingTitle(level=2, title=Title(inlines=[Text("Floating Title Text")]))
    renderer.visit(node)

    rubric = doc[0]
    assert isinstance(rubric, nodes.rubric)
    assert rubric.astext() == "Floating Title Text"
    assert "level-2" in rubric["classes"]

    # Line break
    source = "First line +\nSecond line"
    document = asciidoc_to_docutils(source)
    para = document[0]
    assert isinstance(para, nodes.paragraph)
    assert len(para.children) == 3  # Text, raw, Text
    assert isinstance(para.children[1], nodes.raw)
    assert para.children[1].astext() == "<br/>"


def test_special_inline_macros_conversion():
    source = (
        "Press kbd:[Ctrl+Alt+Del] or btn:[Save] or select menu:File[New > Project]."
    )
    document = asciidoc_to_docutils(source)
    para = document[0]
    assert isinstance(para, nodes.paragraph)

    inline_children = para.children
    kbd_node = next(
        c
        for c in inline_children
        if isinstance(c, nodes.inline) and "kbd" in c["classes"]
    )
    assert kbd_node.astext() == "Ctrl+Alt+Del"

    btn_node = next(
        c
        for c in inline_children
        if isinstance(c, nodes.inline) and "button" in c["classes"]
    )
    assert btn_node.astext() == "Save"

    menu_node = next(
        c
        for c in inline_children
        if isinstance(c, nodes.inline) and "menu" in c["classes"]
    )
    assert menu_node.astext() == "File > New > Project"


def test_callout_list_conversion():
    source = """
[source,python]
----
print("hello") # <1>
----
<1> Prints hello.
"""
    document = asciidoc_to_docutils(source)
    # listing block and callout list
    assert len(document) == 2
    clist = document[1]
    assert isinstance(clist, nodes.enumerated_list)
    assert "callout" in clist["classes"]
    item = clist[0]
    assert isinstance(item, nodes.list_item)
    assert "Prints hello." in item.astext()


def test_spans_subscript_superscript_conversion():
    source = "H ~2~ O and E = mc ^2^ and regular text."
    document = asciidoc_to_docutils(source)
    para = document[0]
    assert isinstance(para, nodes.paragraph)

    sub = next(c for c in para.children if isinstance(c, nodes.subscript))
    assert sub.astext() == "2"

    sup = next(c for c in para.children if isinstance(c, nodes.superscript))
    assert sup.astext() == "2"


def test_table_alignment_and_style_conversion():
    # Alignment and spans in tables
    source = """
[cols="3"]
|===
^.>s| Cell 1
<.<e| Cell 2
m| Cell 3
|===
"""
    document = asciidoc_to_docutils(source)
    table = document[0]
    assert isinstance(table, nodes.table)

    tgroup = table[0]
    tbody = tgroup[-1]
    row = tbody[0]

    cell1 = row[0]
    assert cell1["align"] == "center"
    assert cell1["valign"] == "bottom"
    assert isinstance(cell1[0][0], nodes.strong)  # style 's' wraps in strong

    cell2 = row[1]
    assert cell2["align"] == "left"
    assert cell2["valign"] == "top"
    assert isinstance(cell2[0][0], nodes.emphasis)  # style 'e' wraps in emphasis

    cell3 = row[2]
    assert isinstance(cell3[0][0], nodes.literal)  # style 'm' wraps in literal


def test_ref_xref_and_links_conversion():
    # Link
    source_link = "Go to link:https://google.com[Google]."
    doc_link = asciidoc_to_docutils(source_link)
    para_link = doc_link[0]
    ref = next(c for c in para_link.children if isinstance(c, nodes.reference))
    assert ref["refuri"] == "https://google.com"

    # Xref without extension
    source_xref1 = "See xref:another-doc[Other Doc]."
    doc_xref1 = asciidoc_to_docutils(source_xref1)
    para_xref1 = doc_xref1[0]
    ref_xref1 = next(c for c in para_xref1.children if isinstance(c, nodes.reference))
    assert ref_xref1["refuri"] == "another-doc.html"

    # Xref with .adoc extension
    source_xref2 = "See xref:sub/another-doc.adoc[Other]."
    doc_xref2 = asciidoc_to_docutils(source_xref2)
    para_xref2 = doc_xref2[0]
    ref_xref2 = next(c for c in para_xref2.children if isinstance(c, nodes.reference))
    assert ref_xref2["refuri"] == "sub/another-doc.html"

    # Referencing footnoteref with target that doesn't exist yet
    source_fn = "Reference footnoteref:[non-existent] first."
    doc_fn = asciidoc_to_docutils(source_fn)
    # This should auto-create a blank paragraph footnote body
    assert len(doc_fn) == 2
    fn_body = doc_fn[1]
    assert isinstance(fn_body, nodes.footnote)
    assert fn_body["ids"] == ["fn-non-existent"]


def test_passthrough_stem_and_media_conversion():
    # Stem
    source_stem = "An inline stem:[E = mc^2] math equation."
    doc_stem = asciidoc_to_docutils(source_stem)
    para_stem = doc_stem[0]
    math_node = next(c for c in para_stem.children if isinstance(c, nodes.math))
    assert math_node.astext() == "E = mc^2"
    assert "asciimath" in math_node["classes"]

    # Stem Block
    source_stem_block = "[stem]\n++++\nx^2 + y^2 = z^2\n++++"
    doc_stem_block = asciidoc_to_docutils(source_stem_block)
    math_block = doc_stem_block[0]
    assert isinstance(math_block, nodes.math_block)
    assert "x^2 + y^2 = z^2" in math_block.astext()

    # Image
    source_img = "image::logo.png[Alt Logo]"
    doc_img = asciidoc_to_docutils(source_img)
    img_node = doc_img[0]
    assert isinstance(img_node, nodes.image)
    assert img_node["uri"] == "logo.png"
    assert img_node["alt"] == "Alt Logo"

    # Audio & Video
    source_media = "audio::track.mp3[]\n\nvideo::clip.mp4[]"
    doc_media = asciidoc_to_docutils(source_media)
    audio_node = doc_media[0]
    video_node = doc_media[1]
    assert isinstance(audio_node, nodes.raw)
    assert "track.mp3" in audio_node.astext()
    assert isinstance(video_node, nodes.raw)
    assert "clip.mp4" in video_node.astext()

    # Passthrough
    source_pass = "++++\n<div id='raw'>passthrough</div>\n++++"
    doc_pass = asciidoc_to_docutils(source_pass)
    pass_node = doc_pass[0]
    assert isinstance(pass_node, nodes.raw)
    assert "passthrough" in pass_node.astext()


def test_sidebar_and_toc_conversion():
    source_sidebar = """
.Sidebar Title
****
This is a sidebar block.
****
"""
    doc_sidebar = asciidoc_to_docutils(source_sidebar)
    sidebar_node = doc_sidebar[0]
    assert isinstance(sidebar_node, nodes.sidebar)
    assert sidebar_node[0].astext() == "Sidebar Title"
    assert sidebar_node[1].astext() == "This is a sidebar block."

    # Toc macro
    source_toc = "toc::[]"
    doc_toc = asciidoc_to_docutils(source_toc)
    toc_node = doc_toc[0]
    assert isinstance(toc_node, nodes.topic)
    assert "contents" in toc_node["classes"]


def test_open_block_and_toctree_conversion():
    source_open = """
--
This is an open block paragraph.
--
"""
    doc_open = asciidoc_to_docutils(source_open)
    container_node = doc_open[0]
    assert isinstance(container_node, nodes.container)
    assert container_node[0].astext() == "This is an open block paragraph."

    # Sphinx toctree
    source_toctree = """
[style=toctree,maxdepth=2,caption="My Table of Contents"]
--
intro
installation
usage
--
"""
    doc_toctree = asciidoc_to_docutils(source_toctree)
    toctree_node = doc_toctree[0]
    from sphinx import addnodes

    assert isinstance(toctree_node, addnodes.toctree)
    assert toctree_node["maxdepth"] == 2
    assert toctree_node["caption"] == "My Table of Contents"
    assert "intro" in toctree_node["includefiles"]


def test_thematic_break_conversion():
    source = "Paragraph 1\n\n'''\n\nParagraph 2"
    document = asciidoc_to_docutils(source)
    assert len(document) == 3
    assert isinstance(document[1], nodes.transition)


def test_page_break_conversion():
    source = "Paragraph 1\n\n<<<\n\nParagraph 2"
    document = asciidoc_to_docutils(source)
    assert len(document) == 3
    assert isinstance(document[1], nodes.raw)
    assert document[1].astext() == "<!-- page break -->"


def test_asciidoc_to_docutils_fallbacks():
    # Test setting fallback when get_default_settings is not available
    # We patch docutils.frontend to emulate get_default_settings missing
    from unittest.mock import patch

    with patch("docutils.frontend.get_default_settings", side_effect=ImportError):
        # This will trigger the OptionParser fallback
        doc = asciidoc_to_docutils("Some paragraph")
        assert isinstance(doc, nodes.document)
        assert doc[0].astext() == "Some paragraph"


def test_docutils_backend_additional_coverage():
    import docutils.nodes as dnodes

    from asciidoctrine.docutils_backend import DocutilsRenderer
    from asciidoctrine.nodes import (
        Callout,
        DescriptionListTerm,
        Paragraph,
        Table,
        TableCell,
        TableRow,
        Text,
    )

    # 1. Section with custom id (Line 95)
    doc_id = asciidoc_to_docutils("[#custom-sec-id]\n== My Section")
    sec_node = doc_id[0]
    assert "custom-sec-id" in sec_node["ids"]

    # 2. Ordered list (Line 231)
    doc_ordered = asciidoc_to_docutils("1. First\n2. Second")
    ol_node = doc_ordered[0]
    assert isinstance(ol_node, dnodes.enumerated_list)

    # 3. ListItem and CalloutListItem blocks visitor (Line 200)
    from asciidoctrine.nodes import CalloutListItem, ListItem, Sidebar

    renderer = DocutilsRenderer(dnodes.document(None, None))
    li_node_ast = ListItem(
        marker="*",
        principal=[Text(value="Principal Text")],
        blocks=[Sidebar(blocks=[Paragraph(inlines=[Text(value="Nested block")])])],
    )
    renderer.visit(li_node_ast)
    li_node_docutils = renderer.document[0]
    assert len(li_node_docutils) == 2

    # Also test CalloutListItem to cover line 200
    renderer = DocutilsRenderer(dnodes.document(None, None))
    co_li_node_ast = CalloutListItem(
        number=1,
        principal=[Text(value="Callout Principal Text")],
        blocks=[Sidebar(blocks=[Paragraph(inlines=[Text(value="Nested block")])])],
    )
    renderer.visit(co_li_node_ast)
    co_li_node_docutils = renderer.document[0]
    assert len(co_li_node_docutils) == 2

    # 4. Visit Callout (Line 206-208)
    renderer = DocutilsRenderer(dnodes.document(None, None))
    callout_node = Callout(number=1)
    renderer.visit(callout_node)
    assert len(renderer.document) == 1
    assert "callout" in renderer.document[0]["classes"]

    # 5. Visit Table with max_cols = 0 -> 1 (Line 251)
    renderer = DocutilsRenderer(dnodes.document(None, None))
    table_node = Table(rows=[TableRow(cells=[])])
    renderer.visit(table_node)
    # Should not crash, creates colspec with max_cols = 1

    # 6. Visit TableCell with rowspan (Line 282)
    renderer = DocutilsRenderer(dnodes.document(None, None))
    cell_node = TableCell(blocks=[Paragraph(inlines=[Text(value="Cell")])])
    cell_node.rowspan = 3
    row_node = TableRow(cells=[cell_node])
    table_node2 = Table(rows=[row_node])
    renderer.visit(table_node2)
    # In docutils: table -> tgroup -> tbody -> row -> entry
    entry_node = renderer.document[0][0][1][0][0]
    assert entry_node["morerows"] == 2

    # 7. DescriptionListTerm without parent (Line 356)
    renderer = DocutilsRenderer(dnodes.document(None, None))
    term_node = DescriptionListTerm(inlines=[Text(value="Term")])
    renderer.visit(term_node)
    assert renderer.document[0].astext() == "Term"

    # 8. Visit Ref with absolute URL (Line 447)
    from asciidoctrine.nodes import Ref

    renderer = DocutilsRenderer(dnodes.document(None, None))
    ref_node_ast = Ref(target="https://google.com", variant="other")
    renderer.visit(ref_node_ast)
    ref_node_docutils = renderer.document[0]
    assert isinstance(ref_node_docutils, dnodes.reference)
    assert ref_node_docutils["refuri"] == "https://google.com"

    # 9. Visit Quote (Line 511-517)
    doc_quote = asciidoc_to_docutils(
        "[quote, Author, Title]\n____\nThis is a quote.\n____"
    )
    quote_node = doc_quote[0]
    assert isinstance(quote_node, dnodes.block_quote)

    # 10. Visit Verse (Line 521-528)
    doc_verse = asciidoc_to_docutils(
        "[verse, Author, Title]\n____\nThis is a verse.\n____"
    )
    verse_node = doc_verse[0]
    assert isinstance(verse_node, dnodes.block_quote)
    assert "verse" in verse_node["classes"]

    # 11. Visit Open with Sphinx ImportError (Lines 556-558)
    import sys

    sys.modules["sphinx"] = None
    try:
        doc_no_sphinx = asciidoc_to_docutils("[style=toctree]\n--\nintro\n--")
        assert isinstance(doc_no_sphinx[0], dnodes.container)
    finally:
        del sys.modules["sphinx"]

    # 12. Visit Toc with title (Line 574)
    from asciidoctrine.nodes import Toc

    renderer = DocutilsRenderer(dnodes.document(None, None))
    toc_node_ast = Toc()
    toc_node_ast.attributes["title"] = "Custom TOC Title"
    renderer.visit(toc_node_ast)
    toc_node_docutils = renderer.document[0]
    assert isinstance(toc_node_docutils, dnodes.topic)
    assert toc_node_docutils[0].astext() == "Custom TOC Title"


def test_checklist_conversion():
    source = """* [ ] Unchecked item
* [x] Checked item
"""
    document = asciidoc_to_docutils(source)
    blist = document[0]
    assert isinstance(blist, nodes.bullet_list)
    assert "checklist" in blist["classes"]
    assert "task-list" in blist["classes"]

    # First item (unchecked)
    item1 = blist[0]
    assert isinstance(item1, nodes.list_item)
    assert "task-list-item" in item1["classes"]
    para1 = item1[0]
    assert isinstance(para1, nodes.paragraph)
    assert para1[0].astext() == "\u2610 "
    assert "Unchecked item" in para1.astext()

    # Second item (checked)
    item2 = blist[1]
    assert isinstance(item2, nodes.list_item)
    assert "task-list-item" in item2["classes"]
    para2 = item2[0]
    assert isinstance(para2, nodes.paragraph)
    assert para2[0].astext() == "\u2611 "
    assert "Checked item" in para2.astext()


def test_floating_contentless_anchor_conversion():
    source = "This is [[my-target]] anchor."
    document = asciidoc_to_docutils(source)
    para = document[0]
    assert isinstance(para, nodes.paragraph)

    # Check that a target node is inserted instead of reference node
    target_node = para[1]
    assert isinstance(target_node, nodes.target)
    assert "my-target" in target_node["ids"]


def test_collapsible_block_conversion():
    source = """.Summary Title
[%collapsible]
====
This is collapsible.
====
"""
    document = asciidoc_to_docutils(source)
    container = document[0]
    assert isinstance(container, nodes.container)
    assert "collapsible" in container["classes"]
    assert isinstance(container[0], nodes.title)
    assert container[0].astext() == "Summary Title"
    assert isinstance(container[1], nodes.paragraph)
    assert container[1].astext() == "This is collapsible."


def test_quote_attribution_rendering():
    """quote attribution and citetitle must render as a trailing attribution paragraph."""
    import docutils.nodes as dnodes

    # 1. Both attribution and citetitle present
    doc = asciidoc_to_docutils(
        "[quote, Ralph Waldo Emerson, Self-Reliance]\n"
        "____\n"
        "To be yourself in a world that is constantly trying to make you something else.\n"
        "____"
    )
    bq = doc[0]
    assert isinstance(bq, dnodes.block_quote)
    # Last child should be the attribution paragraph
    attr_para = bq[-1]
    assert isinstance(attr_para, dnodes.paragraph)
    assert "attribution" in attr_para["classes"]
    attr_text = attr_para.astext()
    assert "Ralph Waldo Emerson" in attr_text
    assert "Self-Reliance" in attr_text

    # 2. Attribution only (no citetitle)
    doc2 = asciidoc_to_docutils(
        "[quote, Winston Churchill]\n"
        "____\n"
        "Success is not final.\n"
        "____"
    )
    bq2 = doc2[0]
    attr_para2 = bq2[-1]
    assert isinstance(attr_para2, dnodes.paragraph)
    assert "attribution" in attr_para2["classes"]
    assert "Winston Churchill" in attr_para2.astext()

    # 3. No attribution — no trailing attribution paragraph beyond the content
    doc3 = asciidoc_to_docutils(
        "[quote]\n"
        "____\n"
        "Anonymous quote.\n"
        "____"
    )
    bq3 = doc3[0]
    # Should contain only the content paragraph, no extra attribution node
    for child in bq3.children:
        if isinstance(child, dnodes.paragraph):
            assert "attribution" not in child.get("classes", [])


def test_verse_attribution_rendering():
    """verse attribution and citetitle must render as a trailing attribution paragraph."""
    import docutils.nodes as dnodes

    # 1. Both attribution and citetitle present
    doc = asciidoc_to_docutils(
        "[verse, Walt Whitman, Leaves of Grass]\n"
        "____\n"
        "I am large, I contain multitudes.\n"
        "____"
    )
    bq = doc[0]
    assert isinstance(bq, dnodes.block_quote)
    assert "verse" in bq["classes"]
    attr_para = bq[-1]
    assert isinstance(attr_para, dnodes.paragraph)
    assert "attribution" in attr_para["classes"]
    attr_text = attr_para.astext()
    assert "Walt Whitman" in attr_text
    assert "Leaves of Grass" in attr_text

    # 2. Attribution only
    doc2 = asciidoc_to_docutils(
        "[verse, Emily Dickinson]\n"
        "____\n"
        "Hope is the thing with feathers.\n"
        "____"
    )
    bq2 = doc2[0]
    attr_para2 = bq2[-1]
    assert isinstance(attr_para2, dnodes.paragraph)
    assert "attribution" in attr_para2["classes"]
    assert "Emily Dickinson" in attr_para2.astext()

    # 3. No attribution
    doc3 = asciidoc_to_docutils(
        "[verse]\n"
        "____\n"
        "Words without a name.\n"
        "____"
    )
    bq3 = doc3[0]
    for child in bq3.children:
        if isinstance(child, dnodes.paragraph):
            assert "attribution" not in child.get("classes", [])


def test_index_term_conversion():

    # 1. Macro variant
    source = "Some text indexterm:[primary, secondary, tertiary] rest of text."
    document = asciidoc_to_docutils(source)
    para = document[0]
    assert isinstance(para, nodes.paragraph)
    from sphinx import addnodes

    idx = para[1]
    assert isinstance(idx, addnodes.index)
    assert idx["entries"][0][1] == "primary, secondary, tertiary"

    # 2. Flow double variant (visible term)
    source2 = "See ((single index entry)) inside paragraph."
    document2 = asciidoc_to_docutils(source2)
    para2 = document2[0]
    # Check that nodes.index node is inserted, followed by the text inline
    idx2 = para2[1]
    assert isinstance(idx2, addnodes.index)
    assert idx2["entries"][0][1] == "single index entry"
    # The term should be outputted in-place as well
    assert "single index entry" in para2.astext()
