"""
Converts the AsciiDoc AST to a Docutils document tree.
"""

from typing import Any, Dict

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.utils import new_document


def translate_ast_to_docutils(
    ast_node: Dict[str, Any], parent_node: nodes.Element
) -> None:
    node_type = ast_node.get("type")

    if node_type == "document":
        for child in ast_node.get("children", []):
            translate_ast_to_docutils(child, parent_node)

    elif node_type == "paragraph":
        para = nodes.paragraph()
        parent_node += para
        for child in ast_node.get("children", []):
            translate_ast_to_docutils(child, para)

    elif node_type == "strong":
        strong = nodes.strong()
        parent_node += strong
        for child in ast_node.get("children", []):
            translate_ast_to_docutils(child, strong)

    elif node_type == "text":
        parent_node += nodes.Text(ast_node.get("text", ""))


def asciidoc_to_docutils(source: str) -> nodes.document:
    """
    Convert AsciiDoc source string to a Docutils document.
    """
    from .lark_parser import parse_to_ast

    ast = parse_to_ast(source).to_dict()

    settings = OptionParser(components=()).get_default_values()
    document = new_document("<string>", settings=settings)

    translate_ast_to_docutils(ast, document)

    return document
