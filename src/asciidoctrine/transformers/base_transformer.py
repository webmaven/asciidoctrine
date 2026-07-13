from typing import Any, Optional
from typing import List as PyList

from lark import Token


class LocationDict(dict[str, Any]):
    """A dictionary subclass that can hold location coordinates."""

    location: Optional[PyList[dict[str, Any]]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.location = None


class BaseTransformer:
    """
    Base class for all Lark Transformers, providing shared location-tracking utilities.
    """

    def _set_location_from_children(self, node: Any, children: PyList[Any]) -> Any:
        """Sets the location of a node based on its children's locations."""
        from lark import Tree

        valid_locations = []

        def collect_locations(item: Any) -> None:
            # Duck-type: collect from any item carrying a .location attribute (e.g. Node or LocationDict)
            if hasattr(item, "location") and item.location:
                valid_locations.extend(item.location)
            elif isinstance(item, Token):
                if item.type == "_NEWLINE" or item.type.startswith("__ANON_"):
                    return
                if item.line is not None and item.column is not None:
                    valid_locations.append({"line": item.line, "col": item.column})
                if item.end_line is not None and item.end_column is not None:
                    # Subtract 1 for inclusive end column
                    valid_locations.append(
                        {"line": item.end_line, "col": item.end_column - 1}
                    )
            elif isinstance(item, Tree):
                for child in item.children:
                    collect_locations(child)
            elif isinstance(item, list):
                for subitem in item:
                    collect_locations(subitem)

        for child in children:
            collect_locations(child)

        if valid_locations:
            # Filter out any None values just in case
            valid_locations = [
                loc for loc in valid_locations if loc.get("line") is not None
            ]
            if valid_locations:
                # Sort by line then col
                valid_locations.sort(key=lambda x: (x["line"], x["col"]))
                node.location = [valid_locations[0], valid_locations[-1]]
        return node
