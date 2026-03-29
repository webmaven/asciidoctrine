from typing import Any, Dict

from .attributes import resolve_attribute_map, substitute_attributes
from .nodes import Document, Node


class ASGResolver:
    """Resolves semantic elements in the ASG."""

    def __init__(self, document: Document):
        self.attributes = getattr(document, "attributes", {})
        self.resolved_attributes = resolve_attribute_map(self.attributes)

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
            asg["value"] = substitute_attributes(
                asg.get("value", ""), self.resolved_attributes
            )

        for key in [
            "inlines",
            "blocks",
            "items",
            "principal",
            "terms",
            "rows",
            "cells",
        ]:
            if key in asg and isinstance(asg[key], list):
                asg[key] = [self._resolve_recursive(child) for child in asg[key]]

        return asg
