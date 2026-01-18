import re
from typing import Any, Dict

from .nodes import Document, Node


class ASGResolver:
    """Resolves semantic elements in the ASG."""

    def __init__(self, document: Document):
        self.attributes = getattr(document, "attributes", {})
        self.resolved_attributes: Dict[str, str] = {}
        for k, v in self.attributes.items():
            if isinstance(v, list):
                # Resolve each node in the rich attribute value to string
                self.resolved_attributes[k] = "".join(
                    [self._resolve_node_to_string(n) for n in v]
                )
            else:
                self.resolved_attributes[k] = str(v)

    def _resolve_node_to_string(self, node: Any) -> str:
        if hasattr(node, "value"):
            return str(node.value)
        if hasattr(node, "inlines"):
            return "".join([self._resolve_node_to_string(n) for n in node.inlines])
        return ""

    def resolve(self, node: Node) -> Dict[str, Any]:
        """Convert AST to fully-resolved ASG."""
        asg = node.to_dict()
        # Update attributes in ASG with resolved strings
        if asg.get("name") == "document" and "attributes" in asg:
            asg["attributes"] = self.resolved_attributes

        return self._resolve_recursive(asg)

    def _resolve_recursive(self, asg: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve attribute references."""
        if asg.get("name") == "text":
            asg["value"] = self._substitute_attributes(asg.get("value", ""))

        for key in ["inlines", "blocks", "items", "principal"]:
            if key in asg and isinstance(asg[key], list):
                asg[key] = [self._resolve_recursive(child) for child in asg[key]]

        return asg

    def _substitute_attributes(self, text: str) -> str:
        """Replace {name} with attribute values."""

        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            return str(self.resolved_attributes.get(name, match.group(0)))

        return re.sub(r"\{([a-zA-Z0-9_-]+)\}", replace, text)
