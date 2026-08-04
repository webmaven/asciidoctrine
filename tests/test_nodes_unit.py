"""
Unit tests for AST Node classes in nodes.py.
"""

import unittest

from asciidoctrine.nodes import (
    Admonition,
    Audio,
    Author,
    BlockNode,
    Break,
    Button,
    Callout,
    CalloutList,
    CalloutListItem,
    Collapsible,
    DescriptionList,
    DescriptionListItem,
    DescriptionListTerm,
    Docinfo,
    Document,
    Example,
    FloatingTitle,
    Header,
    Image,
    IndexTerm,
    InlineNode,
    InlineStem,
    Kbd,
    List,
    Listing,
    ListItem,
    Literal,
    Menu,
    Node,
    Open,
    PageBreak,
    Paragraph,
    Passthrough,
    Quote,
    Ref,
    Revision,
    Section,
    Sidebar,
    Span,
    Stem,
    Table,
    TableCell,
    TableRow,
    Text,
    ThematicBreak,
    Title,
    Verse,
    Video,
)


class TestNodesUnit(unittest.TestCase):
    def test_base_node_append_and_collections(self):
        node = Node()
        self.assertEqual(node.name, "unknown")
        self.assertEqual(node.type, "block")
        self.assertEqual(node.get_child_collections(), {})

        child = Node()
        node.append(child)
        self.assertEqual(node.get_child_collections(), {"children": [child]})

    def test_base_node_walk(self):
        root = Node()
        child1 = Node()
        child2 = Node()
        root.append(child1)
        child1.append(child2)

        walked = list(root.walk())
        self.assertEqual(walked, [root, child1, child2])

    def test_inline_node_append(self):
        # InlineNode has custom append that updates self.inlines
        class DummyInline(InlineNode):
            def __init__(self):
                super().__init__()
                self.inlines = []

            def get_child_collections(self):
                return {"inlines": self.inlines}

        dummy = DummyInline()
        child = Node()
        dummy.append(child)
        self.assertEqual(dummy.inlines, [child])

    def test_block_node_append(self):
        # BlockNode has custom append that updates self.blocks
        class DummyBlock(BlockNode):
            def __init__(self):
                super().__init__()
                self.blocks = []

            def get_child_collections(self):
                return {"blocks": self.blocks}

        dummy = DummyBlock()
        child = Node()
        dummy.append(child)
        self.assertEqual(dummy.blocks, [child])

    def test_document_node(self):
        doc = Document()
        self.assertEqual(doc.name, "document")
        self.assertEqual(doc.type, "block")

        # Test block append
        block = Paragraph()
        doc.append(block)
        self.assertEqual(doc.blocks, [block])

        # Test dict serialization
        doc.attributes = {"foo": "bar"}
        doc.header = Header(title=Title([Text("Doc Title")]))
        doc_dict = doc.to_dict()
        self.assertEqual(doc_dict["name"], "document")
        self.assertEqual(doc_dict["attributes"], {"foo": "bar"})
        self.assertIn("header", doc_dict)

    def test_title_and_list_serialization(self):
        title = Title([Text("Hello"), Text(" World")])
        self.assertEqual(title.name, "title")
        self.assertEqual(title.get_child_collections(), {"inlines": title.inlines})
        self.assertEqual(
            title.to_list(),
            [
                {"name": "text", "type": "string", "value": "Hello"},
                {"name": "text", "type": "string", "value": " World"},
            ],
        )

    def test_author_and_revision(self):
        author = Author([Text("John Doe")])
        self.assertEqual(author.name, "author")
        self.assertEqual(author.get_child_collections(), {"inlines": author.inlines})

        rev = Revision([Text("v1.0")])
        self.assertEqual(rev.name, "revision")
        self.assertEqual(rev.get_child_collections(), {"inlines": rev.inlines})
        rev.append(Text(" extra"))
        self.assertEqual(len(rev.inlines), 2)

    def test_floating_title(self):
        title = Title([Text("Discrete Title")])
        ft = FloatingTitle(level=2, title=title)
        self.assertEqual(ft.name, "floatingTitle")
        self.assertEqual(ft.level, 2)
        self.assertEqual(ft.get_child_collections(), {"inlines": title.inlines})

        ft_no_title = FloatingTitle(level=3, title=None)
        self.assertEqual(ft_no_title.get_child_collections(), {})

    def test_header_serialization(self):
        title = Title([Text("My Title")])
        author = Author([Text("Jane")])
        revision = Revision([Text("1.0")])
        header = Header(
            title=title, authors=[author], revision=revision, attributes={"key": "val"}
        )

        self.assertEqual(header.name, "header")
        header_dict = header.to_dict()
        self.assertEqual(
            header_dict["title"],
            [{"name": "text", "type": "string", "value": "My Title"}],
        )
        self.assertEqual(header_dict["authors"], [{"fullname": "Jane"}])
        self.assertEqual(
            header_dict["revision"],
            {"name": "revision", "type": "block", "value": "1.0"},
        )
        # _should_serialize_attributes is False on Header by default
        self.assertNotIn("attributes", header_dict)

    def test_docinfo_node_serialization(self):
        docinfo = Docinfo(head_content="<meta>", footer_content="<footer>")
        self.assertEqual(docinfo.head_content, "<meta>")
        self.assertEqual(docinfo.footer_content, "<footer>")

        doc_dict = docinfo.to_dict()
        self.assertEqual(doc_dict["name"], "docinfo")
        self.assertEqual(doc_dict["type"], "metadata")
        self.assertEqual(doc_dict["head_content"], "<meta>")
        self.assertEqual(doc_dict["footer_content"], "<footer>")

        doc = Document()
        doc.docinfo = docinfo
        serialized_doc = doc.to_dict()
        self.assertIn("docinfo", serialized_doc)
        self.assertEqual(serialized_doc["docinfo"]["head_content"], "<meta>")
        self.assertEqual(serialized_doc["docinfo"]["footer_content"], "<footer>")

        hdr = Header(title=Title([Text("Header Title")]), docinfo=docinfo)
        self.assertEqual(hdr.docinfo, docinfo)
        serialized_hdr = hdr.to_dict()
        self.assertIn("docinfo", serialized_hdr)
        self.assertEqual(serialized_hdr["docinfo"]["head_content"], "<meta>")
        self.assertEqual(serialized_hdr["docinfo"]["footer_content"], "<footer>")

    def test_section_node(self):
        title = Title([Text("Sect1")])
        sect = Section(level=1, title=title)
        self.assertEqual(sect.name, "section")
        self.assertEqual(sect.level, 1)
        self.assertEqual(sect.get_child_collections(), {"blocks": sect.blocks})

        child_sect = Section(level=2, title=Title([Text("Sect2")]))
        sect.append(child_sect)
        self.assertEqual(sect.blocks, [child_sect])

    def test_paragraph_node(self):
        p = Paragraph([Text("Para text")])
        self.assertEqual(p.name, "paragraph")
        self.assertEqual(p.get_child_collections(), {"inlines": p.inlines})
        p.append(Text(" suffix"))
        self.assertEqual(len(p.inlines), 2)

    def test_break_node(self):
        br = Break()
        self.assertEqual(br.name, "break")
        self.assertEqual(br.type, "inline")

    def test_kbd_and_button_and_menu(self):
        kbd = Kbd(["Ctrl", "S"])
        self.assertEqual(kbd.name, "kbd")
        self.assertEqual(kbd.value, ["Ctrl", "S"])

        btn = Button("Save")
        self.assertEqual(btn.name, "button")
        self.assertEqual(btn.value, "Save")

        menu = Menu("File", ["New", "Project"])
        self.assertEqual(menu.name, "menu")
        self.assertEqual(menu.menu, "File")
        self.assertEqual(menu.items, ["New", "Project"])
        self.assertEqual(menu.to_dict()["items"], ["New", "Project"])

    def test_callouts_and_stem(self):
        co = Callout(5)
        self.assertEqual(co.name, "callout")
        self.assertEqual(co.value, 5)

        stem = InlineStem("latexmath", "x^2")
        self.assertEqual(stem.name, "stem")
        self.assertEqual(stem.variant, "latexmath")
        self.assertEqual(stem.value, "x^2")

    def test_callout_list_and_item(self):
        cli = CalloutListItem(number=1, blocks=[Paragraph([Text("Note 1")])])
        self.assertEqual(cli.name, "calloutListItem")
        self.assertEqual(
            cli.get_child_collections(), {"principal": [], "blocks": cli.blocks}
        )

        cl = CalloutList([cli])
        self.assertEqual(cl.name, "calloutList")
        self.assertEqual(cl.get_child_collections(), {"items": cl.items})
        cl.append(CalloutListItem(number=2))
        self.assertEqual(len(cl.items), 2)

    def test_span_node(self):
        span = Span(variant="strong", form="constrained", inlines=[Text("hello")])
        self.assertEqual(span.name, "span")
        self.assertEqual(span.variant, "strong")
        self.assertEqual(span.form, "constrained")
        self.assertEqual(span.get_child_collections(), {"inlines": span.inlines})

    def test_ref_node(self):
        ref = Ref(
            variant="link", target="http://example.com", inlines=[Text("link label")]
        )
        self.assertEqual(ref.name, "ref")
        self.assertEqual(ref.variant, "link")
        self.assertEqual(ref.target, "http://example.com")
        self.assertEqual(ref.get_child_collections(), {"inlines": ref.inlines})

    def test_image_audio_video(self):
        img = Image(target="img.png", alt="alt txt", form="macro", type="block")
        self.assertEqual(img.name, "image")
        self.assertEqual(img.type, "block")
        self.assertEqual(img.target, "img.png")
        self.assertEqual(img.form, "macro")
        self.assertEqual(img.attributes, {"alt": "alt txt"})

        audio = Audio(target="sound.mp3")
        self.assertEqual(audio.name, "audio")
        self.assertEqual(audio.target, "sound.mp3")

        video = Video(target="movie.mp4")
        self.assertEqual(video.name, "video")
        self.assertEqual(video.target, "movie.mp4")

    def test_list_and_list_item(self):
        li = ListItem(marker="*", principal=[Text("Item 1")])
        self.assertEqual(li.name, "listItem")
        self.assertEqual(
            li.get_child_collections(), {"principal": li.principal, "blocks": li.blocks}
        )
        li.append(Paragraph([Text("nested block")]))
        self.assertEqual(len(li.blocks), 1)

        lst = List(variant="unordered", marker="*", items=[li])
        self.assertEqual(lst.name, "list")
        self.assertEqual(lst.get_child_collections(), {"items": lst.items})
        lst.append(ListItem(marker="*"))
        self.assertEqual(len(lst.items), 2)

    def test_description_list(self):
        term = DescriptionListTerm(inlines=[Text("Term 1")])
        self.assertEqual(term.name, "descriptionListTerm")
        self.assertEqual(term.get_child_collections(), {"inlines": term.inlines})

        item = DescriptionListItem(terms=[term], blocks=[Paragraph([Text("Desc 1")])])
        self.assertEqual(item.name, "descriptionListItem")
        self.assertEqual(
            item.get_child_collections(), {"terms": item.terms, "blocks": item.blocks}
        )
        item.append(Paragraph([Text("Extra block")]))
        self.assertEqual(len(item.blocks), 2)

        dl = DescriptionList(items=[item])
        self.assertEqual(dl.name, "descriptionList")
        self.assertEqual(dl.get_child_collections(), {"items": dl.items})
        dl.append(item)
        self.assertEqual(len(dl.items), 2)

    def test_verbatim_block_mixin_and_listing(self):
        listing = Listing(
            inlines=[
                Text("code line // <.>\n"),
                Text("other line // <1>\n"),
                Text("html line <!-- . -->\n"),
            ]
        )
        self.assertEqual(listing.name, "listing")
        self.assertEqual(listing.form, "delimited")
        self.assertEqual(listing.get_child_collections(), {"inlines": listing.inlines})

        listing.append(Text("extra line"))
        self.assertEqual(
            listing.code,
            "code line // <.>\nother line // <1>\nhtml line <!-- . -->\nextra line",
        )

        # Test properties (id, language, style, listing_title)
        self.assertIsNone(listing.id)
        listing.id = "my-code"
        self.assertEqual(listing.id, "my-code")
        listing.id = None
        self.assertIsNone(listing.id)

        self.assertIsNone(listing.language)
        listing.language = "python"
        self.assertEqual(listing.language, "python")
        listing.language = None
        self.assertIsNone(listing.language)

        self.assertIsNone(listing.style)
        listing.style = "source"
        self.assertEqual(listing.style, "source")
        listing.style = None
        self.assertIsNone(listing.style)

        # Test listing_title fallback
        listing.attributes["title"] = "Fallback Title"
        self.assertEqual(listing.listing_title, "Fallback Title")

        listing.title = Title([Text("True Title")])
        self.assertEqual(listing.listing_title, "True Title")

    def test_verbatim_block_mixin_callouts_parsing(self):
        # A mix of autoguide, manual, and bare html callouts with \r\n
        code_text = "line 1 // <.>\r\nline 2 // <2> <3>\r\nline 3 <!-- 4 -->\r\nline 4 no callout"
        listing = Listing(inlines=[Text(code_text)])

        self.assertEqual(
            listing.stripped_code, "line 1\r\nline 2\r\nline 3\r\nline 4 no callout"
        )

        expected_callouts = {1: [1], 2: [2, 3], 3: [4]}
        self.assertEqual(listing.callouts, expected_callouts)

    def test_literal_and_passthrough_and_stem(self):
        lit = Literal(inlines=[Text("literal text")], form="delimited")
        self.assertEqual(lit.name, "literal")
        self.assertEqual(lit.delimiter, "....")

        lit_custom = Literal(inlines=[Text("text")], delimiter="----", form="delimited")
        self.assertEqual(lit_custom.delimiter, "----")

        pass_block = Passthrough(inlines=[Text("pass")])
        self.assertEqual(pass_block.name, "passthrough")
        self.assertEqual(
            pass_block.get_child_collections(), {"inlines": pass_block.inlines}
        )

        stem = Stem(variant="latexmath", inlines=[Text("x=y")])
        self.assertEqual(stem.name, "stem")
        self.assertEqual(stem.get_child_collections(), {"inlines": stem.inlines})

    def test_structural_block_types(self):
        # Example
        ex = Example(blocks=[Paragraph([Text("ex")])])
        self.assertEqual(ex.name, "example")
        self.assertEqual(ex.get_child_collections(), {"blocks": ex.blocks})

        # Quote
        q = Quote(blocks=[Paragraph([Text("quote")])])
        self.assertEqual(q.name, "quote")
        self.assertEqual(q.get_child_collections(), {"blocks": q.blocks})

        # Admonition
        adm = Admonition(variant="NOTE", blocks=[Paragraph([Text("note")])])
        self.assertEqual(adm.name, "admonition")
        self.assertEqual(adm.variant, "NOTE")
        self.assertEqual(adm.get_child_collections(), {"blocks": adm.blocks})

        # Sidebar
        sb = Sidebar(blocks=[Paragraph([Text("sidebar")])])
        self.assertEqual(sb.name, "sidebar")
        self.assertEqual(sb.get_child_collections(), {"blocks": sb.blocks})

        # Verse
        v = Verse(blocks=[Paragraph([Text("verse")])])
        self.assertEqual(v.name, "verse")
        self.assertEqual(v.get_child_collections(), {"blocks": v.blocks})

        # Open
        op = Open(blocks=[Paragraph([Text("open")])])
        self.assertEqual(op.name, "open")
        self.assertEqual(op.get_child_collections(), {"blocks": op.blocks})

    def test_table_hierarchy(self):
        cell1 = TableCell(blocks=[Paragraph([Text("cell 1")])])
        self.assertEqual(cell1.name, "cell")
        self.assertEqual(cell1.colspan, 1)
        self.assertEqual(cell1.get_child_collections(), {"blocks": cell1.blocks})

        row = TableRow(cells=[cell1])
        self.assertEqual(row.name, "row")
        self.assertEqual(row.get_child_collections(), {"cells": row.cells})
        row.append(TableCell())
        self.assertEqual(len(row.cells), 2)

        # TableRow inherits from Node and supports fallback append to self.children
        p = Paragraph()
        row.append(p)
        self.assertIn(p, row.children)

        tbl = Table(rows=[row])
        self.assertEqual(tbl.name, "table")
        self.assertEqual(tbl.get_child_collections(), {"rows": tbl.rows})
        tbl.append(TableRow())
        self.assertEqual(len(tbl.rows), 2)

        with self.assertRaises(AttributeError):
            tbl.append(Paragraph())

    def test_breaks(self):
        hr = ThematicBreak()
        self.assertEqual(hr.name, "thematic_break")
        self.assertEqual(hr.type, "block")

        pb = PageBreak()
        self.assertEqual(pb.name, "page_break")
        self.assertEqual(pb.type, "block")

    def test_collapsible_and_index_term(self):
        # Collapsible Block Node
        coll = Collapsible(
            title=Title([Text("Summary")]),
            blocks=[Paragraph([Text("Detail content")])],
            attributes={"options": "collapsible"},
        )
        self.assertEqual(coll.name, "collapsible")
        self.assertEqual(coll.type, "block")
        self.assertEqual(coll.get_child_collections(), {"blocks": coll.blocks})
        d_coll = coll.to_dict()
        self.assertEqual(d_coll["name"], "collapsible")
        self.assertEqual(d_coll["type"], "block")
        self.assertEqual(d_coll["attributes"], {"options": "collapsible"})
        self.assertIn("title", d_coll)
        self.assertEqual(len(d_coll["blocks"]), 1)

        # IndexTerm Inline Node
        idx = IndexTerm(terms=["primary", "secondary"], variant="macro")
        self.assertEqual(idx.name, "indexterm")
        self.assertEqual(idx.type, "inline")
        self.assertEqual(idx.get_child_collections(), {"inlines": idx.inlines})
        d_idx = idx.to_dict()
        self.assertEqual(d_idx["name"], "indexterm")
        self.assertEqual(d_idx["type"], "inline")
        self.assertEqual(d_idx["terms"], ["primary", "secondary"])
        self.assertEqual(d_idx["variant"], "macro")

    def test_literal_properties(self):
        from asciidoctrine.nodes import Literal, Text, Title

        lit = Literal()
        # id
        assert lit.id is None
        lit.id = "my-id"
        assert lit.id == "my-id"
        assert lit.attributes["id"] == "my-id"
        lit.id = None
        assert lit.id is None
        assert "id" not in lit.attributes

        # style
        assert lit.style is None
        lit.style = "my-style"
        assert lit.style == "my-style"
        assert lit.attributes["style"] == "my-style"
        lit.style = None
        assert lit.style is None
        assert "style" not in lit.attributes

        # literal_title via attribute
        lit.attributes["title"] = "Attr Title"
        assert lit.literal_title == "Attr Title"

        # literal_title via title node
        lit.title = Title(inlines=[Text("Node Title")])
        assert lit.literal_title == "Node Title"

    def test_additional_node_serializations_and_collections(self):
        # Title
        t = Title(inlines=[Text("Main Title")])
        self.assertEqual(t.get_child_collections(), {"inlines": t.inlines})
        self.assertEqual(
            t.to_list(), [{"name": "text", "type": "string", "value": "Main Title"}]
        )

        # Author
        a = Author(inlines=[Text("Jane Doe")])
        self.assertEqual(a.get_child_collections(), {"inlines": a.inlines})

        # Revision
        r = Revision(inlines=[Text("v1.0")])
        self.assertEqual(r.get_child_collections(), {"inlines": r.inlines})
        r.append(Text(" extra"))
        self.assertEqual(len(r.inlines), 2)

        # FloatingTitle
        ft = FloatingTitle(level=2, title=t)
        self.assertEqual(ft.get_child_collections(), {"inlines": t.inlines})
        d_ft = ft.to_dict()
        self.assertEqual(d_ft["name"], "floatingTitle")
        self.assertEqual(d_ft["level"], 2)

        # Audio
        audio = Audio(target="music.mp3", attributes={"autoplay": "true"})
        self.assertEqual(audio.get_child_collections(), {})
        d_audio = audio.to_dict()
        self.assertEqual(d_audio["name"], "audio")
        self.assertEqual(d_audio["target"], "music.mp3")

        # Video
        video = Video(target="movie.mp4", attributes={"controls": "true"})
        self.assertEqual(video.get_child_collections(), {})
        d_vid = video.to_dict()
        self.assertEqual(d_vid["name"], "video")
        self.assertEqual(d_vid["target"], "movie.mp4")

        # Button: stores label as self.value, serialized as 'value'
        btn = Button(label="Submit")
        self.assertEqual(btn.get_child_collections(), {})
        d_btn = btn.to_dict()
        self.assertEqual(d_btn["name"], "button")
        self.assertEqual(d_btn["value"], "Submit")

        # Kbd: stores keys list as self.value, serialized as 'value'
        kbd = Kbd(keys=["Ctrl", "C"])
        self.assertEqual(kbd.get_child_collections(), {})
        d_kbd = kbd.to_dict()
        self.assertEqual(d_kbd["name"], "kbd")
        self.assertEqual(d_kbd["value"], ["Ctrl", "C"])

        # Menu: stores menu name and items separately; has custom to_dict()
        menu = Menu(menu="File", items=["Save", "Save As"])
        self.assertEqual(menu.get_child_collections(), {})
        d_menu = menu.to_dict()
        self.assertEqual(d_menu["name"], "menu")
        self.assertEqual(d_menu["menu"], "File")
        self.assertEqual(d_menu["items"], ["Save", "Save As"])

        # Verse
        v = Verse(blocks=[Paragraph([Text("Stanza line")])])
        self.assertEqual(v.get_child_collections(), {"blocks": v.blocks})
        v.append(Paragraph([Text("Second line")]))
        d_v = v.to_dict()
        self.assertEqual(d_v["name"], "verse")

        # CalloutList & CalloutListItem
        cli = CalloutListItem(number=1, blocks=[Paragraph([Text("Callout desc")])])
        cl = CalloutList(items=[cli])
        self.assertEqual(cl.get_child_collections(), {"items": cl.items})
        # CalloutListItem exposes both 'principal' and 'blocks' collections
        self.assertEqual(
            cli.get_child_collections(),
            {"principal": cli.principal, "blocks": cli.blocks},
        )
        d_cl = cl.to_dict()
        self.assertEqual(d_cl["name"], "calloutList")

        # Breaks
        br = Break()
        pb = PageBreak()
        tb = ThematicBreak()
        self.assertEqual(br.get_child_collections(), {})
        self.assertEqual(pb.get_child_collections(), {})
        self.assertEqual(tb.get_child_collections(), {})
        self.assertEqual(br.to_dict()["name"], "break")
        self.assertEqual(pb.to_dict()["name"], "page_break")
        self.assertEqual(tb.to_dict()["name"], "thematic_break")

        # Open
        op = Open(blocks=[Paragraph([Text("Open content")])], delimiter="~~")
        self.assertEqual(op.get_child_collections(), {"blocks": op.blocks})
        d_op = op.to_dict()
        self.assertEqual(d_op["name"], "open")
        self.assertEqual(d_op["delimiter"], "~~")

    def test_listing_properties(self):
        from asciidoctrine.nodes import Listing

        lis = Listing()
        # id
        self.assertIsNone(lis.id)
        lis.id = "code-block-1"
        self.assertEqual(lis.id, "code-block-1")
        self.assertEqual(lis.attributes["id"], "code-block-1")
        lis.id = None
        self.assertIsNone(lis.id)
        self.assertNotIn("id", lis.attributes)

        # language
        self.assertIsNone(lis.language)
        lis.language = "python"
        self.assertEqual(lis.language, "python")
        self.assertEqual(lis.attributes["language"], "python")
        lis.language = None
        self.assertIsNone(lis.language)
        self.assertNotIn("language", lis.attributes)

        # style
        self.assertIsNone(lis.style)
        lis.style = "source"
        self.assertEqual(lis.style, "source")
        self.assertEqual(lis.attributes["style"], "source")
        lis.style = None
        self.assertIsNone(lis.style)
        self.assertNotIn("style", lis.attributes)

        # listing_title via attribute
        lis.attributes["title"] = "Listing Attr Title"
        self.assertEqual(lis.listing_title, "Listing Attr Title")

        # listing_title via title node
        lis.title = Title(inlines=[Text("Listing Node Title")])
        self.assertEqual(lis.listing_title, "Listing Node Title")


if __name__ == "__main__":
    unittest.main()
