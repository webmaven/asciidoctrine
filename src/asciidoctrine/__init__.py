"""AsciiDoctrine: Pure-Python AsciiDoc parser library using Lark.

AsciiDoctrine provides a structured, type-safe representation of AsciiDoc documents.
Core features include:
- `parse_to_ast()`: Parse raw AsciiDoc source code into a syntax-level AST.
- `ASGResolver`: Resolve AST trees into spec-compliant Abstract Semantic Graphs (ASG).
- `WorkspaceCatalog`: Index symbols and target anchors across multi-document workspaces.
- `WorkspaceBuilder`: Orchestrate multi-pass directory parsing and cross-reference resolution.
- `serialize_to_asciidoc()`: Losslessly serialize AST nodes back to AsciiDoc text.
"""

from .lark_parser import AsciiDocSyntaxError, parse_to_ast
from .nodes import (
    Docinfo,
    Document,
    Node,
    NodeTransformer,
    NodeVisitor,
    Paragraph,
    Section,
    Text,
)
from .resolver import ASGResolver, WorkspaceBuilder, WorkspaceCatalog
from .serializer import serialize_to_asciidoc

__version__ = "0.1.0a12"

__all__ = [
    "parse_to_ast",
    "AsciiDocSyntaxError",
    "serialize_to_asciidoc",
    "Node",
    "Docinfo",
    "Document",
    "Section",
    "Paragraph",
    "Text",
    "NodeVisitor",
    "NodeTransformer",
    "ASGResolver",
    "WorkspaceCatalog",
    "WorkspaceBuilder",
]
