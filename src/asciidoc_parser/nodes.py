"""
Custom Abstract Syntax Tree (AST) for AsciiDoc parsing.
"""

from typing import List, Optional, Any, Dict
from enum import Enum

class NodeType(str, Enum):
    DOCUMENT = 'document'
    TITLE = 'title'
    AUTHOR = 'author'
    REVISION = 'revision'
    HEADER = 'header'
    SECTION = 'section'
    PARAGRAPH = 'paragraph'
    TEXT = 'text'
    STRONG = 'strong'
    EMPHASIS = 'emphasis'
    INLINE_CODE = 'literal'
    LINK = 'link'
    IMAGE = 'image'
    BULLET_LIST = 'bullet_list'
    ORDERED_LIST = 'enumerated_list'
    LIST_ITEM = 'list_item'
    LITERAL_BLOCK = 'literal_block'
    EXAMPLE_BLOCK = 'example_block'
    QUOTE_BLOCK = 'quote_block'
    ADMONITION = 'admonition'
    SIDEBAR = 'sidebar'
    TABLE = 'table'
    TABLE_ROW = 'table_row'
    TABLE_CELL = 'table_cell'
    ATTRIBUTE_ENTRY = 'attribute_entry'
    INCLUDE = 'include'

class Node:
    """Base class for all AST nodes."""
    def __init__(self, children: Optional[List['Node']] = None):
        self.children: List[Node] = children or []
        self.node_type: Optional[NodeType] = None

    def append(self, child: 'Node'):
        self.children.append(child)

    _SERIALIZABLE_ATTRS = [
        'text', 'content', 'url', 'alt', 'level',
        'flavor', 'name', 'value'
    ]
    _NODE_ATTRS = ['title_node', 'header']

    def to_dict(self) -> dict:
        """Convert the node and its children to a dictionary (for testing)."""
        data = {'type': self.node_type.value}

        if hasattr(self, 'attributes') and self.attributes:
            data['attributes'] = self.attributes

        for attr in self._SERIALIZABLE_ATTRS:
            if hasattr(self, attr):
                value = getattr(self, attr)
                if value is not None:
                    data[attr] = value

        for attr in self._NODE_ATTRS:
            if hasattr(self, attr):
                node = getattr(self, attr)
                if node:
                    # 'title_node' -> 'title'
                    key = attr.replace('_node', '')
                    data[key] = node.to_dict()

        if self.children:
            data['children'] = [c.to_dict() for c in self.children]
        
        return data

    def walk(self):
        """Walk the AST, yielding each node."""
        yield self
        for child in self.children:
            yield from child.walk()

class InlineNode(Node):
    """Base class for inline content nodes."""
    pass

class BlockNode(Node):
    """Base class for block-level content nodes."""
    pass

class Document(BlockNode):
    """Root node of the document."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.DOCUMENT
        self.header: Optional[Header] = None
        self.attributes: dict[str, str] = {}

class Title(Node):
    """Represents a section title."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.TITLE

class Author(Node):
    """Represents the author line in the document header."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.AUTHOR

class Revision(Node):
    """Represents the revision line in the document header."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.REVISION

class Header(Node):
    """Represents the document header."""
    def __init__(self, title: Optional[Title] = None, author: Optional[Author] = None, revision: Optional[Revision] = None, attributes: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.node_type = NodeType.HEADER
        self.title = title
        self.author = author
        self.revision = revision
        self.attributes = attributes or {}

    def to_dict(self) -> dict:
        data = super().to_dict()
        if self.title:
            data['title'] = self.title.to_dict()
        if self.author:
            data['author'] = self.author.to_dict()
        if self.revision:
            data['revision'] = self.revision.to_dict()
        if self.attributes:
            data['attributes'] = {
                k: [v_node.to_dict() for v_node in v] for k, v in self.attributes.items()
            }
        return data

class Section(BlockNode):
    """Represents a section with a title and content."""
    def __init__(self, level: int, title_node: Node):
        super().__init__()
        self.node_type = NodeType.SECTION
        self.level = level
        self.title_node = title_node

class Paragraph(BlockNode):
    """Represents a paragraph of text."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.PARAGRAPH

class Text(InlineNode):
    """Represents a plain text segment."""
    def __init__(self, text: str):
        super().__init__()
        self.node_type = NodeType.TEXT
        self.text = text

class Strong(InlineNode):
    """Represents bold text."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.STRONG

class Emphasis(InlineNode):
    """Represents italicized text."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.EMPHASIS

class InlineCode(InlineNode):
    """Represents inline code."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.INLINE_CODE

class Link(InlineNode):
    """Represents a hyperlink."""
    def __init__(self, url: str, text: Optional[str] = None):
        super().__init__()
        self.node_type = NodeType.LINK
        self.url = url
        self.text = text or url

class Image(InlineNode):
    """Represents an image."""
    def __init__(self, url: str, alt: str = ""):
        super().__init__()
        self.node_type = NodeType.IMAGE
        self.url = url
        self.alt = alt

class BulletList(BlockNode):
    """Represents an unordered list."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.BULLET_LIST

class OrderedList(BlockNode):
    """Represents an ordered list."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.ORDERED_LIST

class ListItem(BlockNode):
    """Represents an item in a list."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.LIST_ITEM

class LiteralBlock(BlockNode):
    """Represents a literal block (e.g., code block)."""
    def __init__(self, content: str, attributes: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.node_type = NodeType.LITERAL_BLOCK
        self.content = content
        self.attributes = attributes or {}

class ExampleBlock(BlockNode):
    """Represents an example block."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.EXAMPLE_BLOCK

class QuoteBlock(BlockNode):
    """Represents a block quote."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.QUOTE_BLOCK

class Admonition(BlockNode):
    """Represents an admonition block (e.g., NOTE, TIP)."""
    def __init__(self, flavor: str, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.ADMONITION
        self.flavor = flavor

class Sidebar(BlockNode):
    """Represents a sidebar block."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.SIDEBAR

class Table(BlockNode):
    """Represents a table."""
    def __init__(self):
        super().__init__()
        self.node_type = NodeType.TABLE
        self.header_rows: List[TableRow] = []
        self.rows: List[TableRow] = []

class TableRow(Node):
    """Represents a row in a table."""
    def __init__(self):
        super().__init__()
        self.node_type = NodeType.TABLE_ROW
        self.cells: List[TableCell] = []

class TableCell(Node):
    """Represents a cell in a table."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.TABLE_CELL

class AttributeEntry(Node):
    """Represents a document attribute."""
    def __init__(self, name: str, value: str):
        super().__init__()
        self.node_type = NodeType.ATTRIBUTE_ENTRY
        self.name = name
        self.value = value

class Include(Node):
    """Represents an include directive."""
    def __init__(self, filename: str):
        super().__init__()
        self.node_type = NodeType.INCLUDE

class NodeVisitor:
    """Base class for visiting AST nodes."""
    def visit(self, node: Node, **kwargs: Any) -> Any:
        method_name = f'visit_{node.__class__.__name__.lower()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, **kwargs)

    def generic_visit(self, node: Node, **kwargs: Any) -> Any:
        for child in node.children:
            self.visit(child, **kwargs)
