from typing import Any, Dict, Sequence, Tuple, cast
from typing import List as PyList

from lark import Discard, Token

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

    def _set_location_from_children(self, node: Node, children: PyList[Any]) -> Node:
        """Sets the location of a node based on its children's locations."""
        valid_locations = []
        for child in children:
            if isinstance(child, Node) and child.location:
                valid_locations.extend(child.location)
            elif isinstance(child, Token):
                if child.line is not None and child.column is not None:
                    valid_locations.append({"line": child.line, "col": child.column})
                if child.end_line is not None and child.end_column is not None:
                    valid_locations.append({"line": child.end_line, "col": child.end_column})
            elif isinstance(child, list):
                for item in child:
                    if isinstance(item, Node) and item.location:
                        valid_locations.extend(item.location)
                    elif isinstance(item, Token):
                        if item.line is not None and item.column is not None:
                            valid_locations.append({"line": item.line, "col": item.column})
                        if item.end_line is not None and item.end_column is not None:
                            valid_locations.append({"line": item.end_line, "col": item.end_column})

        if valid_locations:
            valid_locations = [loc for loc in valid_locations if loc.get("line") is not None]
            if valid_locations:
                valid_locations.sort(key=lambda x: (x["line"], x["col"]))
                node.location = [valid_locations[0], valid_locations[-1]]
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
            if "location" in item_data:
                item.location = item_data["location"]
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

    def section(self, children: PyList[Any]) -> Section:
        level, title = children[0]
        section = Section(level=level, title=title, blocks=[])
        return cast(Section, self._set_location_from_children(section, children))

    def paragraph(self, children: PyList[Any]) -> Paragraph:
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
        return cast(Paragraph, self._set_location_from_children(para, children))

    def ulist(self, children: PyList[Any]) -> ASTList:
        items = self._nest_list_items(children)
        marker = children[0]["marker"] if children else "*"
        list_node = ASTList(variant="unordered", marker=marker, items=items)
        return cast(ASTList, self._set_location_from_children(list_node, children))

    def olist(self, children: PyList[Any]) -> ASTList:
        items = self._nest_list_items(children)
        marker = children[0]["marker"] if children else "."
        list_node = ASTList(variant="ordered", marker=marker, items=items)
        return cast(ASTList, self._set_location_from_children(list_node, children))

    def dlist(self, children: PyList[Any]) -> DescriptionList:
        list_node = DescriptionList(items=children)
        return cast(DescriptionList, self._set_location_from_children(list_node, children))

    def dlist_item(self, children: PyList[Any]) -> DescriptionListItem:
        terms: PyList[DescriptionListTerm] = []
        blocks: PyList[Node] = []
        for child in children:
            if isinstance(child, DescriptionListTerm):
                terms.append(child)
            elif isinstance(child, list):
                blocks.extend(child)
            elif isinstance(child, BlockNode):
                blocks.append(child)
        item = DescriptionListItem(terms=terms, blocks=blocks)
        return cast(DescriptionListItem, self._set_location_from_children(item, children))

    def dlist_term(self, children: PyList[Any]) -> DescriptionListTerm:
        term = DescriptionListTerm(inlines=children[0])
        return cast(DescriptionListTerm, self._set_location_from_children(term, children))

    def dlist_description(self, children: PyList[Any]) -> PyList[Node]:
        return [c for c in children if isinstance(c, BlockNode)]

    def colist(self, children: PyList[Any]) -> CalloutList:
        list_node = CalloutList(items=children)
        return cast(CalloutList, self._set_location_from_children(list_node, children))

    def colist_item(self, children: PyList[Any]) -> CalloutListItem:
        number = int(children[0].value)
        content = children[1] if len(children) > 1 else []
        item = CalloutListItem(number=number, principal=content)
        return cast(CalloutListItem, self._set_location_from_children(item, children))

    def ulist_item(self, children: PyList[Any]) -> Dict[str, Any]:
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
            "location": [{"line": marker_token.line, "col": marker_token.column},
                         {"line": marker_token.end_line, "col": marker_token.end_column}]
        }
        if checkbox:
            val = checkbox.value.strip("[] ")
            item_data["checked"] = val.lower() in ["x", "*"]

        return item_data

    def olist_item(self, children: PyList[Any]) -> Dict[str, Any]:
        marker_token = children[0]
        level = self._get_list_level(marker_token)
        content = children[1]
        return {
            "level": level,
            "item_type": "enumerated",
            "marker": marker_token.value.strip(),
            "children": content,
            "location": [{"line": marker_token.line, "col": marker_token.column},
                         {"line": marker_token.end_line, "col": marker_token.end_column}]
        }

    def basic_block(self, children: PyList[Any]) -> Any:
        return children[0] if children else Discard

    def admonition_content(self, children: PyList[Any]) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    def sidebar_content(self, children: PyList[Any]) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    def example_content(self, children: PyList[Any]) -> PyList[Any]:
        return [c for c in children if c is not Discard]

    def example_block(self, children: PyList[Any]) -> Example:
        return cast(Example, children[0])

    def example_4(self, children: PyList[Any]) -> Example:
        return cast(Example, self._set_location_from_children(self._build_example_block(children), children))

    def example_5(self, children: PyList[Any]) -> Example:
        return cast(Example, self._set_location_from_children(self._build_example_block(children), children))

    def example_6(self, children: PyList[Any]) -> Example:
        return cast(Example, self._set_location_from_children(self._build_example_block(children), children))

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

    def literal_block(self, children: PyList[Any]) -> Listing:
        content = ""
        attributes: Dict[str, Any] = {}
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type == "LITERAL_BLOCK_DELIM"
        ]

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "LITERAL_BLOCK_CONTENT":
                content = c.value

        delimiter = delims[0].value if delims else "----"
        listing = Listing(
            inlines=[Text(content)], attributes=attributes, delimiter=delimiter
        )
        return cast(Listing, self._set_location_from_children(listing, children))

    def passthrough_block(self, children: PyList[Any]) -> Passthrough:
        content = ""
        attributes: Dict[str, Any] = {}
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

        delimiter = delims[0].value if delims else "++++"
        pass_node = Passthrough(
            inlines=[Text(content)], attributes=attributes, delimiter=delimiter
        )
        return cast(Passthrough, self._set_location_from_children(pass_node, children))

    def admonition(self, children: PyList[Any]) -> Admonition:
        return cast(Admonition, children[0])

    def admonition_4(self, children: PyList[Any]) -> Admonition:
        return cast(Admonition, self._set_location_from_children(self._build_admonition(children), children))

    def admonition_5(self, children: PyList[Any]) -> Admonition:
        return cast(Admonition, self._set_location_from_children(self._build_admonition(children), children))

    def admonition_6(self, children: PyList[Any]) -> Admonition:
        return cast(Admonition, self._set_location_from_children(self._build_admonition(children), children))

    def shorthand_admonition(self, children: PyList[Any]) -> Admonition:
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

    def sidebar(self, children: PyList[Any]) -> Sidebar:
        return cast(Sidebar, children[0])

    def sidebar_4(self, children: PyList[Any]) -> Sidebar:
        return cast(Sidebar, self._set_location_from_children(self._build_sidebar(children), children))

    def sidebar_5(self, children: PyList[Any]) -> Sidebar:
        return cast(Sidebar, self._set_location_from_children(self._build_sidebar(children), children))

    def sidebar_6(self, children: PyList[Any]) -> Sidebar:
        return cast(Sidebar, self._set_location_from_children(self._build_sidebar(children), children))

    def open_block(self, children: PyList[Any]) -> Open:
        blocks = [c for c in children if isinstance(c, BlockNode)]
        merged_inner = self._merge_consecutive_lists(blocks)
        open_node = Open(blocks=merged_inner)
        return cast(Open, self._set_location_from_children(open_node, children))

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

    def quote_block(self, children: PyList[Any]) -> Quote:
        return cast(Quote, children[0])

    def quote_4(self, children: PyList[Any]) -> Quote:
        return cast(Quote, self._set_location_from_children(self._build_quote_block(children), children))

    def quote_5(self, children: PyList[Any]) -> Quote:
        return cast(Quote, self._set_location_from_children(self._build_quote_block(children), children))

    def quote_6(self, children: PyList[Any]) -> Quote:
        return cast(Quote, self._set_location_from_children(self._build_quote_block(children), children))

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

    def table(self, children: PyList[Any]) -> Table:
        rows = [c for c in children if isinstance(c, TableRow)]
        table_node = Table(rows=rows)
        return cast(Table, self._set_location_from_children(table_node, children))

    def table_row(self, children: PyList[Any]) -> TableRow:
        cells = [c for c in children if isinstance(c, TableCell)]
        row = TableRow(cells=cells)
        return cast(TableRow, self._set_location_from_children(row, children))

    def table_cell(self, children: PyList[Any]) -> TableCell:
        inlines = children[0] if children and children[0] else []
        para = Paragraph(inlines=inlines)
        cell = TableCell(blocks=[para])
        return cast(TableCell, self._set_location_from_children(cell, children))
