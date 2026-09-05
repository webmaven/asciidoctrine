import re
from typing import Any, Dict, Optional, Tuple, cast
from typing import List as PyList

from lark import Token, v_args

from ..nodes import (
    Break,
    Button,
    Callout,
    Image,
    IndexTerm,
    InlinePassthrough,
    InlineStem,
    Kbd,
    Menu,
    Node,
    Ref,
    Span,
    Text,
)
from .base_transformer import BaseTransformer

SPAN_DELIMITERS: Dict[Tuple[str, str], Tuple[str, str]] = {
    ("strong", "constrained"): ("*", "*"),
    ("strong", "unconstrained"): ("**", "**"),
    ("emphasis", "constrained"): ("_", "_"),
    ("emphasis", "unconstrained"): ("__", "__"),
    ("code", "constrained"): ("`", "`"),
    ("code", "unconstrained"): ("``", "``"),
    ("mark", "constrained"): ("#", "#"),
    ("mark", "unconstrained"): ("##", "##"),
    ("superscript", "constrained"): ("^", "^"),
    ("subscript", "constrained"): ("~", "~"),
}


class InlineTransformer(BaseTransformer):
    """
    Mixin class for inline-level AsciiDoc transformations.
    """

    # Regex to match backslash-escaped autolink patterns in Text node values.
    # Matches \https://, \http://, \ftp://, etc. and \user@domain patterns.
    _ESCAPED_AUTOLINK_RE = re.compile(
        r"\\((?:https?|ftp|file|irc)://|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5})"
    )

    # attributes: Dict[str, PyList[Node]]  # Will be provided by main transformer

    @v_args(meta=True)
    def attribute_reference(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        import copy

        name = ""
        for c in children:
            if isinstance(c, Token) and c.type == "ATTR_NAME":
                name = c.value
                break

        # Access attributes from the instance (AsciiDocTransformer)
        attrs = cast(Dict[str, PyList[Node]], getattr(self, "attributes"))
        nodes = attrs.get(name, [Text(f"{{{name}}}")])
        # Return a deep copy to avoid modifying the original attribute nodes during
        # merging
        return [copy.deepcopy(n) for n in nodes]

    @v_args(meta=True)
    def text_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        nodes: PyList[Node] = []
        pending_attrs: Optional[Dict[str, str]] = None

        flat_children: PyList[Any] = []
        for child in children:
            if isinstance(child, list) and not isinstance(child, Node):
                flat_children.extend(child)
            else:
                flat_children.append(child)

        i = 0
        while i < len(flat_children):
            child = flat_children[i]

            if isinstance(child, dict):
                pending_attrs = child
                i += 1
                continue

            node: Optional[Node] = None
            if isinstance(child, Token):
                node = Text(str(child.value))
                if (
                    child.line is not None
                    and child.column is not None
                    and child.end_line is not None
                    and child.end_column is not None
                ):
                    node.location = [
                        {"line": child.line, "col": child.column},
                        {"line": child.end_line, "col": child.end_column - 1},
                    ]
            elif isinstance(child, Node):
                node = child

            if node:
                # Handle escaping and angle bracket stripping for bare links and inline macros
                is_bare = (
                    isinstance(node, Ref)
                    and getattr(node, "attributes", {}).get("role") == "bare"
                )
                is_macro = (
                    isinstance(node, Ref)
                    or isinstance(node, Image)
                    or isinstance(
                        node,
                        (
                            Kbd,
                            Button,
                            Menu,
                            Callout,
                            InlineStem,
                            InlinePassthrough,
                            IndexTerm,
                        ),
                    )
                    or getattr(node, "_source_text", None) is not None
                )
                if is_bare:
                    # Escaping check: if previous text ends with '\'
                    if (
                        nodes
                        and isinstance(nodes[-1], Text)
                        and nodes[-1].value.endswith("\\")
                    ):
                        # Strip the trailing backslash
                        nodes[-1].value = nodes[-1].value[:-1]
                        if not nodes[-1].value:
                            nodes.pop()
                        # Convert Ref to plain Text
                        target = getattr(node, "target", "")
                        display = target[7:] if target.startswith("mailto:") else target
                        node = Text(display)
                    else:
                        # Angle bracket check: previous text ends with '<'
                        # and next item is '>' (either Token or Text node from
                        # punctuation stripping in bare_url_link).
                        if (
                            nodes
                            and isinstance(nodes[-1], Text)
                            and nodes[-1].value.endswith("<")
                        ):
                            next_is_gt = False
                            if i + 1 < len(flat_children):
                                next_child = flat_children[i + 1]
                                if (
                                    isinstance(next_child, Token)
                                    and str(next_child.value) == ">"
                                ):
                                    next_is_gt = True
                                elif isinstance(
                                    next_child, Text
                                ) and next_child.value.startswith(">"):
                                    next_is_gt = True
                            if next_is_gt:
                                # Strip '<' from previous text
                                nodes[-1].value = nodes[-1].value[:-1]
                                if not nodes[-1].value:
                                    nodes.pop()
                                # Strip the leading '>' from the next item
                                next_child = flat_children[i + 1]
                                if isinstance(next_child, Token):
                                    # Skip the '>' token entirely
                                    i += 1
                                elif isinstance(next_child, Text):
                                    # Strip leading '>' from Text node in-place
                                    next_child.value = next_child.value[1:]
                                    if not next_child.value:
                                        # Remove the empty Text node from flat_children
                                        flat_children.pop(i + 1)
                elif is_macro:
                    # Macro escaping check: if previous text ends with '\'
                    if (
                        nodes
                        and isinstance(nodes[-1], Text)
                        and nodes[-1].value.endswith("\\")
                    ):
                        trailing_slashes = len(nodes[-1].value) - len(
                            nodes[-1].value.rstrip("\\")
                        )
                        if trailing_slashes % 2 == 1:
                            raw_text = getattr(node, "_source_text", None)
                            if raw_text is None:
                                if isinstance(node, Ref):
                                    label = "".join(
                                        getattr(n, "value", "")
                                        for n in getattr(node, "inlines", [])
                                        if hasattr(n, "value")
                                    )
                                    raw_text = f"{node.variant}:{node.target}[{label}]"
                                else:
                                    raw_text = getattr(node, "value", "")

                            # Check if this macro was wrapped in backticks (e.g. `\xref:...`)
                            is_monospace_wrapped = (
                                nodes[-1].value.endswith("`\\")
                                and (i + 1 < len(flat_children))
                                and (
                                    (
                                        isinstance(flat_children[i + 1], Token)
                                        and str(flat_children[i + 1].value) == "`"
                                    )
                                    or (
                                        isinstance(flat_children[i + 1], Text)
                                        and flat_children[i + 1].value.startswith("`")
                                    )
                                )
                            )

                            raw_text_str = str(raw_text or "")
                            if is_monospace_wrapped:
                                nodes[-1].value = nodes[-1].value[:-2]
                                if not nodes[-1].value:
                                    nodes.pop()
                                next_child = flat_children[i + 1]
                                if isinstance(next_child, Token):
                                    i += 1
                                elif isinstance(next_child, Text):
                                    next_child.value = next_child.value[1:]
                                    if not next_child.value:
                                        flat_children.pop(i + 1)
                                text_node = Text(raw_text_str)
                                if node.location:
                                    text_node.location = node.location
                                node = Span(
                                    variant="code",
                                    form="constrained",
                                    inlines=[text_node],
                                )
                                if text_node.location:
                                    node.location = text_node.location
                            else:
                                nodes[-1].value = nodes[-1].value[:-1]
                                if not nodes[-1].value:
                                    nodes.pop()
                                text_node = Text(raw_text_str)
                                if node.location:
                                    text_node.location = node.location
                                node = text_node
                        else:
                            # Even number of backslashes: strip one backslash, keep macro active
                            nodes[-1].value = nodes[-1].value[:-1]
                elif (
                    isinstance(node, Span)
                    and (
                        node.variant,
                        getattr(node, "form", "constrained") or "constrained",
                    )
                    in SPAN_DELIMITERS
                ):
                    open_delim, close_delim = SPAN_DELIMITERS[
                        (
                            node.variant,
                            getattr(node, "form", "constrained") or "constrained",
                        )
                    ]
                    if (
                        nodes
                        and isinstance(nodes[-1], Text)
                        and nodes[-1].value.endswith("\\")
                    ):
                        trailing_slashes = len(nodes[-1].value) - len(
                            nodes[-1].value.rstrip("\\")
                        )
                        if trailing_slashes % 2 == 1:
                            is_escaped = True
                            slashes_to_remove = (trailing_slashes + 1) // 2
                        elif len(open_delim) > 1 and trailing_slashes == 2:
                            is_escaped = True
                            slashes_to_remove = 2
                        else:
                            is_escaped = False
                            slashes_to_remove = trailing_slashes // 2

                        if slashes_to_remove > 0:
                            nodes[-1].value = nodes[-1].value[:-slashes_to_remove]
                            if (
                                nodes[-1].location
                                and len(nodes[-1].location) == 2
                                and "col" in nodes[-1].location[1]
                            ):
                                nodes[-1].location[1]["col"] -= slashes_to_remove
                            if not nodes[-1].value:
                                nodes.pop()

                        if is_escaped:
                            open_node = Text(open_delim)
                            close_node = Text(close_delim)
                            if (
                                node.location
                                and len(node.location) == 2
                                and "line" in node.location[0]
                                and "col" in node.location[0]
                                and "line" in node.location[1]
                                and "col" in node.location[1]
                            ):
                                start_loc = node.location[0]
                                end_loc = node.location[1]
                                open_node.location = [
                                    {
                                        "line": start_loc["line"],
                                        "col": start_loc["col"],
                                    },
                                    {
                                        "line": start_loc["line"],
                                        "col": start_loc["col"] + len(open_delim) - 1,
                                    },
                                ]
                                close_node.location = [
                                    {
                                        "line": end_loc["line"],
                                        "col": end_loc["col"] - len(close_delim) + 1,
                                    },
                                    {
                                        "line": end_loc["line"],
                                        "col": end_loc["col"],
                                    },
                                ]
                            flat_children[i + 1 : i + 1] = [*node.inlines, close_node]
                            node = open_node

                if pending_attrs:
                    for k, v in pending_attrs.items():
                        if k == "role":
                            existing = node.attributes.get("role")
                            node.attributes["role"] = (
                                f"{existing} {v}" if existing else v
                            )
                        else:
                            node.attributes[k] = v
                    pending_attrs = None

                if (
                    nodes
                    and isinstance(nodes[-1], Text)
                    and isinstance(node, Text)
                    and nodes[-1].attributes == node.attributes
                ):
                    # Merge text nodes, update end location
                    nodes[-1].value += node.value
                    if nodes[-1].location and node.location:
                        nodes[-1].location[1] = node.location[1]
                else:
                    nodes.append(node)

            i += 1

        if pending_attrs:
            attr_str = ",".join([f"{k}={v}" for k, v in pending_attrs.items()])
            nodes.append(Text(f"[{attr_str}]"))

        # Post-processing: strip backslash escapes before autolink patterns.
        # When a backslash precedes a URI scheme or email pattern, the lexer
        # doesn't create a URI/EMAIL token, so the backslash ends up in the
        # Text node value. We strip it here to match AsciiDoc behavior.
        for node in nodes:
            if isinstance(node, Text):
                node.value = self._ESCAPED_AUTOLINK_RE.sub(r"\1", node.value)

        return nodes

    @v_args(meta=True)
    def bold_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return cast(PyList[Node], self.text_content(meta, children))

    @v_args(meta=True)
    def italic_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return cast(PyList[Node], self.text_content(meta, children))

    @v_args(meta=True)
    def marked_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return cast(PyList[Node], self.text_content(meta, children))

    @v_args(meta=True)
    def unconstrained_marked_content(
        self, meta: Any, children: PyList[Any]
    ) -> PyList[Node]:
        return cast(PyList[Node], self.text_content(meta, children))

    @v_args(meta=True)
    def superscript_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return cast(PyList[Node], self.text_content(meta, children))

    @v_args(meta=True)
    def subscript_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return cast(PyList[Node], self.text_content(meta, children))

    @v_args(meta=True)
    def footnote_text_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return cast(PyList[Node], self.text_content(meta, children))

    @v_args(meta=True)
    def bold(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(
            variant="strong", form="constrained", inlines=content[0] if content else []
        )
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def unconstrained_bold(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(
            variant="strong",
            form="unconstrained",
            inlines=content[0] if content else [],
        )
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def italic(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(
            variant="emphasis",
            form="constrained",
            inlines=content[0] if content else [],
        )
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def unconstrained_italic(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(
            variant="emphasis",
            form="unconstrained",
            inlines=content[0] if content else [],
        )
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def literal_content(self, meta: Any, children: PyList[Any]) -> str:
        return str(children[0])

    @v_args(meta=True)
    def monospace_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return self.text_content(meta, children)  # type: ignore

    @v_args(meta=True)
    def unconstrained_monospace_content(
        self, meta: Any, children: PyList[Any]
    ) -> PyList[Node]:
        return self.text_content(meta, children)  # type: ignore

    @v_args(meta=True)
    def monospace(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(
            variant="code",
            form="constrained",
            inlines=content[0] if content else [],
        )
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def unconstrained_monospace(self, meta: Any, children: PyList[Any]) -> Span:
        span = Span(variant="code", form="unconstrained", inlines=children[0])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def marked(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(
            variant="mark",
            form="constrained",
            inlines=content[0] if content else [],
        )
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def unconstrained_marked(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(
            variant="mark",
            form="unconstrained",
            inlines=content[0] if content else [],
        )
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def superscript(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(variant="superscript", inlines=content[0] if content else [])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def subscript(self, meta: Any, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        span = Span(variant="subscript", inlines=content[0] if content else [])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def footnote(self, meta: Any, children: PyList[Any]) -> Ref:
        ref = Ref(variant="footnote", target="", inlines=children[0])
        fn_text = "".join(
            getattr(n, "value", "") for n in children[0] if hasattr(n, "value")
        )
        ref._source_text = f"footnote:[{fn_text}]"
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def footnoteref(self, meta: Any, children: PyList[Any]) -> Ref:
        target = ""
        inlines = []
        for c in children:
            if isinstance(c, Token) and c.type in ("WORD", "FN_ID"):
                target = str(c.value)
            elif isinstance(c, list):
                inlines = c
        ref = Ref(variant="footnote", target=target, inlines=inlines)
        fn_text = "".join(
            getattr(n, "value", "") for n in inlines if hasattr(n, "value")
        )
        if fn_text:
            ref._source_text = f"footnoteref:[{target}, {fn_text}]"
        else:
            ref._source_text = f"footnoteref:[{target}]"
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def double_quoted(self, meta: Any, children: PyList[Any]) -> Span:
        span = Span(variant="double", inlines=children[0] if children else [])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def single_quoted(self, meta: Any, children: PyList[Any]) -> Span:
        span = Span(variant="single", inlines=children[0] if children else [])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def inline_image(self, meta: Any, children: PyList[Any]) -> Image:
        from lark import Token

        if isinstance(children[0], Token) and children[0].type == "IMAGE_PREFIX":
            children = children[1:]
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        alt = attrs.get("style", "")
        img = Image(target=target, alt=alt, form="macro", type="inline")
        img.attributes.update(attrs)
        if "style" in img.attributes:
            img.attributes["alt"] = img.attributes.pop("style")
        raw_attr = getattr(attrs, "raw", alt)
        img._source_text = f"image:{target}[{raw_attr}]"
        return cast(Image, self._set_location_from_children(img, children))

    @v_args(meta=True)
    def icon_inline(self, meta: Any, children: PyList[Any]) -> Image:
        from lark import Token

        if isinstance(children[0], Token) and children[0].type == "ICON_PREFIX":
            children = children[1:]
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        img = Image(target=target, alt="", form="macro", type="inline")
        img.name = "icon"
        img.attributes.update(attrs)
        raw_attr = getattr(attrs, "raw", "")
        img._source_text = f"icon:{target}[{raw_attr}]"
        return cast(Image, self._set_location_from_children(img, children))

    @v_args(meta=True)
    def inline_anchor(self, meta: Any, children: PyList[Any]) -> Ref:
        from lark import Token

        if isinstance(children[0], Token) and children[0].type == "ANCHOR_PREFIX":
            children = children[1:]
        if isinstance(children[0], Token) and children[0].type in ("TARGET", "URI"):
            target = children[0].value
            attrs = (
                children[1]
                if len(children) > 1 and isinstance(children[1], dict)
                else {}
            )
            label = attrs.get("style", target)
            ref = Ref(variant="anchor", target=target.strip(), inlines=[Text(label)])
            raw_attr = getattr(attrs, "raw", "")
            ref._source_text = f"anchor:{target}[{raw_attr}]"
        else:
            nodes = children[0]
            target = "".join(
                [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
            )
            raw_target = target
            if "," in target:
                target, _ = target.split(",", 1)
            ref = Ref(variant="anchor", target=target.strip(), inlines=nodes)
            ref._source_text = f"[[{raw_target}]]"
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def inline_xref(self, meta: Any, children: PyList[Any]) -> Ref:
        from lark import Token

        if isinstance(children[0], Token) and children[0].type == "XREF_PREFIX":
            children = children[1:]
        if isinstance(children[0], Token) and children[0].type in ("TARGET", "URI"):
            target = children[0].value
            attrs = (
                children[1]
                if len(children) > 1 and isinstance(children[1], dict)
                else {}
            )
            label = attrs.get("style", target)
            ref = Ref(variant="xref", target=target.strip(), inlines=[Text(label)])
            raw_attr = getattr(attrs, "raw", label if label != target else "")
            ref._source_text = f"xref:{target}[{raw_attr}]"
        else:
            nodes = children[0]
            target_str = "".join(
                [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
            )
            label_nodes = nodes
            raw_content = target_str
            if "," in target_str:
                target_str, label_text = target_str.split(",", 1)
                label_nodes = [Text(label_text.strip())]

            ref = Ref(variant="xref", target=target_str.strip(), inlines=label_nodes)
            ref._source_text = f"<<{raw_content}>>"
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def inline_link(self, meta: Any, children: PyList[Any]) -> Ref:
        # When the LINK_PREFIX branch matches, children[0] is the
        # LINK_PREFIX token ("link:") and children[1] is the URI/TARGET.
        # When the bare URI branch matches, children[0] is the URI directly.
        from lark import Token

        is_macro_prefix = False
        if (
            len(children) > 0
            and isinstance(children[0], Token)
            and children[0].type == "LINK_PREFIX"
        ):
            is_macro_prefix = True
            target = str(children[1].value)
            attrs = (
                children[2]
                if len(children) > 2 and isinstance(children[2], dict)
                else {}
            )
        else:
            target = str(children[0].value)
            attrs = (
                children[1]
                if len(children) > 1 and isinstance(children[1], dict)
                else {}
            )

        label = attrs.get("style", "")

        # Handle the caret '^' new-window hint
        window = None
        if label.endswith("^"):
            label = label[:-1]
            window = "_blank"

        inlines = []
        if label:
            from asciidoctrine.lark_parser import parse_inlines

            try:
                raw_inlines = parse_inlines(label)

                def _unwrap(nodes: PyList[Node]) -> PyList[Node]:
                    res: PyList[Node] = []
                    for n in nodes:
                        if isinstance(n, Ref):
                            res.extend(_unwrap(n.inlines))
                        else:
                            res.append(n)
                    return res

                inlines = _unwrap(raw_inlines)
            except Exception:
                inlines = [Text(label)]

        ref = Ref(variant="link", target=target.strip(), inlines=inlines)
        if window:
            ref.attributes["window"] = window

        raw_attr = getattr(attrs, "raw", label)
        if is_macro_prefix:
            ref._source_text = f"link:{target}[{raw_attr}]"
        else:
            ref._source_text = f"{target}[{raw_attr}]"

        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def bare_url_link(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        target = str(children[0].value)
        # Strip trailing punctuation (including '>' for angle-bracketed URLs)
        punc_chars = ".,;:!?)>]}"
        stripped_punc = ""
        while target and target[-1] in punc_chars:
            stripped_punc = target[-1] + stripped_punc
            target = target[:-1]

        ref = Ref(
            variant="link",
            target=target.strip(),
            inlines=[Text(target.strip())],
        )
        ref.attributes["role"] = "bare"

        nodes: PyList[Node] = [
            cast(Ref, self._set_location_from_children(ref, children))
        ]
        if stripped_punc:
            punc_node = Text(stripped_punc)
            nodes.append(punc_node)
        return nodes

    @v_args(meta=True)
    def bare_email_link(self, meta: Any, children: PyList[Any]) -> Ref:
        email = str(children[0].value)
        ref = Ref(
            variant="link",
            target=f"mailto:{email}",
            inlines=[Text(email)],
        )
        ref.attributes["role"] = "bare"
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def inline_bibref(self, meta: Any, children: PyList[Any]) -> Ref:
        nodes = children[0]
        target = "".join(
            [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
        )
        if "," in target:
            target, _ = target.split(",", 1)
        ref = Ref(variant="bibref", target=target.strip(), inlines=nodes)
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def inline_break(self, meta: Any, children: PyList[Any]) -> Break:
        return cast(Break, self._set_location_from_children(Break(), children))

    @v_args(meta=True)
    def inline_kbd(self, meta: Any, children: PyList[Any]) -> Kbd:
        content = str(children[0].value)
        keys = [k.strip() for k in content.split("+")]
        kbd = Kbd(keys)
        kbd._source_text = f"kbd:[{content}]"
        return cast(Kbd, self._set_location_from_children(kbd, children))

    @v_args(meta=True)
    def inline_button(self, meta: Any, children: PyList[Any]) -> Button:
        btn = Button(str(children[0].value))
        btn._source_text = f"btn:[{str(children[0].value)}]"
        return cast(Button, self._set_location_from_children(btn, children))

    @v_args(meta=True)
    def inline_menu(self, meta: Any, children: PyList[Any]) -> Menu:
        menu_name = str(children[0].value)
        items_str = str(children[1].value) if len(children) > 1 and children[1] else ""
        items = [i.strip() for i in items_str.split(">")] if items_str else []
        menu = Menu(menu_name, items)
        menu._source_text = f"menu:{menu_name}[{items_str}]"
        return cast(Menu, self._set_location_from_children(menu, children))

    @v_args(meta=True)
    def inline_callout(self, meta: Any, children: PyList[Any]) -> Callout:
        co = Callout(int(children[0].value))
        co._source_text = f"<{children[0].value}>"
        return cast(Callout, self._set_location_from_children(co, children))

    @v_args(meta=True)
    def inline_stem(self, meta: Any, children: PyList[Any]) -> InlineStem:
        variant = "asciimath"
        attrs = cast(Dict[str, PyList[Node]], getattr(self, "attributes"))
        stem_attr = attrs.get("stem", [])
        if stem_attr and hasattr(stem_attr[0], "value"):
            variant = getattr(stem_attr[0], "value")

        content = str(children[0].value) if children and children[0] else ""
        stem = InlineStem(variant=variant, value=content)
        stem._source_text = f"stem:[{content}]"
        return cast(InlineStem, self._set_location_from_children(stem, children))

    @v_args(meta=True)
    def inline_asciimath(self, meta: Any, children: PyList[Any]) -> InlineStem:
        content = str(children[0].value) if children and children[0] else ""
        stem = InlineStem(variant="asciimath", value=content)
        stem._source_text = f"asciimath:[{content}]"
        return cast(InlineStem, self._set_location_from_children(stem, children))

    @v_args(meta=True)
    def inline_latexmath(self, meta: Any, children: PyList[Any]) -> InlineStem:
        content = str(children[0].value) if children and children[0] else ""
        stem = InlineStem(variant="latexmath", value=content)
        stem._source_text = f"latexmath:[{content}]"
        return cast(InlineStem, self._set_location_from_children(stem, children))

    @v_args(meta=True)
    def inline_pass_macro(self, meta: Any, children: PyList[Any]) -> InlinePassthrough:
        content = str(children[0].value) if children and children[0] else ""
        pass_node = InlinePassthrough(value=content)
        pass_node.form = "macro"
        pass_node._source_text = f"pass:[{content}]"
        return cast(
            InlinePassthrough, self._set_location_from_children(pass_node, children)
        )

    @v_args(meta=True)
    def inline_triple_plus(self, meta: Any, children: PyList[Any]) -> InlinePassthrough:
        content = str(children[0].value) if children and children[0] else ""
        pass_node = InlinePassthrough(value=content)
        pass_node.form = "triple_plus"
        return cast(
            InlinePassthrough, self._set_location_from_children(pass_node, children)
        )

    @v_args(meta=True)
    def inline_indexterm_macro(self, meta: Any, children: PyList[Any]) -> IndexTerm:
        content = ""
        if children and children[0] is not None:
            content = str(children[0].value)
        terms = [
            t.strip().strip('"').strip("'") for t in content.split(",") if t.strip()
        ]
        indexterm = IndexTerm(terms=terms, variant="macro")
        indexterm._source_text = f"indexterm:[{content}]"
        return cast(IndexTerm, self._set_location_from_children(indexterm, children))

    @v_args(meta=True)
    def inline_indexterm_flow_double(
        self, meta: Any, children: PyList[Any]
    ) -> IndexTerm:
        nodes = children[0] if children else []
        text_val = "".join(
            [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
        )
        terms = [text_val.strip()] if text_val.strip() else []
        indexterm = IndexTerm(terms=terms, variant="flow_double", inlines=nodes)
        return cast(IndexTerm, self._set_location_from_children(indexterm, children))

    @v_args(meta=True)
    def inline_indexterm_flow_triple(
        self, meta: Any, children: PyList[Any]
    ) -> IndexTerm:
        nodes = children[0] if children else []
        text_val = "".join(
            [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
        )
        terms = [t.strip() for t in text_val.split(",") if t.strip()]
        indexterm = IndexTerm(terms=terms, variant="flow_triple", inlines=nodes)
        return cast(IndexTerm, self._set_location_from_children(indexterm, children))
