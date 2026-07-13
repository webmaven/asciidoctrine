from typing import Any, Dict, Optional, cast
from typing import List as PyList

from lark import Token, v_args

from ..nodes import (
    Break,
    Button,
    Callout,
    Image,
    InlineStem,
    Kbd,
    Menu,
    Node,
    Ref,
    Span,
    Text,
)
from .base_transformer import BaseTransformer


class InlineTransformer(BaseTransformer):
    """
    Mixin class for inline-level AsciiDoc transformations.
    """

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

        for child in flat_children:
            if isinstance(child, dict):
                pending_attrs = child
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

        if pending_attrs:
            attr_str = ",".join([f"{k}={v}" for k, v in pending_attrs.items()])
            nodes.append(Text(f"[{attr_str}]"))

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
    def superscript_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
        return cast(PyList[Node], self.text_content(meta, children))

    @v_args(meta=True)
    def subscript_content(self, meta: Any, children: PyList[Any]) -> PyList[Node]:
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
        span = Span(variant="code", form="constrained", inlines=children[0])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def unconstrained_monospace(self, meta: Any, children: PyList[Any]) -> Span:
        span = Span(variant="code", form="unconstrained", inlines=children[0])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def marked(self, meta: Any, children: PyList[Any]) -> Span:
        span = Span(variant="mark", inlines=children[0] if children else [])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def superscript(self, meta: Any, children: PyList[Any]) -> Span:
        span = Span(variant="superscript", inlines=children[0] if children else [])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def subscript(self, meta: Any, children: PyList[Any]) -> Span:
        span = Span(variant="subscript", inlines=children[0] if children else [])
        return cast(Span, self._set_location_from_children(span, children))

    @v_args(meta=True)
    def footnote(self, meta: Any, children: PyList[Any]) -> Ref:
        ref = Ref(variant="footnote", target="", inlines=children[0])
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def footnoteref(self, meta: Any, children: PyList[Any]) -> Ref:
        target = ""
        inlines = []
        for c in children:
            if isinstance(c, Token) and c.type == "WORD":
                target = str(c.value)
            elif isinstance(c, list):
                inlines = c
        ref = Ref(variant="footnote", target=target, inlines=inlines)
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
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        alt = attrs.get("style", "")
        img = Image(target=target, alt=alt, form="macro", type="inline")
        img.attributes.update(attrs)
        if "style" in img.attributes:
            img.attributes["alt"] = img.attributes.pop("style")
        return cast(Image, self._set_location_from_children(img, children))

    @v_args(meta=True)
    def icon_inline(self, meta: Any, children: PyList[Any]) -> Image:
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        img = Image(target=target, alt="", form="macro", type="inline")
        img.name = "icon"
        img.attributes.update(attrs)
        return cast(Image, self._set_location_from_children(img, children))

    @v_args(meta=True)
    def inline_anchor(self, meta: Any, children: PyList[Any]) -> Ref:
        if isinstance(children[0], Token) and children[0].type == "TARGET":
            target = children[0].value
            attrs = (
                children[1]
                if len(children) > 1 and isinstance(children[1], dict)
                else {}
            )
            label = attrs.get("style", target)
            ref = Ref(variant="anchor", target=target.strip(), inlines=[Text(label)])
        else:
            nodes = children[0]
            target = "".join(
                [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
            )
            if "," in target:
                target, _ = target.split(",", 1)
            ref = Ref(variant="anchor", target=target.strip(), inlines=nodes)
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def inline_xref(self, meta: Any, children: PyList[Any]) -> Ref:
        if isinstance(children[0], Token) and children[0].type == "TARGET":
            target = children[0].value
            attrs = (
                children[1]
                if len(children) > 1 and isinstance(children[1], dict)
                else {}
            )
            label = attrs.get("style", target)
            ref = Ref(variant="xref", target=target.strip(), inlines=[Text(label)])
        else:
            nodes = children[0]
            target_str = "".join(
                [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
            )
            label_nodes = nodes
            if "," in target_str:
                target_str, label_text = target_str.split(",", 1)
                label_nodes = [Text(label_text.strip())]

            ref = Ref(variant="xref", target=target_str.strip(), inlines=label_nodes)
        return cast(Ref, self._set_location_from_children(ref, children))

    @v_args(meta=True)
    def inline_link(self, meta: Any, children: PyList[Any]) -> Ref:
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
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
                inlines = parse_inlines(label)
            except Exception:
                inlines = [Text(label)]

        ref = Ref(variant="link", target=target.strip(), inlines=inlines)
        if window:
            ref.attributes["window"] = window

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
        return cast(Kbd, self._set_location_from_children(kbd, children))

    @v_args(meta=True)
    def inline_button(self, meta: Any, children: PyList[Any]) -> Button:
        btn = Button(str(children[0].value))
        return cast(Button, self._set_location_from_children(btn, children))

    @v_args(meta=True)
    def inline_menu(self, meta: Any, children: PyList[Any]) -> Menu:
        menu_name = str(children[0].value)
        items_str = str(children[1].value) if len(children) > 1 and children[1] else ""
        items = [i.strip() for i in items_str.split(">")] if items_str else []
        menu = Menu(menu_name, items)
        return cast(Menu, self._set_location_from_children(menu, children))

    @v_args(meta=True)
    def inline_callout(self, meta: Any, children: PyList[Any]) -> Callout:
        co = Callout(int(children[0].value))
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
        return cast(InlineStem, self._set_location_from_children(stem, children))

    @v_args(meta=True)
    def inline_asciimath(self, meta: Any, children: PyList[Any]) -> InlineStem:
        content = str(children[0].value) if children and children[0] else ""
        stem = InlineStem(variant="asciimath", value=content)
        return cast(InlineStem, self._set_location_from_children(stem, children))

    @v_args(meta=True)
    def inline_latexmath(self, meta: Any, children: PyList[Any]) -> InlineStem:
        content = str(children[0].value) if children and children[0] else ""
        stem = InlineStem(variant="latexmath", value=content)
        return cast(InlineStem, self._set_location_from_children(stem, children))
