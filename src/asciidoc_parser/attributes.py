import re
from typing import Any, Dict


def substitute_attributes(text: str, attributes: Dict[str, str]) -> str:
    """Replace {name} with attribute values in text."""

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        return str(attributes.get(name, match.group(0)))

    return re.sub(r"\{([a-zA-Z0-9_-]+)\}", replace, text)


def resolve_node_to_string(node: Any) -> str:
    """Recursively resolve an AST node to its string representation."""
    if hasattr(node, "value"):
        return str(node.value)
    if hasattr(node, "inlines"):
        return "".join([resolve_node_to_string(n) for n in node.inlines])
    if hasattr(node, "principal"):
        return resolve_node_to_string(node.principal)
    return ""


def resolve_attribute_map(attributes: Dict[str, Any]) -> Dict[str, str]:
    """Resolve a map of rich attribute values (nodes) to simple strings."""
    resolved: Dict[str, str] = {}
    for k, v in attributes.items():
        if isinstance(v, list):
            resolved[k] = "".join([resolve_node_to_string(n) for n in v])
        else:
            resolved[k] = str(v)
    return resolved
