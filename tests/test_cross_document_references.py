import pytest
import asciidoctrine



pytestmark = pytest.mark.unit
def test_package_exports() -> None:
    assert hasattr(asciidoctrine, "WorkspaceCatalog")
    assert hasattr(asciidoctrine, "WorkspaceBuilder")
