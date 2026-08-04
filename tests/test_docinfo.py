import os
import tempfile
from asciidoctrine.lark_parser import parse_to_ast
from asciidoctrine.resolver import ASGResolver


def test_docinfo_shared_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        head_path = os.path.join(tmpdir, "docinfo.html")
        footer_path = os.path.join(tmpdir, "docinfo-footer.html")
        with open(head_path, "w") as f:
            f.write("<meta name=\"keywords\" content=\"AsciiDoc\">\n")
        with open(footer_path, "w") as f:
            f.write("<script>console.log('footer');</script>\n")

        doc_source = ":docinfo: shared\n\nHello World\n"
        doc = parse_to_ast(doc_source, base_dir=tmpdir)
        asg = ASGResolver(doc).resolve(doc)

        assert "docinfo" in asg
        assert asg["docinfo"]["name"] == "docinfo"
        assert "<meta name=\"keywords\" content=\"AsciiDoc\">" in asg["docinfo"]["head_content"]
        assert "<script>console.log('footer');</script>" in asg["docinfo"]["footer_content"]


def test_docinfo_private_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        head_path = os.path.join(tmpdir, "testdoc-docinfo.html")
        with open(head_path, "w") as f:
            f.write("<style>body { color: red; }</style>\n")

        doc_source = ":docname: testdoc\n:docinfo: private\n\nHello World\n"
        doc = parse_to_ast(doc_source, base_dir=tmpdir)
        asg = ASGResolver(doc, current_file_id="testdoc.adoc").resolve(doc)

        assert "docinfo" in asg
        assert "<style>body { color: red; }</style>" in asg["docinfo"]["head_content"]


def test_docinfo_attribute_substitution():
    with tempfile.TemporaryDirectory() as tmpdir:
        head_path = os.path.join(tmpdir, "docinfo.html")
        with open(head_path, "w") as f:
            f.write("<meta name=\"author\" content=\"{author}\">\n")

        doc_source = ":docinfo: shared\n:author: Jane Doe\n\nHello World\n"
        doc = parse_to_ast(doc_source, base_dir=tmpdir)
        asg = ASGResolver(doc).resolve(doc)

        assert "docinfo" in asg
        assert "<meta name=\"author\" content=\"Jane Doe\">" in asg["docinfo"]["head_content"]


def test_docinfo_safe_mode_traversal_prevention():
    with tempfile.TemporaryDirectory() as tmpdir:
        sub_dir = os.path.join(tmpdir, "sub")
        os.makedirs(sub_dir)
        secret_path = os.path.join(tmpdir, "docinfo.html")
        with open(secret_path, "w") as f:
            f.write("<meta name=\"secret\" content=\"leaked\">\n")

        doc_source = ":docinfo: shared\n:docinfodir: ..\n\nHello World\n"
        # safe_mode >= 2 should block reading outside sub_dir
        doc = parse_to_ast(doc_source, base_dir=sub_dir, safe_mode=2)
        asg = ASGResolver(doc).resolve(doc)

        # docinfo should either be missing or not contain secret_path content
        if "docinfo" in asg:
            assert "leaked" not in asg["docinfo"]["head_content"]
