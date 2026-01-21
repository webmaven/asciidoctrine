from typing import Any, Dict, Optional, Sequence, Tuple, cast
from typing import List as PyList

from lark import Discard, Token

from ..nodes import (
    Admonition,
    BlockNode,
    Example,
    Listing,
    ListItem,
    Node,
    Paragraph,
    Section,
    Sidebar,
    Text,
)
from ..nodes import (
    List as ASTList,
)

class BlockTransformer:
    """
    Mixin class for block-level AsciiDoc transformations.
    """

    @staticmethod
    def _merge_consecutive_lists(blocks: Sequence[BlockNode]) -> PyList[Node]:
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
            else:
                merged_blocks.append(current_block)
        return merged_blocks

    @staticmethod
    def _get_list_level(marker_token: Token) -> int:
        marker = marker_token.value.strip()
        if marker.startswith("-"):
            return 1
        if marker.startswith("*"):
            return len(marker)
        if marker.startswith("."):
            return len(marker)
        return 1

    @staticmethod
    def _nest_list_items(items: PyList[Dict[str, Any]]) -> PyList[ListItem]:
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

            list_node.items.append(
                ListItem(
                    marker=marker,
                    principal=item_data["children"],
                    checked=item_data.get("checked"),
                )
            )

        all_root_children: PyList[ListItem] = []
        for rl in root_lists:
            all_root_children.extend(rl.items)
        return all_root_children

    def section(self, children: PyList[Any]) -> Section:
        # Now section is flat: children[0] is (level, title)
        level, title = children[0]
        return Section(level=level, title=title, blocks=[])

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
            else:
                consolidated.append(node)

        return Paragraph(inlines=consolidated)

    def ulist(self, children: PyList[Any]) -> ASTList:
        items = BlockTransformer._nest_list_items(children)
        marker = children[0]["marker"] if children else "*"
        return ASTList(variant="unordered", marker=marker, items=items)

    def olist(self, children: PyList[Any]) -> ASTList:
        items = BlockTransformer._nest_list_items(children)
        marker = children[0]["marker"] if children else "."
        return ASTList(variant="ordered", marker=marker, items=items)

    def ulist_item(self, children: PyList[Any]) -> Dict[str, Any]:
        marker_token = children[0]
        level = BlockTransformer._get_list_level(marker_token)

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

    def olist_item(self, children: PyList[Any]) -> Dict[str, Any]:
        marker_token = children[0]
        level = BlockTransformer._get_list_level(marker_token)
        content = children[1]
        return {
            "level": level,
            "item_type": "enumerated",
            "marker": marker_token.value.strip(),
            "children": content,
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
        return self._build_example_block(children)

    def example_5(self, children: PyList[Any]) -> Example:
        return self._build_example_block(children)

    def example_6(self, children: PyList[Any]) -> Example:
        return self._build_example_block(children)

    def _build_example_block(self, children: PyList[Any]) -> Example:
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type.startswith("ADMONITION_DELIM_")
        ]

        blocks = [c for c in children if isinstance(c, BlockNode)]
        merged_inner = self._merge_consecutive_lists(blocks) # type: ignore
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

        if len(delims) >= 2:
            if len(delims[0]) != len(delims[-1]):
                raise ValueError(
                    f"Mismatched literal block delimiter lengths: {len(delims[0])} vs {len(delims[-1])}"
                )

        for c in children:
            if isinstance(c, dict):
                attributes = c
            elif isinstance(c, Token) and c.type == "LITERAL_BLOCK_CONTENT":
                content = c.value

        delimiter = delims[0].value if delims else "----"
        return Listing(
            inlines=[Text(content)], attributes=attributes, delimiter=delimiter
        )

    def admonition(self, children: PyList[Any]) -> Admonition:
        return cast(Admonition, children[0])

    def admonition_4(self, children: PyList[Any]) -> Admonition:
        return self._build_admonition(children)

    def admonition_5(self, children: PyList[Any]) -> Admonition:
        return self._build_admonition(children)

    def admonition_6(self, children: PyList[Any]) -> Admonition:
        return self._build_admonition(children)

    def _build_admonition(self, children: PyList[Any]) -> Admonition:
        start_token = children[0]
        variant = start_token.value.strip("[] ").lower()
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type.startswith("ADMONITION_DELIM_")
        ]

        blocks = [c for c in children if isinstance(c, BlockNode)]

        merged_inner = self._merge_consecutive_lists(blocks) # type: ignore
        delimiter = delims[0].value if delims else "===="
        return Admonition(variant=variant, blocks=merged_inner, delimiter=delimiter)

    def sidebar(self, children: PyList[Any]) -> Sidebar:
        return cast(Sidebar, children[0])

    def sidebar_4(self, children: PyList[Any]) -> Sidebar:
        return self._build_sidebar(children)

    def sidebar_5(self, children: PyList[Any]) -> Sidebar:
        return self._build_sidebar(children)

    def sidebar_6(self, children: PyList[Any]) -> Sidebar:
        return self._build_sidebar(children)

    def _build_sidebar(self, children: PyList[Any]) -> Sidebar:
        delims = [
            c
            for c in children
            if isinstance(c, Token) and c.type.startswith("SIDEBAR_DELIM_")
        ]

        blocks = [c for c in children if isinstance(c, BlockNode)]
        merged_inner = self._merge_consecutive_lists(blocks) # type: ignore
        delimiter = delims[0].value if delims else "****"
        return Sidebar(blocks=merged_inner, delimiter=delimiter)
