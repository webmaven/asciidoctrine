import io
from typing import Any

from .nodes import Node, NodeVisitor


class AsciiDocSerializerVisitor(NodeVisitor):
    """
    Visitor that traverses an AsciiDoc AST/ASG and serializes it back to AsciiDoc source markup.

    Supports lossless round-trip serialization for all core AsciiDoc block and inline node types,
    preserving structural boundaries, attributes, delimiters, and inline formatting semantics.

    *Attributes:*

    `stream`::
      Internal `io.StringIO` buffer used to accumulate serialized markup text.
    `line_ending`::
      Line ending character sequence (defaults to `\\n` or matches the document's original ending).

    *Example:*

    [source,python]
    ----
    from asciidoctrine.lark_parser import parse_to_ast
    from asciidoctrine.serializer import AsciiDocSerializerVisitor

    doc = parse_to_ast("== Section Title\\n\\nParagraph text.")
    visitor = AsciiDocSerializerVisitor()
    text = visitor.serialize(doc)
    assert "== Section Title" in text
    ----
    """

    def __init__(self) -> None:
        self.stream = io.StringIO()
        self.line_ending = "\n"

    def serialize(self, node: Node) -> str:
        """
        Traverse the specified AST node and return its serialized AsciiDoc markup string.

        *Parameters:*

        `node`:: The root `Node` instance to serialize.

        *Returns:*

        A string containing the serialized AsciiDoc source markup.
        """
        if getattr(node, "name", None) == "document":
            self.line_ending = getattr(node, "line_ending", "\n")
        self.visit(node)
        val = self.stream.getvalue()
        # If the root document had no trailing newline, strip the very last trailing newline if present.
        if getattr(node, "name", None) == "document" and not getattr(
            node, "had_trailing_newline", True
        ):
            if val.endswith("\r\n"):
                val = val[:-2]
            elif val.endswith("\n"):
                val = val[:-1]
        return val

    def write(self, s: str) -> None:
        """
        Write a string segment to the internal stream, translating line endings if required.

        *Parameters:*

        `s`:: String content to write.
        """
        if self.line_ending != "\n":
            s = s.replace("\n", self.line_ending)
        self.stream.write(s)

    def _format_macro_attributes(self, node: Node, default_first_attr: str = "") -> str:
        """
        Helper to format macro bracket attributes (`[attrlist]`).

        *Parameters:*

        `node`:: The macro `Node` containing attributes.
        `default_first_attr`:: Optional attribute key (e.g. `'alt'`) placed first if positional attributes are absent.

        *Returns:*

        Comma-separated string of formatted macro attributes.
        """
        attrs = getattr(node, "attributes", {}) or {}
        parts: list[str] = []
        positional = attrs.get("positional")
        if positional:
            parts.extend(str(p) for p in positional)
        elif default_first_attr and default_first_attr in attrs:
            parts.append(str(attrs[default_first_attr]))

        skip_keys = {
            "positional",
            "positional_attributes",
            "form",
            "target",
            "id",
        }
        if default_first_attr and not positional:
            skip_keys.add(default_first_attr)

        for k, v in attrs.items():
            if k in skip_keys or (isinstance(k, str) and k.isdigit()):
                continue
            if isinstance(v, bool):
                if v:
                    parts.append(str(k))
            else:
                val_s = str(v)
                if " " in val_s or "," in val_s:
                    parts.append(f'{k}="{val_s}"')
                else:
                    parts.append(f"{k}={val_s}")
        return ", ".join(parts)

    def write_block_metadata(self, node: Node) -> None:
        """
        Serialize block-level metadata (anchor IDs, roles, titles, and block attributes).

        *Parameters:*

        `node`:: The `Node` whose metadata is being serialized.
        """
        attrs = getattr(node, "attributes", {}) or {}

        # 1. Anchor / ID
        if "id" in attrs and attrs["id"]:
            self.write(f"[[{attrs['id']}]]\n")

        # 2. Role
        if "role" in attrs and attrs["role"]:
            self.write(f"[.{attrs['role']}]\n")

        # 3. Title (Explicit Node or attribute)
        node_name = getattr(node, "name", "")
        if node_name != "heading":
            title_node = getattr(node, "title", None)
            if title_node:
                self.write(".")
                if isinstance(title_node, list):
                    for t in title_node:
                        self.visit(t)
                elif isinstance(title_node, str):
                    self.write(title_node)
                else:
                    self.visit(title_node)
                self.write("\n")
            elif "title" in attrs and attrs["title"]:
                self.write(f".{attrs['title']}\n")

        # 4. Other Attributes
        ignored_keys = {
            "id",
            "role",
            "title",
            "form",
            "delimiter",
            "checked",
            "positional",
            "positional_attributes",
        }
        style = attrs.get("style")
        language = attrs.get("language")
        if style:
            ignored_keys.add("style")
        if language:
            ignored_keys.add("language")

        attr_parts: list[str] = []
        is_list = node_name == "list"
        if is_list:
            ignored_keys.update({"numeration", "start", "reversed"})
            # 1. Numeration style
            numeration = (
                getattr(node, "numeration", None)
                or attrs.get("numeration")
                or (
                    style
                    if style
                    in (
                        "loweralpha",
                        "upperalpha",
                        "lowerroman",
                        "upperroman",
                        "arabic",
                    )
                    else None
                )
            )
            if numeration:
                attr_parts.append(numeration)
                if style == numeration:
                    style = None

            # 2. Start offset
            start = getattr(node, "start", None)
            if start is None and "start" in attrs:
                try:
                    start = int(attrs["start"])
                except (ValueError, TypeError):
                    pass
            if start is not None:
                attr_parts.append(f"start={start}")

            # 3. Reversed option
            is_reversed = (
                getattr(node, "reversed", False)
                or "reversed" in str(attrs.get("options", "")).split(",")
                or attrs.get("reversed") is not None
                or style == "reversed"
            )
            if is_reversed:
                attr_parts.append("%reversed")
                if style == "reversed":
                    style = None
                if "options" in attrs:
                    opts = [
                        o.strip()
                        for o in str(attrs["options"]).split(",")
                        if o.strip() and o.strip() != "reversed"
                    ]
                    if not opts:
                        ignored_keys.add("options")
                    else:
                        attrs = dict(attrs)
                        attrs["options"] = ",".join(opts)

        elif node_name == "quote":
            ignored_keys.update({"attribution", "citetitle"})
            attribution = getattr(node, "attribution", None) or attrs.get("attribution")
            citetitle = getattr(node, "citetitle", None) or attrs.get("citetitle")
            if attribution or citetitle:
                attr_parts.append("quote")
                if attribution:
                    attr_parts.append(
                        f'"{attribution}"'
                        if ("," in str(attribution))
                        else str(attribution)
                    )
                    if citetitle:
                        attr_parts.append(
                            f'"{citetitle}"'
                            if ("," in str(citetitle))
                            else str(citetitle)
                        )
                elif citetitle:
                    attr_parts.append('""')
                    attr_parts.append(
                        f'"{citetitle}"' if ("," in str(citetitle)) else str(citetitle)
                    )

        elif node_name == "verse":
            ignored_keys.update({"attribution", "citetitle"})
            attribution = getattr(node, "attribution", None) or attrs.get("attribution")
            citetitle = getattr(node, "citetitle", None) or attrs.get("citetitle")
            attr_parts.append("verse")
            if attribution:
                attr_parts.append(
                    f'"{attribution}"'
                    if ("," in str(attribution))
                    else str(attribution)
                )
                if citetitle:
                    attr_parts.append(
                        f'"{citetitle}"' if ("," in str(citetitle)) else str(citetitle)
                    )
            elif citetitle:
                attr_parts.append('""')
                attr_parts.append(
                    f'"{citetitle}"' if ("," in str(citetitle)) else str(citetitle)
                )

        elif node_name == "collapsible":
            ignored_keys.add("options")
            opts_raw = attrs.get("options", "")
            opts = (
                [o.strip() for o in str(opts_raw).split(",") if o.strip()]
                if opts_raw
                else []
            )
            if "collapsible" in opts:
                opts.remove("collapsible")
            attr_parts.append("%collapsible")
            if opts:
                attrs = dict(attrs)
                attrs["options"] = ",".join(opts)
                ignored_keys.discard("options")

        if (
            style
            and node_name.lower() != "stem"
            and style.lower()
            not in (
                node_name.lower(),
                "collapsible",
                "verse",
                "quote",
            )
        ):
            attr_parts.append(style)
            if language:
                attr_parts.append(language)

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
                    attr_parts.append(f"{k}={v}")

        if attr_parts:
            self.write(f"[{', '.join(attr_parts)}]\n")

    # --- Block Visitors ---

    def visit_document(self, node: Node) -> None:
        """
        Serialize a root document AST node.

        *Parameters:*

        `node`:: The `Document` AST node to serialize.
        """
        header = getattr(node, "header", None)
        if header:
            self.visit(header)

        blocks = getattr(node, "blocks", []) or []
        for i, block in enumerate(blocks):
            if i > 0 or header:
                self.write("\n")
            self.visit(block)

    def visit_header(self, node: Node) -> None:
        """
        Serialize a document header (title, authors, revision, document attributes).

        *Parameters:*

        `node`:: The `Header` AST node to serialize.
        """
        title = getattr(node, "title", None)
        if title:
            self.write("= ")
            if isinstance(title, list):
                for t in title:
                    self.visit(t)
            elif isinstance(title, str):
                self.write(title)
            else:
                self.visit(title)
            self.write("\n")

        authors = getattr(node, "authors", []) or []
        if authors:
            author_strs = []
            for author in authors:
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

    def visit_section(self, node: Node) -> None:
        """
        Serialize a section node with leading `=` markers matching its heading depth.

        *Parameters:*

        `node`:: The `Section` AST node to serialize.
        """
        self.write_block_metadata(node)
        level = getattr(node, "level", 1)
        if level is None:
            level = 1
        prefix = "=" * (level + 1)
        self.write(f"{prefix} ")
        title = getattr(node, "title", None)
        if title:
            if isinstance(title, list):
                for t in title:
                    self.visit(t)
            elif isinstance(title, str):
                self.write(title)
            else:
                self.visit(title)
        self.write("\n")

        blocks = getattr(node, "blocks", []) or []
        for block in blocks:
            self.write("\n")
            self.visit(block)

    def visit_heading(self, node: Node) -> None:
        """
        Serialize a discrete heading node back to AsciiDoc source markup.

        Emits block-level attributes (anchor id, role, named attrs) first,
        then the `[discrete]` directive merged with any extra named attributes,
        followed by the heading marker and title inlines.

        *Parameters:*

        `node`:: The `DiscreteHeading` node to serialize.
        """
        attrs = getattr(node, "attributes", {}) or {}

        # 1. Anchor / ID — emitted as a standalone anchor line before [discrete]
        if attrs.get("id"):
            self.write(f"[[{attrs['id']}]]\n")

        # 2. Role — emitted as a standalone attribute line before [discrete]
        if attrs.get("role"):
            self.write(f"[.{attrs['role']}]\n")

        # 3. [discrete] with any remaining extra named attributes merged in
        _skip: set[str] = {
            "id",
            "role",
            "title",
            "form",
            "delimiter",
            "checked",
            "positional",
            "positional_attributes",
            "style",
            "language",
        }
        extra: list[str] = []
        for k, v in attrs.items():
            if k in _skip or (isinstance(k, str) and k.isdigit()):
                continue
            if isinstance(v, bool):
                if v:
                    extra.append(str(k))
            else:
                val_s = str(v)
                extra.append(
                    f'{k}="{val_s}"'
                    if (" " in val_s or "," in val_s)
                    else f"{k}={val_s}"
                )

        if extra:
            self.write(f"[discrete,{','.join(extra)}]\n")
        else:
            self.write("[discrete]\n")

        level = getattr(node, "level", 1)
        if level is None:
            level = 1
        prefix = "=" * (level + 1)
        self.write(f"{prefix} ")
        title = getattr(node, "title", None)
        if title:
            if isinstance(title, list):
                for t in title:
                    self.visit(t)
            elif isinstance(title, str):
                self.write(title)
            else:
                self.visit(title)
        self.write("\n")

    visit_floatingtitle = visit_heading
    visit_discreteheading = visit_heading

    def visit_title(self, node: Node) -> None:
        """
        Serialize a title inline node sequence.

        *Parameters:*

        `node`:: The `Title` node to serialize.
        """
        for inline in getattr(node, "inlines", []):
            self.visit(inline)

    def visit_paragraph(self, node: Node) -> None:
        """
        Serialize a paragraph block node.

        *Parameters:*

        `node`:: The `Paragraph` AST node to serialize.
        """
        self.write_block_metadata(node)
        for inline in getattr(node, "inlines", []):
            self.visit(inline)
        self.write("\n")

    def visit_listing(self, node: Node) -> None:
        """
        Serialize a listing/source code block node (`----`).

        *Parameters:*

        `node`:: The `Listing` AST node to serialize.
        """
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "----") or "----"
        self.write(f"{delim}\n")
        code = getattr(node, "code", "")
        self.write(code)
        if code and not code.endswith("\n"):
            self.write("\n")
        self.write(f"{delim}\n")

    def visit_literal(self, node: Node) -> None:
        """
        Serialize a literal block node (`....` delimited or indented).

        *Parameters:*

        `node`:: The `Literal` AST node to serialize.
        """
        self.write_block_metadata(node)
        form = getattr(node, "form", "delimited")
        if form == "delimited":
            delim = getattr(node, "delimiter", "....") or "...."
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

    def visit_comment(self, node: Node) -> None:
        """
        Serialize a delimited comment block node (`////`).

        *Parameters:*

        `node`:: The `Comment` AST node to serialize.
        """
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "////") or "////"
        self.write(f"{delim}\n")
        value = getattr(node, "value", "")
        self.write(value)
        if value and not value.endswith("\n"):
            self.write("\n")
        self.write(f"{delim}\n")

    def visit_sidebar(self, node: Node) -> None:
        """
        Serialize a sidebar block node (`****`).

        *Parameters:*

        `node`:: The `Sidebar` AST node to serialize.
        """
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "****") or "****"
        self.write(f"{delim}\n")
        for block in getattr(node, "blocks", []):
            self.visit(block)
        val = self.stream.getvalue()
        if not val.endswith("\n"):
            self.write("\n")
        self.write(f"{delim}\n")

    def visit_example(self, node: Node) -> None:
        """
        Serialize an example block node (`====`).

        *Parameters:*

        `node`:: The `Example` AST node to serialize.
        """
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "====") or "===="
        self.write(f"{delim}\n")
        for block in getattr(node, "blocks", []):
            self.visit(block)
        val = self.stream.getvalue()
        if not val.endswith("\n"):
            self.write("\n")
        self.write(f"{delim}\n")

    def visit_quote(self, node: Node) -> None:
        """
        Serialize a quote block node.

        Emits block metadata (such as `[quote, attribution, citetitle]`) followed
        by either delimited `____` blocks or paragraph-form quote blocks.

        *Parameters:*

        `node`:: The `Quote` AST node to serialize.
        """
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", None)
        form = getattr(node, "form", "delimited" if delim else "paragraph")
        if form == "delimited" or delim:
            d = delim or "____"
            self.write(f"{d}\n")
            for block in getattr(node, "blocks", []):
                self.visit(block)
            val = self.stream.getvalue()
            if not val.endswith("\n"):
                self.write("\n")
            self.write(f"{d}\n")
        else:
            for block in getattr(node, "blocks", []):
                self.visit(block)

    def visit_verse(self, node: Node) -> None:
        """
        Serialize a verse block node.

        Emits `[verse, attribution, citetitle]` metadata followed by either
        delimited `____` lines or paragraph-form verse lines.

        *Parameters:*

        `node`:: The `Verse` AST node to serialize.
        """
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", None)
        form = getattr(node, "form", "delimited" if delim else "paragraph")
        if form == "delimited" or delim:
            d = delim or "____"
            self.write(f"{d}\n")
            for block in getattr(node, "blocks", []):
                self.visit(block)
            val = self.stream.getvalue()
            if not val.endswith("\n"):
                self.write("\n")
            self.write(f"{d}\n")
        else:
            for block in getattr(node, "blocks", []):
                self.visit(block)

    def visit_collapsible(self, node: Node) -> None:
        """
        Serialize an interactive collapsible block node.

        Emits `.Title` caption, `[%collapsible]` option directive, and
        `====` delimited content.

        *Parameters:*

        `node`:: The `Collapsible` AST node to serialize.
        """
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "====") or "===="
        self.write(f"{delim}\n")
        for block in getattr(node, "blocks", []):
            self.visit(block)
        val = self.stream.getvalue()
        if not val.endswith("\n"):
            self.write("\n")
        self.write(f"{delim}\n")

    def visit_admonition(self, node: Node) -> None:
        """
        Serialize an admonition node (`NOTE: ...` paragraph form or `[NOTE]\n====` delimited form).

        *Parameters:*

        `node`:: The `Admonition` AST node to serialize.
        """
        form = getattr(node, "form", "paragraph")
        variant = getattr(node, "variant", "note").upper()
        if form == "delimited":
            self.write(f"[{variant}]\n")
            delim = getattr(node, "delimiter", "====") or "===="
            self.write(f"{delim}\n")
            for block in getattr(node, "blocks", []):
                self.visit(block)
            val = self.stream.getvalue()
            if not val.endswith("\n"):
                self.write("\n")
            self.write(f"{delim}\n")
        else:
            self.write(f"{variant}: ")
            blocks = getattr(node, "blocks", [])
            if blocks:
                first_block = blocks[0]
                for inline in getattr(first_block, "inlines", []):
                    self.visit(inline)
                self.write("\n")
                for block in blocks[1:]:
                    self.write("+\n")
                    self.visit(block)

    def visit_open(self, node: Node) -> None:
        """
        Serialize an open container block node.

        Emits preceding block metadata followed by the open block delimiter
        (`--` or `~~~~`) and child block elements.

        *Parameters:*

        `node`:: The `Open` AST node to serialize.
        """
        self.write_block_metadata(node)
        delim = getattr(node, "delimiter", "--") or "--"
        self.write(f"{delim}\n")
        for block in getattr(node, "blocks", []):
            self.visit(block)
        val = self.stream.getvalue()
        if not val.endswith("\n"):
            self.write("\n")
        self.write(f"{delim}\n")

    def visit_list(self, node: Node) -> None:
        """
        Serialize a list AST node back to AsciiDoc source markup.

        Emits preceding block metadata lines (such as `[loweralpha]`, `[start=N]`,
        `[%reversed]`, anchor ID, and title), followed by each child list item.

        *Parameters:*

        `node`:: The `List` node to serialize.
        """
        self.write_block_metadata(node)
        for item in getattr(node, "items", []):
            self.visit(item)

    def visit_listitem(self, node: Node) -> None:
        """
        Serialize a single list item node back to AsciiDoc source markup.

        Emits the item marker string, optional checklist prefix (`[x]` or `[ ]`),
        principal inline nodes, and attached continuation blocks (`+`).

        *Parameters:*

        `node`:: The `ListItem` node to serialize.
        """
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

    visit_list_item = visit_listitem

    def visit_calloutlist(self, node: Node) -> None:
        """
        Serialize a callout list block containing callout list items.

        *Parameters:*

        `node`:: The `CalloutList` AST node to serialize.
        """
        self.write_block_metadata(node)
        for item in getattr(node, "items", []):
            self.visit(item)

    visit_callout_list = visit_calloutlist

    def visit_calloutlistitem(self, node: Node) -> None:
        """
        Serialize a single callout list item node with its numerical marker.

        *Parameters:*

        `node`:: The `CalloutListItem` AST node to serialize.
        """
        marker = getattr(node, "marker", None)
        if not marker:
            num = getattr(node, "value", 1)
            marker = f"<{num}>"
        self.write(f"{marker} ")
        for inline in getattr(node, "principal", []):
            self.visit(inline)
        self.write("\n")
        for block in getattr(node, "blocks", []):
            self.write("+\n")
            self.visit(block)

    visit_callout_list_item = visit_calloutlistitem

    def visit_descriptionlist(self, node: Node) -> None:
        """
        Serialize a description list block node.

        *Parameters:*

        `node`:: The `DescriptionList` AST node to serialize.
        """
        self.write_block_metadata(node)
        for item in getattr(node, "items", []):
            self.visit(item)

    visit_description_list = visit_descriptionlist

    def visit_descriptionlistitem(self, node: Node) -> None:
        """
        Serialize a description list item node (terms followed by descriptions).

        *Parameters:*

        `node`:: The `DescriptionListItem` AST node to serialize.
        """
        for term in getattr(node, "terms", []):
            self.visit(term)
        blocks = getattr(node, "blocks", [])
        for i, block in enumerate(blocks):
            if i > 0:
                self.write("+\n")
            self.visit(block)

    visit_description_list_item = visit_descriptionlistitem

    def visit_descriptionlistterm(self, node: Node) -> None:
        """
        Serialize a description list term inline node with its trailing marker (`::`).

        *Parameters:*

        `node`:: The `DescriptionListTerm` AST node to serialize.
        """
        for inline in getattr(node, "inlines", []):
            self.visit(inline)
        marker = getattr(node, "marker", "::") or "::"
        self.write(f"{marker}\n")

    visit_description_list_term = visit_descriptionlistterm

    def visit_table(self, node: Node) -> None:
        """
        Serialize a table block node (`|===`).

        *Parameters:*

        `node`:: The `Table` AST node to serialize.
        """
        self.write_block_metadata(node)
        self.write("|===\n")
        for row in getattr(node, "rows", []):
            self.visit(row)
        self.write("|===\n")

    def visit_row(self, node: Node) -> None:
        """
        Serialize a table row by serializing its cells in order.

        *Parameters:*

        `node`:: The `TableRow` AST node to serialize.
        """
        cells = getattr(node, "cells", []) or []
        for i, cell in enumerate(cells):
            self.visit_cell(cell, is_first=(i == 0))
        self.write("\n")

    def visit_cell(self, node: Node, is_first: bool = False) -> None:
        """
        Serialize a single table cell with optional colspan, rowspan, alignment, and style specifiers.

        *Parameters:*

        `node`:: The `TableCell` AST node to serialize.
        `is_first`:: Boolean indicating whether this cell is the first cell in its row.
        """
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
                "asciidoc": "a",
                "code": "c",
                "default": "d",
                "emphasis": "e",
                "header": "h",
                "literal": "l",
                "monospaced": "m",
                "strong": "s",
                "verse": "v",
            }
            specifiers.append(style_map.get(style.lower(), style))

        prefix = "".join(specifiers)
        lead = "" if is_first else " "
        self.write(f"{lead}{prefix}| ")

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
        """
        Serialize a thematic break horizontal rule (`'''`).

        *Parameters:*

        `node`:: The `ThematicBreak` AST node to serialize.
        """
        self.write("'''\n")

    def visit_page_break(self, node: Node) -> None:
        """
        Serialize a page break (`<<<`).

        *Parameters:*

        `node`:: The `PageBreak` AST node to serialize.
        """
        self.write("<<<\n")

    def visit_attribute_entry(self, node: Node) -> None:
        """
        Serialize an attribute entry declaration (`:name: value`).

        *Parameters:*

        `node`:: The `AttributeEntry` AST node to serialize.
        """
        name = getattr(node, "attribute_name", "")
        value = getattr(node, "value", "")
        if value:
            self.write(f":{name}: {value}\n")
        else:
            self.write(f":{name}:\n")

    def visit_attributes(self, node: Node) -> None:
        """
        Serialize an `Attributes` semantic block node back to attribute entries.

        *Parameters:*

        `node`:: The `Attributes` block node to serialize.
        """
        attrs = getattr(node, "attributes", {}) or {}
        for k, v in attrs.items():
            if v is True:
                self.write(f":{k}:\n")
            elif v is not None:
                self.write(f":{k}: {v}\n")

    def visit_include(self, node: Node) -> None:
        """
        Serialize an include directive macro (`include::file[]`).

        *Parameters:*

        `node`:: The `Include` AST node to serialize.
        """
        filename = getattr(node, "filename", "")
        self.write(f"include::{filename}[]\n")

    def visit_toc(self, node: Node) -> None:
        """
        Serialize a table of contents block macro (`toc::target[attrs]`).

        *Parameters:*

        `node`:: The `Toc` block node to serialize.
        """
        target = getattr(node, "target", "")
        attr_str = self._format_macro_attributes(node)
        self.write(f"toc::{target}[{attr_str}]\n")

    # --- Inline Visitors ---

    def visit_text(self, node: Node) -> None:
        """
        Serialize a raw text inline leaf node.

        *Parameters:*

        `node`:: The `Text` AST node to serialize.
        """
        self.write(getattr(node, "value", ""))

    def visit_break(self, node: Node) -> None:
        """
        Serialize a forced line break inline node (` +\\n`).

        *Parameters:*

        `node`:: The `Break` AST node to serialize.
        """
        self.write(" +\n")

    def visit_span(self, node: Node) -> None:
        """
        Serialize an inline formatted text span (bold, italic, code, mark, sub, super, quotes).

        *Parameters:*

        `node`:: The `Span` inline node to serialize.
        """
        variant = getattr(node, "variant", "")
        form = getattr(node, "form", "constrained")

        markup_map = {
            "strong": ("*", "**"),
            "emphasis": ("_", "__"),
            "code": ("`", "``"),
            "mark": ("#", "##"),
            "superscript": ("^", "^"),
            "subscript": ("~", "~"),
        }

        if variant in markup_map:
            markers = markup_map[variant]
            marker = markers[0] if form == "constrained" else markers[1]
            self.write(marker)
            for child in getattr(node, "inlines", []):
                self.visit(child)
            self.write(marker)
        elif variant == "double":
            self.write('"`')
            for child in getattr(node, "inlines", []):
                self.visit(child)
            self.write('`"')
        elif variant == "single":
            self.write("'`")
            for child in getattr(node, "inlines", []):
                self.visit(child)
            self.write("`'")
        else:
            for child in getattr(node, "inlines", []):
                self.visit(child)

    def visit_ref(self, node: Node) -> None:
        """
        Serialize an inline reference node (hyperlink, cross-reference, footnote, anchor, or bibref).

        *Parameters:*

        `node`:: The `Ref` inline node to serialize.
        """
        variant = getattr(node, "variant", "link")
        target = getattr(node, "target", "")
        source_text = getattr(node, "_source_text", "") or ""

        if variant == "link":
            has_scheme = (
                target.startswith("http://")
                or target.startswith("https://")
                or target.startswith("mailto:")
            )
            attrs = getattr(node, "attributes", {}) or {}
            inlines = getattr(node, "inlines", []) or []
            if attrs.get("role") == "bare":
                clean_target = target[7:] if target.startswith("mailto:") else target
                self.write(clean_target)
            elif has_scheme and not inlines and not attrs:
                self.write(target)
            else:
                prefix = "" if has_scheme else "link:"
                self.write(f"{prefix}{target}[")

                label_parts = []
                for child in inlines:
                    label_parts.append(AsciiDocSerializerVisitor().serialize(child))
                self.write("".join(label_parts))

                if attrs.get("window") == "_blank":
                    self.write("^")
                self.write("]")
        elif variant == "xref":
            label_parts = []
            for child in getattr(node, "inlines", []):
                label_parts.append(AsciiDocSerializerVisitor().serialize(child))
            label = "".join(label_parts)
            if source_text.startswith("xref:"):
                self.write(f"xref:{target}[{label}]")
            else:
                self.write(f"<<{target}")
                if label and label != target:
                    self.write(f", {label}")
                self.write(">>")
        elif variant == "footnote":
            if not target:
                self.write("footnote:[")
                label_parts = []
                for child in getattr(node, "inlines", []):
                    label_parts.append(AsciiDocSerializerVisitor().serialize(child))
                self.write("".join(label_parts))
                self.write("]")
            else:
                self.write(f"footnoteref:[{target}")
                label_parts = []
                for child in getattr(node, "inlines", []):
                    label_parts.append(AsciiDocSerializerVisitor().serialize(child))
                if label_parts:
                    self.write(f", {''.join(label_parts)}")
                self.write("]")
        elif variant == "anchor":
            label_parts = []
            for child in getattr(node, "inlines", []):
                label_parts.append(AsciiDocSerializerVisitor().serialize(child))
            label = "".join(label_parts)
            if source_text.startswith("anchor:"):
                self.write(f"anchor:{target}[{label}]")
            else:
                if label and label != target:
                    self.write(f"[[{target}, {label}]]")
                else:
                    self.write(f"[[{target}]]")
        elif variant == "bibref":
            label_parts = []
            for child in getattr(node, "inlines", []):
                label_parts.append(AsciiDocSerializerVisitor().serialize(child))
            label = "".join(label_parts)
            if label and label != target:
                self.write(f"[[[{target}, {label}]]]")
            else:
                self.write(f"[[[{target}]]]")

    def visit_image(self, node: Node) -> None:
        """
        Serialize an image macro node (either block macro or inline macro).

        *Parameters:*

        `node`:: The `Image` node to serialize.
        """
        target = getattr(node, "target", "")
        form = getattr(node, "form", "macro")
        node_type = getattr(node, "type", "block")
        attr_str = self._format_macro_attributes(node, default_first_attr="alt")

        if node_type == "inline" or form == "inline":
            self.write(f"image:{target}[{attr_str}]")
        else:
            self.write(f"image::{target}[{attr_str}]\n")

    def visit_audio(self, node: Node) -> None:
        """
        Serialize an audio block macro (`audio::target[attrs]`).

        *Parameters:*

        `node`:: The `Audio` block node to serialize.
        """
        target = getattr(node, "target", "")
        attr_str = self._format_macro_attributes(node)
        self.write(f"audio::{target}[{attr_str}]\n")

    def visit_video(self, node: Node) -> None:
        """
        Serialize a video block macro (`video::target[attrs]`).

        *Parameters:*

        `node`:: The `Video` block node to serialize.
        """
        target = getattr(node, "target", "")
        attr_str = self._format_macro_attributes(node)
        self.write(f"video::{target}[{attr_str}]\n")

    def visit_kbd(self, node: Node) -> None:
        """
        Serialize a keyboard macro node (`kbd:[keys]`).

        *Parameters:*

        `node`:: The `Kbd` inline node to serialize.
        """
        keys = getattr(node, "value", []) or []
        self.write(f"kbd:[{'+'.join(keys)}]")

    def visit_button(self, node: Node) -> None:
        """
        Serialize a GUI button macro node (`btn:[label]`).

        *Parameters:*

        `node`:: The `Button` inline node to serialize.
        """
        label = getattr(node, "value", "")
        self.write(f"btn:[{label}]")

    def visit_menu(self, node: Node) -> None:
        """
        Serialize a menu macro node (`menu:Menu[Item > Subitem]`).

        *Parameters:*

        `node`:: The `Menu` inline node to serialize.
        """
        menu = getattr(node, "menu", "")
        items = getattr(node, "items", []) or []
        self.write(f"menu:{menu}[{' > '.join(items)}]")

    def visit_callout(self, node: Node) -> None:
        """
        Serialize an inline callout reference node (`<1>`).

        *Parameters:*

        `node`:: The `Callout` inline node to serialize.
        """
        num = getattr(node, "value", 1)
        self.write(f"<{num}>")

    def visit_stem(self, node: Node) -> None:
        """
        Serialize a mathematical expression node (either inline or block stem).

        *Parameters:*

        `node`:: The `Stem` or `InlineStem` AST node to serialize.
        """
        node_type = getattr(node, "type", "block")
        variant = getattr(node, "variant", "asciimath")
        if node_type == "inline":
            val = getattr(node, "value", "")
            self.write(f"{variant}:[{val}]")
        else:
            self.write_block_metadata(node)
            attrs = getattr(node, "attributes", {}) or {}
            block_style = attrs.get("style") or "stem"
            self.write(f"[{block_style}]\n")
            delim = getattr(node, "delimiter", "++++") or "++++"
            self.write(f"{delim}\n")
            for inline in getattr(node, "inlines", []):
                self.visit(inline)
            val = self.stream.getvalue()
            if not val.endswith("\n"):
                self.write("\n")
            self.write(f"{delim}\n")

    def visit_passthrough(self, node: Node) -> None:
        """
        Serialize a passthrough node (`pass:[content]`, `+++content+++`, or `++++` block).

        *Parameters:*

        `node`:: The `Passthrough` or `InlinePassthrough` node to serialize.
        """
        node_type = getattr(node, "type", "block")
        if node_type == "inline":
            form = getattr(node, "form", "macro")
            val = getattr(node, "value", "")
            if form == "triple_plus":
                self.write(f"+++{val}+++")
            else:
                self.write(f"pass:[{val}]")
        else:
            self.write_block_metadata(node)
            delim = getattr(node, "delimiter", "++++") or "++++"
            self.write(f"{delim}\n")
            for inline in getattr(node, "inlines", []):
                self.visit(inline)
            val = self.stream.getvalue()
            if not val.endswith("\n"):
                self.write("\n")
            self.write(f"{delim}\n")

    def visit_indexterm(self, node: Node) -> None:
        """
        Serializes an `IndexTerm` AST node back to its canonical AsciiDoc source form.

        *Parameters:*

        `node`:: The `IndexTerm` AST node to serialize.

        *Syntactic Forms:*

        * Flow double: visible index term with double parentheses.
        * Flow triple: hidden index term with triple parentheses.
        * Macro: indexterm macro syntax with comma-separated terms.
        """
        variant = getattr(node, "variant", "macro")
        if variant == "flow_double":
            self.write("((")
            inlines = getattr(node, "inlines", [])
            if inlines:
                for inline in inlines:
                    self.visit(inline)
            else:
                primary = getattr(node, "primary", "")
                if not primary:
                    node_terms = getattr(node, "terms", None)
                    if node_terms:
                        primary = str(node_terms[0])
                self.write(primary)
            self.write("))")
        elif variant == "flow_triple":
            terms = list(getattr(node, "terms", []))
            if not terms:
                primary = getattr(node, "primary", "")
                if primary:
                    terms.append(primary)
                secondary = getattr(node, "secondary", None)
                if secondary:
                    terms.append(secondary)
                tertiary = getattr(node, "tertiary", None)
                if tertiary:
                    terms.append(tertiary)
            terms_str = ", ".join(terms)
            self.write(f"((({terms_str})))")
        else:
            terms = list(getattr(node, "terms", []))
            if not terms:
                primary = getattr(node, "primary", "")
                if primary:
                    terms.append(primary)
                secondary = getattr(node, "secondary", None)
                if secondary:
                    terms.append(secondary)
                tertiary = getattr(node, "tertiary", None)
                if tertiary:
                    terms.append(tertiary)
            formatted_terms = []
            for t in terms:
                if "," in t and not (
                    (t.startswith('"') and t.endswith('"'))
                    or (t.startswith("'") and t.endswith("'"))
                ):
                    formatted_terms.append(f'"{t}"')
                else:
                    formatted_terms.append(t)
            args_str = ",".join(formatted_terms)
            self.write(f"indexterm:[{args_str}]")

    def visit_author(self, node: Node) -> None:
        """
        Serialize an author node from its child inlines.

        *Parameters:*

        `node`:: The `Author` inline node to serialize.
        """
        for inline in getattr(node, "inlines", []):
            self.visit(inline)

    def visit_revision(self, node: Node) -> None:
        """
        Serialize a revision node from its child inlines.

        *Parameters:*

        `node`:: The `Revision` node to serialize.
        """
        for inline in getattr(node, "inlines", []):
            self.visit(inline)

    def visit_docinfo(self, node: Node) -> None:
        """
        No-op serializer for injected docinfo metadata.

        *Parameters:*

        `node`:: The `Docinfo` metadata node to serialize.
        """
        pass

    def generic_visit(self, node: Node, **kwargs: Any) -> Any:
        """
        Fallback visitor traversing all child node collections of unhandled nodes.

        *Parameters:*

        `node`:: The AST node to traverse.
        `**kwargs`:: Additional arguments forwarded to child node visitors.
        """
        for collection in node.get_child_collections().values():
            for child in collection:
                self.visit(child, **kwargs)


def serialize_to_asciidoc(node: Node) -> str:
    """
    Public API to serialize any AST node back to its AsciiDoc string representation.

    *Parameters:*

    `node`::
      The `Node` AST instance to serialize (e.g. `Document`, `Section`, `Paragraph`, etc.).

    *Returns:*

    A string containing the serialized AsciiDoc markup representation.

    *Notes:*

    If serializing a preprocessed AST document (`is_preprocessed=True`), the output will be a flat, expanded document since original `include::` directives cannot be reconstructed.

    *Example:*

    [source,python]
    ----
    from asciidoctrine.lark_parser import parse_to_ast
    from asciidoctrine.serializer import serialize_to_asciidoc

    doc = parse_to_ast("= Document Title\\n\\nThis is a *bold* paragraph.")
    output = serialize_to_asciidoc(doc)
    assert "= Document Title" in output
    ----
    """
    if getattr(node, "name", None) == "document" and getattr(
        node, "is_preprocessed", False
    ):
        import warnings

        warnings.warn(
            "Serializing a preprocessed AST will output a flat, expanded document. "
            "Original include directives cannot be reconstructed.",
            UserWarning,
            stacklevel=2,
        )
    visitor = AsciiDocSerializerVisitor()
    return visitor.serialize(node)
