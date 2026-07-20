import os
import re
from typing import Any, Dict, Optional, Tuple, Union, cast
from typing import List as PyList

from lark import Discard, Lark, Token, Transformer, v_args
from lark.exceptions import UnexpectedInput

from .attributes import resolve_node_to_string
from .nodes import (
    Admonition,
    AttributeEntry,
    Audio,
    Author,
    BlockNode,
    Collapsible,
    Document,
    Example,
    FloatingTitle,
    Header,
    Image,
    Include,
    Node,
    NodeVisitor,
    Open,
    PageBreak,
    Paragraph,
    Passthrough,
    Quote,
    Revision,
    Section,
    Stem,
    Table,
    TableCell,
    TableRow,
    Text,
    ThematicBreak,
    Title,
    Toc,
    Verse,
    Video,
)
from .preprocessor import Preprocessor
from .transformers.base_transformer import LocationDict
from .transformers.block_transformer import BlockTransformer
from .transformers.inline_transformer import InlineTransformer


class AsciiDocSyntaxError(ValueError):
    """Raised when AsciiDoc source parsing encounters a syntax error."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        context: Optional[str] = None,
        filepath: Optional[str] = None,
    ):
        super().__init__(message)
        self.line = line
        self.column = column
        self.context = context
        self.filepath = filepath


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

    @v_args(meta=True)
    def document(self, meta: Any, children: Children) -> Document:
        doc = cast(Document, children[0])
        # Propagate all collected attributes (both header and body) to the Document node
        for k, v in self.attributes.items():
            if k not in doc.attributes:
                doc.attributes[k] = v
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
        return self.text_content(meta, children)  # type: ignore

    def AUTHOR_SPECIAL_CHARS(self, token: Token) -> Token:
        return Token("WORD", token.value)

    @v_args(meta=True)
    def document_title(self, meta: Any, children: Children) -> Title:
        all_nodes = []
        for c in children:
            if isinstance(c, list):
                all_nodes.extend(c)
        title = Title(all_nodes)
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
                                block = Quote(blocks=blocks, delimiter=delimiter)  # type: ignore
                            else:
                                block.attributes["style"] = v
                        elif variant in ["discrete", "float"]:
                            if isinstance(block, Section) and block.title:
                                block = FloatingTitle(
                                    level=block.level, title=block.title
                                )
                            else:
                                block.attributes["style"] = v

                        elif variant == "stem":
                            # Determine variant (asciimath or latexmath)
                            stem_variant = self.attributes.get(
                                "stem", [Text("asciimath")]
                            )
                            if isinstance(stem_variant, list) and stem_variant:
                                variant_str = getattr(
                                    stem_variant[0], "value", "asciimath"
                                )
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
        if isinstance(block, Table) and "cols" in block.attributes:
            try:
                cols_val = block.attributes["cols"]
                if isinstance(cols_val, list):
                    cols_str = "".join(n.value for n in cols_val if hasattr(n, "value"))
                elif hasattr(cols_val, "value"):
                    cols_str = cols_val.value
                else:
                    cols_str = str(cols_val)

                cols_str = cols_str.strip()
                num_cols = 0
                if cols_str.endswith("*"):
                    try:
                        num_cols = int(cols_str[:-1])
                    except ValueError:
                        pass
                elif "," in cols_str:
                    num_cols = len(cols_str.split(","))
                else:
                    try:
                        num_cols = int(cols_str)
                    except ValueError:
                        pass

                if num_cols > 0:
                    flat_cells = []
                    for row in block.rows:
                        for cell in row.cells:
                            if isinstance(cell, TableCell):
                                flat_cells.append(cell)

                    grid: PyList[PyList[Any]] = []
                    cell_idx = 0
                    while cell_idx < len(flat_cells):
                        r = 0
                        c = 0
                        found = False
                        while not found:
                            if r >= len(grid):
                                grid.append([None] * num_cols)
                            for col in range(num_cols):
                                if grid[r][col] is None:
                                    c = col
                                    found = True
                                    break
                            if not found:
                                r += 1

                        cell = flat_cells[cell_idx]
                        cell_idx += 1

                        colspan = getattr(cell, "colspan", 1) or 1
                        rowspan = getattr(cell, "rowspan", 1) or 1

                        for dr in range(rowspan):
                            for dc in range(colspan):
                                nr = r + dr
                                nc = c + dc
                                if nc < num_cols:
                                    while nr >= len(grid):
                                        grid.append([None] * num_cols)
                                    if dr == 0 and dc == 0:
                                        grid[nr][nc] = cell
                                    else:
                                        grid[nr][nc] = "spanned"

                    new_rows = []
                    for r in range(len(grid)):
                        row_cells: PyList[TableCell] = [
                            cell for cell in grid[r] if isinstance(cell, TableCell)
                        ]
                        if row_cells:
                            new_rows.append(TableRow(cells=row_cells))
                    block.rows = new_rows
            except Exception:
                pass

        # Check if the block is collapsible
        options = block.attributes.get("options", "")
        is_collapsible = False
        if isinstance(options, str):
            is_collapsible = "collapsible" in [
                opt.strip() for opt in options.split(",")
            ]
        elif isinstance(options, list):
            opt_strings = []
            for opt in options:
                if hasattr(opt, "value"):
                    opt_strings.append(opt.value)
                else:
                    opt_strings.append(str(opt))
            is_collapsible = "collapsible" in opt_strings

        style = block.attributes.get("style", "")
        if isinstance(style, str) and style.lower() == "collapsible":
            is_collapsible = True

        if is_collapsible and isinstance(block, (Example, Open)):
            blocks = block.blocks if hasattr(block, "blocks") else [block]
            collapsible_block = Collapsible(
                title=block.title,
                blocks=blocks,
                attributes=block.attributes,
            )
            collapsible_block.location = block.location
            block = collapsible_block

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
        return self.attributed_block(meta, children)  # type: ignore

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

        all_nodes = []
        for c in children:
            if isinstance(c, list):
                all_nodes.extend(c)
        title = Title(all_nodes)
        self._set_location_from_children(title, children)
        return level, title

    @v_args(meta=True)
    def attribute_content(self, meta: Any, children: Children) -> str:
        return cast(str, children[0].value)

    @v_args(meta=True)
    def attribute_list(self, meta: Any, children: Children) -> Dict[str, str]:
        attrs = LocationDict()
        if meta:
            attrs.location = [
                {"line": meta.line, "col": meta.column},
                {"line": meta.end_line, "col": meta.end_column - 1},
            ]

        attr_str = ""
        for c in children:
            if isinstance(c, Token) and c.type == "attribute_content":
                attr_str = c.value
                break
            elif isinstance(c, str) and c not in ("[", "]", "\n", "\r", "\r\n"):
                attr_str = c
                break

        if not attr_str:
            return attrs

        # Split parts by comma, respecting quoted strings
        parts = []
        current = []
        in_double = False
        in_single = False
        for char in attr_str:
            if char == '"' and not in_single:
                in_double = not in_double
                current.append(char)
            elif char == "'" and not in_double:
                in_single = not in_single
                current.append(char)
            elif char == "," and not in_double and not in_single:
                parts.append("".join(current))
                current = []
            else:
                current.append(char)
        parts.append("".join(current))
        parts = [p.strip() for p in parts]

        for idx, part in enumerate(parts, 1):
            if not part:
                continue
            if "=" in part:
                k, v = part.split("=", 1)
                attrs[k.strip()] = v.strip().strip('"').strip("'")
            elif part.startswith("#") or part.startswith("."):
                # Parse shorthands (supporting multiple, e.g. #id.role)
                curr = part
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
            elif part.startswith("%"):
                option = part[1:]
                if "options" in attrs:
                    attrs["options"] += f",{option}"
                else:
                    attrs["options"] = option

        # Map positional attributes (non-named, non-shorthand, non-option for style/language)
        positional_parts = [
            p for p in parts if p and "=" not in p and not p.startswith(("#", ".", "%"))
        ]
        if positional_parts:
            attrs["style"] = positional_parts[0]
            if attrs["style"].lower() == "source" and len(positional_parts) > 1:
                attrs["language"] = positional_parts[1]

        # Store 1-based string keys and the full positional list
        positional_list = []
        for idx, part in enumerate(parts, 1):
            if not part:
                continue
            if "=" in part:
                continue
            # Shorthands (id, role, options) are included as positional attributes in their raw format
            val = part.strip('"').strip("'")
            attrs[str(idx)] = val
            positional_list.append(val)

        if positional_list:
            attrs["positional"] = positional_list

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
            value_str = "".join(
                [resolve_node_to_string(n) for n in value_nodes]
            ).strip()
            node = AttributeEntry(name, value_str)

        return cast(AttributeEntry, self._set_location_from_children(node, children))

    @v_args(meta=True)
    def block_macro(self, meta: Any, children: Children) -> BlockNode:
        name = str(children[0].value).lower()
        target = ""
        target_token = next(
            (
                c
                for c in children
                if isinstance(c, Token) and c.type == "MACRO_TARGET"
            ),
            None,
        )
        if target_token is not None:
            target = str(target_token.value)
        attrs = {}
        attr_token = next(
            (
                c
                for c in children
                if isinstance(c, Token) and c.type == "attribute_content"
            ),
            None,
        )
        if attr_token is not None:
            attrs = self.attribute_list(meta, [attr_token])

        block: BlockNode
        if name == "image":
            alt = attrs.get("style", "")
            block = Image(target=target, alt=alt, form="macro", type="block")
            block.attributes.update(attrs)
            if "style" in block.attributes:
                block.attributes["alt"] = block.attributes.pop("style")
        elif name == "toc":
            block = Toc(target=target, attributes=attrs)
        elif name == "include":
            block = Include(filename=target)
            block.attributes.update(attrs)
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

        block.is_macro = True
        return cast(BlockNode, self._set_location_from_children(block, children))

    @v_args(meta=True)
    def thematic_break(self, meta: Any, children: Children) -> ThematicBreak:
        return cast(
            ThematicBreak, self._set_location_from_children(ThematicBreak(), children)
        )

    @v_args(meta=True)
    def page_break(self, meta: Any, children: Children) -> PageBreak:
        return cast(PageBreak, self._set_location_from_children(PageBreak(), children))

    @v_args(meta=True)
    def anchor(self, meta: Any, children: Children) -> Dict[str, str]:
        return {"id": str(children[0].value)}

    @v_args(meta=True)
    def inline_attribute_list(self, meta: Any, children: Children) -> Dict[str, str]:
        return self.attribute_list(meta, children)  # type: ignore

    # --- Terminals ---

    def WHITESPACE(self, token: Token) -> Any:
        return token

    def _WS(self, token: Token) -> Any:
        return Discard

    def SECTION_TITLE_LEAD(self, token: Token) -> Any:
        return token

    def _NEWLINE(self, token: Token) -> Any:
        return Discard


DEFAULT_GRAMMAR = os.path.join(os.path.dirname(__file__), "grammar.lark")


class ASTSyntaxAuditor(NodeVisitor):
    """
    Traverses the parsed AST to enforce strict syntax validation on elements
    that Lark's permissive Earley parser falls back on (e.g. malformed paragraphs or blocks).
    """

    def __init__(
        self,
        source_lines: PyList[str],
        line_map: Optional[Dict[int, Tuple[str, int]]] = None,
    ) -> None:
        super().__init__()
        self.source_lines = source_lines
        self.line_map = line_map or {}

    def _get_origin(self, line_idx: int) -> Tuple[Optional[str], int]:
        return self.line_map.get(line_idx, (None, line_idx))

    def visit_paragraph(self, node: Node) -> None:
        if node.location:
            line_idx = node.location[0].get("line", 1)
        else:
            line_idx = 1

        # Reconstruct raw paragraph text from its inline children to preserve exact coordinates
        text_content = ""
        for child in getattr(node, "inlines", []):
            if hasattr(child, "value") and child.value is not None:
                text_content += str(child.value)
            elif hasattr(child, "children"):
                def get_text(n: Node) -> str:
                    t = ""
                    if hasattr(n, "value") and n.value is not None:
                        t += str(n.value)
                    for c in getattr(n, "children", []):
                        t += get_text(c)
                    return t
                text_content += get_text(child)

        lines = text_content.splitlines()
        for offset, line in enumerate(lines):
            idx = line_idx + offset
            line_strip = line.strip()
            if not line_strip:
                continue

            # 1. Malformed block attribute lists (unclosed or unbalanced brackets)
            if line_strip.startswith("[") and not line_strip.startswith("[["):
                open_brackets = line_strip.count("[")
                close_brackets = line_strip.count("]")
                if open_brackets != close_brackets:
                    origin_file, origin_line = self._get_origin(idx)
                    raise AsciiDocSyntaxError(
                        f"Syntax error: Malformed block attribute list (unbalanced brackets) at line {origin_line}.",
                        line=origin_line,
                        column=1,
                        context=line,
                        filepath=origin_file,
                    )

            # 2. Malformed block macros (e.g. image::logo.png with missing brackets)
            # Handled on actual block macro nodes (Image, Include, etc.) under generic_visit,
            # but if it was parsed as a Paragraph instead:
            if "::" in line_strip and "[" not in line_strip and "]" not in line_strip:
                if not any(
                    line_strip.startswith(prefix)
                    for prefix in ["http://", "https://", "ftp://", "file://"]
                ):
                    macro_match = re.match(
                        r"^\s*([a-zA-Z0-9_-]+)::([^\s\[:]+)$", line_strip
                    )
                    if macro_match:
                        origin_file, origin_line = self._get_origin(idx)
                        raise AsciiDocSyntaxError(
                            f"Syntax error: Malformed block macro '{macro_match.group(1)}::' (missing brackets) at line {origin_line}.",
                            line=origin_line,
                            column=len(line) - len(line.lstrip()) + 1,
                            context=line,
                            filepath=origin_file,
                        )

            # 3. Malformed description lists (e.g. marker on its own with no term)
            if re.match(r"^\s*(::+|;;)\s+", line_strip) or line_strip in (
                "::",
                ":::",
                "::::",
                ";;",
            ):
                origin_file, origin_line = self._get_origin(idx)
                raise AsciiDocSyntaxError(
                    f"Syntax error: Malformed description list marker (missing term) at line {origin_line}.",
                    line=origin_line,
                    column=1,
                    context=line,
                    filepath=origin_file,
                )

            # 4. Malformed inline anchors (unclosed [[)
            if "[[" in line_strip and "]]" not in line_strip:
                origin_file, origin_line = self._get_origin(idx)
                raise AsciiDocSyntaxError(
                    f"Syntax error: Unclosed inline anchor at line {origin_line}.",
                    line=origin_line,
                    column=line.find("[[") + 1,
                    context=line,
                    filepath=origin_file,
                )

            # 5. Unclosed inline footnotes
            for fn_type in ("footnote:[", "footnoteref:["):
                if fn_type in line_strip:
                    start_idx = line_strip.find(fn_type)
                    sub = line_strip[start_idx:]
                    open_cnt = 0
                    closed = False
                    for char in sub:
                        if char == "[":
                            open_cnt += 1
                        elif char == "]":
                            open_cnt -= 1
                            if open_cnt == 0:
                                closed = True
                                break
                    if not closed:
                        origin_file, origin_line = self._get_origin(idx)
                        raise AsciiDocSyntaxError(
                            f"Syntax error: Unclosed inline footnote at line {origin_line}.",
                            line=origin_line,
                            column=line.find(fn_type) + 1,
                            context=line,
                            filepath=origin_file,
                        )

        self.generic_visit(node)

    def visit_cell(self, node: Node) -> None:
        if node.location:
            line_idx = node.location[0].get("line")
            col_idx = node.location[0].get("col", 1)
            if line_idx and 1 <= line_idx <= len(self.source_lines):
                line = self.source_lines[line_idx - 1]
                # Extract text starting at this cell's column
                cell_text = line[col_idx - 1 :]
                if cell_text.startswith("|") and cell_text != "|===":
                    spec_match = re.match(r"^\|([0-9.+\*]*[<>\^.]*[adehlms]?)\s", cell_text)
                    if spec_match:
                        spec_content = spec_match.group(1)
                        if spec_content:
                            is_valid = True
                            if ".." in spec_content:
                                is_valid = False
                            elif spec_content.endswith("."):
                                is_valid = False
                            elif any(c in spec_content for c in "0123456789.+*"):
                                has_plus = "+" in spec_content
                                has_star = "*" in spec_content
                                if not (has_plus or has_star):
                                    is_valid = False
                            if not is_valid:
                                origin_file, origin_line = self._get_origin(line_idx)
                                raise AsciiDocSyntaxError(
                                    f"Syntax error: Malformed table cell specifier '{spec_content}' at line {origin_line}.",
                                    line=origin_line,
                                    column=col_idx + 1,
                                    context=line,
                                    filepath=origin_file,
                                )
        self.generic_visit(node)

    def generic_visit(self, node: Node, **kwargs: Any) -> Any:
        if getattr(node, "is_macro", False) and node.location:
            line_idx = node.location[0].get("line")
            if line_idx and 1 <= line_idx <= len(self.source_lines):
                line = self.source_lines[line_idx - 1]
                line_strip = line.strip()
                if "[" not in line_strip or "]" not in line_strip:
                    origin_file, origin_line = self._get_origin(line_idx)
                    raise AsciiDocSyntaxError(
                        f"Syntax error: Malformed block macro '{node.name}::' (missing brackets) at line {origin_line}.",
                        line=origin_line,
                        column=len(line) - len(line.lstrip()) + 1,
                        context=line,
                        filepath=origin_file,
                    )
        return super().generic_visit(node, **kwargs)


def parse_to_ast(
    source: str,
    grammar_file: str = DEFAULT_GRAMMAR,
    base_dir: Optional[str] = None,
    safe_mode: bool = True,
    preprocess_directives: bool = True,
    strict: bool = True,
) -> Document:
    # Detect if the original document preferred Windows CRLF or standard Unix LF
    # by checking if the very first newline sequence in the file is \r\n
    first_lf = source.find("\n")
    if first_lf != -1 and first_lf > 0 and source[first_lf - 1] == "\r":
        line_ending = "\r\n"
    else:
        line_ending = "\n"

    had_trailing_newline = (
        source.endswith("\n") or source.endswith("\r") if source else True
    )

    # Standardize all line endings to LF for internal parsing robust performance
    source = source.replace("\r\n", "\n").replace("\r", "\n")

    if source and not source.endswith("\n"):
        source += "\n"

    preprocessor = Preprocessor(
        base_dir, safe_mode=safe_mode, preprocess_directives=preprocess_directives
    )
    processed_source = preprocessor.process(source)

    if strict:
        # Check for unclosed verbatim blocks
        if getattr(preprocessor, "root_in_verbatim", None) is not None:
            raise AsciiDocSyntaxError(
                f"Syntax error: Unclosed verbatim block '{preprocessor.root_in_verbatim}'."
            )
        # Check for unclosed block delimiters
        if getattr(preprocessor, "root_delimiter_stack", None):
            raise AsciiDocSyntaxError(
                f"Syntax error: Unclosed block delimiter '{preprocessor.root_delimiter_stack[-1]}'."
            )

    with open(grammar_file, "r") as f:
        grammar = f.read()
    parser = Lark(
        grammar,
        start="document",
        parser="earley",
        ambiguity="resolve",
        propagate_positions=True,
    )
    try:
        tree = parser.parse(processed_source)
    except UnexpectedInput as e:
        context = e.get_context(processed_source)
        origin_file, origin_line = preprocessor.line_map.get(e.line, (None, e.line))
        message = f"Syntax error at line {origin_line}, column {e.column}.\n{context}"
        if origin_file and origin_file != "<root>":
            message = f"Syntax error in {os.path.basename(origin_file)} at line {origin_line}, column {e.column}.\n{context}"
        raise AsciiDocSyntaxError(
            message, line=origin_line, column=e.column, context=context, filepath=origin_file
        ) from e
    ast_root = AsciiDocTransformer().transform(tree)
    if not isinstance(ast_root, Document):
        raise TypeError("Parsing did not return a Document node.")
    ast_root.had_trailing_newline = had_trailing_newline
    ast_root.line_ending = line_ending
    ast_root.is_preprocessed = preprocessor.is_preprocessed
    ast_root.included_files = sorted(list(preprocessor.included_files_set))

    if strict:
        ASTSyntaxAuditor(
            processed_source.splitlines(), line_map=preprocessor.line_map
        ).visit(ast_root)

    return ast_root


_INLINE_PARSER = None


def parse_inlines(
    source: str,
    grammar_file: str = DEFAULT_GRAMMAR,
) -> PyList[Node]:
    """
    Parses a string containing only inline elements directly starting from 'text_content'.
    """
    global _INLINE_PARSER
    if _INLINE_PARSER is None:
        with open(grammar_file, "r") as f:
            grammar = f.read()
        _INLINE_PARSER = Lark(
            grammar,
            start="text_content",
            parser="earley",
            ambiguity="resolve",
            propagate_positions=True,
        )
    try:
        tree = _INLINE_PARSER.parse(source)
    except UnexpectedInput as e:
        context = e.get_context(source)
        message = f"Syntax error at line {e.line}, column {e.column}.\n{context}"
        raise AsciiDocSyntaxError(
            message, line=e.line, column=e.column, context=context
        ) from e
    result = AsciiDocTransformer().transform(tree)
    if isinstance(result, list):
        return result
    elif isinstance(result, Node):
        return [result]
    else:
        return []
