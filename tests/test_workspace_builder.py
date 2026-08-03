import os
import shutil
import tempfile
from pathlib import Path

from asciidoctrine.resolver import WorkspaceBuilder


def test_workspace_builder() -> None:
    tmp_dir = tempfile.mkdtemp()
    try:
        # Create dummy directory structure
        Path(tmp_dir, "subdir").mkdir(parents=True, exist_ok=True)

        with open(os.path.join(tmp_dir, "doc1.adoc"), "w") as f:
            f.write("= Document One\n:id: doc1\n\n[[intro]]\n== Intro\n")

        with open(os.path.join(tmp_dir, "subdir", "doc2.adoc"), "w") as f:
            f.write("= Document Two\n\nRefer to <<../doc1.adoc#intro,link>>\n")

        builder = WorkspaceBuilder(tmp_dir)
        graphs = builder.build()

        assert "doc1.adoc" in graphs
        assert "subdir/doc2.adoc" in graphs

        doc2_asg = graphs["subdir/doc2.adoc"]
        ref = doc2_asg["blocks"][0]["inlines"][1]  # <<../doc1.adoc#intro>>
        assert ref["resolved_strategy"] == "cross_file"
        assert ref["resolved_file_target"] == "doc1.adoc"
        assert ref["resolved_anchor_target"] == "intro"

    finally:
        shutil.rmtree(tmp_dir)
