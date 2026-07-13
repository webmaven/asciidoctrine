import os
import unittest

from asciidoctrine import parse_to_ast, serialize_to_asciidoc


class TestAsciiDocSerializer(unittest.TestCase):
    def setUp(self):
        # Create a dummy include file in the current working directory
        with open("otherfile.adoc", "w") as f:
            f.write("This is include content.")

    def tearDown(self):
        if os.path.exists("otherfile.adoc"):
            os.remove("otherfile.adoc")

    def _assert_roundtrip(self, source: str):
        """Helper to verify that serializing the AST yields semantically identical AST."""
        # Parse original source
        ast_original = parse_to_ast(source)
        dict_original = ast_original.to_dict()

        # Serialize
        serialized = serialize_to_asciidoc(ast_original)

        # Re-parse serialized source
        try:
            ast_serialized = parse_to_ast(serialized)
            dict_serialized = ast_serialized.to_dict()
        except Exception as e:
            print("\n--- Failed to re-parse serialized text ---")
            print(serialized)
            print("------------------------------------------")
            raise e

        # Compare basic structure
        try:
            self.assertEqual(dict_serialized["name"], dict_original["name"])
            self.assertEqual(dict_serialized["type"], dict_original["type"])
            self.assertEqual(
                len(dict_serialized.get("blocks", [])),
                len(dict_original.get("blocks", [])),
            )
        except AssertionError as e:
            print("\n--- Assertion Failed ---")
            print("Serialized output was:")
            print(repr(serialized))
            print("Original dict blocks:", len(dict_original.get("blocks", [])))
            print("Serialized dict blocks:", len(dict_serialized.get("blocks", [])))
            print("------------------------")
            raise e

    def test_basic_paragraph(self):
        source = "Hello world! This is a simple paragraph.\n"
        self._assert_roundtrip(source)

    def test_formatting(self):
        source = "This is *bold*, _italic_, and `code` formatting.\n"
        self._assert_roundtrip(source)

    def test_headers_and_sections(self):
        source = """= Document Title
Michael R. Bernstein <michael@example.com>
v1.0, 2026-07-11
:custom-attr: values-only

== First Section
Some content inside section.
"""
        self._assert_roundtrip(source)

    def test_lists_and_checklists(self):
        source = """* List item 1
* List item 2
* [ ] Unchecked item
* [x] Checked item
"""
        self._assert_roundtrip(source)

    def test_ordered_list(self):
        source = """. First
. Second
. Third
"""
        self._assert_roundtrip(source)

    def test_description_list(self):
        source = """Term 1:: Definition of term 1
Term 2::
Definition of term 2
"""
        self._assert_roundtrip(source)

    def test_verbatim_listing(self):
        source = """[source,python]
----
def greet():
    print("Hello")
----
"""
        self._assert_roundtrip(source)

    def test_complex_blocks(self):
        source = """****
This is a sidebar block
****

====
This is an example block
====

[NOTE]
====
This is a delimited admonition note
====
"""
        self._assert_roundtrip(source)

    def test_block_metadata(self):
        source = """[[my-unique-id]]
[.my-custom-role]
.This is a paragraph title
This is the paragraph body.
"""
        self._assert_roundtrip(source)

    def test_tables(self):
        source = """|===
| Cell 1 | Cell 2
| Cell 3 | Cell 4
|===
"""
        self._assert_roundtrip(source)

    def test_breaks_and_macros(self):
        source = """'''
<<<
include::otherfile.adoc[]
toc::[]
:some-body-attr: body-value
"""
        self._assert_roundtrip(source)

    def test_trailing_newline_roundtrip(self):
        # Case 1: No trailing newline
        source1 = "Hello world! This is a simple paragraph."
        ast1 = parse_to_ast(source1)
        serialized1 = serialize_to_asciidoc(ast1)
        self.assertEqual(serialized1, source1)

        # Case 2: Standard trailing newline
        source2 = "Hello world! This is a simple paragraph.\n"
        ast2 = parse_to_ast(source2)
        serialized2 = serialize_to_asciidoc(ast2)
        self.assertEqual(serialized2, source2)

        # Case 3: Multiple trailing newlines (normalized to a single trailing newline by serializer)
        source3 = "Hello world! This is a simple paragraph.\n\n"
        ast3 = parse_to_ast(source3)
        serialized3 = serialize_to_asciidoc(ast3)
        self.assertEqual(serialized3, "Hello world! This is a simple paragraph.\n")

    def test_all_line_ending_combinations_roundtrip(self):
        # Combinations of modern line endings (Unix LF and Windows CRLF)
        combinations = {
            "unix_lf_with": "= Document Title\n\nThis is paragraph content.\n",
            "unix_lf_without": "= Document Title\n\nThis is paragraph content.",
            "windows_crlf_with": "= Document Title\r\n\r\nThis is paragraph content.\r\n",
            "windows_crlf_without": "= Document Title\r\n\r\nThis is paragraph content.",
        }

        for name, source in combinations.items():
            with self.subTest(combination=name):
                ast = parse_to_ast(source)
                serialized = serialize_to_asciidoc(ast)
                self.assertEqual(serialized, source)

    def test_pathological_paste_preserves_original_ending(self):
        # A small CRLF document with a massive LF pasted block below it (with a trailing newline)
        source = (
            "= Document Title\r\n\r\nParagraph 1\r\n\r\n"
            + "\n".join([f"Pasted line {i}" for i in range(50)])
            + "\n"
        )
        ast = parse_to_ast(source)
        serialized = serialize_to_asciidoc(ast)

        # The entire serialized output should use CRLF
        self.assertTrue(serialized.startswith("= Document Title\r\n"))
        self.assertIn("\r\nParagraph 1\r\n", serialized)
        self.assertNotIn("\n", serialized.replace("\r\n", ""))
        self.assertTrue(serialized.endswith("\r\n"))

    def test_footnotes_serialization(self):
        # 1. Standard auto-numbered footnote
        source1 = (
            "This is a paragraph with footnote:[Auto-numbered footnote content].\n"
        )
        ast1 = parse_to_ast(source1)
        serialized1 = serialize_to_asciidoc(ast1)
        self.assertEqual(serialized1, source1)

        # 2. Named footnote definition and subsequent reference
        source2 = "Define here footnoteref:[my-custom-id, Named footnote content], and reference again footnoteref:[my-custom-id].\n"
        ast2 = parse_to_ast(source2)
        serialized2 = serialize_to_asciidoc(ast2)
        self.assertEqual(serialized2, source2)
