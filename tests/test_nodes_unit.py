"""
Unit tests for AST Node classes in nodes.py.
"""

import unittest

import pytest

from asciidoctrine.nodes import (
    Admonition,
    AttributeEntry,
    Attributes,
    Audio,
    Author,
    BlockNode,
    Break,
    Button,
    Callout,
    CalloutList,
    CalloutListItem,
    Collapsible,
    Comment,
    DescriptionList,
    DescriptionListItem,
    DescriptionListTerm,
    Docinfo,
    Document,
    Example,
    FloatingTitle,
    Header,
    Image,
    Include,
    IndexTerm,
    InlineNode,
    InlinePassthrough,
    InlineStem,
    Kbd,
    List,
    Listing,
    ListItem,
    Literal,
    Menu,
    Node,
    NodeTransformer,
    NodeVisitor,
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
    Toc,
    Verse,
    Video,
)

pytestmark = pytest.mark.unit


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


# ---------------------------------------------------------------------------
# Additional node type tests (constructors, properties, mixin methods)
# ---------------------------------------------------------------------------


class TestNodeBase:
    def test_walk_yields_self_and_children(self) -> None:
        root = Document()
        p = Paragraph(inlines=[Text("hello")])
        root.blocks.append(p)
        walked = list(root.walk())
        # Should include root, p, and the Text inline
        names = [n.name for n in walked]
        assert "document" in names
        assert "paragraph" in names
        assert "text" in names

    def test_node_append_adds_to_children(self) -> None:
        node = Node()
        child = Node()
        node.append(child)
        assert child in node.children

    def test_node_get_child_collections_empty(self) -> None:
        node = Node()
        assert node.get_child_collections() == {}

    def test_node_get_child_collections_with_children(self) -> None:
        node = Node()
        child = Node()
        node.children.append(child)
        colls = node.get_child_collections()
        assert "children" in colls
        assert child in colls["children"]

    def test_to_dict_includes_location(self) -> None:
        node = Text("hi")
        node.location = [{"line": 1, "col": 1}, {"line": 1, "col": 3}]
        d = node.to_dict()
        assert "location" in d
        assert d["location"][0]["line"] == 1

    def test_to_dict_title_with_to_list(self) -> None:
        p = Paragraph()
        title = Title(inlines=[Text("My Title")])
        p.title = title
        d = p.to_dict()
        assert "title" in d
        assert d["title"][0]["value"] == "My Title"

    def test_to_dict_title_as_list(self) -> None:
        """Cover the `isinstance(self.title, list)` branch."""
        p = Paragraph()
        p.title = [Text("Direct List Title")]  # type: ignore[assignment]
        d = p.to_dict()
        assert "title" in d

    def test_to_dict_with_attributes(self) -> None:
        p = Paragraph()
        p.attributes = {"role": "lead"}
        d = p.to_dict()
        assert d["attributes"]["role"] == "lead"

    def test_to_dict_no_attributes_when_disabled(self) -> None:
        doc = Document()
        # _should_serialize_attributes is False on Document
        d = doc.to_dict()
        # attributes key comes from Document.to_dict override, not base
        assert "name" in d


# ---------------------------------------------------------------------------
# InlineNode and BlockNode append overrides
# ---------------------------------------------------------------------------


class TestInlineAndBlockAppend:
    def test_inline_node_append_goes_to_inlines(self) -> None:
        span = Span(variant="strong")
        span.append(Text("bold"))
        assert len(span.inlines) == 1
        assert span.inlines[0].name == "text"

    def test_block_node_append_goes_to_blocks(self) -> None:
        doc = Document()
        p = Paragraph()
        doc.append(p)
        assert p in doc.blocks


# ---------------------------------------------------------------------------
# Docinfo
# ---------------------------------------------------------------------------


class TestDocinfo:
    def test_init_defaults(self) -> None:
        d = Docinfo()
        assert d.name == "docinfo"
        assert d.type == "metadata"
        assert d.head_content == ""
        assert d.footer_content == ""

    def test_init_with_content(self) -> None:
        d = Docinfo(head_content="<style/>", footer_content="<script/>")
        assert d.head_content == "<style/>"
        assert d.footer_content == "<script/>"

    def test_to_dict(self) -> None:
        d = Docinfo(head_content="HEAD", footer_content="FOOT")
        result = d.to_dict()
        assert result["head_content"] == "HEAD"
        assert result["footer_content"] == "FOOT"
        assert result["name"] == "docinfo"


# ---------------------------------------------------------------------------
# Document.to_dict branches
# ---------------------------------------------------------------------------


class TestDocumentToDict:
    def test_to_dict_with_list_valued_attributes(self) -> None:
        doc = Document()
        doc.attributes = {"author": [Text("John")], "simple": "plain"}
        d = doc.to_dict()
        assert d["attributes"]["simple"] == "plain"
        assert d["attributes"]["author"] == "John"

    def test_to_dict_with_docinfo(self) -> None:
        doc = Document()
        doc.docinfo = Docinfo(head_content="HEAD", footer_content="FOOT")
        d = doc.to_dict()
        assert "docinfo" in d
        assert d["docinfo"]["head_content"] == "HEAD"

    def test_to_dict_with_footnotes(self) -> None:
        doc = Document()
        doc.footnotes = [{"id": None, "index": 1, "text": "A footnote"}]
        d = doc.to_dict()
        assert "footnotes" in d
        assert len(d["footnotes"]) == 1

    def test_to_dict_with_header(self) -> None:
        doc = Document()
        doc.header = Header(title=Title(inlines=[Text("My Doc")]))
        d = doc.to_dict()
        assert "header" in d
        assert d["header"]["title"][0]["value"] == "My Doc"


# ---------------------------------------------------------------------------
# FloatingTitle
# ---------------------------------------------------------------------------


class TestFloatingTitle:
    def test_init(self) -> None:
        t = Title(inlines=[Text("Floating")])
        ft = FloatingTitle(level=2, title=t)
        assert ft.name == "floatingTitle"
        assert ft.level == 2
        assert ft.title is t

    def test_get_child_collections(self) -> None:
        t = Title(inlines=[Text("Hi")])
        ft = FloatingTitle(level=1, title=t)
        colls = ft.get_child_collections()
        assert "inlines" in colls

    def test_get_child_collections_no_title(self) -> None:
        # FloatingTitle with a Title that has no inlines
        t = Title(inlines=[])
        ft = FloatingTitle(level=1, title=t)
        colls = ft.get_child_collections()
        # returns inlines from title, which is empty
        assert colls.get("inlines", []) == []


# ---------------------------------------------------------------------------
# Header.to_dict branches
# ---------------------------------------------------------------------------


class TestHeaderToDict:
    def test_to_dict_no_content(self) -> None:
        h = Header()
        assert h.to_dict() == {}

    def test_to_dict_with_title(self) -> None:
        h = Header(title=Title(inlines=[Text("Title")]))
        d = h.to_dict()
        assert "title" in d

    def test_to_dict_with_authors(self) -> None:
        author = Author(inlines=[Text("Alice")])
        h = Header(authors=[author])
        d = h.to_dict()
        assert "authors" in d
        assert d["authors"][0]["fullname"] == "Alice"

    def test_to_dict_with_revision(self) -> None:
        rev = Revision(inlines=[Text("v1.0")])
        h = Header(revision=rev)
        d = h.to_dict()
        assert "revision" in d
        assert d["revision"]["value"] == "v1.0"

    def test_to_dict_with_docinfo(self) -> None:
        di = Docinfo(head_content="<meta/>")
        h = Header(docinfo=di)
        d = h.to_dict()
        assert "docinfo" in d

    def test_revision_append(self) -> None:
        rev = Revision()
        t = Text("v2.0")
        rev.append(t)
        assert t in rev.inlines


# ---------------------------------------------------------------------------
# Audio and Video
# ---------------------------------------------------------------------------


class TestAudioVideo:
    def test_audio_init(self) -> None:
        a = Audio(target="sound.mp3", attributes={"autoplay": "true"})
        assert a.name == "audio"
        assert a.target == "sound.mp3"
        assert a.attributes["autoplay"] == "true"

    def test_audio_init_no_attrs(self) -> None:
        a = Audio(target="x.wav")
        assert a.attributes == {}

    def test_video_init(self) -> None:
        v = Video(target="clip.mp4", attributes={"width": "640"})
        assert v.name == "video"
        assert v.target == "clip.mp4"

    def test_video_init_no_attrs(self) -> None:
        v = Video(target="y.webm")
        assert v.attributes == {}


# ---------------------------------------------------------------------------
# DescriptionList and friends
# ---------------------------------------------------------------------------


class TestDescriptionList:
    def test_description_list_append_item(self) -> None:
        dl = DescriptionList()
        term = DescriptionListTerm(inlines=[Text("Term")])
        item = DescriptionListItem(terms=[term])
        dl.append(item)
        assert item in dl.items

    def test_description_list_item_get_child_collections(self) -> None:
        term = DescriptionListTerm(inlines=[Text("Foo")])
        item = DescriptionListItem(terms=[term], blocks=[Paragraph()])
        colls = item.get_child_collections()
        assert "terms" in colls
        assert "blocks" in colls

    def test_description_list_term_get_child_collections(self) -> None:
        term = DescriptionListTerm(inlines=[Text("Bar")])
        colls = term.get_child_collections()
        assert "inlines" in colls


# ---------------------------------------------------------------------------
# VerbatimBlockMixin – Listing
# ---------------------------------------------------------------------------


class TestListingProperties:
    def _make_listing(
        self, code: str, callout_numbers: list[int] | None = None
    ) -> Listing:
        inlines: list[Node] = [Text(code)]
        if callout_numbers:
            for n in callout_numbers:
                inlines.append(Callout(n))
        return Listing(inlines=inlines)

    def test_code_property_plain(self) -> None:
        lst = Listing(inlines=[Text("x = 1\n")])
        assert lst.code == "x = 1\n"

    def test_code_property_with_callout_inline(self) -> None:
        lst = Listing(inlines=[Text("x = 1"), Callout(1)])
        assert "<1>" in lst.code

    def test_stripped_code_no_callouts(self) -> None:
        lst = Listing(inlines=[Text("hello world  <1>\n")])
        # strips the trailing callout marker
        stripped = lst.stripped_code
        assert "<1>" not in stripped

    def test_stripped_code_with_callout_inline_objects(self) -> None:
        lst = Listing(inlines=[Text("code\n"), Callout(1)])
        stripped = lst.stripped_code
        assert stripped == "code\n"

    def test_callouts_from_inline_objects(self) -> None:
        lst = Listing(inlines=[Text("line1\nline2\n"), Callout(1)])
        callout_map = lst.callouts
        assert isinstance(callout_map, dict)

    def test_callouts_from_text_markers(self) -> None:
        lst = Listing(inlines=[Text("line one  <1>\nline two\n")])
        callout_map = lst.callouts
        assert 1 in callout_map
        assert 1 in callout_map[1]

    def test_callouts_auto_numbered(self) -> None:
        lst = Listing(inlines=[Text("code  <.>\n")])
        callout_map = lst.callouts
        assert 1 in callout_map
        assert callout_map[1] == [1]

    def test_id_setter(self) -> None:
        lst = Listing()
        lst.id = "my-id"
        assert lst.attributes["id"] == "my-id"

    def test_id_setter_none_removes(self) -> None:
        lst = Listing(attributes={"id": "old"})
        lst.id = None
        assert "id" not in lst.attributes

    def test_language_setter(self) -> None:
        lst = Listing()
        lst.language = "python"
        assert lst.attributes["language"] == "python"

    def test_language_setter_none_removes(self) -> None:
        lst = Listing(attributes={"language": "old"})
        lst.language = None
        assert "language" not in lst.attributes

    def test_style_setter(self) -> None:
        lst = Listing()
        lst.style = "source"
        assert lst.attributes["style"] == "source"

    def test_style_setter_none_removes(self) -> None:
        lst = Listing(attributes={"style": "old"})
        lst.style = None
        assert "style" not in lst.attributes

    def test_listing_title_from_title_node(self) -> None:
        lst = Listing()
        lst.title = Title(inlines=[Text("My Code")])
        assert lst.listing_title == "My Code"

    def test_listing_title_from_attributes(self) -> None:
        lst = Listing(attributes={"title": "Attr Title"})
        assert lst.listing_title == "Attr Title"

    def test_listing_title_none(self) -> None:
        lst = Listing()
        assert lst.listing_title is None

    def test_listing_append(self) -> None:
        lst = Listing()
        t = Text("x")
        lst.append(t)
        assert t in lst.inlines


# ---------------------------------------------------------------------------
# Literal
# ---------------------------------------------------------------------------


class TestLiteralProperties:
    def test_id_setter(self) -> None:
        lit = Literal()
        lit.id = "lit-id"
        assert lit.attributes["id"] == "lit-id"

    def test_id_setter_none_removes(self) -> None:
        lit = Literal(attributes={"id": "old"})
        lit.id = None
        assert "id" not in lit.attributes

    def test_style_setter(self) -> None:
        lit = Literal()
        lit.style = "verse"
        assert lit.attributes["style"] == "verse"

    def test_style_setter_none_removes(self) -> None:
        lit = Literal(attributes={"style": "old"})
        lit.style = None
        assert "style" not in lit.attributes

    def test_literal_title_from_title_node(self) -> None:
        lit = Literal()
        lit.title = Title(inlines=[Text("Lit Title")])
        assert lit.literal_title == "Lit Title"

    def test_literal_title_from_attributes(self) -> None:
        lit = Literal(attributes={"title": "My Literal"})
        assert lit.literal_title == "My Literal"

    def test_literal_title_none(self) -> None:
        lit = Literal()
        assert lit.literal_title is None

    def test_literal_form_indented(self) -> None:
        lit = Literal(form="indented")
        assert lit.form == "indented"
        assert (
            not hasattr(lit, "delimiter") or lit.delimiter is None
        )  # indented has no delimiter

    def test_literal_delimiter_explicit(self) -> None:
        lit = Literal(delimiter="....")
        assert lit.delimiter == "...."

    def test_literal_append(self) -> None:
        lit = Literal()
        t = Text("y")
        lit.append(t)
        assert t in lit.inlines


# ---------------------------------------------------------------------------
# Passthrough (block)
# ---------------------------------------------------------------------------


class TestPassthroughBlock:
    def test_init_defaults(self) -> None:
        p = Passthrough()
        assert p.name == "passthrough"
        assert p.type == "block"
        assert p.form == "delimited"
        assert p.delimiter == "++++"

    def test_init_with_inlines(self) -> None:
        p = Passthrough(inlines=[Text("<b>raw</b>")])
        assert len(p.inlines) == 1

    def test_init_with_custom_delimiter(self) -> None:
        p = Passthrough(delimiter="+++")
        assert p.delimiter == "+++"

    def test_get_child_collections(self) -> None:
        p = Passthrough(inlines=[Text("x")])
        assert "inlines" in p.get_child_collections()


# ---------------------------------------------------------------------------
# Comment (block)
# ---------------------------------------------------------------------------


class TestCommentBlock:
    def test_init(self) -> None:
        c = Comment(value="// a comment")
        assert c.name == "comment"
        assert c.type == "block"
        assert c.value == "// a comment"
        assert c.delimiter == "////"

    def test_init_custom_delimiter(self) -> None:
        c = Comment(value="x", delimiter="//--")
        assert c.delimiter == "//--"

    def test_get_child_collections_empty(self) -> None:
        c = Comment("x")
        assert c.get_child_collections() == {}


# ---------------------------------------------------------------------------
# Stem (block)
# ---------------------------------------------------------------------------


class TestStemBlock:
    def test_init_delimited(self) -> None:
        s = Stem(variant="latexmath", delimiter="----")
        assert s.name == "stem"
        assert s.form == "delimited"
        assert s.delimiter == "----"

    def test_init_paragraph(self) -> None:
        s = Stem(variant="latexmath")
        assert s.form == "paragraph"
        assert s.delimiter is None

    def test_get_child_collections(self) -> None:
        s = Stem(variant="latexmath", inlines=[Text("x^2")])
        assert "inlines" in s.get_child_collections()


# ---------------------------------------------------------------------------
# Collapsible
# ---------------------------------------------------------------------------


class TestCollapsible:
    def test_init(self) -> None:
        c = Collapsible()
        assert c.name == "collapsible"
        assert c.type == "block"

    def test_to_dict_without_title(self) -> None:
        c = Collapsible(blocks=[Paragraph(inlines=[Text("inner")])])
        d = c.to_dict()
        assert d["name"] == "collapsible"
        assert "title" not in d

    def test_to_dict_with_title(self) -> None:
        t = Title(inlines=[Text("Collapse Me")])
        c = Collapsible(title=t, blocks=[Paragraph()])
        d = c.to_dict()
        assert "title" in d


# ---------------------------------------------------------------------------
# Quote, Admonition, Sidebar, Verse, Open
# ---------------------------------------------------------------------------


class TestDelimitedBlocks:
    def test_quote_init(self) -> None:
        q = Quote(attribution="Author", citetitle="Book")
        assert q.name == "quote"
        assert q.attribution == "Author"
        assert q.citetitle == "Book"
        assert q.form == "delimited"

    def test_admonition_delimited(self) -> None:
        a = Admonition(variant="NOTE", delimiter="====")
        assert a.form == "delimited"
        assert a.variant == "NOTE"

    def test_admonition_paragraph(self) -> None:
        a = Admonition(variant="TIP", delimiter=None)
        assert a.form == "paragraph"

    def test_sidebar_init(self) -> None:
        s = Sidebar()
        assert s.name == "sidebar"
        assert s.delimiter == "****"

    def test_verse_delimited(self) -> None:
        v = Verse(delimiter="____", attribution="Keats")
        assert v.form == "delimited"
        assert v.attribution == "Keats"

    def test_verse_paragraph(self) -> None:
        v = Verse()
        assert v.form == "paragraph"

    def test_open_init(self) -> None:
        o = Open()
        assert o.name == "open"
        assert o.delimiter == "--"


# ---------------------------------------------------------------------------
# Table, TableRow, TableCell
# ---------------------------------------------------------------------------


class TestTableNodes:
    def test_table_append_row(self) -> None:
        table = Table()
        row = TableRow()
        table.append(row)
        assert row in table.rows

    def test_tablerow_append_cell(self) -> None:
        row = TableRow()
        cell = TableCell()
        row.append(cell)
        assert cell in row.cells

    def test_tablerow_append_non_cell_fallback(self) -> None:
        row = TableRow()
        p = Paragraph()
        row.append(p)
        assert p in row.children

    def test_tablecell_defaults(self) -> None:
        cell = TableCell()
        assert cell.colspan == 1
        assert cell.rowspan == 1
        assert cell.align is None
        assert cell.style is None


# ---------------------------------------------------------------------------
# ThematicBreak and PageBreak
# ---------------------------------------------------------------------------


class TestBreakNodes:
    def test_thematic_break(self) -> None:
        tb = ThematicBreak()
        assert tb.name == "thematic_break"
        assert tb.type == "block"

    def test_page_break(self) -> None:
        pb = PageBreak()
        assert pb.name == "page_break"
        assert pb.type == "block"


# ---------------------------------------------------------------------------
# AttributeEntry, Attributes, Include, Toc
# ---------------------------------------------------------------------------


class TestMetaNodes:
    def test_attribute_entry(self) -> None:
        ae = AttributeEntry(name="version", value="1.0")
        assert ae.name == "attribute_entry"
        assert ae.attribute_name == "version"
        assert ae.value == "1.0"

    def test_attributes_node(self) -> None:
        a = Attributes({"key": {"value": "val"}})
        assert a.name == "attributes"
        assert "key" in a.attributes

    def test_include_node(self) -> None:
        inc = Include(filename="subdir/file.adoc")
        assert inc.name == "include"
        assert inc.filename == "subdir/file.adoc"

    def test_toc_node(self) -> None:
        toc = Toc(target="", attributes={"levels": "2"})
        assert toc.name == "toc"
        assert toc.attributes["levels"] == "2"

    def test_toc_defaults(self) -> None:
        toc = Toc()
        assert toc.target == ""
        assert toc.attributes == {}


# ---------------------------------------------------------------------------
# IndexTerm
# ---------------------------------------------------------------------------


class TestIndexTerm:
    def test_init(self) -> None:
        it = IndexTerm(terms=["AsciiDoc", "markup"], variant="macro")
        assert it.name == "indexterm"
        assert it.terms == ["AsciiDoc", "markup"]
        assert it.variant == "macro"

    def test_to_dict_no_inlines(self) -> None:
        it = IndexTerm(terms=["topic"])
        d = it.to_dict()
        assert d["terms"] == ["topic"]
        assert "inlines" not in d

    def test_to_dict_with_inlines(self) -> None:
        it = IndexTerm(terms=["topic"], inlines=[Text("visible")])
        d = it.to_dict()
        assert "inlines" in d
        assert d["inlines"][0]["value"] == "visible"

    def test_get_child_collections(self) -> None:
        it = IndexTerm(terms=["x"], inlines=[Text("y")])
        colls = it.get_child_collections()
        assert "inlines" in colls


# ---------------------------------------------------------------------------
# NodeVisitor and NodeTransformer
# ---------------------------------------------------------------------------


class TestNodeVisitorTransformer:
    def test_visitor_dispatch_to_specific_method(self) -> None:
        calls = []

        class MyVisitor(NodeVisitor):
            def visit_text(self, node: Node, **kwargs: object) -> None:
                calls.append(node.name)

        v = MyVisitor()
        t = Text("hello")
        v.visit(t)
        assert "text" in calls

    def test_visitor_generic_visit_traverses_children(self) -> None:
        calls = []

        class MyVisitor(NodeVisitor):
            def visit_text(self, node: Node, **kwargs: object) -> None:
                calls.append(node.name)

        v = MyVisitor()
        doc = Document()
        doc.blocks.append(Paragraph(inlines=[Text("x")]))
        v.visit(doc)
        assert "text" in calls

    def test_transformer_generic_visit_can_remove_nodes(self) -> None:
        class FilterTransformer(NodeTransformer):
            def visit_text(self, node: Node, **kwargs: object) -> None:
                return None  # drop all text nodes

        ft = FilterTransformer()
        p = Paragraph(inlines=[Text("remove me"), Text("me too")])
        result = ft.visit(p)
        assert isinstance(result, Paragraph)
        assert len(result.inlines) == 0

    def test_transformer_generic_visit_can_expand_nodes(self) -> None:
        class ExpandTransformer(NodeTransformer):
            def visit_text(self, node: Node, **kwargs: object) -> list[Node]:
                return [node, Text("extra")]

        et = ExpandTransformer()
        p = Paragraph(inlines=[Text("a")])
        result = et.visit(p)
        assert isinstance(result, Paragraph)
        assert len(result.inlines) == 2


# ---------------------------------------------------------------------------
# Miscellaneous inline nodes
# ---------------------------------------------------------------------------


class TestMiscInlineNodes:
    def test_break_node(self) -> None:
        b = Break()
        assert b.name == "break"
        assert b.type == "inline"

    def test_kbd_node(self) -> None:
        k = Kbd(keys=["Ctrl", "C"])
        assert k.name == "kbd"
        assert k.value == ["Ctrl", "C"]

    def test_button_node(self) -> None:
        b = Button(label="OK")
        assert b.name == "button"
        assert b.value == "OK"

    def test_menu_node_to_dict(self) -> None:
        m = Menu(menu="File", items=["Open", "Save"])
        d = m.to_dict()
        assert d["menu"] == "File"
        assert d["items"] == ["Open", "Save"]

    def test_callout_node(self) -> None:
        c = Callout(number=3)
        assert c.name == "callout"
        assert c.value == 3

    def test_inline_stem_node(self) -> None:
        s = InlineStem(variant="latexmath", value="x^2")
        assert s.name == "stem"
        assert s.variant == "latexmath"
        assert s.value == "x^2"

    def test_inline_passthrough_node(self) -> None:
        ip = InlinePassthrough(value="+pass+")
        assert ip.name == "passthrough"
        assert ip.type == "inline"
        assert ip.value == "+pass+"

    def test_inline_passthrough_get_child_collections_empty(self) -> None:
        ip = InlinePassthrough(value="x")
        assert ip.get_child_collections() == {}


# ---------------------------------------------------------------------------
# List.append branching
# ---------------------------------------------------------------------------


class TestListAppend:
    def test_list_append_list_item(self) -> None:
        lst = List(variant="unordered", marker="*")
        item = ListItem(marker="*", principal=[Text("item")])
        lst.append(item)
        assert item in lst.items


# ---------------------------------------------------------------------------
# CalloutList.append branching
# ---------------------------------------------------------------------------


class TestCalloutListAppend:
    def test_calloutlist_append_item(self) -> None:
        cl = CalloutList()
        item = CalloutListItem(number=1, principal=[Text("desc")])
        cl.append(item)
        assert item in cl.items


# ---------------------------------------------------------------------------
# Image node
# ---------------------------------------------------------------------------


class TestImageNode:
    def test_image_block(self) -> None:
        img = Image(target="img.png", alt="alt text")
        assert img.name == "image"
        assert img.target == "img.png"
        assert img.attributes["alt"] == "alt text"

    def test_image_inline_type(self) -> None:
        img = Image(target="icon.svg", alt="icon", type="inline")
        assert img.type == "inline"

    def test_image_form(self) -> None:
        img = Image(target="a.png", form="macro")
        assert img.form == "macro"
