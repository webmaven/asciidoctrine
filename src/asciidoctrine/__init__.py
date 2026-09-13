"""
AsciiDoctrine: High-performance, pure-Python AsciiDoc parser and semantic processor based on Lark.

AsciiDoctrine provides a structured, type-safe representation of AsciiDoc documents.
Core features include:

* `parse_to_ast()`: Parse raw AsciiDoc source code into a syntax-level AST.
* `parse_inlines()`: Parse raw inline AsciiDoc source code into a syntax-level AST.
* `FileProvider`, `FsLoader`, `MemoryLoader`: Abstract and virtual filesystem loaders for hermetic parsing.
* `ASGResolver`: Resolve AST trees into spec-compliant Abstract Semantic Graphs (ASG).
* `resolve_to_ast()`: Resolve semantic elements and attributes in-place on an AST Document.
* `WorkspaceCatalog`: Index symbols and target anchors across multi-document workspaces.
* `WorkspaceBuilder`: Orchestrate multi-pass directory or in-memory parsing and cross-reference resolution.
* `clear_parser_cache()`: Clear compiled Lark parser instances.
* `clear_ast_cache()`: Clear the in-process LRU cache for snippet ASTs.
* `serialize_to_asciidoc()`: Losslessly serialize AST nodes back to AsciiDoc text.
* `dumps()`: Convenience wrapper around `serialize_to_asciidoc()`.
* `loads()`: Convenience wrapper around `parse_to_ast()`.
"""

from typing import Any

from .lark_parser import (
    AsciiDocSyntaxError,
    clear_ast_cache,
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
from .resolver import (
    ASGResolver,
    WorkspaceBuilder,
    WorkspaceCatalog,
    resolve_to_ast,
)
from .serializer import serialize_to_asciidoc

__version__ = "0.2.0a7"


def dumps(doc: Document) -> str:
    """
    Serialize an AST Document node back to its AsciiDoc string representation.

    Convenience wrapper around `serialize_to_asciidoc`.

    *Parameters:*

    `doc`:: The `Document` AST instance to serialize.

    *Returns:*

    A string containing the serialized AsciiDoc markup representation.

    *Example:*

    [source,python]
    ----
    import asciidoctrine

    doc = asciidoctrine.loads("= Document Title\\n\\nFirst paragraph.")
    text = asciidoctrine.dumps(doc)
    assert "= Document Title" in text
    ----
    """
    return serialize_to_asciidoc(doc)


def loads(source: str, **kwargs: Any) -> Document:
    """
    Parse an AsciiDoc source string into a syntax-level AST Document.

    Convenience wrapper around `parse_to_ast`.

    *Parameters:*

    `source`:: The raw AsciiDoc source text to parse.
    `**kwargs`:: Optional configuration keyword arguments forwarded to `parse_to_ast` (e.g. `strict`, `line_ending`).

    *Returns:*

    A `Document` AST node representing the parsed structure.

    *Example:*

    [source,python]
    ----
    import asciidoctrine

    doc = asciidoctrine.loads("= Document Title\\n\\nFirst paragraph.")
    assert doc.name == "document"
    assert len(doc.blocks) == 1
    ----
    """
    return parse_to_ast(source, **kwargs)


__all__ = [
    "__version__",
    "dumps",
    "loads",
    "parse_to_ast",
    "parse_inlines",
    "get_document_parser",
    "get_inline_parser",
    "clear_parser_cache",
    "clear_ast_cache",
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
    "resolve_to_ast",
    "WorkspaceCatalog",
    "WorkspaceBuilder",
]
