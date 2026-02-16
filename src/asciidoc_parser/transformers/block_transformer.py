from typing import Any, Dict, Sequence, Tuple, cast
from typing import List as PyList

from lark import Discard, Token, v_args

from ..nodes import (
    Admonition,
    BlockNode,
    CalloutList,
    CalloutListItem,
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


class BlockTransformer:
    """
    Mixin class for block-level AsciiDoc transformations.
    """

    def _set_location(self, node: Node, meta: Any) -> Node:
        """Sets the location of a node from Lark meta."""
        node.location = [
            {"line": meta.line, "col": meta.column},
            {"line": meta.end_line, "col": meta.end_column - 1},
        ]
        return node

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
            elif (
                isinstance(current_block, DescriptionList)
                and isinstance(prev_block, DescriptionList)
            ):
                prev_block.items.extend(current_block.items)
                if prev_block.location and current_block.location:
                    prev_block.location[1] = current_block.location[1]
            else:
                merged_blocks.append(current_block)
        return merged_blocks

    def _get_list_level(self, marker_token: Token) -> int:
        marker = marker_token.value.strip()
        if marker.startswith("-"):
            return 1
        if marker.startswith("*"):
            return len(marker)
        if marker.startswith("."):
            return len(marker)
        return 1

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
                parent_list = stack[-1][1]
                if parent_list.items:
                    last_item = parent_list.items[-1]
                    variant = "unordered" if item_type == "bullet" else "ordered"
                    list_node = ASTList(variant=variant, marker=marker)
                    last_item.blocks.append(list_node)
                    stack.append((level, list_node))
                else:
                    list_node = stack[-1][1]
            else:
                list_node = stack[-1][1]

            item = ListItem(
                marker=marker,
                principal=item_data["children"],
                checked=item_data.get("checked"),
            )
            if "meta" in item_data:
                self._set_location(item, item_data["meta"])
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
        return cast(Section, self._set_location(section, meta))

    @v_args(meta=True)
    def paragraph(self, meta: Any, children: PyList[Any]) -> Paragraph:
        children = [c for c in children if c is not Discard]
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
                if consolidated[-1].location and node.location:
                    consolidated[-1].location[1] = node.location[1]
            else:
                consolidated.append(node)

        para = Paragraph(inlines=consolidated)
        return cast(Paragraph, self._set_location(para, meta))

    @v_args(meta=True)
    def ulist(self, meta: Any, children: PyList[Any]) -> ASTList:
        items = self._nest_list_items(children)
        marker = children[0]["marker"] if children else "*"
        list_node = ASTList(variant="unordered", marker=marker, items=items)
        return cast(ASTList, self._set_location(list_node, meta))

    @v_args(meta=True)
    def olist(self, meta: Any, children: PyList[Any]) -> ASTList:
        items = self._nest_list_items(children)
        marker = children[0]["marker"] if children else "."
        list_node = ASTList(variant="ordered", marker=marker, items=items)
        return cast(ASTList, self._set_location(list_node, meta))

    @v_args(meta=True)
    def dlist(self, meta: Any, children: PyList[Any]) -> DescriptionList:
        list_node = DescriptionList(items=children)
        return cast(DescriptionList, self._set_location(list_node, meta))

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
        return cast(DescriptionListItem, self._set_location(item, meta))

    @v_args(meta=True)
    def dlist_term(self, meta: Any, children: PyList[Any]) -> DescriptionListTerm:
        # children[0] is text_content (list of inlines)
        term = DescriptionListTerm(inlines=children[0])
        return cast(DescriptionListTerm, self._set_location(term, meta))

    @v_args(meta=True)
    def dlist_description(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return [c for c in children if isinstance(c, BlockNode)]

    @v_args(meta=True)
    def colist(self, meta: Any, children: PyList[Any]) -> CalloutList:
        list_node = CalloutList(items=children)
        return cast(CalloutList, self._set_location(list_node, meta))

    @v_args(meta=True)
    def colist_item(self, meta: Any, children: PyList[Any]) -> CalloutListItem:
        number = int(children[0].value)
        content = children[1] if len(children) > 1 else []
        item = CalloutListItem(number=number, principal=content)
        return cast(CalloutListItem, self._set_location(item, meta))

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
        return cast(Example, self._set_location(self._build_example_block(children), meta))

    @v_args(meta=True)
    def example_5(self, meta: Any, children: PyList[Any]) -> Example:
        return cast(Example, self._set_location(self._build_example_block(children), meta))

    @v_args(meta=True)
    def example_6(self, meta: Any, children: PyList[Any]) -> Example:
        return cast(Example, self._set_location(self._build_example_block(children), meta))

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
            c
            for c in children
            if isinstance(c, Token) and c.type == "LISTING_DELIM"
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
            self._set_location(text_node, content_token)
        listing = Listing(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Listing, self._set_location(listing, meta))

    @v_args(meta=True)
    def literal_block(self, meta: Any, children: PyList[Any]) -> Literal:
        content = ""
        attributes: Dict[str, Any] = {}
        content_token = None
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type == "LITERAL_DELIM"
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
            self._set_location(text_node, content_token)
        literal = Literal(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Literal, self._set_location(literal, meta))

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
            self._set_location(text_node, content_token)
        pass_node = Passthrough(
            inlines=[text_node], attributes=attributes, delimiter=delimiter
        )
        return cast(Passthrough, self._set_location(pass_node, meta))

    @v_args(meta=True)
    def admonition(self, meta: Any, children: PyList[Any]) -> Admonition:
        return cast(Admonition, children[0])

    @v_args(meta=True)
    def admonition_4(self, meta: Any, children: PyList[Any]) -> Admonition:
        return cast(Admonition, self._set_location(self._build_admonition(children), meta))

    @v_args(meta=True)
    def admonition_5(self, meta: Any, children: PyList[Any]) -> Admonition:
        return cast(Admonition, self._set_location(self._build_admonition(children), meta))

    @v_args(meta=True)
    def admonition_6(self, meta: Any, children: PyList[Any]) -> Admonition:
        return cast(Admonition, self._set_location(self._build_admonition(children), meta))

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
        self._set_location(para, meta)
        adm = Admonition(variant=variant, blocks=[para], delimiter=None)
        return cast(Admonition, self._set_location(adm, meta))

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
        return cast(Sidebar, self._set_location(self._build_sidebar(children), meta))

    @v_args(meta=True)
    def sidebar_5(self, meta: Any, children: PyList[Any]) -> Sidebar:
        return cast(Sidebar, self._set_location(self._build_sidebar(children), meta))

    @v_args(meta=True)
    def sidebar_6(self, meta: Any, children: PyList[Any]) -> Sidebar:
        return cast(Sidebar, self._set_location(self._build_sidebar(children), meta))

    @v_args(meta=True)
    def open_block(self, meta: Any, children: PyList[Any]) -> Open:
        blocks = [c for c in children if isinstance(c, BlockNode)]
        merged_inner = self._merge_consecutive_lists(blocks)
        open_node = Open(blocks=merged_inner)
        return cast(Open, self._set_location(open_node, meta))

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
        return cast(Quote, self._set_location(self._build_quote_block(children), meta))

    @v_args(meta=True)
    def quote_5(self, meta: Any, children: PyList[Any]) -> Quote:
        return cast(Quote, self._set_location(self._build_quote_block(children), meta))

    @v_args(meta=True)
    def quote_6(self, meta: Any, children: PyList[Any]) -> Quote:
        return cast(Quote, self._set_location(self._build_quote_block(children), meta))

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

    @v_args(meta=True)
    def table(self, meta: Any, children: PyList[Any]) -> Table:
        rows = [c for c in children if isinstance(c, TableRow)]
        table_node = Table(rows=rows)
        return cast(Table, self._set_location(table_node, meta))

    @v_args(meta=True)
    def table_row(self, meta: Any, children: PyList[Any]) -> TableRow:
        cells = [c for c in children if isinstance(c, TableCell)]
        row = TableRow(cells=cells)
        return cast(TableRow, self._set_location(row, meta))

    @v_args(meta=True)
    def table_cell(self, meta: Any, children: PyList[Any]) -> TableCell:
        inlines = children[0] if children and children[0] else []
        para = Paragraph(inlines=inlines)
        cell = TableCell(blocks=[para])
        return cast(TableCell, self._set_location(cell, meta))
