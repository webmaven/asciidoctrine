
"""
Custom Abstract Syntax Tree (AST) for AsciiDoc parsing.
"""

from typing import List, Optional, Any, Dict
from enum import Enum

class NodeType(str, Enum):
    """An enumeration of all possible node types in the AST."""
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
    BULLET_LIST = 'bullet_list'
    ORDERED_LIST = 'enumerated_list'
    LIST_ITEM = 'list_item'
    LITERAL_BLOCK = 'literal_block'
    EXAMPLE_BLOCK = 'example_block'
    ADMONITION = 'admonition'
    SIDEBAR = 'sidebar'
    ATTRIBUTE_ENTRY = 'attribute_entry'

class Node:
    """Base class for all AST nodes."""
    def __init__(self, children: Optional[List['Node']] = None):
        self.children: List[Node] = children or []
        self.node_type: Optional[NodeType] = None

    def append(self, child: 'Node'):
        self.children.append(child)

    _SERIALIZABLE_ATTRS = [
        'text', 'content', 'level',
        'flavor', 'name', 'value'
    ]
    _NODE_ATTRS = ['title_node', 'header']

    def to_dict(self) -> dict:
        """
        Recursively converts the node and its subtree into a dictionary.

        This method is primarily used for debugging and testing to allow for
        easy comparison of the parsed AST structure with an expected output.
        It serializes the node's type, its serializable attributes (like
        `text` or `level`), any nested node attributes (like `title_node`),
        and its children.

        Returns:
            A dictionary representation of the node.
        """
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
    """A base class for nodes that represent inline content, such as text formatting."""
    pass

class BlockNode(Node):
    """A base class for nodes that represent block-level content, such as paragraphs or lists."""
    pass

class Document(BlockNode):
    """The root node of the entire AsciiDoc document AST."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.DOCUMENT
        self.header: Optional[Header] = None
        self.attributes: dict[str, str] = {}

class Title(Node):
    """Represents the title of a document or a section."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.TITLE

class Author(Node):
    """Represents an author entry in the document header."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.AUTHOR

class Revision(Node):
    """Represents a revision entry in the document header."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.REVISION

class Header(Node):
    """A container for the document's header metadata."""
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
    """Represents a structural section of the document."""
    def __init__(self, level: int, title_node: Node):
        super().__init__()
        self.node_type = NodeType.SECTION
        self.level = level
        self.title_node = title_node

class Paragraph(BlockNode):
    """A block-level node representing a paragraph of text."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.PARAGRAPH

class Text(InlineNode):
    """A leaf node representing a segment of plain text."""
    def __init__(self, text: str):
        super().__init__()
        self.node_type = NodeType.TEXT
        self.text = text

class Strong(InlineNode):
    """An inline node for bold text (`*text*`)."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.STRONG

class Emphasis(InlineNode):
    """An inline node for italicized text (`_text_`)."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.EMPHASIS

class InlineCode(InlineNode):
    """An inline node for monospaced/code text (`+text+`)."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.INLINE_CODE

class BulletList(BlockNode):
    """A block node representing an unordered (bulleted) list."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.BULLET_LIST

class OrderedList(BlockNode):
    """A block node representing an ordered (numbered or lettered) list."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.ORDERED_LIST

class ListItem(BlockNode):
    """A node representing a single item within a list. It can contain blocks."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.LIST_ITEM

class LiteralBlock(BlockNode):
    """A block for preformatted text, typically used for code listings."""
    def __init__(self, content: str, attributes: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.node_type = NodeType.LITERAL_BLOCK
        self.content = content
        self.attributes = attributes or {}

class ExampleBlock(BlockNode):
    """A block for content that should be rendered as an example."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.EXAMPLE_BLOCK

class Admonition(BlockNode):
    """A block for admonitions like NOTE, TIP, IMPORTANT, etc."""
    def __init__(self, flavor: str, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.ADMONITION
        self.flavor = flavor

class Sidebar(BlockNode):
    """A block for content that is separate from the main flow of text."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.node_type = NodeType.SIDEBAR

class AttributeEntry(Node):
    """A node representing an attribute declaration in the document header."""
    def __init__(self, name: str, value: str):
        super().__init__()
        self.node_type = NodeType.ATTRIBUTE_ENTRY
        self.name = name
        self.value = value
