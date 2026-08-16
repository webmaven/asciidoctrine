"""
Unit tests for AsciiDocSerializerVisitor in asciidoctrine.

These tests call visitor methods directly on hand-built nodes so that
branch-level coverage doesn't depend on the full Lark parse pipeline.
"""

import pytest

from asciidoctrine.nodes import (
    Admonition,
    Break,
    Button,
    Callout,
    CalloutList,
    CalloutListItem,
    Comment,
    DescriptionList,
    DescriptionListItem,
    DescriptionListTerm,
    Document,
    Example,
    Image,
    IndexTerm,
    InlinePassthrough,
    InlineStem,
    Kbd,
    Listing,
    ListItem,
    Literal,
    Menu,
    Node,
    Open,
    Paragraph,
    Passthrough,
    Quote,
    Ref,
    Section,
    Sidebar,
    Span,
    Table,
    TableCell,
    TableRow,
    Text,
)
from asciidoctrine.nodes import List as ASTList
from asciidoctrine.serializer import AsciiDocSerializerVisitor, serialize_to_asciidoc

pytestmark = pytest.mark.unit


def _ser(node: Node) -> str:
    """Helper: serialize a single node and return its string."""
    v = AsciiDocSerializerVisitor()
    v.visit(node)
    return v.stream.getvalue()


# ---------------------------------------------------------------------------
# write — CRLF line-ending translation
# ---------------------------------------------------------------------------


def test_write_crlf_translation():
    v = AsciiDocSerializerVisitor()
    v.line_ending = "\r\n"
    v.write("line one\nline two\n")
    assert v.stream.getvalue() == "line one\r\nline two\r\n"


# ---------------------------------------------------------------------------
# serialize — no-trailing-newline stripping
# ---------------------------------------------------------------------------


def test_serialize_strips_trailing_lf_when_no_trailing_newline():
    doc = Document(blocks=[Paragraph(inlines=[Text("hello")])])
    doc.had_trailing_newline = False
    doc.line_ending = "\n"
    result = serialize_to_asciidoc(doc)
    assert not result.endswith("\n")
    assert "hello" in result


def test_serialize_strips_trailing_crlf_when_no_trailing_newline():
    doc = Document(blocks=[Paragraph(inlines=[Text("hello")])])
    doc.had_trailing_newline = False
    doc.line_ending = "\r\n"
    result = serialize_to_asciidoc(doc)
    assert not result.endswith("\r\n")


# ---------------------------------------------------------------------------
# write_block_metadata — title-from-attribute, bool attrs, quoted values
# ---------------------------------------------------------------------------


def test_write_block_metadata_title_from_attribute():
    v = AsciiDocSerializerVisitor()
    node = Paragraph(inlines=[Text("body")])
    node.attributes["title"] = "My Title"
    v.write_block_metadata(node)
    assert ".My Title\n" in v.stream.getvalue()


def test_write_block_metadata_bool_true_attribute():
    """A True bool attribute must be serialized as just the key (no value)."""
    v = AsciiDocSerializerVisitor()
    node = Paragraph(inlines=[Text("body")])
    node.attributes["autoplay"] = True
    v.write_block_metadata(node)
    out = v.stream.getvalue()
    assert "autoplay" in out
    # Must NOT include '=True'
    assert "=True" not in out


def test_write_block_metadata_quoted_value_with_space():
    """Attribute values containing spaces must be quoted."""
    v = AsciiDocSerializerVisitor()
    node = Paragraph(inlines=[Text("body")])
    node.attributes["cols"] = "1 2 3"
    v.write_block_metadata(node)
    assert '"1 2 3"' in v.stream.getvalue()


def test_write_block_metadata_quoted_value_with_comma():
    v = AsciiDocSerializerVisitor()
    node = Paragraph(inlines=[Text("body")])
    node.attributes["cols"] = "1,2"
    v.write_block_metadata(node)
    assert '"1,2"' in v.stream.getvalue()


def test_write_block_metadata_style_with_language():
    v = AsciiDocSerializerVisitor()
    node = Listing(inlines=[Text("code")], attributes={})
    node.attributes["style"] = "source"
    node.attributes["language"] = "python"
    v.write_block_metadata(node)
    out = v.stream.getvalue()
    assert "source" in out
    assert "python" in out


# ---------------------------------------------------------------------------
# visit_header — authors, revision, bool/None/value attrs
# ---------------------------------------------------------------------------


def test_visit_header_with_authors_and_revision():
    from asciidoctrine.nodes import Header

    header = Header()
    author = Node()
    author.inlines = [Text("Jane Doe")]
    header.authors = [author]
    rev = Node()
    rev.inlines = [Text("v2.0, 2026-01-01")]
    header.revision = rev
    header.attributes = {"toc": True, "stem": None, "backend": "html5"}

    out = _ser(header)
    assert "Jane Doe\n" in out
    assert "v2.0, 2026-01-01\n" in out
    # bool True → `:toc:\n`
    assert ":toc:\n" in out
    # None value → skipped (not written)
    assert ":stem:" not in out
    # regular value → `:backend: html5\n`
    assert ":backend: html5\n" in out


def test_visit_header_no_authors_no_revision():
    from asciidoctrine.nodes import Header

    header = Header()
    header.attributes = {}
    out = _ser(header)
    assert out == ""


# ---------------------------------------------------------------------------
# visit_listing — code with and without trailing newline
# ---------------------------------------------------------------------------


def test_visit_listing_code_no_trailing_newline():
    listing = Listing(inlines=[Text("print('hi')")], attributes={})
    listing.attributes["style"] = "source"
    out = _ser(listing)
    # Serializer uses `.code` property; if inlines, code may come from inlines
    # The important thing: delimiter appears twice and content is present
    assert "----" in out


def test_visit_listing_with_explicit_code():
    """Direct `.code` attribute path."""
    v = AsciiDocSerializerVisitor()
    node = Node()
    node.name = "listing"
    node.attributes = {}
    node.title = None
    # Simulate .code without trailing newline
    node.code = "some code"
    node.delimiter = "----"
    v.visit_listing(node)
    out = v.stream.getvalue()
    assert "----\nsome code\n----\n" == out


def test_visit_listing_code_with_trailing_newline():
    v = AsciiDocSerializerVisitor()
    node = Node()
    node.name = "listing"
    node.attributes = {}
    node.title = None
    node.code = "some code\n"
    node.delimiter = "----"
    v.visit_listing(node)
    out = v.stream.getvalue()
    assert out == "----\nsome code\n----\n"


# ---------------------------------------------------------------------------
# visit_literal — indented form
# ---------------------------------------------------------------------------


def test_visit_literal_indented_form():
    v = AsciiDocSerializerVisitor()
    node = Node()
    node.name = "literal"
    node.attributes = {}
    node.title = None
    node.form = "indented"
    node.code = "line one\nline two"
    v.visit_literal(node)
    out = v.stream.getvalue()
    assert " line one\n" in out
    assert " line two\n" in out


def test_visit_literal_delimited_no_trailing_newline():
    v = AsciiDocSerializerVisitor()
    node = Node()
    node.name = "literal"
    node.attributes = {}
    node.title = None
    node.form = "delimited"
    node.code = "literal content"  # no trailing newline
    node.delimiter = "...."
    v.visit_literal(node)
    out = v.stream.getvalue()
    assert out == "....\nliteral content\n....\n"


# ---------------------------------------------------------------------------
# visit_span — unrecognized variant fallback
# ---------------------------------------------------------------------------


def test_visit_span_unrecognized_variant_fallback():
    span = Span(variant="mark", inlines=[Text("highlighted")])
    out = _ser(span)
    # 'mark' is not in markup_map → falls through to generic inline dump
    assert "highlighted" in out


def test_visit_span_double_quoted():
    span = Span(variant="double", inlines=[Text("quoted")])
    out = _ser(span)
    assert "quoted" in out


def test_visit_span_unconstrained_strong():
    span = Span(variant="strong", form="unconstrained", inlines=[Text("bold")])
    out = _ser(span)
    assert out == "**bold**"


# ---------------------------------------------------------------------------
# visit_ref — all branches
# ---------------------------------------------------------------------------


def test_visit_ref_link_bare_role():
    ref = Ref(variant="link", target="https://example.com", inlines=[Text("example")])
    ref.attributes["role"] = "bare"
    out = _ser(ref)
    assert out == "https://example.com"


def test_visit_ref_link_bare_mailto():
    ref = Ref(
        variant="link", target="mailto:user@example.com", inlines=[Text("user")]
    )
    ref.attributes["role"] = "bare"
    out = _ser(ref)
    assert out == "user@example.com"


def test_visit_ref_link_uri_no_inlines():
    """URI with no inlines and no attrs → write target directly."""
    ref = Ref(variant="link", target="https://example.com", inlines=[])
    out = _ser(ref)
    assert out == "https://example.com"


def test_visit_ref_link_non_uri_target():
    """Non-URI target (relative path) → prefix with 'link:'."""
    ref = Ref(
        variant="link", target="./docs/guide.html", inlines=[Text("Guide")]
    )
    out = _ser(ref)
    assert out.startswith("link:./docs/guide.html[")
    assert "Guide" in out


def test_visit_ref_link_with_window_blank():
    ref = Ref(
        variant="link", target="https://example.com", inlines=[Text("Visit")]
    )
    ref.attributes["window"] = "_blank"
    out = _ser(ref)
    assert "^" in out
    assert "Visit" in out


def test_visit_ref_xref_with_label():
    ref = Ref(variant="xref", target="section-id", inlines=[Text("Section")])
    out = _ser(ref)
    assert out == "<<section-id, Section>>"


def test_visit_ref_xref_no_label():
    ref = Ref(variant="xref", target="section-id", inlines=[])
    out = _ser(ref)
    assert out == "<<section-id>>"


def test_visit_ref_footnote_no_target():
    ref = Ref(variant="footnote", target="", inlines=[Text("Footnote text")])
    out = _ser(ref)
    assert out == "footnote:[Footnote text]"


def test_visit_ref_footnote_with_target_and_label():
    ref = Ref(variant="footnote", target="fn-1", inlines=[Text("Named footnote")])
    out = _ser(ref)
    assert out.startswith("footnoteref:[fn-1")
    assert "Named footnote" in out


def test_visit_ref_footnote_with_target_no_label():
    ref = Ref(variant="footnote", target="fn-1", inlines=[])
    out = _ser(ref)
    assert out == "footnoteref:[fn-1]"


# ---------------------------------------------------------------------------
# visit_image — block form
# ---------------------------------------------------------------------------


def test_visit_image_block_form():
    img = Image(target="diagram.png", alt="A diagram", form="macro", type="block")
    out = _ser(img)
    assert out == "image::diagram.png[A diagram]\n"


def test_visit_image_inline_form():
    img = Image(target="icon.png", alt="icon", form="macro", type="inline")
    out = _ser(img)
    assert out == "image:icon.png[icon]"


# ---------------------------------------------------------------------------
# visit_audio / visit_video
# ---------------------------------------------------------------------------


def test_visit_audio():
    node = Node()
    node.name = "audio"
    node.target = "speech.mp3"
    v = AsciiDocSerializerVisitor()
    v.visit_audio(node)
    assert v.stream.getvalue() == "audio::speech.mp3[]\n"


def test_visit_video():
    node = Node()
    node.name = "video"
    node.target = "clip.mp4"
    v = AsciiDocSerializerVisitor()
    v.visit_video(node)
    assert v.stream.getvalue() == "video::clip.mp4[]\n"


# ---------------------------------------------------------------------------
# visit_kbd / visit_button / visit_menu
# ---------------------------------------------------------------------------


def test_visit_kbd():
    kbd = Kbd(["Ctrl", "Shift", "T"])
    out = _ser(kbd)
    assert out == "kbd:[Ctrl+Shift+T]"


def test_visit_button():
    btn = Button("Save")
    out = _ser(btn)
    assert out == "btn:[Save]"


def test_visit_menu_with_items():
    menu = Menu("File", ["New", "Project"])
    out = _ser(menu)
    assert out == "menu:File[New > Project]"


def test_visit_menu_no_items():
    menu = Menu("Help", [])
    out = _ser(menu)
    assert out == "menu:Help[]"


# ---------------------------------------------------------------------------
# visit_callout
# ---------------------------------------------------------------------------


def test_visit_callout():
    co = Callout(number=3)
    out = _ser(co)
    assert out == "<3>"


# ---------------------------------------------------------------------------
# visit_stem — block form
# ---------------------------------------------------------------------------


def test_visit_stem_block_form():
    v = AsciiDocSerializerVisitor()
    node = Node()
    node.name = "stem"
    node.type = "block"
    node.variant = "latexmath"
    node.value = "x^2"
    node.delimiter = "++++"
    node.attributes = {}
    node.title = None
    node.inlines = [Text("x^2")]
    v.visit_stem(node)
    out = v.stream.getvalue()
    assert "[latexmath]\n" in out
    assert "++++\n" in out
    assert "x^2" in out


def test_visit_stem_inline_form():
    node = InlineStem(variant="asciimath", value="e=mc^2")
    out = _ser(node)
    assert out == "asciimath:[e=mc^2]"


# ---------------------------------------------------------------------------
# visit_passthrough — inline triple_plus and macro forms
# ---------------------------------------------------------------------------


def test_visit_passthrough_inline_triple_plus():
    node = InlinePassthrough(value="<b>raw</b>")
    node.form = "triple_plus"
    out = _ser(node)
    assert out == "+++<b>raw</b>+++"


def test_visit_passthrough_inline_macro():
    node = InlinePassthrough(value="raw content")
    node.form = "macro"
    out = _ser(node)
    assert out == "pass:[raw content]"


def test_visit_passthrough_block_form():
    v = AsciiDocSerializerVisitor()
    node = Node()
    node.name = "passthrough"
    node.type = "block"
    node.delimiter = "++++"
    node.attributes = {}
    node.title = None
    node.inlines = [Text("raw block")]
    v.visit_passthrough(node)
    out = v.stream.getvalue()
    assert "++++\n" in out
    assert "raw block" in out


# ---------------------------------------------------------------------------
# visit_admonition — delimited form and multi-block paragraph form
# ---------------------------------------------------------------------------


def test_visit_admonition_delimited_form():
    adm = Admonition(
        variant="warning",
        blocks=[Paragraph(inlines=[Text("Watch out")])],
        delimiter="====",
    )
    adm.form = "delimited"
    out = _ser(adm)
    assert "[WARNING]\n" in out
    assert "====\n" in out
    assert "Watch out" in out


def test_visit_admonition_paragraph_form_multi_block():
    """Paragraph-form admonition with extra blocks uses '+' continuation."""
    adm = Admonition(
        variant="note",
        blocks=[
            Paragraph(inlines=[Text("First.")]),
            Paragraph(inlines=[Text("Second.")]),
        ],
        delimiter=None,
    )
    out = _ser(adm)
    assert "NOTE: First.\n" in out
    assert "+\n" in out
    assert "Second." in out


# ---------------------------------------------------------------------------
# visit_listitem — nested list continuation (no '+' prefix for sub-lists)
# ---------------------------------------------------------------------------


def test_visit_listitem_checked_true():
    item = ListItem(marker="*", principal=[Text("done")], checked=True)
    out = _ser(item)
    assert "* [x] done\n" == out


def test_visit_listitem_checked_false():
    item = ListItem(marker="*", principal=[Text("todo")], checked=False)
    out = _ser(item)
    assert "* [ ] todo\n" == out


def test_visit_listitem_nested_list_no_continuation():
    """A nested ASTList block must NOT get a '+' prefix."""
    nested = ASTList(variant="unordered", marker="**")
    nested_item = ListItem(marker="**", principal=[Text("child")])
    nested.items = [nested_item]
    parent = ListItem(marker="*", principal=[Text("parent")], blocks=[nested])
    out = _ser(parent)
    assert "+\n" not in out
    assert "** child\n" in out


def test_visit_listitem_continuation_block():
    """A non-list block in a listitem must get a '+' prefix."""
    para = Paragraph(inlines=[Text("continuation")])
    item = ListItem(marker="*", principal=[Text("main")], blocks=[para])
    out = _ser(item)
    assert "+\n" in out
    assert "continuation" in out


# ---------------------------------------------------------------------------
# visit_cell — rowspan, align, valign, style specifiers
# ---------------------------------------------------------------------------


def test_visit_cell_rowspan_only():
    cell = TableCell(blocks=[Paragraph(inlines=[Text("data")])])
    cell.colspan = 1
    cell.rowspan = 3
    cell.align = None
    cell.valign = None
    cell.style = None
    out = _ser(cell)
    assert "1.3+" in out


def test_visit_cell_colspan_only():
    cell = TableCell(blocks=[Paragraph(inlines=[Text("data")])])
    cell.colspan = 2
    cell.rowspan = 1
    cell.align = None
    cell.valign = None
    cell.style = None
    out = _ser(cell)
    assert "2+" in out


def test_visit_cell_align_and_valign():
    cell = TableCell(blocks=[Paragraph(inlines=[Text("data")])])
    cell.colspan = 1
    cell.rowspan = 1
    cell.align = "center"
    cell.valign = "middle"
    cell.style = None
    out = _ser(cell)
    assert "^" in out  # center align
    assert ".^" in out  # middle valign


def test_visit_cell_style_emphasis():
    cell = TableCell(blocks=[Paragraph(inlines=[Text("em")])])
    cell.colspan = 1
    cell.rowspan = 1
    cell.align = None
    cell.valign = None
    cell.style = "emphasis"
    out = _ser(cell)
    assert "e" in out  # style_map["emphasis"] = "e"


def test_visit_cell_multiple_blocks():
    """Cells with >1 block must visit each block individually (not strip para newline)."""
    cell = TableCell(
        blocks=[
            Paragraph(inlines=[Text("block one")]),
            Paragraph(inlines=[Text("block two")]),
        ]
    )
    cell.colspan = 1
    cell.rowspan = 1
    cell.align = None
    cell.valign = None
    cell.style = None
    out = _ser(cell)
    assert "block one" in out
    assert "block two" in out
    assert "\n\n" in out  # separator between multiple blocks


# ---------------------------------------------------------------------------
# visit_descriptionlistitem — multiple blocks with '+' continuation
# ---------------------------------------------------------------------------


def test_visit_descriptionlistitem_multiple_blocks():
    term = DescriptionListTerm(inlines=[Text("Term")])
    item = DescriptionListItem(
        terms=[term],
        blocks=[
            Paragraph(inlines=[Text("First block")]),
            Paragraph(inlines=[Text("Second block")]),
        ],
    )
    out = _ser(item)
    assert "Term::\n" in out
    assert "+\n" in out
    assert "Second block" in out


# ---------------------------------------------------------------------------
# generic_visit fallback
# ---------------------------------------------------------------------------


def test_generic_visit_fallback():
    """generic_visit must recurse into child collections."""

    class CustomNode(Node):
        def get_child_collections(self):
            return {"inlines": [Text("child text")]}

    node = CustomNode()
    out = _ser(node)
    assert "child text" in out


# ---------------------------------------------------------------------------
# serialize_to_asciidoc — preprocessed document warning
# ---------------------------------------------------------------------------


def test_serialize_preprocessed_warning():
    import warnings

    doc = Document(blocks=[Paragraph(inlines=[Text("content")])])
    doc.is_preprocessed = True
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        serialize_to_asciidoc(doc)
    assert len(w) == 1
    assert issubclass(w[0].category, UserWarning)
    assert "preprocessed" in str(w[0].message).lower()
