import os
import re
from typing import Any, Dict, Optional, Sequence, Tuple, Union, cast
from typing import List as PyList

from lark import Discard, Lark, Token, Transformer

from .attributes import resolve_node_to_string
from .nodes import (
    AttributeEntry,
    Author,
    BlockNode,
    Document,
    Header,
    Image,
    Node,
    PageBreak,
    Revision,
    Section,
    Ref,
    Text,
    ThematicBreak,
    Title,
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

    def document(self, children: Children) -> Document:
        return cast(Document, children[0])

    def document_header_with_body(self, children: Children) -> Document:
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
        return doc

    def body_only(self, children: Children) -> Document:
        final_blocks = self._finalize_document_blocks(children)
        return Document(final_blocks)

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

    def document_header(self, children: Children) -> Header:
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
        from .nodes import Admonition, Example

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
                        else:
                            block.attributes["style"] = v
                    else:
                        block.attributes[k] = v
        return block

    def block_metadata(self, children: Children) -> Any:
        return children[0]

    def block_title(self, children: Children) -> Title:
        return Title(children[0])

    def attributed_simple_block(self, children: Children) -> BlockNode:
        return self.attributed_block(children)

    def section_title(self, children: Children) -> Tuple[int, Title]:
        level = 1
        lead = [
            c
            for c in children
            if isinstance(c, Token) and c.type == "SECTION_TITLE_LEAD"
        ]
        if lead:
            level = max(1, lead[0].value.strip().count("=") - 1)

        nodes = [c for c in children if isinstance(c, list)]
        title_nodes = nodes[0] if nodes else []
        return level, Title(title_nodes)

    def attribute_content(self, children: Children) -> str:
        return cast(str, children[0].value)

    def attribute_list(self, children: Children) -> Dict[str, str]:
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

    def attribute_entry(self, children: Children) -> AttributeEntry:
        name = ""
        value_nodes: PyList[Node] = []
        for c in children:
            if isinstance(c, Token) and (c.type == "ATTR_NAME" or c.type == "COLON"):
                if c.type == "ATTR_NAME":
                    name = c.value
            elif isinstance(c, list):
                value_nodes = c

        self.attributes[name] = value_nodes

        # Use centralized logic to resolve rich nodes to a string value
        value_str = "".join([resolve_node_to_string(n) for n in value_nodes]).strip()

        return AttributeEntry(name, value_str)

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

    def thematic_break(self, children: Children) -> ThematicBreak:
        return ThematicBreak()

    def page_break(self, children: Children) -> PageBreak:
        return PageBreak()

    def anchor(self, children: Children) -> Dict[str, str]:
        return {"id": str(children[0].value)}

    def inline_attribute_list(self, children: Children) -> Dict[str, str]:
        return self.attribute_list(children)

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
    parser = Lark(grammar, start="document", parser="earley")
    tree = parser.parse(processed_source)
    ast_root = AsciiDocTransformer().transform(tree)
    if not isinstance(ast_root, Document):
        raise TypeError("Parsing did not return a Document node.")
    return ast_root
