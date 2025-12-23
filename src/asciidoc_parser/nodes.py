"""
Custom Abstract Syntax Tree (AST) for AsciiDoc parsing.
"""

from typing import List, Optional, Any, Dict

class Node:
    """Base class for all AST nodes."""
    def __init__(self, children: Optional[List['Node']] = None):
        self.children: List[Node] = children or []

    def append(self, child: 'Node'):
        self.children.append(child)

    def to_dict(self) -> dict:
        """Convert the node and its children to a dictionary (for testing)."""
        data = {'type': self.__class__.__name__.lower()}
        if hasattr(self, 'text'):
            data['text'] = self.text
        if hasattr(self, 'content'):
            data['content'] = self.content
        if hasattr(self, 'attributes') and self.attributes:
            data['attributes'] = self.attributes
        if hasattr(self, 'url'):
            data['url'] = self.url
        if hasattr(self, 'alt'):
            data['alt'] = self.alt
        if hasattr(self, 'level'):
            data['level'] = self.level
        if hasattr(self, 'flavor'):
            data['flavor'] = self.flavor
        if hasattr(self, 'name'):
            data['name'] = self.name
        if hasattr(self, 'value'):
            data['value'] = self.value
        if hasattr(self, 'title_node') and self.title_node:
            data['title'] = self.title_node.to_dict()
        
        # Special case for dictionary-based children in original tests
        if self.children:
            data['children'] = [c.to_dict() for c in self.children]
        
        # Map class names to specific type strings used in old tests if they differ
        type_map = {
            'strong': 'strong',
            'emphasis': 'emphasis',
            'inlinecode': 'literal',
            'bulletlist': 'bullet_list',
            'orderedlist': 'enumerated_list',
            'document': 'document',
            'paragraph': 'paragraph',
            'section': 'section',
            'title': 'title',
            'listitem': 'list_item',
            'literalblock': 'literal_block',
            'sidebar': 'sidebar',
            'exampleblock': 'example_block',
            'attributeentry': 'attribute_entry'
        }
        data['type'] = type_map.get(data['type'], data['type'])
        
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
        self.title: Optional[str] = None
        self.attributes: dict[str, str] = {}

class Title(Node):
    """Represents a section title."""
    pass

class Section(BlockNode):
    """Represents a section with a title and content."""
    def __init__(self, level: int, title_node: Node):
        super().__init__()
        self.level = level
        self.title_node = title_node

class Paragraph(BlockNode):
    """Represents a paragraph of text."""
    pass

class Text(InlineNode):
    """Represents a plain text segment."""
    def __init__(self, text: str):
        super().__init__()
        self.text = text

class Strong(InlineNode):
    """Represents bold text."""
    pass

class Emphasis(InlineNode):
    """Represents italicized text."""
    pass

class InlineCode(InlineNode):
    """Represents inline code."""
    def __init__(self, children: Optional[List['Node']] = None):
        super().__init__(children)

class Link(InlineNode):
    """Represents a hyperlink."""
    def __init__(self, url: str, text: Optional[str] = None):
        super().__init__()
        self.url = url
        self.text = text or url

class Image(InlineNode):
    """Represents an image."""
    def __init__(self, url: str, alt: str = ""):
        super().__init__()
        self.url = url
        self.alt = alt

class BulletList(BlockNode):
    """Represents an unordered list."""
    pass

class OrderedList(BlockNode):
    """Represents an ordered list."""
    pass

class ListItem(BlockNode):
    """Represents an item in a list."""
    pass

class LiteralBlock(BlockNode):
    """Represents a literal block (e.g., code block)."""
    def __init__(self, content: str, attributes: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.content = content
        self.attributes = attributes or {}

class ExampleBlock(BlockNode):
    """Represents an example block."""
    pass

class QuoteBlock(BlockNode):
    """Represents a block quote."""
    pass

class Admonition(BlockNode):
    """Represents an admonition block (e.g., NOTE, TIP)."""
    def __init__(self, flavor: str, children: Optional[List['Node']] = None):
        super().__init__(children)
        self.flavor = flavor

class Sidebar(BlockNode):
    """Represents a sidebar block."""
    pass

class Table(BlockNode):
    """Represents a table."""
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
