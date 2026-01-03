"""
Converts the AsciiDoc AST to a Docutils document tree.
"""

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.utils import new_document

from . import nodes as ast_nodes


def _get_node_text(node):
    """
    Recursively extracts the raw text from an AST node and its children.
    """
    if isinstance(node, ast_nodes.Text):
        return node.text
    text = ""
    if hasattr(node, 'children'):
        for child in node.children:
            text += _get_node_text(child)
    return text


class DocutilsVisitor(ast_nodes.NodeVisitor):
    """
    Visits the AsciiDoc AST and builds a Docutils document tree.
    """
    def __init__(self, document):
        self.document = document

    def visit(self, node, parent_node=None):
        """
        Overrides the base visit method to pass the parent_node.
        """
        if parent_node is None:
            parent_node = self.document

        method_name = f'visit_{node.__class__.__name__.lower()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, parent_node=parent_node)

    def generic_visit(self, node, parent_node):
        """
        Generic visitor for nodes that don't have a specific visit method.
        This simply visits the children of the node.
        """
        for child in node.children:
            self.visit(child, parent_node=parent_node)

    def visit_document(self, node: ast_nodes.Document, parent_node):
        if node.header:
            self.visit(node.header, parent_node=parent_node)
        for child in node.children:
            self.visit(child, parent_node=parent_node)

    def visit_header(self, node: ast_nodes.Header, parent_node):
        if node.title:
            self.visit(node.title, parent_node=parent_node)

        # Author, revision, etc. go into a docinfo block.
        docinfo = nodes.docinfo()
        if node.author:
            self.visit(node.author, parent_node=docinfo)
        if node.revision:
            self.visit(node.revision, parent_node=docinfo)

        if docinfo.children:
            # Prepend docinfo to the document body
            parent_node.insert(0, docinfo)

    def visit_title(self, node: ast_nodes.Title, parent_node):
        title = nodes.title()
        parent_node += title
        for child in node.children:
            self.visit(child, parent_node=title)

    def visit_author(self, node: ast_nodes.Author, parent_node):
        author = nodes.author()
        parent_node += author
        for child in node.children:
            self.visit(child, parent_node=author)

    def visit_revision(self, node: ast_nodes.Revision, parent_node):
        revision = nodes.revision()
        parent_node += revision
        for child in node.children:
            self.visit(child, parent_node=revision)

    def visit_section(self, node: ast_nodes.Section, parent_node):
        section_title_text = _get_node_text(node.title_node)
        section_id = nodes.make_id(section_title_text)

        section = nodes.section()
        section['ids'].append(section_id)
        parent_node += section

        self.visit(node.title_node, parent_node=section)
        for child in node.children:
            self.visit(child, parent_node=section)

    def visit_paragraph(self, node: ast_nodes.Paragraph, parent_node):
        para = nodes.paragraph()
        parent_node += para
        for child in node.children:
            self.visit(child, parent_node=para)

    def visit_strong(self, node: ast_nodes.Strong, parent_node):
        strong = nodes.strong()
        parent_node += strong
        for child in node.children:
            self.visit(child, parent_node=strong)

    def visit_emphasis(self, node: ast_nodes.Emphasis, parent_node):
        emphasis = nodes.emphasis()
        parent_node += emphasis
        for child in node.children:
            self.visit(child, parent_node=emphasis)

    def visit_inlinecode(self, node: ast_nodes.InlineCode, parent_node):
        literal = nodes.literal()
        parent_node += literal
        for child in node.children:
            self.visit(child, parent_node=literal)

    def visit_text(self, node: ast_nodes.Text, parent_node):
        parent_node += nodes.Text(node.text)

    def visit_literalblock(self, node: ast_nodes.LiteralBlock, parent_node):
        literal_block = nodes.literal_block(node.content, node.content)
        if 'language' in node.attributes:
            literal_block['classes'].append('code')
            literal_block['classes'].append(node.attributes['language'])
        parent_node += literal_block

    def visit_bulletlist(self, node: ast_nodes.BulletList, parent_node):
        bullet_list = nodes.bullet_list()
        parent_node += bullet_list
        for child in node.children:
            self.visit(child, parent_node=bullet_list)

    def visit_orderedlist(self, node: ast_nodes.OrderedList, parent_node):
        enumerated_list = nodes.enumerated_list()
        parent_node += enumerated_list
        for child in node.children:
            self.visit(child, parent_node=enumerated_list)

    def visit_listitem(self, node: ast_nodes.ListItem, parent_node):
        list_item = nodes.list_item()
        parent_node += list_item
        for child in node.children:
            self.visit(child, parent_node=list_item)


def asciidoc_to_docutils(source: str):
    """
    Convert AsciiDoc source string to a Docutils document.
    """
    from .lark_parser import parse_to_ast

    ast = parse_to_ast(source)

    settings = OptionParser(components=(None,)).get_default_values()
    document = new_document('<string>', settings=settings)

    visitor = DocutilsVisitor(document)
    visitor.visit(ast)

    return document
