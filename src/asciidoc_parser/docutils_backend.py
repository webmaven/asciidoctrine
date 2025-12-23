"""
Converts the AsciiDoc AST to a Docutils document tree.
"""

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.utils import new_document

def translate_ast_to_docutils(ast_node, parent_node):
    node_type = ast_node.get('type')

    if node_type == 'document':
        for child in ast_node.get('children', []):
            translate_ast_to_docutils(child, parent_node)

    elif node_type == 'paragraph':
        para = nodes.paragraph()
        parent_node += para
        for child in ast_node.get('children', []):
            translate_ast_to_docutils(child, para)

    elif node_type == 'strong':
        strong = nodes.strong()
        parent_node += strong
        for child in ast_node.get('children', []):
            translate_ast_to_docutils(child, strong)

    elif node_type == 'text':
        parent_node += nodes.Text(ast_node.get('text', ''))

def asciidoc_to_docutils(source: str):
    """
    Convert AsciiDoc source string to a Docutils document.
    """
    from .lark_parser import parse_to_ast
    ast = parse_to_ast(source)

    settings = OptionParser(components=(None,)).get_default_values()
    document = new_document('<string>', settings=settings)

    translate_ast_to_docutils(ast, document)

    return document
