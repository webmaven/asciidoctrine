import os
import re
from typing import Any, Dict, Optional, Tuple, Union, cast
from typing import List as PyList

from lark import Discard, Lark, Token, Transformer, v_args

from .attributes import resolve_node_to_string
from .nodes import (
    Admonition,
    AttributeEntry,
    Audio,
    Author,
    BlockNode,
    Document,
    Example,
    FloatingTitle,
    Header,
    Image,
    Node,
    Open,
    PageBreak,
    Paragraph,
    Passthrough,
    Quote,
    Revision,
    Section,
    Stem,
    Text,
    ThematicBreak,
    Title,
    Toc,
    Verse,
    Video,
)
from .preprocessor import Preprocessor
from .transformers.block_transformer import BlockTransformer
from .transformers.inline_transformer import InlineTransformer

Children = PyList[Any]
Transformed = Union[Node, Any, Dict[str, Any], PyList[Any], str]


class AsciiDocTransformer(
    BlockTransformer, InlineTransformer, Transformer[Token, Transformed]
):
    """
    Transforms the Lark parse tree (CST) into a structured AST.
    Inherits from BlockTransformer and InlineTransformer for modularity.
    """

    # Regex to match author lines (e.g., "John Doe <john.doe@example.com>")
    AUTHOR_REGEX = re.compile(r"[\w\s]+(<.*>)?")
    # Regex to match revision lines (e.g., "v1.0, 2023-01-01")
    REVISION_REGEX = re.compile(r"(v\d+\.\d+.*)|(\d{4}-\d{2}-\d{2})")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.attributes: Dict[str, PyList[Node]] = {}

    def _set_location_from_meta(self, node: Node, meta: Any) -> Node:
        """Sets the location of a node from Lark meta."""
        node.location = [
            {"line": meta.line, "col": meta.column},
            {"line": meta.end_line, "col": meta.end_column - 1},
        ]
        return node

    def _set_location_from_children(self, node: Node, children: PyList[Any]) -> Node:
        """Sets the location of a node based on its children's locations."""
        from lark import Tree
        valid_locations = []

        def collect_locations(item: Any):
            if isinstance(item, Node) and item.location:
                valid_locations.extend(item.location)
            elif isinstance(item, Token):
                if item.type == "_NEWLINE" or item.type.startswith("__ANON_"):
                    return
                if item.line is not None and item.column is not None:
                    valid_locations.append({"line": item.line, "col": item.column})
                if item.end_line is not None and item.end_column is not None:
                    # Subtract 1 for inclusive end column
                    valid_locations.append(
                        {"line": item.end_line, "col": item.end_column - 1}
                    )
            elif isinstance(item, Tree):
                for child in item.children:
                    collect_locations(child)
            elif isinstance(item, list):
                for subitem in item:
                    collect_locations(subitem)

        for child in children:
            collect_locations(child)

        if valid_locations:
            # Filter out any None values just in case
            valid_locations = [
                loc for loc in valid_locations if loc.get("line") is not None
            ]
            if valid_locations:
                # Sort by line then col
                valid_locations.sort(key=lambda x: (x["line"], x["col"]))
                node.location = [valid_locations[0], valid_locations[-1]]
        return node

    @v_args(meta=True)
    def document(self, meta: Any, children: Children) -> Document:
        doc = cast(Document, children[0])
        return cast(Document, self._set_location_from_children(doc, children))

    @v_args(meta=True)
    def document_header_with_body(self, meta: Any, children: Children) -> Document:
        header = None
        blocks = []

        for i, child in enumerate(children):
            if isinstance(child, Header):
                header = child
                blocks = [c for c in children[i + 1 :] if isinstance(c, BlockNode)]
                break

        final_blocks = self._finalize_document_blocks(blocks)
        doc = Document(final_blocks)
        if header:
            doc.header = header
            doc.attributes.update(header.attributes)
            self.attributes.update(header.attributes)
        return cast(Document, self._set_location_from_children(doc, children))

    @v_args(meta=True)
    def body_only(self, meta: Any, children: Children) -> Document:
        final_blocks = self._finalize_document_blocks(children)
        doc = Document(final_blocks)
        return cast(Document, self._set_location_from_children(doc, children))

    def _finalize_document_blocks(self, blocks: PyList[Any]) -> PyList[Node]:
        block_nodes = [b for b in blocks if isinstance(b, BlockNode)]
        # 1. Merge consecutive lists of same type
        merged = self._merge_consecutive_lists(block_nodes)
        # 2. Nest sections correctly
        return self._nest_sections(merged)

    def _nest_sections(self, blocks: PyList[Node]) -> PyList[Node]:
        root: PyList[Node] = []
        stack: PyList[Section] = []
        for block in blocks:
            if isinstance(block, Section):
                while stack and stack[-1].level >= block.level:
                    stack.pop()
                if stack:
                    stack[-1].blocks.append(block)
                else:
                    root.append(block)
                stack.append(block)
            else:
                if stack:
                    stack[-1].blocks.append(block)
                else:
                    root.append(block)
        return root

    @v_args(meta=True)
    def document_header(self, meta: Any, children: Children) -> Header:
        title = children[0]
        authors = []
        revision = None

        text_lines = [c for c in children[1:] if isinstance(c, list)]

        if len(text_lines) > 0:
            line1_nodes = text_lines[0]
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

        header = Header(
            title=title, authors=authors, revision=revision, attributes=attributes
        )
        return cast(Header, self._set_location_from_children(header, children))

    @v_args(meta=True)
    def author_rev_line(self, meta: Any, children: Children) -> PyList[Node]:
        return self.text_content(meta, children)

    def AUTHOR_SPECIAL_CHARS(self, token: Token) -> Token:
        return Token("WORD", token.value)

    @v_args(meta=True)
    def document_title(self, meta: Any, children: Children) -> Title:
        nodes = [c for c in children if isinstance(c, list)]
        title = Title(nodes[0] if nodes else [])
        return cast(Title, self._set_location_from_children(title, children))

    @v_args(meta=True)
    def block(self, meta: Any, children: Children) -> Transformed:
        return children[0] if children else Discard

    @v_args(meta=True)
    def blank_line(self, meta: Any, children: Children) -> Any:
        return Discard

    @v_args(meta=True)
    def comment(self, meta: Any, children: Children) -> Any:
        return Discard

    @v_args(meta=True)
    def attributed_block(self, meta: Any, children: Children) -> BlockNode:
        metadata = [c for c in children[:-1] if c is not Discard]
        block = cast(BlockNode, children[-1])

        for item in metadata:
            if isinstance(item, Title):
                block.title = item
            elif isinstance(item, dict):
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
                                block = Admonition(variant=variant, blocks=block.blocks)
                            else:
                                block.attributes["style"] = v
                        elif variant == "verse":
                            if isinstance(block, (Paragraph, Quote, Example, Open)):
                                blocks = (
                                    block.blocks
                                    if hasattr(block, "blocks")
                                    else [block]
                                )
                                delimiter = getattr(block, "delimiter", None)
                                block = Verse(blocks=blocks, delimiter=delimiter)
                            else:
                                block.attributes["style"] = v
                        elif variant == "quote":
                            if isinstance(block, (Paragraph, Example, Open)):
                                blocks = (
                                    block.blocks
                                    if hasattr(block, "blocks")
                                    else [block]
                                )
                                delimiter = getattr(block, "delimiter", None)
                                block = Quote(blocks=blocks, delimiter=delimiter)
                            else:
                                block.attributes["style"] = v
                        elif variant in ["discrete", "float"]:
                            if isinstance(block, Section):
                                block = FloatingTitle(level=block.level, title=block.title)
                            else:
                                block.attributes["style"] = v
                        elif variant == "stem":
                            # Determine variant (asciimath or latexmath)
                            stem_variant = self.attributes.get("stem", [Text("asciimath")])
                            if isinstance(stem_variant, list) and stem_variant:
                                variant_str = getattr(stem_variant[0], "value", "asciimath")
                            else:
                                variant_str = "asciimath"

                            if isinstance(block, (Passthrough, Paragraph)):
                                block = Stem(
                                    variant=variant_str,
                                    inlines=block.inlines,
                                    delimiter=getattr(block, "delimiter", None),
                                )
                            else:
                                block.attributes["style"] = v
                        else:
                            block.attributes["style"] = v
                    else:
                        block.attributes[k] = v
        return cast(BlockNode, self._set_location_from_children(block, children))

    @v_args(meta=True)
    def block_metadata(self, meta: Any, children: Children) -> Any:
        return children[0]

    @v_args(meta=True)
    def block_title(self, meta: Any, children: Children) -> Title:
        title = Title(children[0])
        return cast(Title, self._set_location_from_children(title, children))

    @v_args(meta=True)
    def attributed_simple_block(self, meta: Any, children: Children) -> BlockNode:
        return self.attributed_block(meta, children)

    @v_args(meta=True)
    def section_title(self, meta: Any, children: Children) -> Tuple[int, Title]:
        level = 1
        lead = [
            c
            for c in children
            if isinstance(c, Token) and c.type == "SECTION_TITLE_LEAD"
        ]
        if lead:
            level = max(0, lead[0].value.strip().count("=") - 1)

        nodes = [c for c in children if isinstance(c, list)]
        title_nodes = nodes[0] if nodes else []
        title = Title(title_nodes)
        self._set_location_from_children(title, children)
        return level, title

    @v_args(meta=True)
    def attribute_content(self, meta: Any, children: Children) -> str:
        return cast(str, children[0].value)

    @v_args(meta=True)
    def attribute_list(self, meta: Any, children: Children) -> Dict[str, str]:
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

        parts = [p.strip() for p in attr_str.split(",")]

        if parts and "=" not in parts[0] and not parts[0].startswith(("#", ".")):
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

    @v_args(meta=True)
    def attribute_entry(self, meta: Any, children: Children) -> AttributeEntry:
        name = ""
        value_nodes: PyList[Node] = []
        negated = False

        for c in children:
            if isinstance(c, Token):
                if c.type == "ATTR_NAME":
                    name = c.value
                elif c.type == "BANG":
                    negated = True
            elif isinstance(c, list):
                value_nodes = c

        node: AttributeEntry
        if negated:
            if name in self.attributes:
                del self.attributes[name]
            node = AttributeEntry(name, "!")  # Using "!" as a marker for negation
        else:
            self.attributes[name] = value_nodes
            # Use centralized logic to resolve rich nodes to a string value
            value_str = "".join([resolve_node_to_string(n) for n in value_nodes]).strip()
            node = AttributeEntry(name, value_str)
        
        return cast(AttributeEntry, self._set_location_from_children(node, children))

    @v_args(meta=True)
    def block_macro(self, meta: Any, children: Children) -> BlockNode:
        name = str(children[0].value).lower()
        target = str(children[1].value) if len(children) > 1 and children[1] else ""
        attrs = (
            children[2] if len(children) > 2 and isinstance(children[2], dict) else {}
        )

        block: BlockNode
        if name == "image":
            alt = attrs.get("style", "")
            block = Image(target=target, alt=alt, form="macro", type="block")
            block.attributes.update(attrs)
            if "style" in block.attributes:
                block.attributes["alt"] = block.attributes.pop("style")
        elif name == "toc":
            block = Toc(target=target, attributes=attrs)
        elif name == "audio":
            block = Audio(target=target, attributes=attrs)
        elif name == "video":
            block = Video(target=target, attributes=attrs)
        else:
            # Generic block macro
            block = BlockNode()
            block.name = name
            node = block
            node.attributes.update(attrs)
            if target:
                node.attributes["target"] = target
        
        return cast(BlockNode, self._set_location_from_children(block, children))

    @v_args(meta=True)
    def thematic_break(self, meta: Any, children: Children) -> ThematicBreak:
        return cast(ThematicBreak, self._set_location_from_children(ThematicBreak(), children))

    @v_args(meta=True)
    def page_break(self, meta: Any, children: Children) -> PageBreak:
        return cast(PageBreak, self._set_location_from_children(PageBreak(), children))

    @v_args(meta=True)
    def anchor(self, meta: Any, children: Children) -> Dict[str, str]:
        return {"id": str(children[0].value)}

    @v_args(meta=True)
    def inline_attribute_list(self, meta: Any, children: Children) -> Dict[str, str]:
        return self.attribute_list(meta, children)

    # --- Terminals ---

    def WHITESPACE(self, token: Token) -> Token:
        return Token("WORD", " ")

    def SECTION_TITLE_LEAD(self, token: Token) -> Any:
        return token

    def _NEWLINE(self, token: Token) -> Any:
        return Discard


DEFAULT_GRAMMAR = os.path.join(os.path.dirname(__file__), "grammar.lark")


def parse_to_ast(
    source: str,
    grammar_file: str = DEFAULT_GRAMMAR,
    base_dir: Optional[str] = None,
    safe_mode: bool = True,
) -> Document:
    preprocessor = Preprocessor(base_dir, safe_mode=safe_mode)
    processed_source = preprocessor.process(source)

    with open(grammar_file, "r") as f:
        grammar = f.read()
    parser = Lark(
        grammar,
        start="document",
        parser="earley",
        ambiguity="resolve",
        propagate_positions=True,
    )
    tree = parser.parse(processed_source)
    ast_root = AsciiDocTransformer().transform(tree)
    if not isinstance(ast_root, Document):
        raise TypeError("Parsing did not return a Document node.")
    return ast_root
