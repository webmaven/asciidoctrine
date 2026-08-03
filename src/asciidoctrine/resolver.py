from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional, cast
from typing import List as PyList

from .attributes import resolve_attribute_map, substitute_attributes
from .lark_parser import parse_to_ast
from .nodes import (
    AttributeEntry,
    Attributes,
    Document,
    Node,
    NodeTransformer,
    Ref,
    Text,
)


class WorkspaceCatalog:
    """The global symbol table managing cross-file anchors across an AsciiDoc project."""

    def __init__(self) -> None:
        self.by_fqid: Dict[str, Node] = {}  # Maps "file_id#anchor_id" -> Live Node instance
        self.by_local_id: Dict[str, PyList[str]] = defaultdict(list)  # Maps "anchor_id" -> List of files

    def index_document(self, file_id: str, document: Document) -> None:
        """Recursively parses an un-mutated AST via get_child_collections."""
        # Always index the document root under an empty anchor for file-level links (e.g. xref:doc.adoc[])
        self.by_fqid[f"{file_id}#"] = document

        stack: PyList[Node] = [document]
        header = getattr(document, "header", None)
        if header:
            stack.append(header)

        while stack:
            current_node = stack.pop()

            # Register anchor ID, handling potential duplicates or object wrappers
            node_id = getattr(current_node, "id", None) or current_node.attributes.get("id")
            if node_id:
                id_str = str(node_id.value) if hasattr(node_id, "value") else str(node_id)
                fqid = f"{file_id}#{id_str}"
                self.by_fqid[fqid] = current_node
                if file_id not in self.by_local_id[id_str]:
                    self.by_local_id[id_str].append(file_id)

            # Traverse child branches
            for collection in current_node.get_child_collections().values():
                stack.extend(reversed(collection))


class ASGResolver(NodeTransformer):
    """Resolves semantic elements in the AST using a typed NodeTransformer pattern."""

    def __init__(
        self,
        document: Document,
        catalog: Optional[WorkspaceCatalog] = None,
        current_file_id: Optional[str] = None,
    ) -> None:
        self.attributes = getattr(document, "attributes", {})
        self.resolved_attributes = resolve_attribute_map(self.attributes)
        self.catalog = catalog or WorkspaceCatalog()
        doc_id = getattr(document, "id", None)
        self.current_file_id: str = (
            current_file_id
            if current_file_id is not None
            else (str(doc_id) if doc_id is not None else "root")
        )

    def resolve(self, node: Node) -> Dict[str, Any]:
        """Convert AST to fully-resolved ASG without mutating input."""
        import copy

        copied_node = copy.deepcopy(node)
        self.visit(copied_node)

        asg = copied_node.to_dict()

        # 3. Inject resolved document-level attributes
        if asg.get("name") == "document" and "attributes" in asg:
            asg["attributes"] = self.resolved_attributes

        return asg

    def generic_visit(self, node: Node, **kwargs: Any) -> Node:
        # First, clean block-level attributes in-place for any node that is not a document or attributes node
        if node.name not in ("document", "attributes") and node.attributes:
            cleaned_attrs = {}
            for k, v in node.attributes.items():
                if k == "positional" or k.isdigit():
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

    def visit_ref(self, node: Ref, **kwargs: Any) -> Node:
        """Resolves interdocument cross-references natively."""
        if node.variant != "xref":
            return self.generic_visit(node, **kwargs)

        target_str = str(node.target)

        # Robust parsing of file vs anchor links
        target_file: Optional[str] = None
        target_anchor: str = ""
        if "#" in target_str:
            parts = target_str.split("#", 1)
            target_file = parts[0] if parts[0] else None
            target_anchor = parts[1]
        elif target_str.endswith(".adoc"):
            target_file = target_str
        else:
            target_anchor = target_str

        # Helper to resolve relative path references
        resolved_file = target_file
        if target_file:
            import os

            cur_dir = os.path.dirname(self.current_file_id)
            raw_path = os.path.join(cur_dir, target_file) if cur_dir else target_file
            resolved_file = os.path.normpath(raw_path).replace("\\", "/")

        # --- 3-TIER RESOLUTION FALLBACK ---
        # 1. Explicit file target
        if resolved_file and f"{resolved_file}#{target_anchor}" in self.catalog.by_fqid:
            node.target_node_instance = self.catalog.by_fqid[f"{resolved_file}#{target_anchor}"]
            node.resolved_file_target = resolved_file
            node.resolved_strategy = (
                "same_file" if resolved_file == self.current_file_id else "cross_file"
            )

        # 2. Local file implicit match
        elif f"{self.current_file_id}#{target_anchor}" in self.catalog.by_fqid:
            node.target_node_instance = self.catalog.by_fqid[
                f"{self.current_file_id}#{target_anchor}"
            ]
            node.resolved_file_target = self.current_file_id
            node.resolved_strategy = "same_file"

        # 3. Global lookup
        elif (
            target_anchor in self.catalog.by_local_id
            and len(self.catalog.by_local_id[target_anchor]) == 1
        ):
            matching_file = self.catalog.by_local_id[target_anchor][0]
            node.target_node_instance = self.catalog.by_fqid[f"{matching_file}#{target_anchor}"]
            node.resolved_file_target = matching_file
            node.resolved_strategy = (
                "same_file" if matching_file == self.current_file_id else "cross_file"
            )
        else:
            raise KeyError(f"Cross-reference error: '{target_str}' not found in workspace.")

        node.resolved_anchor_target = target_anchor
        return self.generic_visit(node, **kwargs)


class WorkspaceBuilder:
    """Orchestrates parsing a folder directory of AsciiDoc files into a unified multi-file ASG."""

    def __init__(
        self, workspace_root: str, lark_parser_instance: Optional[Any] = None
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.parser = lark_parser_instance
        self.catalog = WorkspaceCatalog()
        # Maps canonical File ID paths to their living Document AST nodes
        self.raw_documents: Dict[str, Document] = {}
        # Maps canonical File ID paths to their fully mutated ASG Graph outputs
        self.resolved_asg_graphs: Dict[str, Dict[str, Any]] = {}

    def _get_file_id(self, absolute_path: Path) -> str:
        """Generates a stable, predictable, platform-agnostic string File ID relative to the workspace root."""
        return str(absolute_path.relative_to(self.workspace_root).as_posix())

    def discover_and_parse_project(self) -> None:
        """
        PASS 1: Scan directories on disk, run the preprocessor and Lark parser loops,
        and save the raw, un-mutated AST documents into memory.
        """
        for adoc_file in sorted(self.workspace_root.rglob("*.adoc")):
            canonical_path = adoc_file.resolve()
            file_id = self._get_file_id(canonical_path)

            with open(canonical_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            # Parse to a pure, unmutated AST Document class instance.
            # We explicitly pass base_dir so nested includes resolve properly.
            if self.parser and hasattr(self.parser, "parse"):
                ast_root = self.parser.parse(raw_content)
            else:
                ast_root = parse_to_ast(raw_content, base_dir=str(canonical_path.parent))

            self.raw_documents[file_id] = ast_root

    def index_workspace_symbols(self) -> None:
        """
        PASS 2: Walk the saved un-mutated AST trees using get_child_collections()
        to build the centralized Global Symbol Table.
        """
        for file_id, ast_tree in self.raw_documents.items():
            self.catalog.index_document(file_id, ast_tree)

    def resolve_workspace_semantics(self) -> None:
        """
        PASS 3: Execute deepcopies, evaluate attribute maps, and execute the
        ASGResolver visitor loops to wire up cross-file object pointers.
        """
        for file_id, ast_tree in self.raw_documents.items():
            # Pass current_file_id to avoid strict mypy errors on dynamically assigning .id to Document
            resolver = ASGResolver(ast_tree, catalog=self.catalog, current_file_id=file_id)
            self.resolved_asg_graphs[file_id] = resolver.resolve(ast_tree)

    def build(self) -> Dict[str, Dict[str, Any]]:
        """Runs the entire multi-pass orchestration sequence sequentially."""
        self.discover_and_parse_project()
        self.index_workspace_symbols()
        self.resolve_workspace_semantics()
        return self.resolved_asg_graphs

