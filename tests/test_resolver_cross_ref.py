import pytest

from asciidoctrine.nodes import Document, Paragraph, Ref, Section
from asciidoctrine.resolver import ASGResolver, WorkspaceCatalog

pytestmark = pytest.mark.unit


def test_cross_reference_resolution() -> None:
    catalog = WorkspaceCatalog()

    # Doc A (target)
    doc_a = Document()
    sect = Section(level=1)
    sect.attributes = {"id": "target_sec"}
    doc_a.blocks.append(sect)

    # Doc B (source)
    doc_b = Document()
    p = Paragraph()
    ref = Ref(variant="xref", target="doc_a.adoc#target_sec")
    p.inlines.append(ref)
    doc_b.blocks.append(p)

    # Index both docs
    catalog.index_document("doc_a.adoc", doc_a)
    catalog.index_document("doc_b.adoc", doc_b)

    # Resolve Doc B, explicitly passing its current_file_id
    resolver = ASGResolver(doc_b, catalog=catalog, current_file_id="doc_b.adoc")
    asg = resolver.resolve(doc_b)

    # Check resolved ref properties
    resolved_p = asg["blocks"][0]
    resolved_ref = resolved_p["inlines"][0]
    assert resolved_ref["resolved_strategy"] == "cross_file"
    assert resolved_ref["resolved_file_target"] == "doc_a.adoc"
    assert resolved_ref["resolved_anchor_target"] == "target_sec"
