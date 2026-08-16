import pytest
from asciidoctrine.nodes import Ref



pytestmark = pytest.mark.unit
def test_ref_semantic_properties() -> None:
    ref = Ref(variant="xref", target="doc.adoc#intro")
    assert hasattr(ref, "resolved_strategy")
    assert hasattr(ref, "resolved_file_target")
    assert hasattr(ref, "resolved_anchor_target")
    assert hasattr(ref, "target_node_instance")

    ref.resolved_strategy = "cross_file"
    ref.resolved_file_target = "doc.adoc"
    ref.resolved_anchor_target = "intro"

    serialized = ref.to_dict()
    assert serialized.get("resolved_strategy") == "cross_file"
    assert serialized.get("resolved_file_target") == "doc.adoc"
    assert serialized.get("resolved_anchor_target") == "intro"
    assert "target_node_instance" not in serialized
