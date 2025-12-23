
import os
from lark import Lark, Transformer, Discard, Token
from .nodes import (
    Node, Document, Title, Section, Paragraph, Text, Strong, Emphasis, 
    InlineCode, BulletList, OrderedList, ListItem, LiteralBlock, Admonition, Sidebar, ExampleBlock,
    AttributeEntry
)

def _merge_consecutive_lists(blocks):
    if not blocks:
        return []

    merged_blocks = [blocks[0]]
    for current_block in blocks[1:]:
        prev_block = merged_blocks[-1]
        
        # Merge consecutive lists of the same type
        if (isinstance(current_block, (BulletList, OrderedList)) and
                type(current_block) is type(prev_block)):
            prev_block.children.extend(current_block.children)
        else:
            merged_blocks.append(current_block)
    return merged_blocks

def _get_list_level(marker_token):
    marker = marker_token.value.strip()
    if marker.startswith('-'):
        return 1
    if marker.startswith('*'):
        return len(marker)
    if marker.startswith('.'):
        return len(marker)
    return 1 # for 1., 2., etc.

def _nest_list_items(items):
    if not items:
        return []

    root_lists = []
    stack = [] # (level, list_node)

    for item_data in items:
        level = item_data['level']
        item_type = item_data['item_type']
        list_type = 'bullet_list' if item_type == 'bullet' else 'enumerated_list'

        # Pop stack if we are at a shallower level
        while stack and level < stack[-1][0]:
            stack.pop()

        if not stack:
            # New root level list
            list_node = BulletList() if item_type == 'bullet' else OrderedList()
            root_lists.append(list_node)
            stack.append((level, list_node))
        elif level > stack[-1][0]:
            # Deeper level: sublist of the last item in the current list
            parent_list = stack[-1][1]
            if parent_list.children:
                last_item = parent_list.children[-1]
                list_node = BulletList() if item_type == 'bullet' else OrderedList()
                last_item.append(list_node)
                stack.append((level, list_node))
            else:
                # Fallback: same level if parent list is empty (should not happen)
                list_node = stack[-1][1]
        else:
            # Same level, but maybe different type? 
            # In AsciiDoc, changing type at same level starts a new list or is an error.
            # We'll stick to the current list if types match, or just continue.
            list_node = stack[-1][1]

        # Add the item to the determined list node
        list_node.append(ListItem(item_data['children']))

    # Return the children of the root list(s). 
    all_root_children = []
    for rl in root_lists:
        all_root_children.extend(rl.children)
    return all_root_children

class AsciiDocTransformer(Transformer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attributes = {}

    def document(self, children):
        filtered_children = [c for c in children if c is not Discard]
        merged_children = _merge_consecutive_lists(filtered_children)
        return Document(merged_children)

    def block(self, children):
        return children[0] if children else Discard

    def blank_line(self, children):
        return Discard

    # --- Blocks ---

    def section(self, children):
        children = [c for c in children if c is not Discard]
        title_node, *blocks = children
        section_node = Section(level=1, title_node=title_node)
        section_node.children = _merge_consecutive_lists(blocks)
        return section_node

    def section_title(self, children):
        # We want the result of text_content, which is a list of nodes.
        nodes = [c for c in children if isinstance(c, list)]
        if not nodes:
            # Fallback for unexpected structure
            content = [c for c in children if c is not Discard]
            return Title(content if isinstance(content, list) else [content])
        return Title(nodes[0])

    def paragraph(self, children):
        children = [c for c in children if c is not Discard]
        return Paragraph(children[0])

    def ulist(self, children):
        return BulletList(_nest_list_items(children))

    def olist(self, children):
        return OrderedList(_nest_list_items(children))

    def ulist_item(self, children):
        # Children are: [ULIST_MARKER, text_content]
        marker_token = children[0]
        level = _get_list_level(marker_token)
        content = children[1]
        return {'level': level, 'item_type': 'bullet', 'children': content}

    def olist_item(self, children):
        # Children are: [OLIST_MARKER, text_content]
        marker_token = children[0]
        level = _get_list_level(marker_token)
        content = children[1]
        return {'level': level, 'item_type': 'enumerated', 'children': content}

    def basic_block(self, children):
        return children[0] if children else Discard

    def admonition_content(self, children):
        return [c for c in children if c is not Discard]

    def sidebar_content(self, children):
        return [c for c in children if c is not Discard]

    def example_content(self, children):
        return [c for c in children if c is not Discard]

    def example_block(self, children):
        inner = []
        for c in children:
            if isinstance(c, list):
                inner = c
                break
        merged_inner = _merge_consecutive_lists(inner)
        return ExampleBlock(children=merged_inner)

    def attribute_content(self, children):
        # returns the attribute string (e.g. "source,python")
        return children[0].value

    def attribute_list(self, children):
        # find the actual attribute string among children
        attr_str = ""
        for c in children:
            if isinstance(c, str) and c not in ('[', ']', '\n', '\r', '\r\n'):
                attr_str = c
                break
        
        # Basic parsing: split by comma
        parts = [p.strip() for p in attr_str.split(',')]
        attrs = {}
        if parts:
            attrs['style'] = parts[0]
        if len(parts) > 1:
            if parts[0] == 'source':
                attrs['language'] = parts[1]
        return attrs

    def literal_block(self, children):
        # children: attribute_list? LITERAL_BLOCK_DELIM _NEWLINE LITERAL_BLOCK_CONTENT LITERAL_BLOCK_DELIM
        content = ''
        attributes = {}
        
        for c in children:
            if isinstance(c, dict): # We assume dict is from attribute_list
                attributes = c
            elif isinstance(c, Token) and c.type == 'LITERAL_BLOCK_CONTENT':
                content = c.value
                
        return LiteralBlock(content, attributes)

    def admonition(self, children):
        # children: [ADMONITION_START, _NEWLINE, ADMONITION_DELIM, _NEWLINE, block_content, ADMONITION_DELIM]
        start_token = children[0]
        flavor = start_token.value.strip('[] ').lower()
        
        # Find the block_content (list of blocks)
        inner = []
        for c in children:
            if isinstance(c, list):
                inner = c
                break
        
        merged_inner = _merge_consecutive_lists(inner)
        return Admonition(flavor=flavor, children=merged_inner)

    def sidebar(self, children):
        # children: [SIDEBAR_DELIM, _NEWLINE, block_content, SIDEBAR_DELIM]
        inner = []
        for c in children:
            if isinstance(c, list):
                inner = c
                break
        merged_inner = _merge_consecutive_lists(inner)
        return Sidebar(children=merged_inner)

    def attribute_entry(self, children):
        name = ""
        value_nodes = []
        for c in children:
            if isinstance(c, Token) and c.type == 'ATTR_NAME':
                name = c.value
            elif isinstance(c, list):
                value_nodes = c

        # Store the rich AST nodes for later substitution
        self.attributes[name] = value_nodes

        # For the AttributeEntry node itself, create a simple string value for now.
        value_str = ""
        parts = []
        for node in value_nodes:
            if hasattr(node, 'text'):
                parts.append(node.text)
            elif hasattr(node, 'children'):
                 # This is a bit naive but works for basic attribute values
                 parts.append("".join([child.text for child in node.children if hasattr(child, 'text')]))
        value_str = "".join(parts).strip()
        return AttributeEntry(name, value_str)

    # --- Inlines ---

    def attribute_reference(self, children):
        name = ""
        for c in children:
            if isinstance(c, Token) and c.type == 'ATTR_NAME':
                name = c.value
                break

        # Return the list of nodes, or a Text node with the unresolved reference
        return self.attributes.get(name, Text(f"{{{name}}}"))

    def text_content(self, children):
        nodes = []
        text_buffer = ''

        # Flatten the list of children, in case of attribute substitution returning a list of nodes
        flat_children = []
        for child in children:
            if isinstance(child, list):
                flat_children.extend(child)
            else:
                flat_children.append(child)

        for child in flat_children:
            if isinstance(child, Token):
                text_buffer += str(child.value)
            elif isinstance(child, Text):
                text_buffer += child.text
            elif isinstance(child, Node):
                if text_buffer:
                    nodes.append(Text(text_buffer))
                    text_buffer = ''
                nodes.append(child)
        if text_buffer:
            nodes.append(Text(text_buffer))
        return nodes

    def bold(self, children):
        content = [c for c in children if isinstance(c, list)]
        return Strong(content[0] if content else [])

    def italic(self, children):
        content = [c for c in children if isinstance(c, list)]
        return Emphasis(content[0] if content else [])

    def monospace(self, children):
        content = [c for c in children if isinstance(c, list)]
        # For monospace, we flatten to raw text as per older tests if needed,
        # but here we follow the 'children' requirement.
        nodes = content[0] if content else []
        return InlineCode(nodes)

    # --- Terminals ---

    def WHITESPACE(self, token):
        # Consolidate whitespace into a single space
        return Token('WORD', ' ')

    # Discard unneeded tokens
    def SECTION_TITLE_LEAD(self, token): return Discard
    def LITERAL_BLOCK_DELIM(self, token): return Discard
    def _NEWLINE(self, token): return Discard


DEFAULT_GRAMMAR = os.path.join(os.path.dirname(__file__), 'grammar.lark')

def parse_to_ast(source, grammar_file=DEFAULT_GRAMMAR):
    with open(grammar_file, "r") as f:
        grammar = f.read()
    # Using LALR or Earley is common, but we are moving to PEG
    # For now, let's keep it compatible. PEG in Lark is experimental.
    parser = Lark(grammar, start='document', parser='earley')
    tree = parser.parse(source)
    ast_root = AsciiDocTransformer().transform(tree)
    # Return as dict for test compatibility
    return ast_root.to_dict() if hasattr(ast_root, 'to_dict') else ast_root
