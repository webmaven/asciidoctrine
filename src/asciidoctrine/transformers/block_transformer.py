from typing import Any, Dict, Optional, Sequence, Tuple, cast
from typing import List as PyList

from lark import Discard, Token, v_args

from ..nodes import (
    Admonition,
    BlockNode,
    CalloutList,
    CalloutListItem,
    Comment,
    DescriptionList,
    DescriptionListItem,
    DescriptionListTerm,
    Example,
    Listing,
    ListItem,
    Literal,
    Node,
    Open,
    Paragraph,
    Passthrough,
    Quote,
    Section,
    Sidebar,
    Table,
    TableCell,
    TableRow,
    Text,
)
from ..nodes import (
    List as ASTList,
)
from .base_transformer import BaseTransformer


class BlockTransformer(BaseTransformer):
    """
    Mixin class for block-level AsciiDoc transformations.
    """

    def _merge_consecutive_lists(self, blocks: Sequence[BlockNode]) -> PyList[Node]:
        if not blocks:
            return []

        merged_blocks: PyList[Node] = [blocks[0]]
        for current_block in blocks[1:]:
            prev_block = merged_blocks[-1]

            if (
                isinstance(current_block, ASTList)
                and isinstance(prev_block, ASTList)
                and current_block.variant == prev_block.variant
            ):
                prev_block.items.extend(current_block.items)
                if prev_block.location and current_block.location:
                    prev_block.location[1] = current_block.location[1]
            elif isinstance(current_block, DescriptionList) and isinstance(
                prev_block, DescriptionList
            ):
                prev_block.items.extend(current_block.items)
                if prev_block.location and current_block.location:
                    prev_block.location[1] = current_block.location[1]
            elif isinstance(current_block, CalloutList) and isinstance(
                prev_block, CalloutList
            ):
                prev_block.items.extend(current_block.items)
                if prev_block.location and current_block.location:
                    prev_block.location[1] = current_block.location[1]
            else:
                merged_blocks.append(current_block)
        return merged_blocks

    def _get_list_level(self, marker_token: Token) -> int:
        raw_marker = marker_token.value
        indent = len(raw_marker) - len(raw_marker.lstrip())
        marker = raw_marker.strip()

        # Base level from marker
        if marker.startswith("-"):
            level = 1
        elif marker.startswith("*"):
            level = len(marker)
        elif marker.startswith("."):
            level = len(marker)
        else:
            level = 1

        # Add 1 level for every 2 spaces of indentation (common convention)
        level += indent // 2
        return level

    def _nest_list_items(self, items: PyList[Dict[str, Any]]) -> PyList[ListItem]:
        if not items:
            return []

        root_lists: PyList[ASTList] = []
        stack: PyList[Tuple[int, ASTList]] = []

        for item_data in items:
            level = item_data["level"]
            item_type = item_data["item_type"]
            marker = item_data["marker"]

            while stack and level < stack[-1][0]:
                stack.pop()

            list_node: ASTList
            if not stack:
                variant = "unordered" if item_type == "bullet" else "ordered"
                list_node = ASTList(variant=variant, marker=marker)
                root_lists.append(list_node)
                stack.append((level, list_node))
            elif level > stack[-1][0]:
                # Deepen nesting
                parent_list = stack[-1][1]
                # If parent list has items, nest under the last item
                if parent_list.items:
                    last_item = parent_list.items[-1]
                    variant = "unordered" if item_type == "bullet" else "ordered"
                    list_node = ASTList(variant=variant, marker=marker)
                    last_item.blocks.append(list_node)
                    stack.append((level, list_node))
                else:
                    # Parent list exists but has no items (should not happen normally)
                    list_node = parent_list
                    # Update its level to the new one if it was just started
                    stack[-1] = (level, list_node)
            else:
                # Sibling at same level
                list_node = stack[-1][1]
                # Ensure variant matches if possible, or start new list if it changed
                variant = "unordered" if item_type == "bullet" else "ordered"
                if list_node.variant != variant:
                    # Variant change at same level implies a new list sibling
                    # In our AST, these are often merged, but let's see.
                    pass

            item = ListItem(
                marker=marker,
                principal=item_data["children"],
                checked=item_data.get("checked"),
            )
            if "raw_children" in item_data:
                self._set_location_from_children(item, item_data["raw_children"])
            list_node.items.append(item)

            # Update list_node location to encompass items
            if not list_node.location:
                list_node.location = item.location
            elif item.location:
                list_node.location[1] = item.location[1]

        all_root_children: PyList[ListItem] = []
        for rl in root_lists:
            all_root_children.extend(rl.items)
        return all_root_children

    @v_args(meta=True)
    def section(self, meta: Any, children: PyList[Any]) -> Section:
        # Now section is flat: children[0] is (level, title)
        level, title = children[0]
        section = Section(level=level, title=title, blocks=[])
        return cast(Section, self._set_location_from_children(section, children))

    @v_args(meta=True)
    def indented_literal(self, meta: Any, children: PyList[Any]) -> Literal:
        # children[0] is INDENTED_LITERAL_LEAD
        # children[1] is text_content (list of nodes)
        # Note: TCK might expect lead whitespace stripped or kept depending on
        # the 'indent' attribute.
        # By default, we keep the content but strip the leading token itself if it's
        # just spaces.
        content = children[1]
        node = Literal(inlines=content, form="indented")
        return cast(Literal, self._set_location_from_children(node, children))

    @v_args(meta=True)
    def paragraph(self, meta: Any, children: PyList[Any]) -> Paragraph:
        actual_lines = [c for c in children if isinstance(c, list)]
        all_inlines: PyList[Node] = []
        for i, line in enumerate(actual_lines):
            if i > 0:
                all_inlines.append(Text("\n"))
            all_inlines.extend(line)

        consolidated: PyList[Node] = []
        for node in all_inlines:
            if (
                consolidated
                and isinstance(consolidated[-1], Text)
                and isinstance(node, Text)
                and consolidated[-1].attributes == node.attributes
            ):
                consolidated[-1].value += node.value
                if node.location:
                    if not consolidated[-1].location:
                        consolidated[-1].location = node.location
                    else:
                        consolidated[-1].location[1] = node.location[1]
            else:
                consolidated.append(node)

        para = Paragraph(inlines=consolidated)
        return cast(Paragraph, self._set_location_from_children(para, children))

    @v_args(meta=True)
    def ulist(self, meta: Any, children: PyList[Any]) -> ASTList:
        items = self._nest_list_items(children)
        marker = children[0]["marker"] if children else "*"
        list_node = ASTList(variant="unordered", marker=marker, items=items)
        return cast(ASTList, self._set_location_from_children(list_node, items))

    @v_args(meta=True)
    def olist(self, meta: Any, children: PyList[Any]) -> ASTList:
        items = self._nest_list_items(children)
        marker = children[0]["marker"] if children else "."
        list_node = ASTList(variant="ordered", marker=marker, items=items)
        return cast(ASTList, self._set_location_from_children(list_node, items))

    @v_args(meta=True)
    def dlist(self, meta: Any, children: PyList[Any]) -> DescriptionList:
        list_node = DescriptionList(items=children)
        return cast(
            DescriptionList, self._set_location_from_children(list_node, children)
        )

    @v_args(meta=True)
    def dlist_item(self, meta: Any, children: PyList[Any]) -> DescriptionListItem:
        terms: PyList[DescriptionListTerm] = []
        blocks: PyList[Node] = []
        for child in children:
            if isinstance(child, DescriptionListTerm):
                terms.append(child)
            elif isinstance(child, list):  # description blocks
                blocks.extend(child)
            elif isinstance(child, BlockNode):
                blocks.append(child)
        item = DescriptionListItem(terms=terms, blocks=blocks)
        return cast(
            DescriptionListItem, self._set_location_from_children(item, children)
        )

    @v_args(meta=True)
    def dlist_term(self, meta: Any, children: PyList[Any]) -> DescriptionListTerm:
        # children[0] is text_content (list of inlines)
        # children[1] is DLIST_MARKER
        inlines = children[0]

        # Strip leading whitespace from the first text node
        if inlines and isinstance(inlines[0], Text):
            original_val = inlines[0].value
            inlines[0].value = original_val.lstrip()
            if inlines[0].location and len(original_val) > len(inlines[0].value):
                # Adjust start column
                diff = len(original_val) - len(inlines[0].value)
                inlines[0].location[0]["col"] += diff

        term = DescriptionListTerm(inlines=inlines)
        return cast(
            DescriptionListTerm, self._set_location_from_children(term, children)
        )

    @v_args(meta=True)
    def dlist_description(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return [c for c in children if isinstance(c, BlockNode)]

    @v_args(meta=True)
    def colist(self, meta: Any, children: PyList[Any]) -> CalloutList:
        list_node = CalloutList(items=children)
        return cast(CalloutList, self._set_location_from_children(list_node, children))

    @v_args(meta=True)
    def colist_item(self, meta: Any, children: PyList[Any]) -> CalloutListItem:
        number = int(children[0].value)
        # Filter out WHITESPACE tokens to find the actual list of inline text nodes
        nodes = [
            c
            for c in children[1:]
            if not (hasattr(c, "type") and getattr(c, "type") == "WHITESPACE")
        ]
        content = nodes[0] if nodes else []
        item = CalloutListItem(number=number, principal=content)
        return cast(CalloutListItem, self._set_location_from_children(item, children))

    @v_args(meta=True)
    def ulist_item(self, meta: Any, children: PyList[Any]) -> Dict[str, Any]:
        marker_token = children[0]
        level = self._get_list_level(marker_token)

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
            "raw_children": children,
            "meta": meta,
        }
        if checkbox:
            val = checkbox.value.strip("[] ")
            item_data["checked"] = val.lower() in ["x", "*"]

        return item_data

    @v_args(meta=True)
    def olist_item(self, meta: Any, children: PyList[Any]) -> Dict[str, Any]:
        marker_token = children[0]
        level = self._get_list_level(marker_token)
        content = children[1]
        return {
            "level": level,
            "item_type": "enumerated",
            "marker": marker_token.value.strip(),
            "children": content,
            "raw_children": children,
            "meta": meta,
        }

    @v_args(meta=True)
    def basic_block(self, meta: Any, children: PyList[Any]) -> Any:
        return children[0] if children else Discard

    @v_args(meta=True)
    def admonition_content(self, meta: Any, children: PyList[Any]) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    @v_args(meta=True)
    def sidebar_content(self, meta: Any, children: PyList[Any]) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    @v_args(meta=True)
    def example_content(self, meta: Any, children: PyList[Any]) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    @v_args(meta=True)
    def example_block(self, meta: Any, children: PyList[Any]) -> Example:
        return cast(Example, children[0])

    @v_args(meta=True)
    def example_4(self, meta: Any, children: PyList[Any]) -> Example:
        return cast(
            Example,
            self._set_location_from_children(
                self._build_example_block(children), children
            ),
        )

    @v_args(meta=True)
    def example_5(self, meta: Any, children: PyList[Any]) -> Example:
        return cast(
            Example,
            self._set_location_from_children(
                self._build_example_block(children), children
            ),
        )

    @v_args(meta=True)
    def example_6(self, meta: Any, children: PyList[Any]) -> Example:
        return cast(
            Example,
            self._set_location_from_children(
                self._build_example_block(children), children
            ),
        )

    def _build_example_block(self, children: PyList[Any]) -> Example:
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type.startswith("ADMONITION_DELIM_")
        ]

        blocks = [c for c in children if isinstance(c, BlockNode)]
        merged_inner = self._merge_consecutive_lists(blocks)
        delimiter = delims[0].value if delims else "===="
        return Example(blocks=merged_inner, delimiter=delimiter)

    @v_args(meta=True)
    def listing_block(self, meta: Any, children: PyList[Any]) -> Listing:
        content = ""
        attributes: Dict[str, Any] = {}
        content_token = None
        delims = [
            c for c in children if isinstance(c, Token) and c.type == "LISTING_DELIM"
        ]

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "LISTING_CONTENT":
                content = c.value
                content_token = c

        delimiter = delims[0].value if delims else "----"
        text_node = Text(content)
        if content_token:
            self._set_location_from_children(text_node, [content_token])
        listing = Listing(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Listing, self._set_location_from_children(listing, children))

    @v_args(meta=True)
    def literal_block(self, meta: Any, children: PyList[Any]) -> Literal:
        content = ""
        attributes: Dict[str, Any] = {}
        content_token = None
        delims = [
            c for c in children if isinstance(c, Token) and c.type == "LITERAL_DELIM"
        ]

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "LITERAL_CONTENT":
                content = c.value
                content_token = c

        delimiter = delims[0].value if delims else "...."
        text_node = Text(content)
        if content_token:
            self._set_location_from_children(text_node, [content_token])
        literal = Literal(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Literal, self._set_location_from_children(literal, children))

    @v_args(meta=True)
    def passthrough_block(self, meta: Any, children: PyList[Any]) -> Passthrough:
        content = ""
        attributes: Dict[str, Any] = {}
        content_token = None
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type == "PASSTHROUGH_BLOCK_DELIM"
        ]

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "PASSTHROUGH_CONTENT":
                content = c.value
                content_token = c

        delimiter = delims[0].value if delims else "++++"
        text_node = Text(content)
        if content_token:
            self._set_location_from_children(text_node, [content_token])
        pass_node = Passthrough(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Passthrough, self._set_location_from_children(pass_node, children))

    @v_args(meta=True)
    def outer_listing_block(self, meta: Any, children: PyList[Any]) -> Listing:
        content = ""
        attributes: Dict[str, Any] = {}
        content_token = None
        start_token = None

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "OUTER_LISTING_START":
                start_token = c
            elif isinstance(c, Token) and c.type == "OUTER_LISTING_CONTENT":
                content = c.value
                content_token = c

        delimiter = "----"
        if start_token:
            import re

            m = re.search(r"_(\d+)--$", start_token.value)
            if m:
                delimiter = "-" * int(m.group(1))

        text_node = Text(content)
        if content_token:
            self._set_location_from_children(text_node, [content_token])
        listing = Listing(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Listing, self._set_location_from_children(listing, children))

    @v_args(meta=True)
    def outer_literal_block(self, meta: Any, children: PyList[Any]) -> Literal:
        content = ""
        attributes: Dict[str, Any] = {}
        content_token = None
        start_token = None

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "OUTER_LITERAL_START":
                start_token = c
            elif isinstance(c, Token) and c.type == "OUTER_LITERAL_CONTENT":
                content = c.value
                content_token = c

        delimiter = "...."
        if start_token:
            import re

            m = re.search(r"_(\d+)--$", start_token.value)
            if m:
                delimiter = "." * int(m.group(1))

        text_node = Text(content)
        if content_token:
            self._set_location_from_children(text_node, [content_token])
        literal = Literal(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Literal, self._set_location_from_children(literal, children))

    @v_args(meta=True)
    def outer_passthrough_block(self, meta: Any, children: PyList[Any]) -> Passthrough:
        content = ""
        attributes: Dict[str, Any] = {}
        content_token = None
        start_token = None

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "OUTER_PASSTHROUGH_START":
                start_token = c
            elif isinstance(c, Token) and c.type == "OUTER_PASSTHROUGH_CONTENT":
                content = c.value
                content_token = c

        delimiter = "++++"
        if start_token:
            import re

            m = re.search(r"_(\d+)--$", start_token.value)
            if m:
                delimiter = "+" * int(m.group(1))

        text_node = Text(content)
        if content_token:
            self._set_location_from_children(text_node, [content_token])
        pass_node = Passthrough(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Passthrough, self._set_location_from_children(pass_node, children))

    @v_args(meta=True)
    def outer_comment_block(self, meta: Any, children: PyList[Any]) -> Comment:
        content = ""
        attributes: Dict[str, Any] = {}
        start_token = None

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "OUTER_COMMENT_START":
                start_token = c
            elif isinstance(c, Token) and c.type == "OUTER_COMMENT_CONTENT":
                content = c.value

        delimiter = "////"
        if start_token:
            import re

            m = re.search(r"_(\d+)--$", start_token.value)
            if m:
                delimiter = "/" * int(m.group(1))

        comment = Comment(value=content, attributes=attributes, delimiter=delimiter)
        return cast(Comment, self._set_location_from_children(comment, children))

    @v_args(meta=True)
    def admonition(self, meta: Any, children: PyList[Any]) -> Admonition:
        return cast(Admonition, children[0])

    @v_args(meta=True)
    def admonition_4(self, meta: Any, children: PyList[Any]) -> Admonition:
        return cast(
            Admonition,
            self._set_location_from_children(
                self._build_admonition(children), children
            ),
        )

    @v_args(meta=True)
    def admonition_5(self, meta: Any, children: PyList[Any]) -> Admonition:
        return cast(
            Admonition,
            self._set_location_from_children(
                self._build_admonition(children), children
            ),
        )

    @v_args(meta=True)
    def admonition_6(self, meta: Any, children: PyList[Any]) -> Admonition:
        return cast(
            Admonition,
            self._set_location_from_children(
                self._build_admonition(children), children
            ),
        )

    @v_args(meta=True)
    def shorthand_admonition(self, meta: Any, children: PyList[Any]) -> Admonition:
        variant = "note"
        content = []
        for child in children:
            if isinstance(child, Token) and child.type == "ADMONITION_TYPE":
                variant = str(child.value).lower()
            elif isinstance(child, list):
                content = child
        para = Paragraph(inlines=content)
        self._set_location_from_children(para, children)
        adm = Admonition(variant=variant, blocks=[para], delimiter=None)
        return cast(Admonition, self._set_location_from_children(adm, children))

    def _build_admonition(self, children: PyList[Any]) -> Admonition:
        start_token = children[0]
        variant = start_token.value.strip("[] ").lower()
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type.startswith("ADMONITION_DELIM_")
        ]

        blocks = [c for c in children if isinstance(c, BlockNode)]

        merged_inner = self._merge_consecutive_lists(blocks)
        delimiter = delims[0].value if delims else "===="
        return Admonition(variant=variant, blocks=merged_inner, delimiter=delimiter)

    @v_args(meta=True)
    def sidebar(self, meta: Any, children: PyList[Any]) -> Sidebar:
        return cast(Sidebar, children[0])

    @v_args(meta=True)
    def sidebar_4(self, meta: Any, children: PyList[Any]) -> Sidebar:
        return cast(
            Sidebar,
            self._set_location_from_children(self._build_sidebar(children), children),
        )

    @v_args(meta=True)
    def sidebar_5(self, meta: Any, children: PyList[Any]) -> Sidebar:
        return cast(
            Sidebar,
            self._set_location_from_children(self._build_sidebar(children), children),
        )

    @v_args(meta=True)
    def sidebar_6(self, meta: Any, children: PyList[Any]) -> Sidebar:
        return cast(
            Sidebar,
            self._set_location_from_children(self._build_sidebar(children), children),
        )

    @v_args(meta=True)
    def open_block(self, meta: Any, children: PyList[Any]) -> Open:
        return cast(Open, children[0])

    @v_args(meta=True)
    def open_block_legacy(self, meta: Any, children: PyList[Any]) -> Open:
        import warnings

        warnings.warn(
            "The legacy '--' open block delimiter is deprecated. Use '~~~~' (or longer) tilde delimiters instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return cast(
            Open,
            self._set_location_from_children(
                self._build_open_block(children), children
            ),
        )

    @v_args(meta=True)
    def open_block_4(self, meta: Any, children: PyList[Any]) -> Open:
        return cast(
            Open,
            self._set_location_from_children(
                self._build_open_block(children), children
            ),
        )

    @v_args(meta=True)
    def open_block_5(self, meta: Any, children: PyList[Any]) -> Open:
        return cast(
            Open,
            self._set_location_from_children(
                self._build_open_block(children), children
            ),
        )

    @v_args(meta=True)
    def open_block_6(self, meta: Any, children: PyList[Any]) -> Open:
        return cast(
            Open,
            self._set_location_from_children(
                self._build_open_block(children), children
            ),
        )

    @v_args(meta=True)
    def open_block_long(self, meta: Any, children: PyList[Any]) -> Open:
        return cast(
            Open,
            self._set_location_from_children(
                self._build_open_block(children), children
            ),
        )

    def _build_open_block(self, children: PyList[Any]) -> Open:
        delims = [
            c
            for c in children
            if isinstance(c, Token)
            and (c.type == "OPEN_BLOCK_DELIM" or c.type.startswith("OPEN_BLOCK_DELIM_"))
        ]
        blocks = [c for c in children if isinstance(c, BlockNode)]
        merged_inner = self._merge_consecutive_lists(blocks)
        delimiter = delims[0].value if delims else "--"
        return Open(blocks=merged_inner, delimiter=delimiter)

    def _build_sidebar(self, children: PyList[Any]) -> Sidebar:
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type.startswith("SIDEBAR_DELIM_")
        ]

        blocks = [c for c in children if isinstance(c, BlockNode)]
        merged_inner = self._merge_consecutive_lists(blocks)
        delimiter = delims[0].value if delims else "****"
        return Sidebar(blocks=merged_inner, delimiter=delimiter)

    @v_args(meta=True)
    def quote_block(self, meta: Any, children: PyList[Any]) -> Quote:
        return cast(Quote, children[0])

    @v_args(meta=True)
    def quote_4(self, meta: Any, children: PyList[Any]) -> Quote:
        return cast(
            Quote,
            self._set_location_from_children(
                self._build_quote_block(children), children
            ),
        )

    @v_args(meta=True)
    def quote_5(self, meta: Any, children: PyList[Any]) -> Quote:
        return cast(
            Quote,
            self._set_location_from_children(
                self._build_quote_block(children), children
            ),
        )

    @v_args(meta=True)
    def quote_6(self, meta: Any, children: PyList[Any]) -> Quote:
        return cast(
            Quote,
            self._set_location_from_children(
                self._build_quote_block(children), children
            ),
        )

    def _build_quote_block(self, children: PyList[Any]) -> Quote:
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type.startswith("QUOTE_DELIM_")
        ]

        blocks = [c for c in children if isinstance(c, BlockNode)]
        merged_inner = self._merge_consecutive_lists(blocks)
        delimiter = delims[0].value if delims else "____"
        return Quote(blocks=merged_inner, delimiter=delimiter)

    @v_args(inline=True)
    def span_both(self, cols: Optional[Token], rows: Token) -> Dict[str, int]:
        c = int(cols.value) if cols else 1
        r = int(rows.value)
        return {"colspan": c, "rowspan": r}

    @v_args(inline=True)
    def span_cols(self, cols: Token) -> Dict[str, int]:
        c = int(cols.value)
        return {"colspan": c}

    @v_args(inline=True)
    def multiplier(self, mult: Token) -> Dict[str, int]:
        return {"multiplier": int(mult.value)}

    @v_args(inline=True)
    def align_both(self, horiz: Token, vert: Optional[Token]) -> Dict[str, str]:
        h_map = {"<": "left", ">": "right", "^": "center"}
        v_map = {".<": "top", ".>": "bottom", ".^": "middle"}
        align = h_map.get(horiz.value)
        valign = v_map.get(vert.value) if vert else None
        res = {}
        if align:
            res["align"] = align
        if valign:
            res["valign"] = valign
        return res

    @v_args(inline=True)
    def align_vert(self, vert: Token) -> Dict[str, str]:
        v_map = {".<": "top", ".>": "bottom", ".^": "middle"}
        valign = v_map.get(vert.value)
        res = {}
        if valign:
            res["valign"] = valign
        return res

    def table_cell_spec(self, children: PyList[Any]) -> Dict[str, Any]:
        res = {}
        for child in children:
            if isinstance(child, dict):
                res.update(child)
            elif isinstance(child, Token) and child.type == "STYLE_SPEC":
                res["style"] = child.value
        return res

    @v_args(meta=True)
    def table(self, meta: Any, children: PyList[Any]) -> Table:
        raw_cells = [c for c in children if isinstance(c, TableCell)]

        # 1. Expand multipliers
        cells = []
        for cell in raw_cells:
            mult = getattr(cell, "multiplier", None)
            if mult and mult > 1:
                for _ in range(mult):
                    new_cell = TableCell(blocks=cell.blocks)
                    new_cell.colspan = cell.colspan
                    new_cell.rowspan = cell.rowspan
                    new_cell.align = cell.align
                    new_cell.valign = cell.valign
                    new_cell.style = cell.style
                    cells.append(new_cell)
            else:
                cells.append(cell)

        # 2. Determine default num_cols
        if cells:
            first_line = cells[0].location[0]["line"] if cells[0].location else 1
            num_cols = sum(
                1 for c in cells if c.location and c.location[0]["line"] == first_line
            )
            if num_cols == 0:
                num_cols = 1
        else:
            num_cols = 1

        # 3. Perform grid grouping into TableRow objects
        table_node = Table()
        grid: PyList[PyList[Any]] = []
        cell_idx = 0
        while cell_idx < len(cells):
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

            cell = cells[cell_idx]
            cell_idx += 1

            colspan = cell.colspan or 1
            rowspan = cell.rowspan or 1

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

        rows = []
        for r in range(len(grid)):
            row_cells: PyList[TableCell] = [
                cell for cell in grid[r] if isinstance(cell, TableCell)
            ]
            if row_cells:
                rows.append(TableRow(cells=row_cells))

        table_node.rows = rows
        return cast(Table, self._set_location_from_children(table_node, children))

    @v_args(meta=True)
    def table_row(self, meta: Any, children: PyList[Any]) -> TableRow:
        cells = [c for c in children if isinstance(c, TableCell)]
        row = TableRow(cells=cells)
        return cast(TableRow, self._set_location_from_children(row, children))

    @v_args(meta=True)
    def table_cell(self, meta: Any, children: PyList[Any]) -> TableCell:
        spec = {}
        content_token = None
        for child in children:
            if isinstance(child, dict):
                spec = child
            elif isinstance(child, Token) and child.type == "TABLE_CELL":
                content_token = child

        content_str = content_token.value if content_token else ""
        if content_str.startswith("|"):
            content_str = content_str[1:]
        content_str = content_str.strip()

        blocks = []
        if content_str:
            from asciidoctrine.lark_parser import parse_to_ast

            try:
                nested_doc = parse_to_ast(content_str)
                blocks = nested_doc.blocks
            except Exception:
                blocks = [Paragraph(inlines=[Text(content_str)])]
        else:
            blocks = []

        cell = TableCell(blocks=blocks)
        cell.colspan = spec.get("colspan", 1)
        cell.rowspan = spec.get("rowspan", 1)
        cell.align = spec.get("align")
        cell.valign = spec.get("valign")
        cell.style = spec.get("style")
        if "multiplier" in spec:
            cell.multiplier = spec["multiplier"]

        return cast(TableCell, self._set_location_from_children(cell, children))
