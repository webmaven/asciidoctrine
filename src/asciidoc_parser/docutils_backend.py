"""
Converts the AsciiDoc AST to a Docutils document tree.
"""

from typing import Any, Dict, List, Optional, Union, cast

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.utils import new_document

from .nodes import (
    Admonition,
    BlockNode,
    Document,
    Example,
    Header,
    Image,
    List as ASTList,
    ListItem,
    Listing,
    Node,
    NodeVisitor,
    Paragraph,
    Quote,
    Ref,
    Revision,
    Section,
    Sidebar,
    Span,
    Table,
    TableCell,
    TableRow,
    Text,
    ThematicBreak,
    Title,
)


class DocutilsRenderer(NodeVisitor):
    def __init__(self, document: nodes.document):
        self.document = document
        self.current_node: nodes.Element = document

    def visit_document(self, node: Document):
        if node.header and node.header.title:
            title = nodes.title()
            old_parent = self.current_node
            self.current_node = title
            for inline in node.header.title.inlines:
                self.visit(inline)
            self.document += title
            self.current_node = old_parent

        for block in node.blocks:
            self.visit(block)

    def visit_section(self, node: Section):
        section = nodes.section()
        # Always ensure an ID exists for Sphinx/Docutils
        if "id" in node.attributes:
            section["ids"].append(node.attributes["id"])
        self.document.set_id(section)
        
        title = nodes.title()
        old_parent = self.current_node
        self.current_node = title
        for inline in node.title.inlines:
            self.visit(inline)
        section += title
        
        self.current_node = section
        for block in node.blocks:
            self.visit(block)
        
        old_parent += section
        self.current_node = old_parent

    def visit_paragraph(self, node: Paragraph):
        para = nodes.paragraph()
        old_parent = self.current_node
        self.current_node = para
        for inline in node.inlines:
            self.visit(inline)
        old_parent += para
        self.current_node = old_parent

    def visit_text(self, node: Text):
        self.current_node += nodes.Text(node.value)

    def visit_span(self, node: Span):
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

    def visit_list(self, node: ASTList):
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

    def visit_listitem(self, node: ListItem):
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

    def visit_ref(self, node: Ref):
        # Handle cross-references and links
        ref_node = nodes.reference()
        
        # Determine URI or Reference ID
        target = node.target
        if node.variant == "link":
             ref_node["refuri"] = target
        elif node.variant == "xref":
             # If target looks like a filename without extension, assume .html for Sphinx/HTML
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

    def visit_listing(self, node: Listing):
        content = "".join([getattr(n, "value", "") for n in node.inlines if hasattr(n, "value")])
        literal = nodes.literal_block(content, content)
        if "language" in node.attributes:
            literal["classes"].append(node.attributes["language"])
        self.current_node += literal

    def visit_admonition(self, node: Admonition):
        mapping = {
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

    def visit_image(self, node: Image):
        img = nodes.image(uri=node.target, alt=node.attributes.get("alt", ""))
        self.current_node += img

    def visit_thematic_break(self, node: ThematicBreak):
        self.current_node += nodes.thematic_break()

    def visit_sidebar(self, node: Sidebar):
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
