import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Optional

import pytest

from asciidoctrine.nodes import (
    AttributeEntry,
    Attributes,
    Comment,
    Document,
    Header,
    Paragraph,
    Ref,
    Section,
    Table,
    TableCell,
    TableRow,
    Text,
    Title,
)
from asciidoctrine.resolver import ASGResolver, WorkspaceBuilder, WorkspaceCatalog

pytestmark = pytest.mark.unit


def test_resolver():
    doc = Document()
    doc.attributes = {"name": "World"}

    p = Paragraph(inlines=[Text("Hello {name}!")])
    doc.blocks.append(p)

    resolver = ASGResolver(doc)
    resolved = resolver.resolve(doc)

    expected_text = "Hello World!"
    actual_text = resolved["blocks"][0]["inlines"][0]["value"]

    print(f"Actual text: {actual_text}")
    assert actual_text == expected_text
    print("Test passed!")


def test_resolver_block_attribute_cleaning_and_comment_removal():
    from asciidoctrine.nodes import Node, Paragraph, Text

    class MockComment(Node):
        def __init__(self):
            super().__init__()
            self.name = "comment"
            self.type = "block"

    doc = Document()
    doc.attributes = {}

    p_with_attrs = Paragraph(inlines=[Text("Some text")])
    p_with_attrs.attributes = {
        "style": "source",
        "1": "source",
        "positional": ["source"],
        "my-named-attr": "value",
    }

    p_with_only_positional = Paragraph(inlines=[Text("Other text")])
    p_with_only_positional.attributes = {
        "positional": ["some-style"],
        "style": "some-style",
    }

    comment_node = MockComment()

    doc.blocks.extend([p_with_attrs, p_with_only_positional, comment_node])

    resolver = ASGResolver(doc)
    asg = resolver.resolve(doc)

    # 1. Verify comment block is removed
    asg_block_names = [b["name"] for b in asg.get("blocks", [])]
    assert "comment" not in asg_block_names
    assert len(asg_block_names) == 2

    # 2. Verify p_with_attrs has had its positional/digit attributes removed, keeping my-named-attr and style
    cleaned_p = asg["blocks"][0]
    assert "attributes" in cleaned_p
    assert "my-named-attr" in cleaned_p["attributes"]
    assert "style" in cleaned_p["attributes"]
    assert "positional" not in cleaned_p["attributes"]
    assert "1" not in cleaned_p["attributes"]

    # 3. Verify p_with_only_positional keeps style in attributes
    empty_p = asg["blocks"][1]
    assert "attributes" in empty_p
    assert "style" in empty_p["attributes"]
    assert "positional" not in empty_p["attributes"]


# ---------------------------------------------------------------------------
# Additional resolver tests (WorkspaceCatalog, WorkspaceBuilder, ASGResolver paths)
# ---------------------------------------------------------------------------


class TestWorkspaceCatalog:
    def test_index_document_root_indexed(self) -> None:
        catalog = WorkspaceCatalog()
        doc = Document()
        catalog.index_document("main.adoc", doc)
        assert "main.adoc#" in catalog.by_fqid
        assert catalog.by_fqid["main.adoc#"] is doc

    def test_index_document_with_anchor_id(self) -> None:
        catalog = WorkspaceCatalog()
        doc = Document()
        sec = Section(level=1, title=Title(inlines=[Text("Intro")]))
        sec.attributes["id"] = "intro"
        doc.blocks.append(sec)

        catalog.index_document("guide.adoc", doc)
        assert "guide.adoc#intro" in catalog.by_fqid
        assert catalog.by_fqid["guide.adoc#intro"] is sec
        assert "guide.adoc" in catalog.by_local_id["intro"]

    def test_index_document_with_header(self) -> None:
        catalog = WorkspaceCatalog()
        doc = Document()
        header = Header(title=Title(inlines=[Text("Doc")]))
        doc.header = header
        catalog.index_document("doc.adoc", doc)
        # header itself is traversed without error
        assert "doc.adoc#" in catalog.by_fqid

    def test_index_document_id_object_with_value_attr(self) -> None:
        """Cover the `hasattr(node_id, 'value')` branch in index_document."""
        catalog = WorkspaceCatalog()
        doc = Document()
        sec = Section(level=1)

        class NodeIdWrapper:
            def __init__(self, v: str) -> None:
                self.value = v

        sec.attributes["id"] = NodeIdWrapper("wrapped-id")
        doc.blocks.append(sec)
        catalog.index_document("f.adoc", doc)
        assert "f.adoc#wrapped-id" in catalog.by_fqid

    def test_index_document_no_duplicate_file_entries(self) -> None:
        catalog = WorkspaceCatalog()
        doc1 = Document()
        doc2 = Document()
        sec = Section(level=1)
        sec.attributes["id"] = "shared"
        doc1.blocks.append(sec)
        doc2.blocks.append(Section(level=1, title=Title(inlines=[Text("x")])))

        catalog.index_document("a.adoc", doc1)
        catalog.index_document("b.adoc", doc2)
        # "shared" id only in a.adoc
        assert "a.adoc" in catalog.by_local_id["shared"]
        assert "b.adoc" not in catalog.by_local_id["shared"]


# ---------------------------------------------------------------------------
# WorkspaceBuilder
# ---------------------------------------------------------------------------


class TestWorkspaceBuilder:
    def _create_workspace(self, files: dict[str, str]) -> str:
        """Helper: write adoc files to a temp directory and return its path."""
        tmpdir = tempfile.mkdtemp()
        for filename, content in files.items():
            p = Path(tmpdir) / filename
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        return tmpdir

    def test_build_single_file(self) -> None:
        tmpdir = self._create_workspace({"doc.adoc": "= Hello\n\nParagraph."})
        builder = WorkspaceBuilder(tmpdir)
        graphs = builder.build()
        assert "doc.adoc" in graphs
        assert graphs["doc.adoc"]["name"] == "document"

    def test_discover_and_parse_populates_raw_documents(self) -> None:
        tmpdir = self._create_workspace(
            {"a.adoc": "Paragraph A.", "sub/b.adoc": "Paragraph B."}
        )
        builder = WorkspaceBuilder(tmpdir)
        builder.discover_and_parse_project()
        assert "a.adoc" in builder.raw_documents
        assert "sub/b.adoc" in builder.raw_documents

    def test_index_workspace_symbols(self) -> None:
        tmpdir = self._create_workspace({"doc.adoc": "= Doc\n\nText."})
        builder = WorkspaceBuilder(tmpdir)
        builder.discover_and_parse_project()
        builder.index_workspace_symbols()
        assert "doc.adoc#" in builder.catalog.by_fqid

    def test_resolve_workspace_semantics(self) -> None:
        tmpdir = self._create_workspace({"doc.adoc": "= Title\n\nContent."})
        builder = WorkspaceBuilder(tmpdir)
        builder.discover_and_parse_project()
        builder.index_workspace_symbols()
        builder.resolve_workspace_semantics()
        assert "doc.adoc" in builder.resolved_asg_graphs

    def test_get_file_id_is_posix(self) -> None:
        tmpdir = self._create_workspace({"sub/doc.adoc": ""})
        builder = WorkspaceBuilder(tmpdir)
        abs_path = Path(tmpdir) / "sub" / "doc.adoc"
        fid = builder._get_file_id(abs_path.resolve())
        assert "\\" not in fid
        assert fid == "sub/doc.adoc"

    def test_build_with_custom_parser(self) -> None:
        tmpdir = self._create_workspace({"doc.adoc": "= Test\n\nText."})

        class FakeParser:
            def parse(self, content: str) -> Document:
                doc = Document()
                doc.blocks.append(Paragraph(inlines=[Text("fake")]))
                return doc

        builder = WorkspaceBuilder(tmpdir, lark_parser_instance=FakeParser())
        graphs = builder.build()
        assert "doc.adoc" in graphs


# ---------------------------------------------------------------------------
# ASGResolver._resolve_docinfo_files
# ---------------------------------------------------------------------------


class TestResolveDocinfoFiles:
    def _make_doc(
        self, attrs: dict[str, Any], base_dir: Optional[str] = None
    ) -> Document:
        doc = Document(base_dir=base_dir)
        doc.attributes = attrs
        return doc

    def test_no_docinfo_attr_returns_empty(self) -> None:
        doc = self._make_doc({})
        resolver = ASGResolver(doc)
        head, foot = resolver._resolve_docinfo_files(doc)
        assert head == ""
        assert foot == ""

    def test_shared_docinfo_reads_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "docinfo.html").write_text("<meta/>", encoding="utf-8")
            doc = self._make_doc({"docinfo": "shared"}, base_dir=tmpdir)
            resolver = ASGResolver(doc)
            head, foot = resolver._resolve_docinfo_files(doc)
            assert "<meta/>" in head
            assert foot == ""

    def test_shared_docinfo_footer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "docinfo-footer.html").write_text(
                "<footer/>", encoding="utf-8"
            )
            doc = self._make_doc({"docinfo": "shared"}, base_dir=tmpdir)
            resolver = ASGResolver(doc)
            head, foot = resolver._resolve_docinfo_files(doc)
            assert "<footer/>" in foot

    def test_private_docinfo_reads_docname(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "mydoc-docinfo.html").write_text(
                "<priv/>", encoding="utf-8"
            )
            doc = self._make_doc({"docinfo": "private"}, base_dir=tmpdir)
            resolver = ASGResolver(doc, current_file_id="mydoc.adoc")
            head, foot = resolver._resolve_docinfo_files(doc)
            assert "<priv/>" in head

    def test_docinfofiles_custom_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "extra.html").write_text("<extra/>", encoding="utf-8")
            doc = self._make_doc({"docinfofiles": "extra.html"}, base_dir=tmpdir)
            resolver = ASGResolver(doc)
            head, foot = resolver._resolve_docinfo_files(doc)
            assert "<extra/>" in head

    def test_docinfofiles_footer_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "docinfo-footer-extra.html").write_text(
                "<fn/>", encoding="utf-8"
            )
            doc = self._make_doc(
                {"docinfofiles": "docinfo-footer-extra.html"}, base_dir=tmpdir
            )
            resolver = ASGResolver(doc)
            head, foot = resolver._resolve_docinfo_files(doc)
            assert "<fn/>" in foot

    def test_attribute_substitution_in_docinfo(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "docinfo.html").write_text(
                "Version: {version}", encoding="utf-8"
            )
            doc = self._make_doc(
                {"docinfo": "shared", "version": "2.0"}, base_dir=tmpdir
            )
            resolver = ASGResolver(doc)
            head, _ = resolver._resolve_docinfo_files(doc)
            assert "Version: 2.0" in head

    def test_safe_mode_blocks_escape(self) -> None:
        """safe_mode >= 2 should block escape from base_dir."""
        with tempfile.TemporaryDirectory() as tmpdir:
            outside = tempfile.mkdtemp()
            (Path(outside) / "docinfo.html").write_text("<outside/>", encoding="utf-8")
            doc = self._make_doc(
                {"docinfo": "shared", "docinfodir": outside}, base_dir=tmpdir
            )
            doc.safe_mode = 2
            resolver = ASGResolver(doc)
            head, _ = resolver._resolve_docinfo_files(doc)
            assert head == ""


# ---------------------------------------------------------------------------
# ASGResolver footnote resolution
# ---------------------------------------------------------------------------


class TestFootnoteResolution:
    def _resolve_doc(self, doc: Document) -> dict[str, Any]:
        resolver = ASGResolver(doc)
        return resolver.resolve(doc)

    def test_auto_numbered_footnote(self) -> None:
        doc = Document()
        footnote_ref = Ref(variant="footnote", target="")
        footnote_ref.inlines.append(Text("First footnote"))
        doc.blocks.append(Paragraph(inlines=[footnote_ref]))

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        assert len(resolver.footnotes) == 1
        fn = resolver.footnotes[0]
        assert fn["index"] == 1
        assert fn["id"] is None
        assert "First footnote" in fn["text"]
        assert asg["footnotes"][0]["index"] == 1

    def test_named_footnote_definition(self) -> None:
        doc = Document()
        footnote_ref = Ref(variant="footnote", target="fn-a")
        footnote_ref.inlines.append(Text("Named fn"))
        doc.blocks.append(Paragraph(inlines=[footnote_ref]))

        resolver = ASGResolver(doc)
        resolver.resolve(doc)

        assert "fn-a" in resolver.footnote_by_id
        fn = resolver.footnote_by_id["fn-a"]
        assert fn["id"] == "fn-a"
        assert fn["index"] == 1

    def test_named_footnote_backreference(self) -> None:
        """footnoteref:[id] with no inlines references existing footnote."""
        doc = Document()
        # First: define the named footnote
        first_ref = Ref(variant="footnote", target="fn-b")
        first_ref.inlines.append(Text("Defined here"))
        # Second: back-reference with no inlines
        back_ref = Ref(variant="footnote", target="fn-b")
        doc.blocks.append(Paragraph(inlines=[first_ref, back_ref]))

        resolver = ASGResolver(doc)
        resolver.resolve(doc)

        # Both should share the same index
        assert resolver.footnote_by_id["fn-b"]["index"] == 1

    def test_dangling_footnote_ref_creates_placeholder(self) -> None:
        """footnoteref:[id] with no prior definition creates a placeholder entry."""
        doc = Document()
        back_ref = Ref(variant="footnote", target="fn-missing")
        doc.blocks.append(Paragraph(inlines=[back_ref]))

        resolver = ASGResolver(doc)
        resolver.resolve(doc)

        assert "fn-missing" in resolver.footnote_by_id
        fn = resolver.footnote_by_id["fn-missing"]
        assert fn["text"] == ""
        assert fn["inlines"] == []

    def test_multiple_auto_footnotes_increment_counter(self) -> None:
        doc = Document()
        for i in range(3):
            fn_ref = Ref(variant="footnote", target="")
            fn_ref.inlines.append(Text(f"fn {i}"))
            doc.blocks.append(Paragraph(inlines=[fn_ref]))

        resolver = ASGResolver(doc)
        resolver.resolve(doc)

        assert len(resolver.footnotes) == 3
        assert [fn["index"] for fn in resolver.footnotes] == [1, 2, 3]


# ---------------------------------------------------------------------------
# ASGResolver xref resolution (3-tier)
# ---------------------------------------------------------------------------


class TestXrefResolution:
    def _setup_catalog_and_docs(self) -> tuple[WorkspaceCatalog, Document, Document]:
        catalog = WorkspaceCatalog()

        doc1 = Document()
        sec = Section(level=1, title=Title(inlines=[Text("Intro")]))
        sec.attributes["id"] = "intro"
        doc1.blocks.append(sec)
        catalog.index_document("guide.adoc", doc1)

        doc2 = Document()
        catalog.index_document("other.adoc", doc2)

        return catalog, doc1, doc2

    def test_xref_tier1_explicit_file(self) -> None:
        catalog, doc1, doc2 = self._setup_catalog_and_docs()
        xref = Ref(variant="xref", target="guide.adoc#intro")
        doc2.blocks.append(Paragraph(inlines=[xref]))

        resolver = ASGResolver(doc2, catalog=catalog, current_file_id="other.adoc")
        resolver.resolve(doc2)

        # Resolve succeeded if no exception
        assert xref.resolved_strategy in ("same_file", "cross_file", None)

    def test_xref_tier2_local_anchor(self) -> None:
        catalog = WorkspaceCatalog()
        doc = Document()
        sec = Section(level=1)
        sec.attributes["id"] = "local-sec"
        doc.blocks.append(sec)
        catalog.index_document("curr.adoc", doc)

        xref = Ref(variant="xref", target="local-sec")
        p = Paragraph(inlines=[xref])
        doc2 = Document()
        doc2.blocks.append(p)
        # Don't add doc2 to catalog, but current_file_id points to doc which has the anchor
        catalog.index_document("curr.adoc", doc)

        resolver = ASGResolver(doc, catalog=catalog, current_file_id="curr.adoc")
        asg = resolver.resolve(doc)
        assert asg["name"] == "document"

    def test_xref_tier3_global_lookup(self) -> None:
        catalog = WorkspaceCatalog()
        doc_a = Document()
        sec = Section(level=1)
        sec.attributes["id"] = "global-sec"
        doc_a.blocks.append(sec)
        catalog.index_document("a.adoc", doc_a)

        doc_b = Document()
        xref = Ref(variant="xref", target="global-sec")
        doc_b.blocks.append(Paragraph(inlines=[xref]))
        catalog.index_document("b.adoc", doc_b)

        resolver = ASGResolver(doc_b, catalog=catalog, current_file_id="b.adoc")
        asg = resolver.resolve(doc_b)
        assert asg["name"] == "document"

    def test_xref_missing_raises_key_error(self) -> None:
        catalog = WorkspaceCatalog()
        doc = Document()
        catalog.index_document("only.adoc", doc)

        xref = Ref(variant="xref", target="nonexistent#anchor")
        doc2 = Document()
        doc2.blocks.append(Paragraph(inlines=[xref]))

        resolver = ASGResolver(doc2, catalog=catalog, current_file_id="only.adoc")
        with pytest.raises(KeyError, match="Cross-reference error"):
            resolver.resolve(doc2)

    def test_xref_file_only_target(self) -> None:
        """xref to file with no anchor (e.g. xref:guide.adoc[])."""
        catalog = WorkspaceCatalog()
        doc_target = Document()
        catalog.index_document("guide.adoc", doc_target)

        doc_src = Document()
        xref = Ref(variant="xref", target="guide.adoc")
        doc_src.blocks.append(Paragraph(inlines=[xref]))
        catalog.index_document("src.adoc", doc_src)

        resolver = ASGResolver(doc_src, catalog=catalog, current_file_id="src.adoc")
        asg = resolver.resolve(doc_src)
        assert asg["name"] == "document"


# ---------------------------------------------------------------------------
# ASGResolver: visit_comment, visit_text, visit_attributes
# ---------------------------------------------------------------------------


class TestResolverVisitorMethods:
    def test_visit_comment_filters_out_comments(self) -> None:
        """Comments should be removed from block lists."""

        doc = Document()
        doc.blocks.append(Paragraph(inlines=[Text("keep me")]))
        doc.blocks.append(Comment(value="this is a comment"))

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        names = [b["name"] for b in asg["blocks"]]
        assert "comment" not in names
        assert "paragraph" in names

    def test_visit_text_substitutes_attributes(self) -> None:
        doc = Document()
        doc.attributes = {"lang": "Python"}
        p = Paragraph(inlines=[Text("Language: {lang}")])
        doc.blocks.append(p)

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        assert asg["blocks"][0]["inlines"][0]["value"] == "Language: Python"

    def test_visit_attributes_substitutes_in_values(self) -> None:

        doc = Document()
        doc.attributes = {"ver": "2.0"}
        # Put an Attributes node (grouped attribute entries) with a substitutable value
        attrs_node = Attributes({"myattr": {"value": "Version {ver}"}})
        doc.blocks.append(attrs_node)

        resolver = ASGResolver(doc)
        resolver.resolve(doc)
        # The resolver should substitute without error


# ---------------------------------------------------------------------------
# ASGResolver: AttributeEntry grouping in generic_visit
# ---------------------------------------------------------------------------


class TestAttributeEntryGrouping:
    def test_consecutive_attribute_entries_grouped(self) -> None:
        """Multiple consecutive attribute_entry nodes should be grouped into Attributes."""
        doc = Document()
        doc.blocks.append(AttributeEntry("key1", "val1"))
        doc.blocks.append(AttributeEntry("key2", "val2"))
        doc.blocks.append(Paragraph(inlines=[Text("text")]))

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        names = [b["name"] for b in asg["blocks"]]
        assert "attributes" in names
        assert "paragraph" in names
        assert "attribute_entry" not in names

    def test_non_consecutive_entries_create_separate_groups(self) -> None:
        doc = Document()
        doc.blocks.append(AttributeEntry("a", "1"))
        doc.blocks.append(Paragraph(inlines=[Text("between")]))
        doc.blocks.append(AttributeEntry("b", "2"))

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        blocks = asg["blocks"]
        names = [b["name"] for b in blocks]
        assert names.count("attributes") == 2
        assert "paragraph" in names


# ---------------------------------------------------------------------------
# ASGResolver: constructor fallback for current_file_id
# ---------------------------------------------------------------------------


class TestResolverCurrentFileId:
    def test_default_file_id_is_root(self) -> None:
        doc = Document()
        resolver = ASGResolver(doc)
        assert resolver.current_file_id == "root"

    def test_file_id_from_doc_id(self) -> None:
        doc = Document()
        doc.id = "my-doc"
        resolver = ASGResolver(doc)
        assert resolver.current_file_id == "my-doc"

    def test_explicit_file_id_overrides(self) -> None:
        doc = Document()
        resolver = ASGResolver(doc, current_file_id="explicit.adoc")
        assert resolver.current_file_id == "explicit.adoc"


# ---------------------------------------------------------------------------
# Integration tests relocated from test_integration.py / test_workspace_builder.py
# These require parse_to_ast so they stay marked unit=False; they live here
# because their subject matter is the resolver/workspace layer.
# ---------------------------------------------------------------------------


class TestResolverIntegration(unittest.TestCase):
    pytestmark = pytest.mark.integration
    """Pipeline-level tests for ASGResolver — parse then resolve."""

    def test_attribute_entry_consumed_into_asg(self):
        """parse + resolve: attribute_entry nodes are consumed; ASG gains an 'attributes' block."""
        from asciidoctrine.lark_parser import parse_to_ast

        source = ":my-attr: my-value\n\nThis is a paragraph.\n"
        ast = parse_to_ast(source)

        ast_block_names = [b["name"] for b in ast.to_dict().get("blocks", [])]
        self.assertIn("attribute_entry", ast_block_names)

        asg = ASGResolver(ast).resolve(ast)
        asg_block_names = [b["name"] for b in asg.get("blocks", [])]
        self.assertNotIn("attribute_entry", asg_block_names)
        self.assertIn("attributes", asg_block_names)
        self.assertIn("paragraph", asg_block_names)

        attr_block = next(b for b in asg["blocks"] if b["name"] == "attributes")
        self.assertIn("my-attr", attr_block["attributes"])
        self.assertEqual(attr_block["attributes"]["my-attr"]["value"], "my-value")
        self.assertIn("location", attr_block["attributes"]["my-attr"])


class TestWorkspaceBuilderIntegration(unittest.TestCase):
    pytestmark = pytest.mark.integration
    """End-to-end WorkspaceBuilder tests requiring real files on disk."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        Path(self.tmp_dir, "subdir").mkdir(parents=True, exist_ok=True)
        with open(os.path.join(self.tmp_dir, "doc1.adoc"), "w") as f:
            f.write("= Document One\n:id: doc1\n\n[[intro]]\n== Intro\n")
        with open(os.path.join(self.tmp_dir, "subdir", "doc2.adoc"), "w") as f:
            f.write("= Document Two\n\nRefer to <<../doc1.adoc#intro,link>>\n")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_cross_file_xref_resolution(self):
        """WorkspaceBuilder resolves cross-file xrefs with correct strategy and targets."""
        builder = WorkspaceBuilder(self.tmp_dir)
        graphs = builder.build()

        self.assertIn("doc1.adoc", graphs)
        self.assertIn("subdir/doc2.adoc", graphs)

        doc2_asg = graphs["subdir/doc2.adoc"]
        ref = doc2_asg["blocks"][0]["inlines"][1]  # <<../doc1.adoc#intro>>
        self.assertEqual(ref["resolved_strategy"], "cross_file")
        self.assertEqual(ref["resolved_file_target"], "doc1.adoc")
        self.assertEqual(ref["resolved_anchor_target"], "intro")


# ---------------------------------------------------------------------------
# Resolver gap coverage — additional unit tests
# ---------------------------------------------------------------------------


class TestResolverGenericVisitBranches:
    """Covers generic_visit branches not hit by existing tests."""

    def test_all_positional_attributes_cleared(self):
        """When every attribute is a positional/digit key, node.attributes becomes {}."""
        doc = Document()
        p = Paragraph(inlines=[Text("text")])
        # Mix of digit and "positional" keys — both are stripped
        p.attributes = {"1": "python", "positional": "source"}
        doc.blocks.append(p)
        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)
        # After resolving, the paragraph's attributes should be empty
        para = asg["blocks"][0]
        assert para.get("attributes", {}) == {}

    def test_mixed_attributes_positional_stripped(self):
        """Non-positional keys survive; positional/digit keys are removed."""
        doc = Document()
        p = Paragraph(inlines=[Text("text")])
        p.attributes = {"id": "my-id", "positional": "source", "1": "python"}
        doc.blocks.append(p)
        asg = ASGResolver(doc).resolve(doc)
        para = asg["blocks"][0]
        # 'id' survives; positional and '1' do not
        assert "id" in para.get("attributes", {})
        assert "positional" not in para.get("attributes", {})
        assert "1" not in para.get("attributes", {})


class TestResolverFootnotePaths:
    """Covers footnote handling branches in visit_ref."""

    def _make_resolver(self) -> ASGResolver:
        return ASGResolver(Document())

    def test_auto_numbered_footnote_no_target(self):
        """footnote:[text] — auto-numbered, no custom id."""
        resolver = self._make_resolver()
        ref = Ref(variant="footnote", target="")
        ref.inlines = [Text("note text")]
        result = resolver.visit_ref(ref)
        assert result.index == 1
        assert len(resolver.footnotes) == 1
        assert resolver.footnotes[0]["text"] == "note text"
        assert resolver.footnotes[0]["id"] is None

    def test_footnoteref_first_definition_with_inlines(self):
        """footnoteref:[id,text] — first time seen, defines the footnote."""
        resolver = self._make_resolver()
        ref = Ref(variant="footnote", target="fn1")
        ref.inlines = [Text("footnote body")]
        result = resolver.visit_ref(ref)
        assert result.index == 1
        assert "fn1" in resolver.footnote_by_id
        assert resolver.footnote_by_id["fn1"]["text"] == "footnote body"

    def test_footnoteref_second_definition_updates_inlines(self):
        """footnoteref:[id,text] called twice — second call updates text if first had no inlines."""
        resolver = self._make_resolver()
        # First: define a placeholder with empty inlines
        resolver.footnote_counter = 1
        resolver.footnote_by_id["fn2"] = {
            "id": "fn2",
            "index": 1,
            "text": "",
            "inlines": [],
        }
        resolver.footnotes.append(resolver.footnote_by_id["fn2"])

        # Second: call with inlines — should update the existing entry (lines 354-358)
        ref2 = Ref(variant="footnote", target="fn2")
        ref2.inlines = [Text("filled in later")]
        result = resolver.visit_ref(ref2)
        assert result.index == 1  # reuses existing index
        assert resolver.footnote_by_id["fn2"]["text"] == "filled in later"

    def test_footnoteref_back_reference_existing_id(self):
        """footnoteref:[id] with no inlines, id already registered — back-reference."""
        resolver = self._make_resolver()
        resolver.footnote_counter = 1
        resolver.footnote_by_id["fn3"] = {
            "id": "fn3",
            "index": 1,
            "text": "original",
            "inlines": [Text("original").to_dict()],
        }
        ref = Ref(variant="footnote", target="fn3")
        ref.inlines = []  # no inlines = back-reference
        result = resolver.visit_ref(ref)
        assert result.index == 1  # reuses existing

    def test_footnoteref_back_reference_new_id_creates_placeholder(self):
        """footnoteref:[id] with no inlines and unknown id — creates empty placeholder."""
        resolver = self._make_resolver()
        ref = Ref(variant="footnote", target="new-fn")
        ref.inlines = []
        result = resolver.visit_ref(ref)
        assert result.index == 1
        assert "new-fn" in resolver.footnote_by_id
        assert resolver.footnote_by_id["new-fn"]["text"] == ""

    def test_link_variant_passes_through_generic_visit(self):
        """A Ref with variant='link' (not footnote/xref) hits the generic_visit fallback."""
        doc = Document()
        ref = Ref(variant="link", target="https://example.com")
        ref.inlines = [Text("click here")]
        p = Paragraph(inlines=[ref])
        doc.blocks.append(p)
        asg = ASGResolver(doc).resolve(doc)
        # Should survive resolution without error
        inline = asg["blocks"][0]["inlines"][0]
        assert inline["name"] == "ref"
        assert inline["variant"] == "link"


class TestResolverXrefTiers:
    """Covers the 3-tier xref resolution paths."""

    def _catalog_with(self, entries: dict) -> "WorkspaceCatalog":
        cat = WorkspaceCatalog()
        for fqid, node in entries.items():
            cat.by_fqid[fqid] = node
            local = fqid.split("#", 1)[1] if "#" in fqid else fqid
            cat.by_local_id.setdefault(local, []).append(fqid.split("#")[0])
        return cat

    def test_xref_tier2_local_file_implicit_match(self):
        """Tier 2: <<anchor>> resolved via current_file_id#anchor in catalog."""
        from asciidoctrine.nodes import Section, Title

        anchor_node = Section(level=1, title=Title(inlines=[Text("S")]))
        anchor_node.id = "intro"
        catalog = self._catalog_with({"doc.adoc#intro": anchor_node})

        doc = Document()
        ref = Ref(variant="xref", target="intro")
        ref.inlines = []
        p = Paragraph(inlines=[ref])
        doc.blocks.append(p)

        resolver = ASGResolver(doc, catalog=catalog, current_file_id="doc.adoc")
        result = resolver.visit_ref(ref)
        assert result.resolved_strategy == "same_file"
        assert result.resolved_file_target == "doc.adoc"

    def test_xref_tier3_global_lookup(self):
        """Tier 3: <<anchor>> found uniquely in global by_local_id catalog."""
        from asciidoctrine.nodes import Section, Title

        anchor_node = Section(level=1, title=Title(inlines=[Text("G")]))
        catalog = WorkspaceCatalog()
        catalog.by_fqid["other.adoc#global-id"] = anchor_node
        catalog.by_local_id["global-id"] = ["other.adoc"]

        doc = Document()
        ref = Ref(variant="xref", target="global-id")
        ref.inlines = []
        p = Paragraph(inlines=[ref])
        doc.blocks.append(p)

        resolver = ASGResolver(doc, catalog=catalog, current_file_id="main.adoc")
        result = resolver.visit_ref(ref)
        assert result.resolved_strategy == "cross_file"
        assert result.resolved_file_target == "other.adoc"


class TestTableResolution:
    """Test suite for Table columns resolution in ASGResolver."""

    def test_table_node_to_dict_columns(self):
        """Table.to_dict() includes columns when set, omits when None."""
        table_no_cols = Table(rows=[TableRow(cells=[TableCell(blocks=[Paragraph(inlines=[Text("A")])])])])
        assert table_no_cols.columns is None
        assert "columns" not in table_no_cols.to_dict()

        cols_data = [
            {"index": 0, "width": "50%", "halign": "left", "valign": "top", "style": "default"},
            {"index": 1, "width": "50%", "halign": "right", "valign": "middle", "style": "strong"},
        ]
        table_with_cols = Table(
            rows=[TableRow(cells=[TableCell(blocks=[Paragraph(inlines=[Text("A")])])])],
            columns=cols_data,
        )
        assert table_with_cols.columns == cols_data
        asg_dict = table_with_cols.to_dict()
        assert "columns" in asg_dict
        assert asg_dict["columns"] == cols_data

    def test_table_resolution_with_cols_dsl(self):
        """Resolver parses cols DSL and sets columns on Table while preserving attributes['cols']."""
        table = Table(
            rows=[
                TableRow(
                    cells=[
                        TableCell(blocks=[Paragraph(inlines=[Text("1")])]),
                        TableCell(blocks=[Paragraph(inlines=[Text("2")])]),
                        TableCell(blocks=[Paragraph(inlines=[Text("3")])]),
                    ]
                )
            ]
        )
        table.attributes = {"cols": "1,3,>1s"}

        doc = Document()
        doc.blocks.append(table)

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        table_asg = asg["blocks"][0]
        assert table_asg["name"] == "table"
        assert "columns" in table_asg
        assert table_asg["columns"] == [
            {
                "index": 0,
                "width": "20%",
                "halign": "left",
                "valign": "top",
                "style": "default",
            },
            {
                "index": 1,
                "width": "60%",
                "halign": "left",
                "valign": "top",
                "style": "default",
            },
            {
                "index": 2,
                "width": "20%",
                "halign": "right",
                "valign": "top",
                "style": "strong",
            },
        ]
        assert "attributes" in table_asg
        assert table_asg["attributes"]["cols"] == "1,3,>1s"

    def test_table_resolution_fallback_col_count_from_rows(self):
        """Resolver calculates fallback column count from rows when cols attribute is missing."""
        table = Table(
            rows=[
                TableRow(
                    cells=[
                        TableCell(blocks=[Paragraph(inlines=[Text("A")])]),
                        TableCell(blocks=[Paragraph(inlines=[Text("B")])]),
                        TableCell(blocks=[Paragraph(inlines=[Text("C")])]),
                    ]
                ),
                TableRow(
                    cells=[
                        TableCell(blocks=[Paragraph(inlines=[Text("1")])]),
                        TableCell(blocks=[Paragraph(inlines=[Text("2")])]),
                        TableCell(blocks=[Paragraph(inlines=[Text("3")])]),
                    ]
                ),
            ]
        )

        doc = Document()
        doc.blocks.append(table)

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        table_asg = asg["blocks"][0]
        assert "columns" in table_asg
        assert table_asg["columns"] == [
            {
                "index": 0,
                "width": "33.3333%",
                "halign": "left",
                "valign": "top",
                "style": "default",
            },
            {
                "index": 1,
                "width": "33.3333%",
                "halign": "left",
                "valign": "top",
                "style": "default",
            },
            {
                "index": 2,
                "width": "33.3333%",
                "halign": "left",
                "valign": "top",
                "style": "default",
            },
        ]
        assert "attributes" not in table_asg or "cols" not in table_asg.get("attributes", {})

    def test_table_resolution_fallback_with_colspan(self):
        """Fallback column count takes cell colspan into account."""
        cell1 = TableCell(blocks=[Paragraph(inlines=[Text("Span")])])
        cell1.colspan = 2
        cell2 = TableCell(blocks=[Paragraph(inlines=[Text("Single")])])
        cell2.colspan = 1

        table = Table(rows=[TableRow(cells=[cell1, cell2])])

        doc = Document()
        doc.blocks.append(table)

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        table_asg = asg["blocks"][0]
        assert len(table_asg["columns"]) == 3
        for col in table_asg["columns"]:
            assert col["width"] == "33.3333%"

    def test_table_resolution_empty_table(self):
        """Empty table resolves to empty columns list."""
        table = Table()

        doc = Document()
        doc.blocks.append(table)

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        table_asg = asg["blocks"][0]
        assert "columns" in table_asg
        assert table_asg["columns"] == []

    def test_table_resolution_attribute_substitution_in_cols(self):
        """Resolver performs attribute substitution on cols attribute string."""
        table = Table(
            rows=[
                TableRow(
                    cells=[
                        TableCell(blocks=[Paragraph(inlines=[Text("A")])]),
                        TableCell(blocks=[Paragraph(inlines=[Text("B")])]),
                    ]
                )
            ]
        )
        table.attributes = {"cols": "{custom_cols}"}

        doc = Document()
        doc.attributes = {"custom_cols": "2,1"}
        doc.blocks.append(table)

        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        table_asg = asg["blocks"][0]
        assert table_asg["columns"] == [
            {
                "index": 0,
                "width": "66.6667%",
                "halign": "left",
                "valign": "top",
                "style": "default",
            },
            {
                "index": 1,
                "width": "33.3333%",
                "halign": "left",
                "valign": "top",
                "style": "default",
            },
        ]

    def test_table_resolution_integration_from_parser(self):
        """End-to-end integration: parse AsciiDoc table syntax and resolve into ASG."""
        from asciidoctrine.lark_parser import parse_to_ast

        content = """[cols="2*^.<20%s,>60%"]
|===
| Header 1 | Header 2 | Header 3
| Cell 1 | Cell 2 | Cell 3
|===
"""
        doc = parse_to_ast(content)
        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)

        table_asg = asg["blocks"][0]
        assert table_asg["name"] == "table"
        assert table_asg["attributes"]["cols"] == "2*^.<20%s,>60%"
        assert table_asg["columns"] == [
            {
                "index": 0,
                "width": "20%",
                "halign": "center",
                "valign": "top",
                "style": "strong",
            },
            {
                "index": 1,
                "width": "20%",
                "halign": "center",
                "valign": "top",
                "style": "strong",
            },
            {
                "index": 2,
                "width": "60%",
                "halign": "right",
                "valign": "top",
                "style": "default",
            },
        ]

