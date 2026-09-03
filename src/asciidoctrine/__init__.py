"""
AsciiDoctrine: High-performance, pure-Python AsciiDoc parser and semantic processor based on Lark.

AsciiDoctrine provides a structured, type-safe representation of AsciiDoc documents.
Core features include:

* `parse_to_ast()`: Parse raw AsciiDoc source code into a syntax-level AST.
* `parse_inlines()`: Parse raw inline AsciiDoc source code into a syntax-level AST.
* `FileProvider`, `FsLoader`, `MemoryLoader`: Abstract and virtual filesystem loaders for hermetic parsing.
* `ASGResolver`: Resolve AST trees into spec-compliant Abstract Semantic Graphs (ASG).
* `WorkspaceCatalog`: Index symbols and target anchors across multi-document workspaces.
* `WorkspaceBuilder`: Orchestrate multi-pass directory or in-memory parsing and cross-reference resolution.
* `serialize_to_asciidoc()`: Losslessly serialize AST nodes back to AsciiDoc text.
"""

from .lark_parser import (
    AsciiDocSyntaxError,
    clear_parser_cache,
    get_document_parser,
    get_inline_parser,
    parse_inlines,
    parse_to_ast,
)
from .loader import FileProvider, FsLoader, MemoryLoader
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

__version__ = "0.2.0a6"

__all__ = [
    "__version__",
    "parse_to_ast",
    "parse_inlines",
    "get_document_parser",
    "get_inline_parser",
    "clear_parser_cache",
    "AsciiDocSyntaxError",
    "serialize_to_asciidoc",
    "FileProvider",
    "FsLoader",
    "MemoryLoader",
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
