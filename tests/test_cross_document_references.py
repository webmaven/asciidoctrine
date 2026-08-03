import asciidoctrine


def test_package_exports() -> None:
    assert hasattr(asciidoctrine, "WorkspaceCatalog")
    assert hasattr(asciidoctrine, "WorkspaceBuilder")
