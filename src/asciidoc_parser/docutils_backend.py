"""
Converts the AsciiDoc AST to a Docutils document tree.
"""

from typing import Any, Optional, Union

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.utils import new_document

from .nodes import (
    Admonition,
    Audio,
    Break,
    Button,
    Callout,
    CalloutList,
    CalloutListItem,
    DescriptionList,
    DescriptionListItem,
    DescriptionListTerm,
    Document,
    FloatingTitle,
    Image,
    InlineStem,
    Kbd,
    Listing,
    ListItem,
    Menu,
    NodeVisitor,
    Open,
    Paragraph,
    Passthrough,
    Quote,
    Ref,
    Section,
    Sidebar,
    Span,
    Stem,
    Table,
    TableCell,
    TableRow,
    Text,
    ThematicBreak,
    Toc,
    Verse,
    Video,
)
from .nodes import (
    List as ASTList,
)


class DocutilsRenderer(NodeVisitor):
    def __init__(self, document: nodes.document):
        self.document = document
        self.current_node: nodes.Element = document

    def visit_document(self, node: Document) -> None:
        if node.header and (header_title := node.header.title):
            title = nodes.title()
            old_parent = self.current_node
            self.current_node = title
            for inline in header_title.inlines:
                self.visit(inline)
            self.document += title
            self.current_node = old_parent

        for block in node.blocks:
            self.visit(block)

    def visit_section(self, node: Section) -> None:
        section = nodes.section()
        # Always ensure an ID exists for Sphinx/Docutils
        if "id" in node.attributes:
            section["ids"].append(node.attributes["id"])
        self.document.set_id(section)

        title = nodes.title()
        old_parent = self.current_node
        self.current_node = title
        if node.title:
            for inline in node.title.inlines:
                self.visit(inline)
        section += title

        self.current_node = section
        for block in node.blocks:
            self.visit(block)

        old_parent += section
        self.current_node = old_parent

    def visit_floatingtitle(self, node: FloatingTitle) -> None:
        rubric = nodes.rubric()
        rubric["classes"].append(f"level-{node.level}")
        old_parent = self.current_node
        self.current_node = rubric
        if node.title:
            for inline in node.title.inlines:
                self.visit(inline)
        old_parent += rubric
        self.current_node = old_parent

    def visit_paragraph(self, node: Paragraph) -> None:
        para = nodes.paragraph()
        old_parent = self.current_node
        self.current_node = para
        for inline in node.inlines:
            self.visit(inline)
        old_parent += para
        self.current_node = old_parent

    def visit_text(self, node: Text) -> None:
        self.current_node += nodes.Text(node.value)

    def visit_break(self, node: Break) -> None:
        # Simple line break. In Docutils, this is tricky within a paragraph.
        # We'll use a raw node for HTML as a common use case.
        self.current_node += nodes.raw("", "<br/>", format="html")

    def visit_kbd(self, node: Kbd) -> None:
        kbd_node = nodes.inline(classes=["kbd"])
        kbd_node += nodes.Text("+".join(node.value))
        self.current_node += kbd_node

    def visit_button(self, node: Button) -> None:
        btn_node = nodes.inline(classes=["button"])
        btn_node += nodes.Text(node.value)
        self.current_node += btn_node

    def visit_menu(self, node: Menu) -> None:
        menu_node = nodes.inline(classes=["menu"])
        text = node.menu
        if node.items:
            text += " > " + " > ".join(node.items)
        menu_node += nodes.Text(text)
        self.current_node += menu_node

    def visit_calloutlist(self, node: CalloutList) -> None:
        list_node = nodes.enumerated_list(classes=["arabic", "callout"])
        old_parent = self.current_node
        self.current_node = list_node
        for item in node.items:
            self.visit(item)
        old_parent += list_node
        self.current_node = old_parent

    def visit_calloutlistitem(self, node: CalloutListItem) -> None:
        item = nodes.list_item()
        old_parent = self.current_node
        self.current_node = item

        para = nodes.paragraph()
        self.current_node = para
        for inline in node.principal:
            self.visit(inline)
        item += para

        self.current_node = item
        for block in node.blocks:
            self.visit(block)

        old_parent += item
        self.current_node = old_parent

    def visit_callout(self, node: Callout) -> None:
        co = nodes.inline(classes=["callout"])
        co += nodes.Text(f"({node.value})")
        self.current_node += co

    def visit_span(self, node: Span) -> None:
        mapping = {
            "strong": nodes.strong,
            "emphasis": nodes.emphasis,
            "code": nodes.literal,
            "superscript": nodes.superscript,
            "subscript": nodes.subscript,
        }
        creator = mapping.get(node.variant, nodes.inline)
        span_node = creator()

        old_parent = self.current_node
        self.current_node = span_node
        for inline in node.inlines:
            self.visit(inline)
        old_parent += span_node
        self.current_node = old_parent

    def visit_list(self, node: ASTList) -> None:
        list_node: Union[nodes.bullet_list, nodes.enumerated_list]
        if node.variant == "ordered":
            list_node = nodes.enumerated_list()
        else:
            list_node = nodes.bullet_list()

        old_parent = self.current_node
        self.current_node = list_node
        for item in node.items:
            self.visit(item)
        old_parent += list_node
        self.current_node = old_parent

    def visit_table(self, node: Table) -> None:
        table = nodes.table()
        # Find max cols
        max_cols = 0
        for row in node.rows:
            max_cols = max(max_cols, len(row.cells))

        tgroup = nodes.tgroup(cols=max_cols)
        table += tgroup
        for _ in range(max_cols):
            tgroup += nodes.colspec(colwidth=1)

        tbody = nodes.tbody()
        tgroup += tbody

        old_parent = self.current_node
        self.current_node = tbody
        for row in node.rows:
            self.visit(row)
        old_parent += table
        self.current_node = old_parent

    def visit_row(self, node: TableRow) -> None:
        row = nodes.row()
        old_parent = self.current_node
        self.current_node = row
        for cell in node.cells:
            self.visit(cell)
        old_parent += row
        self.current_node = old_parent

    def visit_cell(self, node: TableCell) -> None:
        entry = nodes.entry()
        old_parent = self.current_node
        self.current_node = entry
        for block in node.blocks:
            self.visit(block)
        old_parent += entry
        self.current_node = old_parent

    def visit_listitem(self, node: ListItem) -> None:
        item = nodes.list_item()
        old_parent = self.current_node
        self.current_node = item

        if node.principal:
            para = nodes.paragraph()
            self.current_node = para
            for inline in node.principal:
                self.visit(inline)
            item += para
            self.current_node = item

        for block in node.blocks:
            self.visit(block)

        old_parent += item
        self.current_node = old_parent

    def visit_descriptionlist(self, node: DescriptionList) -> None:
        list_node = nodes.definition_list()
        old_parent = self.current_node
        self.current_node = list_node
        for item in node.items:
            self.visit(item)
        old_parent += list_node
        self.current_node = old_parent

    def visit_descriptionlistitem(self, node: DescriptionListItem) -> None:
        item = nodes.definition_list_item()
        for term in node.terms:
            self.visit(term, parent=item)

        definition = nodes.definition()
        old_parent = self.current_node
        self.current_node = definition
        for block in node.blocks:
            self.visit(block)

        item += definition
        old_parent += item
        self.current_node = old_parent

    def visit_descriptionlistterm(
        self, node: DescriptionListTerm, **kwargs: Any
    ) -> None:
        term = nodes.term()
        old_parent = self.current_node
        self.current_node = term
        for inline in node.inlines:
            self.visit(inline)

        if "parent" in kwargs:
            kwargs["parent"] += term
        else:
            old_parent += term
        self.current_node = old_parent

    def visit_ref(self, node: Ref) -> None:
        # Handle cross-references and links
        ref_node = nodes.reference()

        # Determine URI or Reference ID
        target = node.target
        if node.variant == "link":
            ref_node["refuri"] = target
        elif node.variant == "xref":
            # If target looks like a filename without extension, assume .html for
            # Sphinx/HTML
            if "." not in target and "/" not in target:
                target = target + ".html"
            else:
                target = target.replace(".adoc", ".html")
            ref_node["refuri"] = target
        else:
            ref_node["refuri"] = target

        old_parent = self.current_node
        self.current_node = ref_node
        for inline in node.inlines:
            self.visit(inline)
        old_parent += ref_node
        self.current_node = old_parent

    def visit_listing(self, node: Listing) -> None:
        content = "".join(
            [getattr(n, "value", "") for n in node.inlines if hasattr(n, "value")]
        )
        literal = nodes.literal_block(content, content)
        if "language" in node.attributes:
            literal["classes"].append(node.attributes["language"])
        self.current_node += literal

    def visit_passthrough(self, node: Passthrough) -> None:
        content = "".join(
            [getattr(n, "value", "") for n in node.inlines if hasattr(n, "value")]
        )
        # Using raw node for passthrough
        self.current_node += nodes.raw("", content, format="html")

    def visit_stem(self, node: Stem) -> None:
        content = "".join(
            [getattr(n, "value", "") for n in node.inlines if hasattr(n, "value")]
        )
        math_block = nodes.math_block(content, content)
        math_block["classes"].append(node.variant)
        self.current_node += math_block

    def visit_inlinestem(self, node: InlineStem) -> None:
        math = nodes.math(node.value, node.value)
        math["classes"].append(node.variant)
        self.current_node += math

    def visit_admonition(self, node: Admonition) -> None:
        mapping: Any = {
            "note": nodes.note,
            "tip": nodes.tip,
            "important": nodes.important,
            "warning": nodes.warning,
            "caution": nodes.caution,
        }
        creator = mapping.get(node.variant, nodes.admonition)
        adm = creator()

        old_parent = self.current_node
        self.current_node = adm
        for block in node.blocks:
            self.visit(block)
        old_parent += adm
        self.current_node = old_parent

    def visit_image(self, node: Image) -> None:
        img = nodes.image(uri=node.target, alt=node.attributes.get("alt", ""))
        self.current_node += img

    def visit_quote(self, node: Quote) -> None:
        bq = nodes.block_quote()
        old_parent = self.current_node
        self.current_node = bq
        for block in node.blocks:
            self.visit(block)
        old_parent += bq
        self.current_node = old_parent

    def visit_verse(self, node: Verse) -> None:
        # Verse is often rendered as a block quote with preserved line breaks
        bq = nodes.block_quote()
        bq["classes"].append("verse")
        old_parent = self.current_node
        self.current_node = bq
        for block in node.blocks:
            self.visit(block)
        old_parent += bq
        self.current_node = old_parent

    def visit_open(self, node: Open) -> None:
        if "style" in node.attributes and node.attributes["style"] == "toctree":
            try:
                from sphinx import addnodes
                toctree = addnodes.toctree()
                toctree["maxdepth"] = int(node.attributes.get("maxdepth", 1))
                toctree["caption"] = node.attributes.get("caption")
                
                # In our AST, toctree links are likely in paragraphs inside the block
                entries = []
                for block in node.blocks:
                    if isinstance(block, Paragraph):
                        # Simple implementation: each word/line is a document name
                        content = "".join(
                            [getattr(n, "value", "") for n in block.inlines]
                        )
                        for line in content.splitlines():
                            if line.strip():
                                entries.append((None, line.strip()))

                toctree["entries"] = entries
                toctree["includefiles"] = [e[1] for e in entries]
                self.current_node += toctree
                return
            except ImportError:
                # Sphinx not available, render as normal container
                pass

        container = nodes.container()
        old_parent = self.current_node
        self.current_node = container
        for block in node.blocks:
            self.visit(block)
        old_parent += container
        self.current_node = old_parent

    def visit_thematic_break(self, node: ThematicBreak) -> None:
        self.current_node += nodes.transition()

    def visit_toc(self, node: Toc) -> None:
        topic = nodes.topic(classes=["contents"])
        if "title" in node.attributes:
            topic += nodes.title("", node.attributes["title"])
        self.current_node += topic

    def visit_audio(self, node: Audio) -> None:
        # Placeholder for audio
        self.current_node += nodes.raw(
            "", f"<!-- audio: {node.target} -->", format="html"
        )

    def visit_video(self, node: Video) -> None:
        # Placeholder for video
        self.current_node += nodes.raw(
            "", f"<!-- video: {node.target} -->", format="html"
        )

    def visit_sidebar(self, node: Sidebar) -> None:
        sb = nodes.sidebar()
        if node.title:
            title = nodes.title()
            old_parent_inner = self.current_node
            self.current_node = title
            for inline in node.title.inlines:
                self.visit(inline)
            sb += title
            self.current_node = old_parent_inner

        old_parent = self.current_node
        self.current_node = sb
        for block in node.blocks:
            self.visit(block)
        old_parent += sb
        self.current_node = old_parent


def asciidoc_to_docutils(source: str, base_dir: Optional[str] = None) -> nodes.document:
    """
    Convert AsciiDoc source string to a Docutils document.
    """
    from .lark_parser import parse_to_ast

    ast = parse_to_ast(source, base_dir=base_dir)

    settings = OptionParser(components=()).get_default_values()
    document = new_document("<string>", settings=settings)

    renderer = DocutilsRenderer(document)
    renderer.visit(ast)

    return document
