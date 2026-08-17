import pytest

from asciidoctrine.lark_parser import parse_to_ast
from asciidoctrine.loader import MemoryLoader
from asciidoctrine.nodes import Document
from asciidoctrine.preprocessor import CircularIncludeError
from asciidoctrine.resolver import ASGResolver, WorkspaceBuilder

pytestmark = pytest.mark.integration


def test_hermetic_workspace_multifile_cross_refs():
    """
    Tests building a 3-document project entirely in memory using MemoryLoader.
    Verifies that WorkspaceBuilder indexes all anchors across documents and resolves
    interdocument xrefs without any filesystem interaction.
    """
    files = {
        "index.adoc": (
            "= Documentation Index\n\n"
            "Welcome! See xref:getting_started.adoc#installation[Installation Steps] "
            "and xref:api_ref.adoc#core-parser[Core Parser API]."
        ),
        "getting_started.adoc": (
            "= Getting Started\n\n"
            "[#installation]\n"
            "== Installation\n\n"
            "Run `pip install asciidoctrine` to install.\n\n"
            "Next: xref:index.adoc#[Back to Index]."
        ),
        "api_ref.adoc": (
            "= API Reference\n\n"
            "[#core-parser]\n"
            "== Parser Function\n\n"
            "`parse_to_ast(source)` parses AsciiDoc.\n\n"
            "See also xref:getting_started.adoc#installation[Prerequisites]."
        ),
    }

    loader = MemoryLoader(files, base_dir="/docs")
    builder = WorkspaceBuilder("/docs", loader=loader)
    graphs = builder.build()

    assert len(graphs) == 3
    assert "index.adoc" in graphs
    assert "getting_started.adoc" in graphs
    assert "api_ref.adoc" in graphs

    # 1. Inspect index.adoc resolved references
    index_asg = graphs["index.adoc"]
    index_para = index_asg["blocks"][0]
    index_refs = [i for i in index_para["inlines"] if i.get("name") == "ref"]
    assert len(index_refs) == 2

    ref_install = index_refs[0]
    assert ref_install["resolved_strategy"] == "cross_file"
    assert ref_install["resolved_file_target"] == "getting_started.adoc"
    assert ref_install["resolved_anchor_target"] == "installation"

    ref_api = index_refs[1]
    assert ref_api["resolved_strategy"] == "cross_file"
    assert ref_api["resolved_file_target"] == "api_ref.adoc"
    assert ref_api["resolved_anchor_target"] == "core-parser"

    # 2. Inspect getting_started.adoc backlink to index document root
    gs_asg = graphs["getting_started.adoc"]
    gs_sec = gs_asg["blocks"][0]
    gs_para = gs_sec["blocks"][1]
    gs_ref = next(i for i in gs_para["inlines"] if i.get("name") == "ref")
    assert gs_ref["resolved_strategy"] == "cross_file"
    assert gs_ref["resolved_file_target"] == "index.adoc"
    assert gs_ref["resolved_anchor_target"] == ""


def test_hermetic_nested_includes_in_memory():
    """
    Tests nested include directives resolved completely in memory via MemoryLoader.
    """
    files = {
        "book.adoc": (
            "= My Book\n\n"
            "include::chapters/ch1.adoc[]\n\n"
            "include::chapters/ch2.adoc[]\n"
        ),
        "chapters/ch1.adoc": (
            "== Chapter 1\n\ninclude::ch1_intro.adoc[]\n\nChapter 1 body.\n"
        ),
        "chapters/ch1_intro.adoc": "Chapter 1 introductory remarks.\n",
        "chapters/ch2.adoc": "== Chapter 2\n\nChapter 2 body.\n",
    }

    loader = MemoryLoader(files, base_dir="/workspace")
    ast = parse_to_ast(files["book.adoc"], base_dir="/workspace", loader=loader)

    assert isinstance(ast, Document)
    assert ast.is_preprocessed is True
    assert len(ast.included_files) == 3

    resolver = ASGResolver(ast)
    asg = resolver.resolve(ast)

    # Check sections
    sec1 = asg["blocks"][0]
    assert sec1["title"][0]["value"] == "Chapter 1"
    # ch1_intro paragraph + body paragraph
    assert "introductory remarks" in sec1["blocks"][0]["inlines"][0]["value"]

    sec2 = asg["blocks"][1]
    assert sec2["title"][0]["value"] == "Chapter 2"


def test_hermetic_circular_include_diagnostics():
    """
    Tests that circular includes are caught with detailed diagnostics in memory.
    """
    files = {
        "a.adoc": "= Doc A\n\ninclude::b.adoc[]",
        "b.adoc": "= Doc B\n\ninclude::c.adoc[]",
        "c.adoc": "= Doc C\n\ninclude::a.adoc[]",
    }

    loader = MemoryLoader(files, base_dir="/workspace")

    with pytest.raises(CircularIncludeError) as exc_info:
        parse_to_ast(files["a.adoc"], base_dir="/workspace", loader=loader)

    err_msg = str(exc_info.value)
    assert "Circular include detected" in err_msg
    assert "a.adoc" in err_msg
    assert "b.adoc" in err_msg
    assert "c.adoc" in err_msg


def test_hermetic_docinfo_resolution_in_memory():
    """
    Tests resolving head and footer docinfo files from an in-memory loader.
    """
    files = {
        "index.adoc": (":docinfo: shared\n= Document Title\n\nContent here."),
        "docinfo.html": "<meta name='custom' content='in-memory-header'>",
        "docinfo-footer.html": "<div id='footer'>in-memory-footer</div>",
    }

    loader = MemoryLoader(files, base_dir="/workspace")
    ast = parse_to_ast(files["index.adoc"], base_dir="/workspace", loader=loader)

    resolver = ASGResolver(ast)
    head_content, footer_content = resolver._resolve_docinfo_files(ast)

    assert "<meta name='custom' content='in-memory-header'>" in head_content
    assert "<div id='footer'>in-memory-footer</div>" in footer_content
