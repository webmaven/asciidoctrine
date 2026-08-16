import pytest
from asciidoctrine.nodes import Document, Paragraph, Section
from asciidoctrine.resolver import WorkspaceCatalog



pytestmark = pytest.mark.unit
def test_workspace_catalog_indexing() -> None:
    catalog = WorkspaceCatalog()
    doc = Document()
    sect = Section(level=1)
    sect.attributes = {"id": "intro"}
    p = Paragraph()
    p.attributes = {"id": "p-1"}

    sect.blocks.append(p)
    doc.blocks.append(sect)

    catalog.index_document("main.adoc", doc)

    assert catalog.by_fqid["main.adoc#"] is doc
    assert catalog.by_fqid["main.adoc#intro"] is sect
    assert catalog.by_fqid["main.adoc#p-1"] is p
    assert catalog.by_local_id["intro"] == ["main.adoc"]
    assert catalog.by_local_id["p-1"] == ["main.adoc"]
