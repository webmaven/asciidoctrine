from __future__ import annotations

from typing import Any, Dict, Iterator, Optional, Sequence, cast
from typing import List as PyList

"""
Custom Abstract Syntax Tree (AST) for AsciiDoc parsing.
"""


class Node:
    """Base class for all AST nodes."""

    # Controls whether self.attributes is automatically serialized in to_dict()
    _should_serialize_attributes: bool = True

    def __init__(self, children: Optional[Sequence[Node]] = None):
        self.children: PyList[Node] = list(children) if children else []
        self.name: str = "unknown"
        self.type: str = "block"
        self.attributes: Dict[str, Any] = {}
        self.title: Optional[Title] = None

    def append(self, child: Node) -> None:
        self.children.append(child)

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        """Return a mapping of collection names to lists of child nodes."""
        return {"children": self.children} if self.children else {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to ASG-compatible dictionary."""
        data: Dict[str, Any] = {"name": self.name, "type": self.type}

        # Handle simple attributes
        for attr in [
            "variant",
            "form",
            "delimiter",
            "level",
            "marker",
            "checked",
            "target",
            "value",
            "attribute_name",
        ]:
            if hasattr(self, attr):
                val = getattr(self, attr)
                if val is not None:
                    data[attr] = val

        # Handle child nodes
        for key, nodes in self.get_child_collections().items():
            data[key] = [n.to_dict() for n in nodes]

        if hasattr(self, "title") and self.title:
            if hasattr(self.title, "to_list"):
                data["title"] = getattr(self.title, "to_list")()
            elif isinstance(self.title, list):
                data["title"] = [n.to_dict() for n in self.title]

        if self.attributes and self._should_serialize_attributes:
            data["attributes"] = self.attributes

        return data

    def walk(self) -> Iterator[Node]:
        """Walk the AST, yielding each node."""
        yield self
        for collection in self.get_child_collections().values():
            for child in collection:
                yield from child.walk()


class InlineNode(Node):
    """A base class for nodes that represent inline content, such as text formatting."""

    def append(self, child: Node) -> None:
        self.inlines.append(child)  # type: ignore[attr-defined]


class BlockNode(Node):
    """A base class for nodes that represent block-level content, such as
    paragraphs or lists."""

    def append(self, child: Node) -> None:
        self.blocks.append(child)  # type: ignore[attr-defined]


class Document(BlockNode):
    """The root node of the entire AsciiDoc document AST."""

    _should_serialize_attributes = False

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(self, blocks: Optional[Sequence[Node]] = None):
        super().__init__()
        self.name = "document"
        self.type = "block"
        self.blocks: PyList[Node] = list(blocks) if blocks else []
        self.header: Optional[Header] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize document with header and resolved attributes."""
        data = super().to_dict()
        if self.attributes or self.header:
            resolved_attrs = {}
            for k, v in self.attributes.items():
                if isinstance(v, list):
                    resolved_attrs[k] = "".join(
                        [
                            getattr(n, "value", "") if hasattr(n, "value") else ""
                            for n in v
                        ]
                    )
                else:
                    resolved_attrs[k] = str(v)
            data["attributes"] = resolved_attrs

        if self.header:
            data["header"] = self.header.to_dict()
        return data


class Title(InlineNode):
    """Represents the title of a document or a section."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(self, inlines: Optional[Sequence[Node]] = None):
        super().__init__()
        self.name = "title"
        self.type = "inline"
        self.inlines: PyList[Node] = list(inlines) if inlines else []

    def to_list(self) -> PyList[Dict[str, Any]]:
        """Return the list of serialized inlines."""
        return [n.to_dict() for n in self.inlines]


class Author(InlineNode):
    """Represents an author entry in the document header."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(self, inlines: Optional[Sequence[Node]] = None):
        super().__init__()
        self.name = "author"
        self.type = "inline"
        self.inlines: PyList[Node] = list(inlines) if inlines else []


class Revision(BlockNode):
    """Represents a revision entry in the document header."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(self, inlines: Optional[Sequence[Node]] = None):
        super().__init__()
        self.name = "revision"
        self.type = "block"
        self.value: str = ""
        self.inlines: PyList[Node] = list(inlines) if inlines else []

    def append(self, child: Node) -> None:
        self.inlines.append(child)


class Header(Node):
    """A container for the document's header metadata."""

    _should_serialize_attributes = False

    def __init__(
        self,
        title: Optional[Title] = None,
        authors: Optional[PyList[Author]] = None,
        revision: Optional[Revision] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.name = "header"
        self.type = "block"
        self.title = title
        self.authors = authors or []
        self.revision = revision
        self.attributes = attributes or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize header metadata."""
        header_data: Dict[str, Any] = {}
        if self.title:
            header_data["title"] = [n.to_dict() for n in self.title.inlines]
        if self.authors:
            authors_list = []
            for author in self.authors:
                fullname = "".join(
                    [
                        getattr(n, "value", "")
                        for n in author.inlines
                        if hasattr(n, "value")
                    ]
                )
                authors_list.append({"fullname": fullname})
            header_data["authors"] = authors_list
        if self.revision:
            value = "".join(
                [
                    getattr(n, "value", "")
                    for n in self.revision.inlines
                    if hasattr(n, "value")
                ]
            )
            header_data["revision"] = {
                "name": "revision",
                "type": "block",
                "value": value,
            }
        return header_data


class Section(BlockNode):
    """Represents a structural section of the document."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self, level: int, title: Title, blocks: Optional[Sequence[Node]] = None
    ):
        super().__init__()
        self.name = "section"
        self.type = "block"
        self.level = level
        self.title = title
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class Paragraph(BlockNode):
    """A block-level node representing a paragraph of text."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(self, inlines: Optional[Sequence[Node]] = None):
        super().__init__()
        self.name = "paragraph"
        self.type = "block"
        self.inlines: PyList[Node] = list(inlines) if inlines else []

    def append(self, child: Node) -> None:
        self.inlines.append(child)


class Text(InlineNode):
    """A leaf node representing a segment of plain text."""

    def __init__(self, value: str):
        super().__init__()
        self.name = "text"
        self.type = "string"
        self.value = value


class Span(InlineNode):
    """An inline node for formatted text (bold, italic, code)."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(
        self,
        variant: str,
        inlines: Optional[Sequence[Node]] = None,
        form: str = "constrained",
    ):
        super().__init__()
        self.name = "span"
        self.type = "inline"
        self.variant = variant
        self.form = form
        self.inlines: PyList[Node] = list(inlines) if inlines else []


class Ref(InlineNode):
    """An inline node for a hyperlink or cross-reference."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(
        self, variant: str, target: str, inlines: Optional[PyList[Node]] = None
    ):
        super().__init__()
        self.name = "ref"
        self.type = "inline"
        self.variant = variant
        self.target = target
        self.inlines: PyList[Node] = list(inlines) if inlines else []


class Image(BlockNode):
    """A block or inline node for an image directive."""

    _should_serialize_attributes = False

    def __init__(
        self, target: str, alt: str = "", form: str = "macro", type: str = "block"
    ):
        super().__init__()
        self.name = "image"
        self.type = type
        self.target = target
        self.form = form
        self.attributes = {"alt": alt}


class List(BlockNode):
    """A block node representing a list (ordered or unordered)."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"items": cast(PyList[Node], self.items)}

    def __init__(
        self,
        variant: str,
        marker: str,
        items: Optional[Sequence[ListItem]] = None,
    ):
        super().__init__()
        self.name = "list"
        self.type = "block"
        self.variant = variant
        self.marker = marker
        self.items: PyList[ListItem] = list(items) if items else []

    def append(self, child: Node) -> None:
        if isinstance(child, ListItem):
            self.items.append(child)
        else:
            super().append(child)


class ListItem(BlockNode):
    """A node representing a single item within a list. It can contain blocks."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"principal": self.principal, "blocks": self.blocks}

    def __init__(
        self,
        marker: str,
        principal: Optional[Sequence[Node]] = None,
        blocks: Optional[Sequence[Node]] = None,
        checked: Optional[bool] = None,
    ):
        super().__init__()
        self.name = "listItem"
        self.type = "block"
        self.marker = marker
        self.principal: PyList[Node] = list(principal) if principal else []
        self.blocks: PyList[Node] = list(blocks) if blocks else []
        self.checked = checked


class Listing(BlockNode):
    """A block for preformatted text, typically used for code listings."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(
        self,
        inlines: Optional[Sequence[Node]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        delimiter: str = "----",
    ):
        super().__init__()
        self.name = "listing"
        self.type = "block"
        self.form = "delimited"
        self.delimiter = delimiter
        self.inlines: PyList[Node] = list(inlines) if inlines else []
        self.attributes = attributes or {}

    def append(self, child: Node) -> None:
        self.inlines.append(child)


class Example(BlockNode):
    """A block for content that should be rendered as an example."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self, blocks: Optional[Sequence[Node]] = None, delimiter: str = "===="
    ):
        super().__init__()
        self.name = "example"
        self.type = "block"
        self.form = "delimited"
        self.delimiter = delimiter
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class Quote(BlockNode):
    """A block representing a quotation."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(self, blocks: Optional[Sequence[Node]] = None):
        super().__init__()
        self.name = "quote"
        self.type = "block"
        self.form = "delimited"
        self.delimiter = "____"
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class Admonition(BlockNode):
    """A block for admonitions like NOTE, TIP, IMPORTANT, etc."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self,
        variant: str,
        blocks: Optional[Sequence[Node]] = None,
        delimiter: str = "====",
    ):
        super().__init__()
        self.name = "admonition"
        self.type = "block"
        self.variant = variant
        self.form = "delimited"
        self.delimiter = delimiter
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class Sidebar(BlockNode):
    """A block for content that is separate from the main flow of text."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self, blocks: Optional[Sequence[Node]] = None, delimiter: str = "****"
    ):
        super().__init__()
        self.name = "sidebar"
        self.type = "block"
        self.form = "delimited"
        self.delimiter = delimiter
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class Table(BlockNode):
    """A node representing a table."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"rows": cast(PyList[Node], self.rows)}

    def __init__(self, rows: Optional[Sequence[TableRow]] = None) -> None:
        super().__init__()
        self.name = "table"
        self.type = "block"
        self.rows: PyList[TableRow] = list(rows) if rows else []

    def append(self, child: Node) -> None:
        if isinstance(child, TableRow):
            self.rows.append(child)
        else:
            super().append(child)



class TableRow(Node):
    """A node representing a single row in a table."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"cells": cast(PyList[Node], self.cells)}

    def __init__(self, cells: Optional[Sequence[TableCell]] = None) -> None:
        super().__init__()
        self.name = "row"
        self.type = "block"
        self.cells: PyList[TableCell] = list(cells) if cells else []

    def append(self, child: Node) -> None:
        if isinstance(child, TableCell):
            self.cells.append(child)
        else:
            super().append(child)



class TableCell(BlockNode):
    """A node representing a single cell in a table row."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(self, blocks: Optional[Sequence[Node]] = None):
        super().__init__()
        self.name = "cell"
        self.type = "block"
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class ThematicBreak(BlockNode):
    """Represents a horizontal rule or thematic break (---, ***, ''')."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "thematic_break"
        self.type = "block"


class PageBreak(BlockNode):
    """Represents a page break (<<<)."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "page_break"
        self.type = "block"


class AttributeEntry(Node):
    """A node representing an attribute declaration in the document header."""

    def __init__(self, name: str, value: str):
        super().__init__()
        self.name = "attribute_entry"
        self.type = "block"
        self.attribute_name = name
        self.value = value


class Include(Node):
    """A node representing an `include::` directive."""

    def __init__(self, filename: str):
        super().__init__()
        self.name = "include"
        self.type = "block"
        self.filename = filename


class NodeVisitor:
    """A base class for implementing the visitor pattern to traverse the AST."""

    def visit(self, node: Node, **kwargs: Any) -> Any:
        method_name = f"visit_{node.name.lower()}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, **kwargs)

    def generic_visit(self, node: Node, **kwargs: Any) -> Any:
        for collection in node.get_child_collections().values():
            for child in collection:
                self.visit(child, **kwargs)
