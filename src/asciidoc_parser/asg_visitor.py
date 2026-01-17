from typing import Any, Dict, List, Optional, Union

from .nodes import (
    Admonition,
    AttributeEntry,
    Author,
    BlockNode,
    BulletList,
    Document,
    Emphasis,
    ExampleBlock,
    Header,
    Image,
    Include,
    InlineCode,
    InlineNode,
    Link,
    ListItem,
    LiteralBlock,
    Node,
    NodeVisitor,
    OrderedList,
    Paragraph,
    QuoteBlock,
    Revision,
    Section,
    Sidebar,
    Strong,
    Table,
    TableCell,
    TableRow,
    Text,
    Title,
)


class ASGVisitor(NodeVisitor):
    """
    Transforms the internal AST into a TCK-compliant Resolved Abstract Semantic Graph (ASG).
    The ASG is represented as a nested dictionary structure that can be serialized to JSON.
    Based on the official ASG schema: https://gitlab.eclipse.org/eclipse/asciidoc-lang/asciidoc-lang/-/blob/main/asg/schema.json
    """

    def visit(self, node: Node, **kwargs: Any) -> Any:
        """
        Recursively visits nodes and returns their ASG representation.
        """
        return super().visit(node, **kwargs)

    def _visit_children(self, node: Node) -> List[Any]:
        results = []
        for child in node.children:
            res = self.visit(child)
            if res is not None:
                results.append(res)
        return results

    def visit_document(self, node: Document) -> Dict[str, Any]:
        asg: Dict[str, Any] = {
            "name": "document",
            "type": "block",
        }
        if node.attributes or node.header:
            asg["attributes"] = node.attributes

        if node.header:
            asg["header"] = self.visit(node.header)

        asg["blocks"] = self._visit_children(node)
        return asg

    def visit_header(self, node: Header) -> Dict[str, Any]:
        header_asg: Dict[str, Any] = {}
        if node.title:
            header_asg["title"] = self.visit(node.title)
        if node.author:
            header_asg["authors"] = [self.visit(node.author)]
        if node.revision:
            header_asg["revision"] = self.visit(node.revision)
        return header_asg

    def visit_title(self, node: Title) -> List[Dict[str, Any]]:
        return self._visit_children(node)

    def visit_section(self, node: Section) -> Dict[str, Any]:
        return {
            "name": "section",
            "type": "block",
            "level": node.level,
            "title": self.visit(node.title_node),
            "blocks": self._visit_children(node)
        }

    def visit_paragraph(self, node: Paragraph) -> Dict[str, Any]:
        return {
            "name": "paragraph",
            "type": "block",
            "inlines": self._visit_children(node)
        }

    def visit_bulletlist(self, node: BulletList) -> Dict[str, Any]:
        return {
            "name": "list",
            "type": "block",
            "variant": "unordered",
            "marker": "*",
            "items": [self.visit(c, marker="*") for c in node.children]
        }

    def visit_orderedlist(self, node: OrderedList) -> Dict[str, Any]:
        return {
            "name": "list",
            "type": "block",
            "variant": "ordered",
            "marker": ".",
            "items": [self.visit(c, marker=".") for c in node.children]
        }

    def visit_listitem(self, node: ListItem, marker: str = "*") -> Dict[str, Any]:
        principal = []
        blocks = []
        for child in node.children:
            res = self.visit(child)
            if res is None:
                continue
            if isinstance(child, InlineNode):
                principal.append(res)
            else:
                blocks.append(res)

        asg: Dict[str, Any] = {
            "name": "listItem",
            "type": "block",
            "marker": marker,
            "principal": principal
        }
        if blocks:
            asg["blocks"] = blocks
        return asg

    def visit_literalblock(self, node: LiteralBlock) -> Dict[str, Any]:
        return {
            "name": "listing",
            "type": "block",
            "inlines": [
                {
                    "name": "text",
                    "type": "string",
                    "value": node.content
                }
            ]
        }

    def visit_exampleblock(self, node: ExampleBlock) -> Dict[str, Any]:
        return {
            "name": "example",
            "type": "block",
            "form": "delimited",
            "delimiter": "====",
            "blocks": self._visit_children(node)
        }

    def visit_quoteblock(self, node: QuoteBlock) -> Dict[str, Any]:
        return {
            "name": "quote",
            "type": "block",
            "form": "delimited",
            "delimiter": "____",
            "blocks": self._visit_children(node)
        }

    def visit_admonition(self, node: Admonition) -> Dict[str, Any]:
        return {
            "name": "admonition",
            "type": "block",
            "form": "delimited",
            "delimiter": "====",
            "variant": node.flavor,
            "blocks": self._visit_children(node)
        }

    def visit_sidebar(self, node: Sidebar) -> Dict[str, Any]:
        return {
            "name": "sidebar",
            "type": "block",
            "form": "delimited",
            "delimiter": "****",
            "blocks": self._visit_children(node)
        }

    def visit_link(self, node: Link) -> Dict[str, Any]:
        return {
            "name": "ref",
            "type": "inline",
            "variant": "link",
            "target": node.url,
            "inlines": [{"name": "text", "type": "string", "value": node.text}]
        }

    def visit_image(self, node: Image) -> Dict[str, Any]:
        return {
            "name": "image",
            "type": "block",
            "form": "macro",
            "target": node.url,
            "attributes": {"alt": node.alt}
        }

    def visit_table(self, node: Table) -> Dict[str, Any]:
        rows = []
        for row in node.header_rows:
            rows.append(self.visit(row))
        for row in node.rows:
            rows.append(self.visit(row))
        return {
            "name": "table",
            "type": "block",
            "rows": rows
        }

    def visit_tablerow(self, node: TableRow) -> Dict[str, Any]:
        return {
            "name": "row",
            "type": "block",
            "cells": [self.visit(cell) for cell in node.cells]
        }

    def visit_tablecell(self, node: TableCell) -> Dict[str, Any]:
        return {
            "name": "cell",
            "type": "block",
            "blocks": self._visit_children(node)
        }

    def visit_attribute_entry(self, node: AttributeEntry) -> None:
        return None

    def visit_include(self, node: Include) -> None:
        return None

    def visit_author(self, node: Author) -> Dict[str, Any]:
        fullname = "".join(
            [getattr(c, "text", "") for c in node.children if hasattr(c, "text")]
        )
        return {
            "fullname": fullname
        }

    def visit_revision(self, node: Revision) -> Dict[str, Any]:
        value = "".join(
            [getattr(c, "text", "") for c in node.children if hasattr(c, "text")]
        )
        return {
            "name": "revision",
            "type": "block",
            "value": value
        }

    def visit_text(self, node: Text) -> Dict[str, Any]:
        return {
            "name": "text",
            "type": "string",
            "value": node.text
        }

    def _visit_span(self, node: Node, variant: str) -> Dict[str, Any]:
        return {
            "name": "span",
            "type": "inline",
            "variant": variant,
            "form": "constrained",
            "inlines": self._visit_children(node)
        }

    def visit_strong(self, node: Strong) -> Dict[str, Any]:
        return self._visit_span(node, "strong")

    def visit_emphasis(self, node: Emphasis) -> Dict[str, Any]:
        return self._visit_span(node, "emphasis")

    def visit_inlinecode(self, node: InlineCode) -> Dict[str, Any]:
        return self._visit_span(node, "code")

    def generic_visit(self, node: Node, **kwargs: Any) -> Any:
        name = node.node_type.value if node.node_type else "unknown"
        return {
            "name": name,
            "type": "block",
            "children": self._visit_children(node)
        }
