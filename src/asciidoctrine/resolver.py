from typing import Any, Dict, Optional, cast

from .attributes import resolve_attribute_map, substitute_attributes
from .nodes import AttributeEntry, Attributes, Document, Node, NodeTransformer, Text


class ASGResolver(NodeTransformer):
    """Resolves semantic elements in the AST using a typed NodeTransformer pattern."""

    def __init__(self, document: Document):
        self.attributes = getattr(document, "attributes", {})
        self.resolved_attributes = resolve_attribute_map(self.attributes)

    def resolve(self, node: Node) -> Dict[str, Any]:
        """Convert AST to fully-resolved ASG."""
        # 1. Transform the AST nodes in-place
        self.visit(node)

        # 2. Serialize the mutated AST to JSON/ASG dict
        asg = node.to_dict()

        # 3. Inject resolved document-level attributes
        if asg.get("name") == "document" and "attributes" in asg:
            asg["attributes"] = self.resolved_attributes

        return asg

    def generic_visit(self, node: Node, **kwargs: Any) -> Node:
        # First, clean block-level attributes in-place for any node that is not a document or attributes node
        if node.name not in ("document", "attributes") and node.attributes:
            cleaned_attrs = {}
            for k, v in node.attributes.items():
                if k == "positional" or k == "style" or k.isdigit():
                    continue
                cleaned_attrs[k] = v
            if cleaned_attrs:
                node.attributes = cleaned_attrs
            else:
                node.attributes = {}

        # Process child collections
        for attr_name, collection in list(node.get_child_collections().items()):
            # 1. Group contiguous AttributeEntry nodes into Attributes nodes
            grouped_children: list[Node] = []
            current_group: list[AttributeEntry] = []

            def flush_group() -> None:
                if not current_group:
                    return
                group_attrs: dict[str, Any] = {}
                first_loc = None
                last_loc = None
                for entry in current_group:
                    name = entry.attribute_name
                    val = entry.value
                    loc = entry.location
                    if loc and len(loc) >= 2:
                        if first_loc is None:
                            first_loc = loc[0]
                        last_loc = loc[1]
                    group_attrs[name] = {
                        "value": val,
                    }
                    if loc:
                        group_attrs[name]["location"] = loc

                attributes_node = Attributes(group_attrs)
                if first_loc and last_loc:
                    attributes_node.location = [first_loc, last_loc]
                grouped_children.append(attributes_node)
                current_group.clear()

            for child in collection:
                if child.name == "attribute_entry":
                    current_group.append(cast(AttributeEntry, child))
                else:
                    flush_group()
                    grouped_children.append(child)
            flush_group()

            # 2. Visit each child and update the collection
            new_collection = []
            for child in grouped_children:
                res = self.visit(child, **kwargs)
                if res is None:
                    continue
                elif isinstance(res, list):
                    new_collection.extend(res)
                else:
                    new_collection.append(res)

            setattr(node, attr_name, new_collection)

        return node

    def visit_text(self, node: Text, **kwargs: Any) -> Node:
        node.value = substitute_attributes(node.value, self.resolved_attributes)
        return node

    def visit_attributes(self, node: Attributes, **kwargs: Any) -> Node:
        for attr_name, attr_info in node.attributes.items():
            if isinstance(attr_info, dict) and "value" in attr_info:
                attr_info["value"] = substitute_attributes(
                    attr_info["value"], self.resolved_attributes
                )
        return node

    def visit_comment(self, node: Node, **kwargs: Any) -> Optional[Node]:
        # Filter out comments from parent lists
        return None
