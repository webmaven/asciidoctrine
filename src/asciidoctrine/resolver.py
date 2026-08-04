from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional, cast
from typing import List as PyList

from .attributes import resolve_attribute_map, substitute_attributes
from .lark_parser import parse_to_ast
from .nodes import (
    AttributeEntry,
    Attributes,
    Docinfo,
    Document,
    Node,
    NodeTransformer,
    Ref,
    Text,
)


class WorkspaceCatalog:
    """The global symbol table managing cross-file anchors and IDs across an AsciiDoc project workspace.

    `WorkspaceCatalog` collects and indexes all target anchors (`[[id]]` or `[#id]`) and document roots
    across all parsed files in a multi-document workspace, mapping them to live `Node` AST instances.

    *Attributes:*

    `by_fqid`:: Fully-Qualified ID map matching `"file_id#anchor_id"` to the live target `Node` AST instance. Document roots are indexed under `"file_id#"`.
    `by_local_id`:: Local anchor ID map matching `"anchor_id"` to a list of file IDs containing that anchor.

    *Example:*

    [source,python]
    ----
    catalog = WorkspaceCatalog()
    catalog.index_document("main.adoc", doc)
    target_node = catalog.by_fqid.get("main.adoc#intro")
    ----
    """

    def __init__(self) -> None:
        self.by_fqid: Dict[
            str, Node
        ] = {}  # Maps "file_id#anchor_id" -> Live Node instance
        self.by_local_id: Dict[str, PyList[str]] = defaultdict(
            list
        )  # Maps "anchor_id" -> List of files

    def index_document(self, file_id: str, document: Document) -> None:
        """Recursively parses an un-mutated AST document tree via `get_child_collections()` to index all anchor IDs.

        `file_id`:: The relative, platform-agnostic file path key (e.g., `"subdir/doc.adoc"`).
        `document`:: The root `Document` AST node instance to index.
        """
        # Always index the document root under an empty anchor for file-level links (e.g. xref:doc.adoc[])
        self.by_fqid[f"{file_id}#"] = document

        stack: PyList[Node] = [document]
        header = getattr(document, "header", None)
        if header:
            stack.append(header)

        while stack:
            current_node = stack.pop()

            # Register anchor ID, handling potential duplicates or object wrappers
            node_id = getattr(current_node, "id", None) or current_node.attributes.get(
                "id"
            )
            if node_id:
                id_str = (
                    str(node_id.value) if hasattr(node_id, "value") else str(node_id)
                )
                fqid = f"{file_id}#{id_str}"
                self.by_fqid[fqid] = current_node
                if file_id not in self.by_local_id[id_str]:
                    self.by_local_id[id_str].append(file_id)

            # Traverse child branches
            for collection in current_node.get_child_collections().values():
                stack.extend(reversed(collection))


class ASGResolver(NodeTransformer):
    """Resolves semantic elements in an AsciiDoc AST using a typed NodeTransformer pattern.

    `ASGResolver` evaluates document-level and block-level attribute substitutions, filters out
    transient syntax-only elements (like comments and standalone attribute entries), and binds
    interdocument cross-references (`Ref` nodes) via 3-tier target resolution using a `WorkspaceCatalog`.

    `document`:: The root `Document` AST node instance to resolve.
    `catalog`:: Optional `WorkspaceCatalog` containing symbol tables for multi-file workspace resolution. Defaults to a new empty catalog if omitted.
    `current_file_id`:: The relative file ID of the document being resolved (e.g. `"chapter1/intro.adoc"`). Used for resolving relative path targets and local file resolution fallbacks.
    """

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

    def _resolve_docinfo_files(self, doc: Document) -> tuple[str, str]:
        docinfo_attr = str(self.resolved_attributes.get("docinfo", "")).strip()
        docinfofiles_attr = str(
            self.resolved_attributes.get("docinfofiles", "")
        ).strip()
        if not docinfo_attr and not docinfofiles_attr:
            return ("", "")

        docinfo_val = [x.strip() for x in docinfo_attr.split(",") if x.strip()]

        is_shared = any(
            v in ("1", "shared", "shared-head", "shared-footer") for v in docinfo_val
        )
        is_private = any(
            v in ("private", "private-head", "private-footer") for v in docinfo_val
        )

        docname = self.resolved_attributes.get("docname")
        if not docname and self.current_file_id and self.current_file_id != "root":
            docname = Path(self.current_file_id).stem
        if not docname:
            docname = "docinfo"

        base_dir_path = (
            Path(doc.base_dir).resolve() if doc.base_dir else Path.cwd().resolve()
        )

        docinfodir = str(self.resolved_attributes.get("docinfodir", "")).strip()
        if docinfodir:
            target_dir = (base_dir_path / docinfodir).resolve()
        else:
            target_dir = base_dir_path

        if getattr(doc, "safe_mode", 0) >= 2:
            try:
                target_dir.relative_to(base_dir_path)
            except ValueError:
                return ("", "")

        head_contents: PyList[str] = []
        footer_contents: PyList[str] = []

        def safe_read(file_path: Path) -> str:
            if not file_path.is_file():
                return ""
            if getattr(doc, "safe_mode", 0) >= 2:
                try:
                    file_path.resolve().relative_to(base_dir_path)
                except ValueError:
                    return ""
            try:
                return file_path.read_text(encoding="utf-8")
            except Exception:
                return ""

        if is_shared:
            for ext in (".html", ".xml"):
                h = safe_read(target_dir / f"docinfo{ext}") or safe_read(
                    target_dir / f"docinfo-head{ext}"
                )
                if h:
                    head_contents.append(h)
                f = safe_read(target_dir / f"docinfo-footer{ext}")
                if f:
                    footer_contents.append(f)

        if is_private and docname:
            for ext in (".html", ".xml"):
                h = safe_read(target_dir / f"{docname}-docinfo{ext}") or safe_read(
                    target_dir / f"{docname}-docinfo-head{ext}"
                )
                if h:
                    head_contents.append(h)
                f = safe_read(target_dir / f"{docname}-docinfo-footer{ext}")
                if f:
                    footer_contents.append(f)

        if docinfofiles_attr:
            custom_files = [
                x.strip() for x in docinfofiles_attr.split(",") if x.strip()
            ]
            for cfile in custom_files:
                cpath = target_dir / cfile
                c_content = safe_read(cpath)
                if c_content:
                    if "footer" in cfile:
                        footer_contents.append(c_content)
                    else:
                        head_contents.append(c_content)

        head_str = "".join(head_contents)
        footer_str = "".join(footer_contents)

        if head_str:
            head_str = substitute_attributes(head_str, self.resolved_attributes)
        if footer_str:
            footer_str = substitute_attributes(footer_str, self.resolved_attributes)

        return (head_str, footer_str)

    def resolve(self, node: Node) -> Dict[str, Any]:
        """Converts an AST node tree to a fully-resolved ASG dictionary without mutating the original input AST.

        Performs a pure deep copy of the input node tree before applying transformations, ensuring the
        syntax-level AST remains unmutated for coordinate tracking and serialization tools.

        `node`:: The root AST node (typically a `Document`) to resolve.

        Returns a spec-compliant Abstract Semantic Graph (ASG) dictionary.
        """
        import copy

        if isinstance(node, Document):
            head_content, footer_content = self._resolve_docinfo_files(node)
            if head_content or footer_content:
                node.docinfo = Docinfo(
                    head_content=head_content, footer_content=footer_content
                )

        copied_node = copy.deepcopy(node)
        self.visit(copied_node)

        asg = copied_node.to_dict()

        # Inject resolved document-level attributes
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
            node.target_node_instance = self.catalog.by_fqid[
                f"{resolved_file}#{target_anchor}"
            ]
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
            node.target_node_instance = self.catalog.by_fqid[
                f"{matching_file}#{target_anchor}"
            ]
            node.resolved_file_target = matching_file
            node.resolved_strategy = (
                "same_file" if matching_file == self.current_file_id else "cross_file"
            )
        else:
            raise KeyError(
                f"Cross-reference error: '{target_str}' not found in workspace."
            )

        node.resolved_anchor_target = target_anchor
        return self.generic_visit(node, **kwargs)


class WorkspaceBuilder:
    """Orchestrates multi-pass parsing and semantic resolution for an entire folder workspace of AsciiDoc files.

    `WorkspaceBuilder` coordinates directory discovery, raw un-mutated AST parsing, global symbol table indexing
    via `WorkspaceCatalog`, and interdocument reference resolution via `ASGResolver`.

    *Attributes:*

    `workspace_root`:: Absolute canonical `Path` to the root directory of the AsciiDoc project.
    `parser`:: Optional custom parser engine instance overriding default `parse_to_ast`.
    `catalog`:: Central global symbol table mapping all anchor IDs across the workspace.
    `raw_documents`:: Map of platform-agnostic file IDs to raw, un-mutated `Document` AST instances.
    `resolved_asg_graphs`:: Map of file IDs to fully-resolved ASG dictionaries.

    *Example:*

    [source,python]
    ----
    builder = WorkspaceBuilder("/path/to/docs")
    graphs = builder.build()
    intro_asg = graphs["intro.adoc"]
    ----
    """

    def __init__(
        self, workspace_root: str, lark_parser_instance: Optional[Any] = None
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.parser = lark_parser_instance
        self.catalog = WorkspaceCatalog()
        self.raw_documents: Dict[str, Document] = {}
        self.resolved_asg_graphs: Dict[str, Dict[str, Any]] = {}

    def _get_file_id(self, absolute_path: Path) -> str:
        """Generates a stable, platform-agnostic string file ID relative to the workspace root.

        `absolute_path`:: Absolute file system `Path` to a document.

        Returns a Posix-style relative path string (e.g. `"subfolder/doc.adoc"`).
        """
        return str(absolute_path.relative_to(self.workspace_root).as_posix())

    def discover_and_parse_project(self) -> None:
        """Pass 1: Scans directory tree for `.adoc` files, runs Lark parsing loops, and stores raw ASTs.

        Recursively walks `workspace_root` matching `*.adoc`. Passes `base_dir` context to `parse_to_ast()`
        so nested include directives resolve relative to their parent file's location.
        """
        for adoc_file in sorted(self.workspace_root.rglob("*.adoc")):
            canonical_path = adoc_file.resolve()
            file_id = self._get_file_id(canonical_path)

            with open(canonical_path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            if self.parser and hasattr(self.parser, "parse"):
                ast_root = self.parser.parse(raw_content)
            else:
                ast_root = parse_to_ast(
                    raw_content, base_dir=str(canonical_path.parent)
                )

            self.raw_documents[file_id] = ast_root

    def index_workspace_symbols(self) -> None:
        """Pass 2: Walks saved un-mutated AST trees to populate the central `WorkspaceCatalog` symbol table."""
        for file_id, ast_tree in self.raw_documents.items():
            self.catalog.index_document(file_id, ast_tree)

    def resolve_workspace_semantics(self) -> None:
        """Pass 3: Resolves attributes, deep-copies AST trees, and binds cross-file references via `ASGResolver`."""
        for file_id, ast_tree in self.raw_documents.items():
            resolver = ASGResolver(
                ast_tree, catalog=self.catalog, current_file_id=file_id
            )
            self.resolved_asg_graphs[file_id] = resolver.resolve(ast_tree)

    def build(self) -> Dict[str, Dict[str, Any]]:
        """Runs the complete multi-pass orchestration sequence sequentially (Pass 1 -> Pass 2 -> Pass 3).

        Returns a dictionary mapping relative file IDs (e.g., `"doc.adoc"`) to their fully-resolved, spec-compliant ASG dictionaries.
        """
        self.discover_and_parse_project()
        self.index_workspace_symbols()
        self.resolve_workspace_semantics()
        return self.resolved_asg_graphs
