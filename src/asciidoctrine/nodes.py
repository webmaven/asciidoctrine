from __future__ import annotations

import re
from typing import Any, Dict, Iterator, Optional, Sequence, cast
from typing import List as PyList

"""
Custom Abstract Syntax Tree (AST) for AsciiDoc parsing.
"""


class Node:
    """
    Base class for all Abstract Syntax Tree (AST) nodes in AsciiDoc.

    `Node` provides tree navigation, child collection indexing, attribute management,
    and serialization methods to convert nodes into ASG-compatible dictionaries or
    traverse them recursively.

    *Attributes:*

    `children`:: List of generic child `Node` instances.
    `name`:: Canonical node name identifier (e.g. `"document"`, `"section"`, `"paragraph"`).
    `type`:: Structural node categorization (e.g. `"block"`, `"inline"`, `"string"`, `"metadata"`).
    `attributes`:: Mapping of AsciiDoc element attributes (e.g. id, role, title, style, options).
    `title`:: Optional `Title` node or title AST representation.
    `location`:: Optional source location coordinate map containing line and column indices.

    *Example:*

    [source,python]
    ----
    from asciidoctrine.nodes import Paragraph, Text

    para = Paragraph([Text("Hello world")])
    assert para.type == "block"
    assert para.name == "paragraph"
    assert len(para.inlines) == 1
    ----
    """

    # Controls whether self.attributes is automatically serialized in to_dict()
    _should_serialize_attributes: bool = True

    def __init__(self, children: Optional[Sequence[Node]] = None):
        self.children: PyList[Node] = list(children) if children else []
        self.name: str = "unknown"
        self.type: str = "block"
        self.attributes: Dict[str, Any] = {}
        self.title: Optional[Title] = None
        self.location: Optional[PyList[Dict[str, int]]] = None

    def append(self, child: Node) -> None:
        self.children.append(child)

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        """Return a mapping of collection names to lists of child nodes."""
        return {"children": self.children} if self.children else {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to ASG-compatible dictionary."""
        data: Dict[str, Any] = {"name": self.name, "type": self.type}

        # Handle location
        if self.location:
            data["location"] = self.location

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
            "colspan",
            "rowspan",
            "align",
            "valign",
            "style",
            "attribution",
            "citetitle",
            "resolved_strategy",
            "resolved_file_target",
            "resolved_anchor_target",
            "index",
            "columns",
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
    """
    A base class for nodes that represent inline content and text formatting.

    Inline nodes represent character-level markup and inline macros, including
    spans (bold, italic, monospace, mark), references (hyperlinks, cross-references, footnotes),
    inline macros (kbd, button, menu), stem equations, and raw text segments.

    *Attributes:*

    `inlines`:: List of child inline-level `Node` instances contained within this node.
    """

    def append(self, child: Node) -> None:
        self.inlines.append(child)  # type: ignore[attr-defined]


class BlockNode(Node):
    """
    A base class for nodes that represent block-level structural content.

    Block nodes represent structural document elements such as sections, paragraphs,
    lists, delimited blocks (listings, sidebars, quotes, examples), tables, and containers.
    They encapsulate child `blocks` or principal inline sequences.

    *Attributes:*

    `blocks`:: List of child block-level `Node` instances contained within this block.
    """

    def append(self, child: Node) -> None:
        self.blocks.append(child)  # type: ignore[attr-defined]

    @property
    def has_metadata(self) -> bool:
        """Return True if this block node has attached attributes or a title."""
        return bool(self.attributes) or (getattr(self, "title", None) is not None)


class Docinfo(Node):
    """Represents header and footer injected document metadata."""

    _should_serialize_attributes = False

    def __init__(self, head_content: str = "", footer_content: str = "") -> None:
        super().__init__()
        self.name = "docinfo"
        self.type = "metadata"
        self.head_content = head_content
        self.footer_content = footer_content

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["head_content"] = self.head_content
        data["footer_content"] = self.footer_content
        return data


class Document(BlockNode):
    """
    The root node of an AsciiDoc document AST.

    `Document` encapsulates the top-level structure of an AsciiDoc file,
    including the optional document `Header` (with title, authors, revision, and document attributes),
    injected `Docinfo` metadata, body block elements, and footnotes.

    *Attributes:*

    `blocks`:: List of top-level `BlockNode` elements constituting the document body.
    `header`:: Optional `Header` node containing document title, authors, and document-level attributes.
    `docinfo`:: Optional `Docinfo` node holding injected raw HTML header/footer content.
    `base_dir`:: Base directory path used during parsing to resolve relative file includes.
    `safe_mode`:: Security confinement level (0 = unsafe, 1 = safe, 2 = server).
    `is_preprocessed`:: Boolean flag indicating if directives were expanded during preprocessing.
    `included_files`:: List of file path strings included during document preprocessing.
    `footnotes`:: List of resolved footnote dictionaries collected across the document.
    `loader`:: Optional `FileProvider` instance used to read source documents and included resources.

    *Example:*

    [source,python]
    ----
    from asciidoctrine.lark_parser import parse_to_ast

    doc = parse_to_ast("= My Document\\nAuthor Name\\n\\nFirst paragraph.")
    assert doc.name == "document"
    assert doc.header is not None
    assert len(doc.blocks) == 1
    ----
    """

    _should_serialize_attributes = False

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self,
        blocks: Optional[Sequence[Node]] = None,
        base_dir: Optional[str] = None,
        safe_mode: int = 0,
    ):
        super().__init__()
        self.name = "document"
        self.type = "block"
        self.blocks: PyList[Node] = list(blocks) if blocks else []
        self.header: Optional[Header] = None
        self.docinfo: Optional[Docinfo] = None
        self.had_trailing_newline: bool = True
        self.line_ending: str = "\n"
        self.is_preprocessed: bool = False
        self.included_files: PyList[str] = []
        self.base_dir: Optional[str] = base_dir
        self.safe_mode: int = safe_mode
        self.footnotes: PyList[Dict[str, Any]] = []
        self.loader: Optional[Any] = None

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
        if hasattr(self, "docinfo") and self.docinfo:
            data["docinfo"] = self.docinfo.to_dict()
        if hasattr(self, "footnotes") and self.footnotes:
            data["footnotes"] = self.footnotes
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


class FloatingTitle(BlockNode):
    """Represents a discrete or floating title that does not start a section."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.title.inlines} if self.title else {}

    def __init__(self, level: int, title: Title):
        super().__init__()
        self.name = "floatingTitle"
        self.type = "block"
        self.level = level
        self.title = title


class Header(Node):
    """A container for the document's header metadata."""

    _should_serialize_attributes = False

    def __init__(
        self,
        title: Optional[Title] = None,
        authors: Optional[PyList[Author]] = None,
        revision: Optional[Revision] = None,
        attributes: Optional[Dict[str, Any]] = None,
        docinfo: Optional[Docinfo] = None,
    ):
        super().__init__()
        self.name = "header"
        self.type = "block"
        self.title = title
        self.authors = authors or []
        self.revision = revision
        self.attributes = attributes or {}
        self.docinfo = docinfo

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
        if hasattr(self, "docinfo") and self.docinfo:
            header_data["docinfo"] = self.docinfo.to_dict()
        return header_data


class Section(BlockNode):
    """
    A structural section container within an AsciiDoc document.

    Sections correspond to headed sections (e.g. +== Section Title+, +=== Subsection Title+),
    storing their heading level, section title inlines, section-level metadata attributes (such as anchor IDs and roles),
    and all nested child blocks contained within the section body.

    *Attributes:*

    `level`:: 1-based integer section depth (1 = `==`, 2 = `===`, etc.).
    `title`:: Optional `Title` inline container representing the section title text.
    `blocks`:: List of child `BlockNode` instances comprising the section body and nested subsections.

    *Example:*

    [source,python]
    ----
    from asciidoctrine.lark_parser import parse_to_ast

    doc = parse_to_ast("== Getting Started\\n\\nFollow these steps.")
    section = doc.blocks[0]
    assert section.name == "section"
    assert section.level == 1
    ----
    """

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self,
        level: int,
        title: Optional[Title] = None,
        blocks: Optional[Sequence[Node]] = None,
    ):
        super().__init__()
        self.name = "section"
        self.type = "block"
        self.level = level
        self.title = title
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class Paragraph(BlockNode):
    """
    A block-level node representing a paragraph of text.

    Paragraphs are contiguous lines of text separated by blank lines or block delimiters.
    They contain a sequence of child inline nodes (formatted text spans, links, references, plain text).

    *Attributes:*

    `inlines`:: List of child `InlineNode` instances (e.g., `Text`, `Span`, `Ref`) forming the paragraph content.

    *Example:*

    [source,python]
    ----
    from asciidoctrine.nodes import Paragraph, Text

    para = Paragraph([Text("This is a paragraph.")])
    assert len(para.inlines) == 1
    ----
    """

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


class Break(InlineNode):
    """An inline node representing a hard line break."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "break"
        self.type = "inline"


class InlinePassthrough(InlineNode):
    """An inline node representing raw passthrough text."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {}

    def __init__(
        self,
        value: str,
        inlines: Optional[Sequence[Node]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.name = "passthrough"
        self.type = "inline"
        self.value = value
        self.inlines: PyList[Node] = list(inlines) if inlines else []
        self.attributes = attributes or {}
        self.form: Optional[str] = None


class Kbd(InlineNode):
    """An inline node for a keyboard shortcut."""

    def __init__(self, keys: PyList[str]):
        super().__init__()
        self.name = "kbd"
        self.type = "inline"
        self.value = keys


class Button(InlineNode):
    """An inline node for a UI button."""

    def __init__(self, label: str):
        super().__init__()
        self.name = "button"
        self.type = "inline"
        self.value = label


class Menu(InlineNode):
    """An inline node for a UI menu selection."""

    def __init__(self, menu: str, items: PyList[str]):
        super().__init__()
        self.name = "menu"
        self.type = "inline"
        self.menu = menu
        self.items = items

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["menu"] = self.menu
        data["items"] = self.items
        return data


class Callout(InlineNode):
    """An inline node representing a callout (e.g., <1>)."""

    def __init__(self, number: int):
        super().__init__()
        self.name = "callout"
        self.type = "inline"
        self.value = number


class InlineStem(InlineNode):
    """An inline node for mathematical expressions."""

    def __init__(self, variant: str, value: str):
        super().__init__()
        self.name = "stem"
        self.type = "inline"
        self.variant = variant
        self.value = value


class CalloutList(BlockNode):
    """A block node representing a list of callout descriptions."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"items": cast(PyList[Node], self.items)}

    def __init__(self, items: Optional[Sequence[CalloutListItem]] = None):
        super().__init__()
        self.name = "calloutList"
        self.type = "block"
        self.items: PyList[CalloutListItem] = list(items) if items else []

    def append(self, child: Node) -> None:
        if isinstance(child, CalloutListItem):
            self.items.append(child)
        else:
            super().append(child)


class CalloutListItem(BlockNode):
    """A node representing a single item in a callout list."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"principal": self.principal, "blocks": self.blocks}

    def __init__(
        self,
        number: int,
        principal: Optional[Sequence[Node]] = None,
        blocks: Optional[Sequence[Node]] = None,
    ):
        super().__init__()
        self.name = "calloutListItem"
        self.type = "block"
        self.marker = f"<{number}>"
        self.value = number
        self.principal: PyList[Node] = list(principal) if principal else []
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class Span(InlineNode):
    """
    An inline node representing formatted or stylized text spans.

    Spans represent text styling constructs such as strong (+*bold*+, +**bold**+),
    emphasis (+_italic_+, +__italic__+), monospaced code (+`code`+, +``code``+),
    superscript (+^super^+), subscript (+~sub~+), or custom-roled text spans (+[.role]#text#+).

    *Attributes:*

    `variant`:: Formatting style kind (e.g. `"strong"`, `"emphasis"`, `"code"`, `"superscript"`, `"subscript"`, `"mark"`).
    `form`:: Syntax boundary constraint: `"constrained"` (e.g., `*word*`) or `"unconstrained"` (e.g., `**chars**`).
    `inlines`:: List of child inline nodes nested within the formatted span.

    *Example:*

    [source,python]
    ----
    from asciidoctrine.nodes import Span, Text

    bold_span = Span(variant="strong", inlines=[Text("important")], form="constrained")
    assert bold_span.variant == "strong"
    ----
    """

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
    """
    An inline node representing hyperlinks, cross-references, and footnote references.

    `Ref` handles URL links, internal cross-references, document anchors,
    and footnote references.

    *Attributes:*

    `variant`:: The reference variant (e.g. `"link"`, `"xref"`, `"anchor"`, `"footnote"`).
    `target`:: Raw target string from source (e.g. `"https://asciidoctor.org"`, `"chapter1.adoc#intro"`, `"intro"`).
    `inlines`:: Optional child inline nodes representing custom link or reference label text.
    `resolved_strategy`:: Set by `ASGResolver` to `"same_file"` or `"cross_file"`.
    `resolved_file_target`:: Set by `ASGResolver` to the resolved target file ID.
    `resolved_anchor_target`:: Set by `ASGResolver` to the resolved target anchor or section ID.
    `target_node_instance`:: Direct live memory pointer to the resolved target `Node` AST instance. Excluded from `to_dict()` serialization to prevent circular references.
    `index`:: 1-based sequential numerical index for footnote references set by `ASGResolver`.

    *Example:*

    [source,python]
    ----
    from asciidoctrine.nodes import Ref, Text

    link = Ref(variant="link", target="https://asciidoctor.org", inlines=[Text("AsciiDoctor")])
    assert link.target == "https://asciidoctor.org"
    ----
    """

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
        self.resolved_strategy: Optional[str] = None
        self.resolved_file_target: Optional[str] = None
        self.resolved_anchor_target: Optional[str] = None
        self.target_node_instance: Optional[Node] = None
        self.index: Optional[int] = None


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


class Audio(BlockNode):
    """A block node for an audio macro."""

    def __init__(self, target: str, attributes: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.name = "audio"
        self.type = "block"
        self.target = target
        self.attributes = attributes or {}


class Video(BlockNode):
    """A block node for a video macro."""

    def __init__(self, target: str, attributes: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.name = "video"
        self.type = "block"
        self.target = target
        self.attributes = attributes or {}


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


class DescriptionList(BlockNode):
    """A block node representing a description list (term-definition pairs)."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"items": cast(PyList[Node], self.items)}

    def __init__(
        self,
        items: Optional[Sequence[DescriptionListItem]] = None,
    ):
        super().__init__()
        self.name = "descriptionList"
        self.type = "block"
        self.items: PyList[DescriptionListItem] = list(items) if items else []

    def append(self, child: Node) -> None:
        if isinstance(child, DescriptionListItem):
            self.items.append(child)
        else:
            super().append(child)


class DescriptionListItem(BlockNode):
    """A node representing a single term-description pair within a description list."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {
            "terms": cast(PyList[Node], self.terms),
            "blocks": self.blocks,
        }

    def __init__(
        self,
        terms: PyList[DescriptionListTerm],
        blocks: Optional[Sequence[Node]] = None,
    ):
        super().__init__()
        self.name = "descriptionListItem"
        self.type = "block"
        self.terms = terms
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class DescriptionListTerm(InlineNode):
    """A node representing the term part of a description list item."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(self, inlines: Optional[Sequence[Node]] = None):
        super().__init__()
        self.name = "descriptionListTerm"
        self.type = "inline"
        self.inlines: PyList[Node] = list(inlines) if inlines else []


CALLOUT_RE = re.compile(
    r"(?:\s+|^)"
    r"(?:(?P<prefix>(?://|#|;;?|--|/\*|<!--)\s*))?"
    r"(?P<markers>(?:<\d+>\s*|<\.>\s*)+)"
    r"(?P<suffix>\*/|-->)?"
    r"\s*$"
)

HTML_BARE_CALLOUT_RE = re.compile(r"(?:\s+|^)<!--\s*(?P<num>\d+|\.)\s*-->\s*$")


class VerbatimBlockMixin:
    """Mixin class for blocks containing verbatim text/code with callouts (e.g., Listing, Literal)."""

    @property
    def code(self) -> str:
        parts = []
        for child in getattr(self, "inlines", []):
            if isinstance(child, Callout):
                parts.append(f" <{child.value}>")
            elif hasattr(child, "value"):
                parts.append(str(child.value))
            elif hasattr(child, "text"):
                parts.append(str(child.text))
            else:
                for sub in child.walk():
                    if hasattr(sub, "value") and getattr(sub, "name", "") == "text":
                        parts.append(str(sub.value))
        return "".join(parts)

    @property
    def stripped_code(self) -> str:
        inlines = getattr(self, "inlines", [])
        if any(isinstance(c, Callout) for c in inlines):
            parts = []
            for child in inlines:
                if not isinstance(child, Callout):
                    if hasattr(child, "value"):
                        parts.append(str(child.value))
                    elif hasattr(child, "text"):
                        parts.append(str(child.text))
            return "".join(parts)

        lines = self.code.splitlines(keepends=True)
        stripped_lines = []
        for line in lines:
            if line.endswith("\r\n"):
                text, nl = line[:-2], "\r\n"
            elif line.endswith("\n"):
                text, nl = line[:-1], "\n"
            else:
                text, nl = line, ""

            m = CALLOUT_RE.search(text)
            if m:
                stripped_text = text[: m.start()]
            else:
                m2 = HTML_BARE_CALLOUT_RE.search(text)
                if m2:
                    stripped_text = text[: m2.start()]
                else:
                    stripped_text = text
            stripped_lines.append(stripped_text + nl)
        return "".join(stripped_lines)

    @property
    def callouts(self) -> Dict[int, PyList[int]]:
        inlines = getattr(self, "inlines", [])
        if any(isinstance(c, Callout) for c in inlines):
            callout_map: Dict[int, PyList[int]] = {}
            cur_line = 1
            for child in inlines:
                if isinstance(child, Callout):
                    val = getattr(child, "value", None)
                    if val is not None:
                        callout_map.setdefault(cur_line, []).append(int(val))
                else:
                    text_val = str(getattr(child, "value", getattr(child, "text", "")))
                    cur_line += text_val.count("\n")
            return callout_map

        lines = self.code.splitlines()
        callout_map = {}
        next_auto = 1
        for idx, line in enumerate(lines, start=1):
            m = CALLOUT_RE.search(line)
            raw_nums = []
            if m:
                markers = m.group("markers")
                raw_nums = re.findall(r"<(\d+|\.)>", markers)
            else:
                m2 = HTML_BARE_CALLOUT_RE.search(line)
                if m2:
                    raw_nums = [m2.group("num")]

            if raw_nums:
                line_callouts = []
                for num in raw_nums:
                    if num == ".":
                        line_callouts.append(next_auto)
                        next_auto += 1
                    else:
                        val = int(num)
                        line_callouts.append(val)
                        next_auto = max(next_auto, val + 1)
                callout_map[idx] = line_callouts
        return callout_map


class Listing(VerbatimBlockMixin, BlockNode):
    """
    A block-level node representing verbatim source code or preformatted listings.

    Listing blocks are enclosed in 4-or-more hyphens (+----+ or +------+) or styled with +[source,language]+.
    They preserve whitespace, provide source highlighting language metadata, and support
    embedded callout markers (+<1>+, +<2>+).

    *Attributes:*

    `inlines`:: List of child inline nodes (e.g. `Text`, `Callout`) containing the verbatim code and callouts.
    `attributes`:: Block attributes mapping, containing keys such as `"language"`, `"title"`, `"style"`, and `"id"`.
    `delimiter`:: The verbatim block delimiter string (defaults to `"----"`).
    `code`:: Property returning the full code content including callout markers.
    `stripped_code`:: Property returning code content with callout markers stripped out.
    `callouts`:: Property returning a mapping of 1-based line numbers to lists of callout integer identifiers.

    *Example:*

    [source,python]
    ----
    from asciidoctrine.lark_parser import parse_to_ast

    doc = parse_to_ast("[source,python]\\n----\\nprint('Hello') <1>\\n----")
    listing = doc.blocks[0]
    assert listing.name == "listing"
    assert listing.language == "python"
    assert 1 in listing.callouts
    ----
    """

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

    @property
    def id(self) -> Optional[str]:
        return self.attributes.get("id")

    @id.setter
    def id(self, value: Optional[str]) -> None:
        if value is None:
            self.attributes.pop("id", None)
        else:
            self.attributes["id"] = value

    @property
    def language(self) -> Optional[str]:
        return self.attributes.get("language")

    @language.setter
    def language(self, value: Optional[str]) -> None:
        if value is None:
            self.attributes.pop("language", None)
        else:
            self.attributes["language"] = value

    @property
    def style(self) -> Optional[str]:
        return self.attributes.get("style")

    @style.setter
    def style(self, value: Optional[str]) -> None:
        if value is None:
            self.attributes.pop("style", None)
        else:
            self.attributes["style"] = value

    @property
    def listing_title(self) -> Optional[str]:
        if self.title:
            parts = []
            for child in self.title.inlines:
                if hasattr(child, "value"):
                    parts.append(str(child.value))
                elif hasattr(child, "text"):
                    parts.append(str(child.text))
                else:
                    for sub in child.walk():
                        if hasattr(sub, "value") and getattr(sub, "name", "") == "text":
                            parts.append(str(sub.value))
            return "".join(parts)
        return self.attributes.get("title")


class Literal(VerbatimBlockMixin, BlockNode):
    """A block for literal text, often used for computer output."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(
        self,
        inlines: Optional[Sequence[Node]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
        form: str = "delimited",
    ):
        super().__init__()
        self.name = "literal"
        self.type = "block"
        self.form = form
        # Only set delimiter if it is provided or if form is delimited
        if delimiter is not None:
            self.delimiter = delimiter
        elif form == "delimited":
            self.delimiter = "...."
        self.inlines: PyList[Node] = list(inlines) if inlines else []
        self.attributes = attributes or {}

    def append(self, child: Node) -> None:
        self.inlines.append(child)

    @property
    def id(self) -> Optional[str]:
        return self.attributes.get("id")

    @id.setter
    def id(self, value: Optional[str]) -> None:
        if value is None:
            self.attributes.pop("id", None)
        else:
            self.attributes["id"] = value

    @property
    def style(self) -> Optional[str]:
        return self.attributes.get("style")

    @style.setter
    def style(self, value: Optional[str]) -> None:
        if value is None:
            self.attributes.pop("style", None)
        else:
            self.attributes["style"] = value

    @property
    def literal_title(self) -> Optional[str]:
        if self.title:
            parts = []
            for child in self.title.inlines:
                if hasattr(child, "value"):
                    parts.append(str(child.value))
                elif hasattr(child, "text"):
                    parts.append(str(child.text))
                else:
                    for sub in child.walk():
                        if hasattr(sub, "value") and getattr(sub, "name", "") == "text":
                            parts.append(str(sub.value))
            return "".join(parts)
        return self.attributes.get("title")


class Passthrough(BlockNode):
    """A block for content that should be passed through without processing."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(
        self,
        inlines: Optional[Sequence[Node]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        delimiter: str = "++++",
    ):
        super().__init__()
        self.name = "passthrough"
        self.type = "block"
        self.form = "delimited"
        self.delimiter = delimiter
        self.inlines: PyList[Node] = list(inlines) if inlines else []
        self.attributes = attributes or {}


class Comment(BlockNode):
    """A delimited comment block."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {}

    def __init__(
        self,
        value: str,
        delimiter: str = "////",
        attributes: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.name = "comment"
        self.type = "block"
        self.value = value
        self.delimiter = delimiter
        self.attributes = attributes or {}


class Stem(BlockNode):
    """A block for mathematical expressions."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def __init__(
        self,
        variant: str,
        inlines: Optional[Sequence[Node]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        delimiter: Optional[str] = None,
    ):
        super().__init__()
        self.name = "stem"
        self.type = "block"
        self.variant = variant
        self.form = "delimited" if delimiter else "paragraph"
        self.delimiter = delimiter
        self.inlines: PyList[Node] = list(inlines) if inlines else []
        self.attributes = attributes or {}


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


class Collapsible(BlockNode):
    """A block node representing an interactive disclosure/collapsible section."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def to_dict(self) -> Dict[str, Any]:
        dct = {
            "name": self.name,
            "type": self.type,
            "blocks": [child.to_dict() for child in self.blocks],
            "attributes": self.attributes,
        }
        if self.title:
            dct["title"] = self.title.to_dict()
        return dct

    def __init__(
        self,
        title: Optional[Title] = None,
        blocks: Optional[Sequence[Node]] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.name = "collapsible"
        self.type = "block"
        self.title = title
        self.blocks: PyList[Node] = list(blocks) if blocks else []
        self.attributes: Dict[str, Any] = attributes or {}


class Quote(BlockNode):
    """A block representing a quotation."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self,
        blocks: Optional[Sequence[Node]] = None,
        delimiter: str = "____",
        attribution: Optional[str] = None,
        citetitle: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.name = "quote"
        self.type = "block"
        self.form = "delimited"
        self.delimiter = delimiter
        self.blocks: PyList[Node] = list(blocks) if blocks else []
        self.attribution: Optional[str] = attribution
        self.citetitle: Optional[str] = citetitle
        self.attributes: Dict[str, Any] = attributes or {}


class Admonition(BlockNode):
    """A block for admonitions like NOTE, TIP, IMPORTANT, etc."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self,
        variant: str,
        blocks: Optional[Sequence[Node]] = None,
        delimiter: Optional[str] = "====",
    ):
        super().__init__()
        self.name = "admonition"
        self.type = "block"
        self.variant = variant
        self.form = "delimited" if delimiter else "paragraph"
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


class Verse(BlockNode):
    """A block for content that should be rendered as a verse."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(
        self,
        blocks: Optional[Sequence[Node]] = None,
        delimiter: Optional[str] = None,
        attribution: Optional[str] = None,
        citetitle: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.name = "verse"
        self.type = "block"
        self.form = "delimited" if delimiter else "paragraph"
        self.delimiter = delimiter
        self.blocks: PyList[Node] = list(blocks) if blocks else []
        self.attribution: Optional[str] = attribution
        self.citetitle: Optional[str] = citetitle
        self.attributes: Dict[str, Any] = attributes or {}


class Open(BlockNode):
    """A block for content that is an anonymous container."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"blocks": self.blocks}

    def __init__(self, blocks: Optional[Sequence[Node]] = None, delimiter: str = "--"):
        super().__init__()
        self.name = "open"
        self.type = "block"
        self.form = "delimited"
        self.delimiter = delimiter
        self.blocks: PyList[Node] = list(blocks) if blocks else []


class Table(BlockNode):
    """
    A block-level node representing a structured table.

    Tables in AsciiDoc are enclosed in +|===+ delimiters and consist of one or more `TableRow`
    elements containing `TableCell` instances. Tables support column specifications, cell alignments,
    spans (colspans, rowspans), and nested block-level content.

    *Attributes:*

    `rows`:: List of `TableRow` instances composing the rows of the table.
    `columns`:: Optional list of resolved column metadata dictionaries.
    `attributes`:: Block attributes mapping (e.g., `"cols"`, `"options"`, `"title"`, `"id"`).

    *Example:*

    [source,python]
    ----
    from asciidoctrine.lark_parser import parse_to_ast

    doc = parse_to_ast("|===\\n| Header 1 | Header 2\\n| Cell 1 | Cell 2\\n|===")
    table = doc.blocks[0]
    assert table.name == "table"
    assert len(table.rows) == 2
    ----
    """

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"rows": cast(PyList[Node], self.rows)}

    def __init__(
        self,
        rows: Optional[Sequence[TableRow]] = None,
        columns: Optional[Sequence[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__()
        self.name = "table"
        self.type = "block"
        self.rows: PyList[TableRow] = list(rows) if rows else []
        self.columns: Optional[PyList[Dict[str, Any]]] = (
            list(columns) if columns is not None else None
        )

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
        self.colspan: int = 1
        self.rowspan: int = 1
        self.align: Optional[str] = None
        self.valign: Optional[str] = None
        self.style: Optional[str] = None
        self.multiplier: Optional[int] = None


class ThematicBreak(BlockNode):
    """Represents a horizontal rule or thematic break (---, ``***``, ''')."""

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


class AttributeEntry(BlockNode):
    """A node representing an attribute declaration in the document header."""

    def __init__(self, name: str, value: str):
        super().__init__()
        self.name = "attribute_entry"
        self.type = "block"
        self.attribute_name = name
        self.value = value


class Attributes(BlockNode):
    """A resolved semantic block grouping contiguous attribute_entry declarations."""

    _should_serialize_attributes = True

    def __init__(self, attributes: Dict[str, Any]):
        super().__init__()
        self.name = "attributes"
        self.type = "block"
        self.attributes = attributes


class Include(BlockNode):
    """A node representing an `include::` directive."""

    def __init__(self, filename: str):
        super().__init__()
        self.name = "include"
        self.type = "block"
        self.filename = filename


class Toc(BlockNode):
    """A node representing a table of contents macro (toc::[])."""

    def __init__(self, target: str = "", attributes: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.name = "toc"
        self.type = "block"
        self.target = target
        self.attributes = attributes or {}


class IndexTerm(InlineNode):
    """A node representing an index term entry."""

    def get_child_collections(self) -> Dict[str, PyList[Node]]:
        return {"inlines": self.inlines}

    def to_dict(self) -> Dict[str, Any]:
        dct: Dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "terms": self.terms,
            "variant": self.variant,
        }
        if self.inlines:
            dct["inlines"] = [child.to_dict() for child in self.inlines]
        return dct

    def __init__(
        self,
        terms: Sequence[str],
        variant: str = "macro",
        inlines: Optional[Sequence[Node]] = None,
    ):
        super().__init__()
        self.name = "indexterm"
        self.type = "inline"
        self.terms: PyList[str] = list(terms)
        self.variant: str = variant  # "macro", "flow_double", "flow_triple"
        self.inlines: PyList[Node] = list(inlines) if inlines else []


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


class NodeTransformer(NodeVisitor):
    """A base class for implementing the transformer pattern to modify/rewrite the AST."""

    def generic_visit(self, node: Node, **kwargs: Any) -> Node:
        for attr_name, collection in list(node.get_child_collections().items()):
            new_collection = []
            for child in collection:
                res = self.visit(child, **kwargs)
                if res is None:
                    continue
                elif isinstance(res, list):
                    new_collection.extend(res)
                else:
                    new_collection.append(res)
            setattr(node, attr_name, new_collection)
        return node
