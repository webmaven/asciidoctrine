import io
from typing import Any, Dict, List, Optional, Sequence
from .nodes import Node, NodeVisitor

class AsciiDocSerializerVisitor(NodeVisitor):
    """
    A visitor that serializes an unresolved AsciiDoc AST back to AsciiDoc source string.
    """
    def __init__(self) -> None:
        self.stream = io.StringIO()

    def serialize(self, node: Node) -> str:
        self.visit(node)
        return self.stream.getvalue()

    def write(self, s: str) -> None:
        self.stream.write(s)

    def write_block_metadata(self, node: Node) -> None:
        """
        Helper to write block-level metadata (anchors, roles, titles, general attributes)
        before serializing the block content.
        """
        attrs = getattr(node, "attributes", {}) or {}

        # 1. Anchor / ID
        if "id" in attrs and attrs["id"]:
            self.write(f"[[{attrs['id']}]]\n")

        # 2. Role
        if "role" in attrs and attrs["role"]:
            self.write(f"[.{attrs['role']}]\n")

        # 3. Title (Explicit Node or attribute)
        title_node = getattr(node, "title", None)
        if title_node:
            self.write(".")
            self.visit(title_node)
            self.write("\n")
        elif "title" in attrs and attrs["title"]:
            self.write(f".{attrs['title']}\n")

        # 4. Other Attributes
        # Format block attributes: [style, language, key=value]
        # Ignore structural/internal attributes already serialized
        ignored_keys = {
            "id", "role", "title", "form", "delimiter", "checked",
            "positional", "positional_attributes"
        }
        style = attrs.get("style")
        language = attrs.get("language")

        attr_parts = []
        if style:
            # Avoid duplicating style if it is already represented
            if style.lower() != getattr(node, "name", "").lower():
                attr_parts.append(style)
                ignored_keys.add("style")
                if language:
                    attr_parts.append(language)
                    ignored_keys.add("language")

        # Remaining key-values
        for k, v in attrs.items():
            if k in ignored_keys or (isinstance(k, str) and k.isdigit()):
                continue
            if isinstance(v, bool):
                if v:
                    attr_parts.append(k)
            else:
                # Quote values with spaces
                if " " in str(v) or "," in str(v):
                    attr_parts.append(f'{k}="{v}"')
                else:
                    attr_parts.append(f'{k}={v}')

        if attr_parts:
            self.write(f"[{', '.join(attr_parts)}]\n")

    # --- Block Visitors ---

    def visit_document(self, node: Node) -> None:
        header = getattr(node, "header", None)
        if header:
            self.visit(header)

        blocks = getattr(node, "blocks", []) or []
        for i, block in enumerate(blocks):
            if i > 0 or header:
                self.write("\n")
            self.visit(block)

    def visit_header(self, node: Node) -> None:
        title = getattr(node, "title", None)
        if title:
            self.write("= ")
            self.visit(title)
            self.write("\n")

        authors = getattr(node, "authors", []) or []
        if authors:
            author_strs = []
            for author in authors:
                # authors are serialized from their inlines or properties
                name_parts = []
                for child in getattr(author, "inlines", []):
                    if hasattr(child, "value"):
                        name_parts.append(str(child.value))
                author_strs.append("".join(name_parts))
            self.write("; ".join(author_strs) + "\n")

        revision = getattr(node, "revision", None)
        if revision:
            rev_parts = []
            for child in getattr(revision, "inlines", []):
                if hasattr(child, "value"):
                    rev_parts.append(str(child.value))
            self.write("".join(rev_parts) + "\n")

        attrs = getattr(node, "attributes", {}) or {}
        for k, v in attrs.items():
            if v is True:
                self.write(f":{k}:\n")
            elif v is not None:
                self.write(f":{k}: {v}\n")

        self.write("\n")

    def visit_section(self, node: Node) -> None:
        self.write_block_metadata(node)
        level = getattr(node, "level", 1)
        prefix = "=" * (level + 1)
        self.write(f"{prefix} ")
        title = getattr(node, "title", None)
        if title:
            self.visit(title)
        self.write("\n")

        blocks = getattr(node, "blocks", []) or []
        for block in blocks:
            self.write("\n")
            self.visit(block)

    def visit_title(self, node: Node) -> None:
        for inline in getattr(node, "inlines", []):
            self.visit(inline)

    def visit_paragraph(self, node: Node) -> None:
        self.write_block_metadata(node)
        for inline in getattr(node, "inlines", []):
            self.visit(inline)
        self.write("\n")

    def visit_listing(self, node: Node) -> None:
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "----")
        self.write(f"{delim}\n")
        # listing/literal content is stored in code
        code = getattr(node, "code", "")
        self.write(code)
        if code and not code.endswith("\n"):
            self.write("\n")
        self.write(f"{delim}\n")

    def visit_literal(self, node: Node) -> None:
        self.write_block_metadata(node)
        form = getattr(node, "form", "delimited")
        if form == "delimited":
            delim = getattr(node, "delimiter", "....")
            self.write(f"{delim}\n")
            code = getattr(node, "code", "")
            self.write(code)
            if code and not code.endswith("\n"):
                self.write("\n")
            self.write(f"{delim}\n")
        else:
            code = getattr(node, "code", "")
            for line in code.splitlines():
                self.write(f" {line}\n")

    def visit_sidebar(self, node: Node) -> None:
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "****")
        self.write(f"{delim}\n")
        for block in getattr(node, "blocks", []):
            self.visit(block)
        self.write(f"{delim}\n")

    def visit_example(self, node: Node) -> None:
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "====")
        self.write(f"{delim}\n")
        for block in getattr(node, "blocks", []):
            self.visit(block)
        self.write(f"{delim}\n")

    def visit_quote(self, node: Node) -> None:
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "____")
        self.write(f"{delim}\n")
        for block in getattr(node, "blocks", []):
            self.visit(block)
        self.write(f"{delim}\n")

    def visit_admonition(self, node: Node) -> None:
        form = getattr(node, "form", "paragraph")
        variant = getattr(node, "variant", "note").upper()
        if form == "delimited":
            # For delimited admonition, the metadata needs to state [NOTE]
            self.write(f"[{variant}]\n")
            delim = getattr(node, "delimiter", "====")
            self.write(f"{delim}\n")
            for block in getattr(node, "blocks", []):
                self.visit(block)
            self.write(f"{delim}\n")
        else:
            # Paragraph form
            self.write(f"{variant}: ")
            blocks = getattr(node, "blocks", [])
            if blocks:
                # Admonitions store text in a paragraph block
                first_block = blocks[0]
                for inline in getattr(first_block, "inlines", []):
                    self.visit(inline)
                self.write("\n")
                # Subsequent blocks can be continued with '+'
                for block in blocks[1:]:
                    self.write("+\n")
                    self.visit(block)

    def visit_open(self, node: Node) -> None:
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "--")
        self.write(f"{delim}\n")
        for block in getattr(node, "blocks", []):
            self.visit(block)
        self.write(f"{delim}\n")

    def visit_list(self, node: Node) -> None:
        self.write_block_metadata(node)
        for item in getattr(node, "items", []):
            self.visit(item)

    def visit_listitem(self, node: Node) -> None:
        marker = getattr(node, "marker", "*")
        self.write(marker)
        checked = getattr(node, "checked", None)
        if checked is not None:
            self.write(" [x] " if checked else " [ ] ")
        else:
            self.write(" ")

        for inline in getattr(node, "principal", []):
            self.visit(inline)
        self.write("\n")

        # Subsequent blocks in the list item require list continuation '+'
        for block in getattr(node, "blocks", []):
            if getattr(block, "name", "") == "list":
                self.visit(block)
            else:
                self.write("+\n")
                self.visit(block)

    def visit_descriptionlist(self, node: Node) -> None:
        self.write_block_metadata(node)
        for item in getattr(node, "items", []):
            self.visit(item)

    def visit_descriptionlistitem(self, node: Node) -> None:
        for term in getattr(node, "terms", []):
            self.visit(term)
        blocks = getattr(node, "blocks", [])
        for i, block in enumerate(blocks):
            if i > 0:
                self.write("+\n")
            self.visit(block)

    def visit_descriptionlistterm(self, node: Node) -> None:
        for inline in getattr(node, "inlines", []):
            self.visit(inline)
        self.write("::\n")

    def visit_table(self, node: Node) -> None:
        self.write_block_metadata(node)
        self.write("|===\n")
        for row in getattr(node, "rows", []):
            self.visit(row)
        self.write("|===\n")

    def visit_row(self, node: Node) -> None:
        for cell in getattr(node, "cells", []):
            self.visit(cell)
        self.write("\n")

    def visit_cell(self, node: Node) -> None:
        # Construct optional cell specifiers: colspan.rowspan+align style
        specifiers = []
        colspan = getattr(node, "colspan", 1)
        rowspan = getattr(node, "rowspan", 1)
        align = getattr(node, "align", None)
        valign = getattr(node, "valign", None)
        style = getattr(node, "style", None)

        if colspan > 1 or rowspan > 1:
            span_str = f"{colspan}"
            if rowspan > 1:
                span_str += f".{rowspan}"
            specifiers.append(span_str + "+")

        align_str = ""
        if align:
            align_map = {"left": "<", "right": ">", "center": "^"}
            align_str += align_map.get(align, "")
        if valign:
            valign_map = {"top": "<", "bottom": ">", "middle": "^"}
            align_str += "." + valign_map.get(valign, "")
        if align_str:
            specifiers.append(align_str)

        if style:
            style_map = {
                "asciidoc": "a", "code": "c", "default": "d", "emphasis": "e",
                "header": "h", "literal": "l", "monospaced": "m", "strong": "s",
                "verse": "v"
            }
            specifiers.append(style_map.get(style.lower(), style))

        prefix = "".join(specifiers)
        self.write(f" {prefix}| ")

        blocks = getattr(node, "blocks", [])
        for i, block in enumerate(blocks):
            if i > 0:
                self.write("\n\n")
            # For compact single paragraph cells, strip trailing newline to prevent breaking cell line
            if getattr(block, "name", "") == "paragraph" and len(blocks) == 1:
                for inline in getattr(block, "inlines", []):
                    self.visit(inline)
            else:
                self.visit(block)

    def visit_thematic_break(self, node: Node) -> None:
        self.write("'''\n")

    def visit_page_break(self, node: Node) -> None:
        self.write("<<<\n")

    def visit_attribute_entry(self, node: Node) -> None:
        name = getattr(node, "attribute_name", "")
        value = getattr(node, "value", "")
        if value:
            self.write(f":{name}: {value}\n")
        else:
            self.write(f":{name}:\n")

    def visit_include(self, node: Node) -> None:
        filename = getattr(node, "filename", "")
        self.write(f"include::{filename}[]\n")

    def visit_toc(self, node: Node) -> None:
        target = getattr(node, "target", "")
        self.write(f"toc::{target}[]\n")

    # --- Inline Visitors ---

    def visit_text(self, node: Node) -> None:
        self.write(getattr(node, "value", ""))

    def visit_break(self, node: Node) -> None:
        self.write(" +\n")

    def visit_span(self, node: Node) -> None:
        variant = getattr(node, "variant", "")
        form = getattr(node, "form", "constrained")

        markup_map = {
            "strong": ("*", "**"),
            "emphasis": ("_", "__"),
            "code": ("`", "``")
        }

        if variant in markup_map:
            markers = markup_map[variant]
            marker = markers[0] if form == "constrained" else markers[1]
            self.write(marker)
            for child in getattr(node, "inlines", []):
                self.visit(child)
            self.write(marker)
        else:
            # Fallback for unrecognized variant spans
            for child in getattr(node, "inlines", []):
                self.visit(child)

    def visit_ref(self, node: Node) -> None:
        variant = getattr(node, "variant", "link")
        target = getattr(node, "target", "")

        if variant == "link":
            # For links, target can be a URL or a label
            # Standard URI scheme check
            has_scheme = target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:")
            prefix = "" if has_scheme else "link:"
            self.write(f"{prefix}{target}[")

            label_parts = []
            for child in getattr(node, "inlines", []):
                # Temporary sub-visitor or check to serialize inner label inlines
                label_parts.append(AsciiDocSerializerVisitor().serialize(child))
            self.write("".join(label_parts))

            # Optional other attributes
            attrs = getattr(node, "attributes", {}) or {}
            if attrs.get("window") == "_blank":
                self.write("^")
            self.write("]")
        elif variant == "xref":
            self.write(f"<<{target}")
            label_parts = []
            for child in getattr(node, "inlines", []):
                label_parts.append(AsciiDocSerializerVisitor().serialize(child))
            if label_parts:
                self.write(f", {''.join(label_parts)}")
            self.write(">>")

    def visit_image(self, node: Node) -> None:
        target = getattr(node, "target", "")
        attrs = getattr(node, "attributes", {}) or {}
        alt = attrs.get("alt", "")
        form = getattr(node, "form", "macro")
        node_type = getattr(node, "type", "block")

        if node_type == "inline" or form == "inline":
            self.write(f"image:{target}[{alt}]")
        else:
            self.write(f"image::{target}[{alt}]\n")

    def visit_audio(self, node: Node) -> None:
        target = getattr(node, "target", "")
        self.write(f"audio::{target}[]\n")

    def visit_video(self, node: Node) -> None:
        target = getattr(node, "target", "")
        self.write(f"video::{target}[]\n")

    def visit_kbd(self, node: Node) -> None:
        keys = getattr(node, "value", []) or []
        self.write(f"kbd:[{'+'.join(keys)}]")

    def visit_button(self, node: Node) -> None:
        label = getattr(node, "value", "")
        self.write(f"btn:[{label}]")

    def visit_menu(self, node: Node) -> None:
        menu = getattr(node, "menu", "")
        items = getattr(node, "items", []) or []
        self.write(f"menu:{menu}[{' > '.join(items)}]")

    def visit_callout(self, node: Node) -> None:
        num = getattr(node, "value", 1)
        self.write(f"<{num}>")

    def visit_stem(self, node: Node) -> None:
        node_type = getattr(node, "type", "block")
        variant = getattr(node, "variant", "asciimath")
        if node_type == "inline":
            val = getattr(node, "value", "")
            self.write(f"{variant}:[{val}]")
        else:
            # Block stem
            self.write_block_metadata(node)
            self.write(f"[{variant}]\n")
            delim = getattr(node, "delimiter", "++++")
            self.write(f"{delim}\n")
            # Inside block stem content is represented in inlines
            for inline in getattr(node, "inlines", []):
                self.visit(inline)
            self.write(f"\n{delim}\n")

    def generic_visit(self, node: Node) -> None:
        # Fallback if no specific visitor matches
        for collection in node.get_child_collections().values():
            for child in collection:
                self.visit(child)


def serialize_to_asciidoc(node: Node) -> str:
    """
    Public API to serialize any AST node back to its AsciiDoc string representation.
    """
    visitor = AsciiDocSerializerVisitor()
    return visitor.serialize(node)
