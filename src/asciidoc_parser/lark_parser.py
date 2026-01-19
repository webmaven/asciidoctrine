import os
import re
from typing import Any, Dict, Optional, Sequence, Tuple, Union, cast
from typing import List as PyList

from lark import Discard, Lark, Token, Transformer

from .nodes import (
    Admonition,
    AttributeEntry,
    Author,
    BlockNode,
    Document,
    Example,
    Header,
    Image,
    Listing,
    ListItem,
    Node,
    PageBreak,
    Paragraph,
    Quote,
    Ref,
    Revision,
    Section,
    Sidebar,
    Span,
    Table,
    TableCell,
    TableRow,
    Text,
    ThematicBreak,
    Title,
)
from .nodes import (
    List as ASTList,
)
from .preprocessor import Preprocessor

Children = PyList[Any]
Transformed = Union[Node, Any, Dict[str, Any], PyList[Any], str]


class AsciiDocTransformer(Transformer[Token, Transformed]):
    """
    Transforms the Lark parse tree (CST) into a structured AST.

    Each method in this class corresponds to a rule in the `grammar.lark` file.
    The method receives the children of the rule as arguments and should return
    an AST node from `nodes.py`.
    """

    # Regex to match author lines (e.g., "John Doe <john.doe@example.com>")
    AUTHOR_REGEX = re.compile(r"[\w\s]+(<.*>)?")
    # Regex to match revision lines (e.g., "v1.0, 2023-01-01")
    REVISION_REGEX = re.compile(r"(v\d+\.\d+.*)|(\d{4}-\d{2}-\d{2})")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.attributes: Dict[str, PyList[Node]] = {}

    @staticmethod
    def _merge_consecutive_lists(blocks: Sequence[BlockNode]) -> PyList[Node]:
        """
        Merges consecutive list blocks of the same type into a single block.

        For example, two `List` nodes of same variant that appear sequentially will be
        merged into one. This is necessary because the parser may generate them
        as separate entities.

        Args:
            blocks: A list of block-level nodes.
        Returns:
            A new list of block-level nodes with consecutive lists merged.
        """
        if not blocks:
            return []

        merged_blocks: PyList[Node] = [blocks[0]]
        for current_block in blocks[1:]:
            prev_block = merged_blocks[-1]

            # Merge consecutive lists of the same type and variant
            if (
                isinstance(current_block, ASTList)
                and isinstance(prev_block, ASTList)
                and current_block.variant == prev_block.variant
            ):
                prev_block.items.extend(current_block.items)
            else:
                merged_blocks.append(current_block)
        return merged_blocks

    @staticmethod
    def _get_list_level(marker_token: Token) -> int:
        """
        Determines the nesting level of a list item from its marker token.

        - `-` is always level 1
        - `*` or `.` level is determined by the number of characters
          (e.g., `**` is level 2)
        - `1.` style markers are always level 1.

        Args:
            marker_token: The Lark Token for the list marker.

        Returns:
            The integer nesting level.
        """
        marker = marker_token.value.strip()
        if marker.startswith("-"):
            return 1
        if marker.startswith("*"):
            return len(marker)
        if marker.startswith("."):
            return len(marker)
        return 1  # for 1., 2., etc.

    @staticmethod
    def _nest_list_items(items: PyList[Dict[str, Any]]) -> PyList[ListItem]:
        """
        Organizes a flat list of items into a nested list structure.

        The parser produces a flat list of all list items with their levels.
        This function reconstructs the correct hierarchy of lists and sublists
        based on those levels.

        Args:
            items: A list of dictionaries, where each dictionary represents a
                   list item with 'level', 'item_type', 'marker', and 'children'.

        Returns:
            A list of root-level `ListItem` nodes.
        """
        if not items:
            return []

        root_lists: PyList[ASTList] = []
        # (level, list_node)
        stack: PyList[Tuple[int, ASTList]] = []

        for item_data in items:
            level = item_data["level"]
            item_type = item_data["item_type"]
            marker = item_data["marker"]

            # Pop from the stack until the parent list of the correct level is found.
            # This handles moving to a shallower nesting level.
            while stack and level < stack[-1][0]:
                stack.pop()

            list_node: ASTList
            if not stack:
                # This is a new root-level list.
                variant = "unordered" if item_type == "bullet" else "ordered"
                list_node = ASTList(variant=variant, marker=marker)
                root_lists.append(list_node)
                stack.append((level, list_node))
            elif level > stack[-1][0]:
                # This is a new sublist, nested inside the previous item.
                parent_list = stack[-1][1]
                if parent_list.items:
                    last_item = parent_list.items[-1]
                    variant = "unordered" if item_type == "bullet" else "ordered"
                    list_node = ASTList(variant=variant, marker=marker)
                    last_item.blocks.append(list_node)
                    stack.append((level, list_node))
                else:
                    # Fallback
                    list_node = stack[-1][1]
            else:
                # Same level
                list_node = stack[-1][1]

            # Add the item to its parent list.
            list_node.items.append(
                ListItem(
                    marker=marker,
                    principal=item_data["children"],
                    checked=item_data.get("checked"),
                )
            )

        # The result should be a list of `ListItem` nodes, not the list containers.
        all_root_children: PyList[ListItem] = []
        for rl in root_lists:
            all_root_children.extend(rl.items)
        return all_root_children

    def document(self, children: Children) -> Document:
        return cast(Document, children[0])

    def document_header_with_body(self, children: Children) -> Document:
        header = None
        blocks = []

        # Find the Header node and take everything after it as body blocks
        for i, child in enumerate(children):
            if isinstance(child, Header):
                header = child
                blocks = [c for c in children[i + 1 :] if isinstance(c, BlockNode)]
                break

        merged_blocks = self._merge_consecutive_lists(blocks)
        doc = Document(merged_blocks)
        if header:
            doc.header = header
            doc.attributes.update(header.attributes)
            self.attributes.update(header.attributes)
        return doc

    def body_only(self, children: Children) -> Document:
        merged_blocks = self._merge_consecutive_lists(children)
        return Document(merged_blocks)

    def document_header(self, children: Children) -> Header:
        title = children[0]
        authors = []
        revision = None

        text_lines = [c for c in children[1:] if isinstance(c, list)]

        if len(text_lines) > 0:
            line1_nodes = text_lines[0]
            # split by semicolon token/text
            author_groups = []
            current_group = []
            for node in line1_nodes:
                if isinstance(node, Text) and not node.attributes and ";" in node.value:
                    parts = node.value.split(";")
                    for i, part in enumerate(parts):
                        if part:
                            current_group.append(Text(part))
                        if i < len(parts) - 1:
                            if current_group:
                                author_groups.append(current_group)
                            current_group = []
                else:
                    current_group.append(node)
            if current_group:
                author_groups.append(current_group)

            valid_authors = []
            for group in author_groups:
                txt = "".join(
                    [getattr(n, "value", "") for n in group if hasattr(n, "value")]
                ).strip()
                if self.AUTHOR_REGEX.fullmatch(txt):
                    valid_authors.append(Author(group))

            if valid_authors:
                authors = valid_authors

        if len(text_lines) > 1:
            line2_text = "".join(
                [node.value for node in text_lines[1] if hasattr(node, "value")]
            )
            if self.REVISION_REGEX.fullmatch(line2_text.strip()):
                revision = Revision(text_lines[1])

        attributes: Dict[str, Any] = {}
        for child in children:
            if isinstance(child, AttributeEntry):
                attributes[child.attribute_name] = self.attributes.get(
                    child.attribute_name, []
                )

        return Header(
            title=title, authors=authors, revision=revision, attributes=attributes
        )

    def author_rev_line(self, children: Children) -> PyList[Node]:
        return self.text_content(children)

    def AUTHOR_SPECIAL_CHARS(self, token: Token) -> Token:
        return Token("WORD", token.value)

    def document_title(self, children: Children) -> Title:
        nodes = [c for c in children if isinstance(c, list)]
        return Title(nodes[0] if nodes else [])

    def block(self, children: Children) -> Transformed:
        return children[0] if children else Discard

    def blank_line(self, children: Children) -> Any:
        return Discard

    def comment(self, children: Children) -> Any:
        return Discard

    def attributed_block(self, children: Children) -> BlockNode:
        # children are (block_metadata)* followed by the actual block
        metadata = [c for c in children[:-1] if c is not Discard]
        block = cast(BlockNode, children[-1])

        for item in metadata:
            if isinstance(item, Title):
                block.title = item
            elif isinstance(item, dict):
                # Merge attributes
                for k, v in item.items():
                    if k == "role":
                        existing = block.attributes.get("role")
                        if existing:
                            block.attributes["role"] = f"{existing} {v}"
                        else:
                            block.attributes["role"] = v
                    elif k == "style":
                        variant = v.lower()
                        if variant in [
                            "note",
                            "tip",
                            "important",
                            "warning",
                            "caution",
                        ]:
                            if isinstance(block, Example):
                                # Convert Example to Admonition
                                block = Admonition(variant=variant, blocks=block.blocks)
                            else:
                                block.attributes["style"] = v
                        else:
                            block.attributes["style"] = v
                    else:
                        block.attributes[k] = v
        return block

    def block_metadata(self, children: Children) -> Any:
        return children[0]

    def block_title(self, children: Children) -> Title:
        # children[0] is the result of text_content, which is a list of nodes.
        return Title(children[0])

    def attributed_simple_block(self, children: Children) -> BlockNode:
        return self.attributed_block(children)

    # --- Blocks ---

    def section(self, children: Children) -> Section:
        children = [c for c in children if c is not Discard]
        title, *blocks = children
        merged_blocks = self._merge_consecutive_lists(blocks)
        return Section(level=1, title=title, blocks=merged_blocks)

    def section_title(self, children: Children) -> Title:
        # We want the result of text_content, which is a list of nodes.
        nodes = [c for c in children if isinstance(c, list)]
        if not nodes:
            # Fallback for unexpected structure
            content = [c for c in children if c is not Discard]
            return Title(content if isinstance(content, list) else [content])
        return Title(nodes[0])

    def paragraph(self, children: Children) -> Paragraph:
        children = [c for c in children if c is not Discard]
        # TCK expects multiple lines in a paragraph to be joined by \n
        all_inlines: PyList[Node] = []
        for i, line in enumerate(children):
            if i > 0:
                all_inlines.append(Text("\n"))
            all_inlines.extend(line)

        consolidated: PyList[Node] = []
        for node in all_inlines:
            if (
                consolidated
                and isinstance(consolidated[-1], Text)
                and isinstance(node, Text)
            ):
                consolidated[-1].value += node.value
            else:
                consolidated.append(node)

        return Paragraph(inlines=consolidated)

    def ulist(self, children: Children) -> ASTList:
        items = AsciiDocTransformer._nest_list_items(children)
        marker = children[0]["marker"] if children else "*"
        return ASTList(variant="unordered", marker=marker, items=items)

    def olist(self, children: Children) -> ASTList:
        items = AsciiDocTransformer._nest_list_items(children)
        marker = children[0]["marker"] if children else "."
        return ASTList(variant="ordered", marker=marker, items=items)

    def ulist_item(self, children: Children) -> Dict[str, Any]:
        # Children are: [ULIST_MARKER, CHECKBOX?, text_content]
        marker_token = children[0]
        level = AsciiDocTransformer._get_list_level(marker_token)

        checkbox = None
        content = None
        if len(children) == 3:
            checkbox = children[1]
            content = children[2]
        else:
            content = children[1]

        item_data = {
            "level": level,
            "item_type": "bullet",
            "marker": marker_token.value.strip(),
            "children": content,
        }
        if checkbox:
            val = checkbox.value.strip("[] ")
            item_data["checked"] = val.lower() in ["x", "*"]

        return item_data

    def olist_item(self, children: Children) -> Dict[str, Any]:
        # Children are: [OLIST_MARKER, text_content]
        marker_token = children[0]
        level = AsciiDocTransformer._get_list_level(marker_token)
        content = children[1]
        return {
            "level": level,
            "item_type": "enumerated",
            "marker": marker_token.value.strip(),
            "children": content,
        }

    def basic_block(self, children: Children) -> Transformed:
        return children[0] if children else Discard

    def admonition_content(self, children: Children) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    def sidebar_content(self, children: Children) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    def example_content(self, children: Children) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    def example_block(self, children: Children) -> Example:
        inner: PyList[Any] = []
        for c in children:
            if isinstance(c, list):
                inner = c
                break
        merged_inner = self._merge_consecutive_lists(inner)
        return Example(blocks=merged_inner)

    def attribute_content(self, children: Children) -> str:
        # returns the attribute string (e.g. "source,python")
        return cast(str, children[0].value)

    def attribute_list(self, children: Children) -> Dict[str, str]:
        # find the actual attribute string among children
        attr_str = ""
        for c in children:
            if isinstance(c, Token) and c.type == "attribute_content":
                attr_str = c.value
                break
            elif isinstance(c, str) and c not in ("[", "]", "\n", "\r", "\r\n"):
                attr_str = c
                break

        if not attr_str:
            return {}

        attrs: Dict[str, str] = {}

        # Handle shorthand [#id.role] or [.role#id]
        if attr_str.startswith("#") or attr_str.startswith("."):
            curr = attr_str
            while curr:
                if curr.startswith("#"):
                    match = re.search(r"^#([^.# \[\]]+)", curr)
                    if match:
                        attrs["id"] = match.group(1)
                        curr = curr[match.end() :]
                    else:
                        break
                elif curr.startswith("."):
                    match = re.search(r"^\.([^.# \[\]]+)", curr)
                    if match:
                        role = match.group(1)
                        if "role" in attrs:
                            attrs["role"] += f" {role}"
                        else:
                            attrs["role"] = role
                        curr = curr[match.end() :]
                    else:
                        break
                else:
                    break
            return attrs

        # Basic parsing: split by comma
        parts = [p.strip() for p in attr_str.split(",")]

        if parts and "=" not in parts[0] and not parts[0].startswith(("#", ".")):
            # Positional (usually style)
            attrs["style"] = parts[0]

        for part in parts:
            if "=" in part:
                k, v = part.split("=", 1)
                attrs[k.strip()] = v.strip().strip('"').strip("'")
            elif part.startswith("#"):
                attrs["id"] = part[1:]
            elif part.startswith("."):
                role = part[1:]
                if "role" in attrs:
                    attrs["role"] += f" {role}"
                else:
                    attrs["role"] = role
            elif part.startswith("%"):
                option = part[1:]
                if "options" in attrs:
                    attrs["options"] += f",{option}"
                else:
                    attrs["options"] = option

        if attrs.get("style") == "source" and len(parts) > 1 and "=" not in parts[1]:
            attrs["language"] = parts[1]

        return attrs

    def ATTR_LIST_CONTENT(self, token: Token) -> Token:
        return Token("attribute_content", token.value)

    def literal_block(self, children: Children) -> Listing:
        # children: attribute_list? LITERAL_BLOCK_DELIM _NEWLINE
        # LITERAL_BLOCK_CONTENT LITERAL_BLOCK_DELIM
        content = ""
        attributes: Dict[str, Any] = {}

        for c in children:
            if isinstance(c, dict):  # We assume dict is from attribute_list
                attributes = c
            elif isinstance(c, Token) and c.type == "LITERAL_BLOCK_CONTENT":
                content = c.value

        return Listing(inlines=[Text(content)], attributes=attributes)

    def admonition(self, children: Children) -> Admonition:
        # children: [ADMONITION_START, _NEWLINE, ADMONITION_DELIM, _NEWLINE,
        # block_content, ADMONITION_DELIM]
        start_token = children[0]
        variant = start_token.value.strip("[] ").lower()

        # Find the block_content (list of blocks)
        inner: PyList[Any] = []
        for c in children:
            if isinstance(c, list):
                inner = c
                break

        merged_inner = self._merge_consecutive_lists(inner)
        return Admonition(variant=variant, blocks=merged_inner)

    def sidebar(self, children: Children) -> Sidebar:
        # children: [SIDEBAR_DELIM, _NEWLINE, block_content, SIDEBAR_DELIM]
        inner: PyList[Any] = []
        for c in children:
            if isinstance(c, list):
                inner = c
                break
        merged_inner = self._merge_consecutive_lists(inner)
        return Sidebar(blocks=merged_inner)

    def attribute_entry(self, children: Children) -> AttributeEntry:
        """
        Processes an attribute entry, storing it in the document-wide
        attribute registry and returning an `AttributeEntry` node.
        """
        name = ""
        value_nodes: PyList[Node] = []
        for c in children:
            if isinstance(c, Token) and (c.type == "ATTR_NAME" or c.type == "COLON"):
                if c.type == "ATTR_NAME":
                    name = c.value
            elif isinstance(c, list):
                value_nodes = c

        # Store the rich AST nodes for later substitution in attribute references.
        self.attributes[name] = value_nodes

        # For the AttributeEntry node itself, create a simple string value.
        value_str = ""
        parts: PyList[str] = []

        for node in value_nodes:
            if hasattr(node, "value") and not isinstance(
                node,
                (
                    ListItem,
                    Listing,
                    Admonition,
                    Sidebar,
                    Example,
                    Quote,
                    Table,
                    TableRow,
                    TableCell,
                ),
            ):
                parts.append(getattr(node, "value"))
            elif hasattr(node, "inlines"):
                parts.append(
                    "".join(
                        [
                            getattr(child, "value")
                            for child in getattr(node, "inlines")
                            if hasattr(child, "value")
                        ]
                    )
                )
        value_str = "".join(parts).strip()

        return AttributeEntry(name, value_str)

    # --- Inlines ---

    def attribute_reference(self, children: Children) -> PyList[Node]:
        name = ""
        for c in children:
            if isinstance(c, Token) and c.type == "ATTR_NAME":
                name = c.value
                break

        # Return the list of nodes, or a list containing a Text node with the
        # unresolved reference
        return self.attributes.get(name, [Text(f"{{{name}}}")])

    def text_content(self, children: Children) -> PyList[Node]:
        nodes: PyList[Node] = []
        pending_attrs: Optional[Dict[str, str]] = None

        flat_children: PyList[Any] = []
        for child in children:
            if isinstance(child, list) and not isinstance(child, Node):
                flat_children.extend(child)
            else:
                flat_children.append(child)

        for child in flat_children:
            if isinstance(child, dict):
                pending_attrs = child
                continue

            node: Optional[Node] = None
            if isinstance(child, Token):
                node = Text(str(child.value))
            elif isinstance(child, Node):
                node = child

            if node:
                if pending_attrs:
                    for k, v in pending_attrs.items():
                        if k == "role":
                            existing = node.attributes.get("role")
                            node.attributes["role"] = (
                                f"{existing} {v}" if existing else v
                            )
                        else:
                            node.attributes[k] = v
                    pending_attrs = None

                # Merge consecutive text nodes if they have same attributes
                if (
                    nodes
                    and isinstance(nodes[-1], Text)
                    and isinstance(node, Text)
                    and nodes[-1].attributes == node.attributes
                ):
                    nodes[-1].value += node.value
                else:
                    nodes.append(node)

        # Handle trailing attribute list if any (unlikely to be valid but for safety)
        if pending_attrs:
            attr_str = ",".join([f"{k}={v}" for k, v in pending_attrs.items()])
            nodes.append(Text(f"[{attr_str}]"))

        return nodes

    def bold(self, children: Children) -> Span:
        content = [c for c in children if isinstance(c, list)]
        nodes = content[0] if content else []
        # If the only child is a Span node of same variant, flatten it.
        if (
            len(nodes) == 1
            and isinstance(nodes[0], Span)
            and nodes[0].variant == "strong"
        ):
            return Span(variant="strong", inlines=nodes[0].inlines)
        return Span(variant="strong", inlines=nodes)

    def italic(self, children: Children) -> Span:
        content = [c for c in children if isinstance(c, list)]
        return Span(variant="emphasis", inlines=content[0] if content else [])

    def monospace(self, children: Children) -> Span:
        content = [c for c in children if isinstance(c, list)]
        nodes = content[0] if content else []
        return Span(variant="code", inlines=nodes)

    def marked(self, children: Children) -> Span:
        return Span(variant="mark", inlines=children[0] if children else [])

    def superscript(self, children: Children) -> Span:
        return Span(variant="superscript", inlines=children[0] if children else [])

    def subscript(self, children: Children) -> Span:
        return Span(variant="subscript", inlines=children[0] if children else [])

    def footnote(self, children: Children) -> Ref:
        return Ref(variant="footnote", target="", inlines=children[0])

    def footnoteref(self, children: Children) -> Ref:
        target = ""
        inlines = []
        # children are [WORD?, text_content?]
        for c in children:
            if isinstance(c, Token) and c.type == "WORD":
                target = str(c.value)
            elif isinstance(c, list):
                inlines = c
        return Ref(variant="footnote", target=target, inlines=inlines)

    def double_quoted(self, children: Children) -> Span:
        return Span(variant="double", inlines=children[0] if children else [])

    def single_quoted(self, children: Children) -> Span:
        return Span(variant="single", inlines=children[0] if children else [])

    def image_block(self, children: Children) -> Image:
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        alt = attrs.get("style", "")
        img = Image(target=target, alt=alt, form="macro", type="block")
        img.attributes.update(attrs)
        if "style" in img.attributes:
            img.attributes["alt"] = img.attributes.pop("style")
        return img

    def inline_image(self, children: Children) -> Image:
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        alt = attrs.get("style", "")
        img = Image(target=target, alt=alt, form="macro", type="inline")
        img.attributes.update(attrs)
        if "style" in img.attributes:
            img.attributes["alt"] = img.attributes.pop("style")
        return img

    def icon_inline(self, children: Children) -> Image:
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        img = Image(target=target, alt="", form="macro", type="inline")
        img.name = "icon"
        img.attributes.update(attrs)
        return img

    def thematic_break(self, children: Children) -> ThematicBreak:
        return ThematicBreak()

    def page_break(self, children: Children) -> PageBreak:
        return PageBreak()

    def inline_anchor(self, children: Children) -> Ref:
        # children[0] is text_content (list of nodes)
        nodes = children[0]
        # target is typically the first part before comma
        # for now, just use the string value of the whole thing as a simplification
        # TCK might want something specific
        target = "".join(
            [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
        )
        if "," in target:
            target, _ = target.split(",", 1)
        return Ref(variant="anchor", target=target.strip(), inlines=nodes)

    def inline_xref(self, children: Children) -> Ref:
        nodes = children[0]
        target = "".join(
            [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
        )
        if "," in target:
            target, _ = target.split(",", 1)
        return Ref(variant="xref", target=target.strip(), inlines=nodes)

    def inline_bibref(self, children: Children) -> Ref:
        nodes = children[0]
        target = "".join(
            [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
        )
        if "," in target:
            target, _ = target.split(",", 1)
        return Ref(variant="bibref", target=target.strip(), inlines=nodes)

    def anchor(self, children: Children) -> Dict[str, str]:
        return {"id": str(children[0].value)}

    def inline_attribute_list(self, children: Children) -> Dict[str, str]:
        return self.attribute_list(children)

    # --- Terminals ---

    def WHITESPACE(self, token: Token) -> Token:
        # Consolidate whitespace into a single space
        return Token("WORD", " ")

    # Discard unneeded tokens
    def SECTION_TITLE_LEAD(self, token: Token) -> Any:
        return Discard

    def LITERAL_BLOCK_DELIM(self, token: Token) -> Any:
        return Discard

    def _NEWLINE(self, token: Token) -> Any:
        return Discard


DEFAULT_GRAMMAR = os.path.join(os.path.dirname(__file__), "grammar.lark")


def parse_to_ast(
    source: str,
    grammar_file: str = DEFAULT_GRAMMAR,
    base_dir: Optional[str] = None,
) -> Document:
    """
    Parses an AsciiDoc source string into an Abstract Syntax Tree (AST).

    This is the main entry point for the parser. It handles preprocessing
    (e.g., includes), parsing the grammar, and transforming the result into
    a structured AST.
    Args:
        source: The AsciiDoc source code as a string.
        grammar_file: Path to the Lark grammar file to use. Defaults to the
                      one packaged with the library.
        base_dir: The base directory for resolving `include::` directives.
                  Defaults to the current working directory.
    Returns:
        A `Document` node representing the root of the AST.
    """
    # Preprocess the source to handle includes
    preprocessor = Preprocessor(base_dir)
    processed_source = preprocessor.process(source)

    with open(grammar_file, "r") as f:
        grammar = f.read()
    # Using LALR or Earley is common, but we are moving to PEG
    # For now, let's keep it compatible. PEG in Lark is experimental.
    parser = Lark(grammar, start="document", parser="earley")
    tree = parser.parse(processed_source)
    ast_root = AsciiDocTransformer().transform(tree)
    if not isinstance(ast_root, Document):
        raise TypeError("Parsing did not return a Document node.")
    return ast_root
