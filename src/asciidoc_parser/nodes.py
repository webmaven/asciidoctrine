"""
Custom Abstract Syntax Tree (AST) for AsciiDoc parsing.
"""

from typing import List, Optional, Any, Dict

class Node:
    """Base class for all AST nodes."""
    _SERIALIZED_ATTRS = ()

    def __init__(self, children: Optional[List['Node']] = None):
        self.children: List[Node] = children or []

    def append(self, child: 'Node'):
        self.children.append(child)

    def to_dict(self) -> dict:
        """Convert the node and its children to a dictionary (for testing)."""
        # Determine the type string, preferring a custom one if it exists.
        type_name = getattr(self, '_type_name', self.__class__.__name__.lower())
        data = {'type': type_name}

        # Serialize attributes based on the class's declaration.
        attrs_to_serialize = getattr(self, '_SERIALIZED_ATTRS', ())

        for attr_name in attrs_to_serialize:
            if hasattr(self, attr_name):
                value = getattr(self, attr_name)

                if value is None:
                    continue

                # Special handling for attributes that should not be included if empty.
                if attr_name == 'attributes' and not value:
                    continue

                # Handle recursive cases
                if attr_name == 'children':
                    if value: # only add if not empty
                        data['children'] = [c.to_dict() for c in value]
                elif attr_name == 'title_node':
                    if value: # only add if not empty
                        data['title'] = value.to_dict()
                else:
                    data[attr_name] = value
        
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
    _SERIALIZED_ATTRS = ('children',)
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.title: Optional[str] = None
        self.attributes: dict[str, str] = {}

class Title(Node):
    """Represents a section title."""
    _SERIALIZED_ATTRS = ('children',)

class Section(BlockNode):
    """Represents a section with a title and content."""
    _SERIALIZED_ATTRS = ('level', 'title_node', 'children')
    def __init__(self, level: int, title_node: Node):
        super().__init__()
        self.level = level
        self.title_node = title_node

class Paragraph(BlockNode):
    """Represents a paragraph of text."""
    _SERIALIZED_ATTRS = ('children',)

class Text(InlineNode):
    """Represents a plain text segment."""
    _SERIALIZED_ATTRS = ('text',)
    def __init__(self, text: str):
        super().__init__()
        self.text = text

class Strong(InlineNode):
    """Represents bold text."""
    _SERIALIZED_ATTRS = ('children',)

class Emphasis(InlineNode):
    """Represents italicized text."""
    _SERIALIZED_ATTRS = ('children',)

class InlineCode(InlineNode):
    """Represents inline code."""
    _type_name = 'literal'
    _SERIALIZED_ATTRS = ('children',)
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)

class Link(InlineNode):
    """Represents a hyperlink."""
    _SERIALIZED_ATTRS = ('url', 'text')
    def __init__(self, url: str, text: Optional[str] = None):
        super().__init__()
        self.url = url
        self.text = text or url

class Image(InlineNode):
    """Represents an image."""
    _SERIALIZED_ATTRS = ('url', 'alt')
    def __init__(self, url: str, alt: str = ""):
        super().__init__()
        self.url = url
        self.alt = alt

class BulletList(BlockNode):
    """Represents an unordered list."""
    _type_name = 'bullet_list'
    _SERIALIZED_ATTRS = ('children',)

class OrderedList(BlockNode):
    """Represents an ordered list."""
    _type_name = 'enumerated_list'
    _SERIALIZED_ATTRS = ('children',)

class ListItem(BlockNode):
    """Represents an item in a list."""
    _type_name = 'list_item'
    _SERIALIZED_ATTRS = ('children',)

class LiteralBlock(BlockNode):
    """Represents a literal block (e.g., code block)."""
    _type_name = 'literal_block'
    _SERIALIZED_ATTRS = ('content', 'attributes')
    def __init__(self, content: str, attributes: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.content = content
        self.attributes = attributes or {}

class QuoteBlock(BlockNode):
    """Represents a block quote."""
    _SERIALIZED_ATTRS = ('children',)

class Admonition(BlockNode):
    """Represents an admonition block (e.g., NOTE, TIP)."""
    _SERIALIZED_ATTRS = ('flavor', 'children')
    def __init__(self, flavor: str, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.flavor = flavor

class Sidebar(BlockNode):
    """Represents a sidebar block."""
    _type_name = 'sidebar'
    _SERIALIZED_ATTRS = ('children',)

class Table(BlockNode):
    """Represents a table."""
    _SERIALIZED_ATTRS = ('children',)
    def __init__(self):
        super().__init__()
        self.header_rows: List[TableRow] = []
        self.rows: List[TableRow] = []

class TableRow(Node):
    """Represents a row in a table."""
    def __init__(self):
        super().__init__()
        self.cells: List[TableCell] = []

class TableCell(Node):
    """Represents a cell in a table."""
    pass

class AttributeEntry(Node):
    """Represents a document attribute."""
    def __init__(self, name: str, value: str):
        super().__init__()
        self.name = name
        self.value = value

class Include(Node):
    """Represents an include directive."""
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

class NodeVisitor:
    """Base class for visiting AST nodes."""
    def visit(self, node: Node, **kwargs: Any) -> Any:
        method_name = f'visit_{node.__class__.__name__.lower()}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, **kwargs)

    def generic_visit(self, node: Node, **kwargs: Any) -> Any:
        for child in node.children:
            self.visit(child, **kwargs)
