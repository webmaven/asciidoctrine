import pytest

import asciidoctrine
from asciidoctrine.nodes import (
    Audio,
    Button,
    Callout,
    Comment,
    Docinfo,
    Document,
    Kbd,
    Listing,
    Literal,
    Menu,
    NodeVisitor,
    PageBreak,
    Paragraph,
    Passthrough,
    Stem,
    Text,
    ThematicBreak,
    Title,
    Toc,
    Video,
)

pytestmark = pytest.mark.unit


def test_package_init_exports():
    assert hasattr(asciidoctrine, "__version__")
    assert hasattr(asciidoctrine, "parse_to_ast")
    assert hasattr(asciidoctrine, "serialize_to_asciidoc")
    assert hasattr(asciidoctrine, "MemoryLoader")
    assert hasattr(asciidoctrine, "FsLoader")
    assert hasattr(asciidoctrine, "ASGResolver")


def test_node_to_dict_and_properties():
    docinfo = Docinfo(head_content="<meta>", footer_content="<footer>")
    assert docinfo.to_dict()["head_content"] == "<meta>"
    assert docinfo.to_dict()["footer_content"] == "<footer>"

    page_break = PageBreak()
    assert page_break.name == "page_break"
    assert page_break.to_dict()["name"] == "page_break"

    thematic_break = ThematicBreak()
    assert thematic_break.name == "thematic_break"
    assert thematic_break.to_dict()["name"] == "thematic_break"

    toc = Toc(attributes={"levels": "3"})
    assert toc.name == "toc"

    pass_block = Passthrough(delimiter="++++", inlines=[Text("raw pass")])
    assert pass_block.name == "passthrough"

    stem = Stem(variant="latexmath", inlines=[Text("sqrt(4)")])
    assert stem.name == "stem"

    audio = Audio(target="sound.mp3")
    assert audio.name == "audio"
    assert audio.target == "sound.mp3"

    video = Video(target="movie.mp4")
    assert video.name == "video"
    assert video.target == "movie.mp4"

    button = Button(label="Submit")
    assert button.name == "button"
    assert button.value == "Submit"

    menu = Menu(menu="File", items=["Export", "PDF"])
    assert menu.name == "menu"
    assert menu.menu == "File"
    assert menu.items == ["Export", "PDF"]

    kbd = Kbd(keys=["Ctrl", "C"])
    assert kbd.name == "kbd"
    assert kbd.value == ["Ctrl", "C"]

    callout = Callout(number=1)
    assert callout.name == "callout"
    assert callout.value == 1

    comment = Comment(value="a comment")
    assert comment.name == "comment"
    assert comment.value == "a comment"

    # Listing accessors
    listing = Listing(delimiter="----")
    listing.id = "my-code"
    assert listing.id == "my-code"
    listing.language = "python"
    assert listing.language == "python"
    listing.style = "source"
    assert listing.style == "source"
    listing.title = Title(inlines=[Text("My Listing")])
    assert listing.listing_title == "My Listing"

    # Literal accessors
    literal = Literal(delimiter="....")
    literal.id = "my-literal"
    assert literal.id == "my-literal"
    literal.style = "literal"
    assert literal.style == "literal"
    literal.title = Title(inlines=[Text("My Literal")])
    assert literal.literal_title == "My Literal"


def test_node_visitor_base():
    class SimpleVisitor(NodeVisitor):
        def __init__(self):
            self.visited = []

        def visit_paragraph(self, node):
            self.visited.append(node.name)

    doc = Document(blocks=[Paragraph(inlines=[Text("hello")])])
    visitor = SimpleVisitor()
    visitor.visit(doc)
    assert "paragraph" in visitor.visited
