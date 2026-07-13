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
        # Clean block-level attributes to remove AST/syntactic artifacts
        if "attributes" in asg and asg.get("name") not in ("document", "attributes"):
            attrs = asg["attributes"]
            if isinstance(attrs, dict):
                cleaned_attrs = {}
                for k, v in attrs.items():
                    # Skip positional indexes ('1', '2', etc.), 'positional' list, and 'style'
                    if k == "positional" or k == "style" or k.isdigit():
                        continue
                    cleaned_attrs[k] = v

                if cleaned_attrs:
                    asg["attributes"] = cleaned_attrs
                else:
                    del asg["attributes"]

        if asg.get("name") == "text":
            asg["value"] = substitute_attributes(
                asg.get("value", ""), self.resolved_attributes
            )

        if asg.get("name") == "attributes" and "attributes" in asg:
            for attr_name, attr_info in asg["attributes"].items():
                if isinstance(attr_info, dict) and "value" in attr_info:
                    attr_info["value"] = substitute_attributes(
                        attr_info["value"], self.resolved_attributes
                    )

        for key in [
            "inlines",
            "blocks",
            "items",
            "principal",
            "terms",
            "rows",
            "cells",
            "title",
            "header",
        ]:
            if key in asg and isinstance(asg[key], list):
                # 1. Group contiguous attribute_entry children into "attributes" blocks
                grouped_children = []
                current_group: list[dict[str, Any]] = []

                def flush_group() -> None:
                    if not current_group:
                        return
                    group_attrs = {}
                    first_loc = None
                    last_loc = None
                    for entry in current_group:
                        name = entry.get("attribute_name")
                        val = entry.get("value", "")
                        loc = entry.get("location")
                        if loc and len(loc) >= 2:
                            if first_loc is None:
                                first_loc = loc[0]
                            last_loc = loc[1]
                        group_attrs[name] = {
                            "value": val,
                        }
                        if loc:
                            group_attrs[name]["location"] = loc

                    attributes_node = {
                        "name": "attributes",
                        "type": "block",
                        "attributes": group_attrs,
                    }
                    if first_loc and last_loc:
                        attributes_node["location"] = [first_loc, last_loc]
                    grouped_children.append(attributes_node)
                    current_group.clear()

                for child in asg[key]:
                    if (
                        isinstance(child, dict)
                        and child.get("name") == "attribute_entry"
                    ):
                        current_group.append(child)
                    else:
                        flush_group()
                        grouped_children.append(child)
                flush_group()

                # 2. Resolve all children recursively (filtering comments only)
                resolved_children = []
                for child in grouped_children:
                    if isinstance(child, dict) and child.get("name") == "comment":
                        continue
                    resolved_children.append(self._resolve_recursive(child))
                asg[key] = resolved_children

        return asg
