from typing import Any, Dict, Optional, cast
from typing import List as PyList

from lark import Token

from ..nodes import (
    Image,
    Node,
    Ref,
    Span,
    Text,
)


class InlineTransformer:
    """
    Mixin class for inline-level AsciiDoc transformations.
    """

    # attributes: Dict[str, PyList[Node]]  # Will be provided by main transformer

    def attribute_reference(self, children: PyList[Any]) -> PyList[Node]:
        name = ""
        for c in children:
            if isinstance(c, Token) and c.type == "ATTR_NAME":
                name = c.value
                break

        # Access attributes from the instance (AsciiDocTransformer)
        attrs = cast(Dict[str, PyList[Node]], getattr(self, "attributes"))
        return attrs.get(name, [Text(f"{{{name}}}")])

    def text_content(self, children: PyList[Any]) -> PyList[Node]:
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
                    nodes[-1].value += node.value
                else:
                    nodes.append(node)

        if pending_attrs:
            attr_str = ",".join([f"{k}={v}" for k, v in pending_attrs.items()])
            nodes.append(Text(f"[{attr_str}]"))

        return nodes

    def bold(self, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        return Span(
            variant="strong", form="constrained", inlines=content[0] if content else []
        )

    def unconstrained_bold(self, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        return Span(
            variant="strong",
            form="unconstrained",
            inlines=content[0] if content else [],
        )

    def italic(self, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        return Span(
            variant="emphasis",
            form="constrained",
            inlines=content[0] if content else [],
        )

    def unconstrained_italic(self, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        return Span(
            variant="emphasis",
            form="unconstrained",
            inlines=content[0] if content else [],
        )

    def literal_content(self, children: PyList[Any]) -> str:
        return str(children[0])

    def monospace(self, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        return Span(
            variant="code", form="constrained", inlines=content[0] if content else []
        )

    def unconstrained_monospace(self, children: PyList[Any]) -> Span:
        content = [c for c in children if isinstance(c, list)]
        return Span(
            variant="code", form="unconstrained", inlines=content[0] if content else []
        )

    def marked(self, children: PyList[Any]) -> Span:
        return Span(variant="mark", inlines=children[0] if children else [])

    def superscript(self, children: PyList[Any]) -> Span:
        return Span(variant="superscript", inlines=children[0] if children else [])

    def subscript(self, children: PyList[Any]) -> Span:
        return Span(variant="subscript", inlines=children[0] if children else [])

    def footnote(self, children: PyList[Any]) -> Ref:
        return Ref(variant="footnote", target="", inlines=children[0])

    def footnoteref(self, children: PyList[Any]) -> Ref:
        target = ""
        inlines = []
        for c in children:
            if isinstance(c, Token) and c.type == "WORD":
                target = str(c.value)
            elif isinstance(c, list):
                inlines = c
        return Ref(variant="footnote", target=target, inlines=inlines)

    def double_quoted(self, children: PyList[Any]) -> Span:
        return Span(variant="double", inlines=children[0] if children else [])

    def single_quoted(self, children: PyList[Any]) -> Span:
        return Span(variant="single", inlines=children[0] if children else [])

    def inline_image(self, children: PyList[Any]) -> Image:
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        alt = attrs.get("style", "")
        img = Image(target=target, alt=alt, form="macro", type="inline")
        img.attributes.update(attrs)
        if "style" in img.attributes:
            img.attributes["alt"] = img.attributes.pop("style")
        return img

    def icon_inline(self, children: PyList[Any]) -> Image:
        target = str(children[0].value)
        attrs = (
            children[1] if len(children) > 1 and isinstance(children[1], dict) else {}
        )
        img = Image(target=target, alt="", form="macro", type="inline")
        img.name = "icon"
        img.attributes.update(attrs)
        return img

    def inline_anchor(self, children: PyList[Any]) -> Ref:
        if isinstance(children[0], Token) and children[0].type == "TARGET":
            # anchor:TARGET[ATTR_LIST_CONTENT]
            target = children[0].value
            attrs = (
                children[1]
                if len(children) > 1 and isinstance(children[1], dict)
                else {}
            )
            label = attrs.get("style", target)
            return Ref(variant="anchor", target=target.strip(), inlines=[Text(label)])
        else:
            # [[text_content]]
            nodes = children[0]
            target = "".join(
                [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
            )
            if "," in target:
                target, _ = target.split(",", 1)
            return Ref(variant="anchor", target=target.strip(), inlines=nodes)

    def inline_xref(self, children: PyList[Any]) -> Ref:
        if isinstance(children[0], Token) and children[0].type == "TARGET":
            # xref:TARGET[ATTR_LIST_CONTENT]
            target = children[0].value
            attrs = (
                children[1]
                if len(children) > 1 and isinstance(children[1], dict)
                else {}
            )
            label = attrs.get("style", target)
            return Ref(variant="xref", target=target.strip(), inlines=[Text(label)])
        else:
            # <<text_content>>
            nodes = children[0]
            target_str = "".join(
                [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
            )
            label_nodes = nodes
            if "," in target_str:
                target_str, label_text = target_str.split(",", 1)
                label_nodes = [Text(label_text.strip())]

            return Ref(variant="xref", target=target_str.strip(), inlines=label_nodes)

    def inline_bibref(self, children: PyList[Any]) -> Ref:
        nodes = children[0]
        target = "".join(
            [getattr(n, "value", "") for n in nodes if hasattr(n, "value")]
        )
        if "," in target:
            target, _ = target.split(",", 1)
        return Ref(variant="bibref", target=target.strip(), inlines=nodes)
