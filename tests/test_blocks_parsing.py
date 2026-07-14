"""
Tests for block-level parsing in AsciiDoc.
"""

import os
import tempfile
import unittest

import pytest

from asciidoctrine.lark_parser import parse_to_ast

pytestmark = pytest.mark.integration


class TestBlocks(unittest.TestCase):
    def setUp(self):
        self._temp_dir_obj = tempfile.TemporaryDirectory()
        self.base_dir = self._temp_dir_obj.name
        with open(os.path.join(self.base_dir, "included.adoc"), "w") as f:
            f.write("This is an *included* file.\n\n* With a list item.\n")

    def tearDown(self):
        self._temp_dir_obj.cleanup()

    def _strip_locations(self, node):
        """Recursively strip 'location' from ASG dict."""
        if isinstance(node, dict):
            node.pop("location", None)
            for key, value in node.items():
                self._strip_locations(value)
        elif isinstance(node, list):
            for item in node:
                self._strip_locations(item)
        return node

    def test_paragraph(self):
        source = "Hello, world.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "paragraph",
                    "type": "block",
                    "inlines": [
                        {"name": "text", "type": "string", "value": "Hello, world."}
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_listing_delimiters_parameterized(self):
        cases = [
            ("----", "This is a literal block.\n"),
            ("-----", "listing\n"),
            ("------", "Another listing.\n"),
        ]
        for delimiter, content in cases:
            with self.subTest(delimiter=delimiter):
                source = f"{delimiter}\n{content}{delimiter}\n"
                ast = self._strip_locations(parse_to_ast(source).to_dict())
                listing = ast["blocks"][0]
                self.assertEqual(listing["name"], "listing")
                self.assertEqual(listing["form"], "delimited")
                self.assertEqual(listing["delimiter"], delimiter)
                self.assertEqual(listing["inlines"][0]["value"], content.strip())

    def test_ulist(self):
        source = "* one\n* two\n* three\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "list")
        self.assertEqual(ast["blocks"][0]["variant"], "unordered")
        self.assertEqual(len(ast["blocks"][0]["items"]), 3)

    def test_olist(self):
        source = "1. one\n2. two\n3. three\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "list")
        self.assertEqual(ast["blocks"][0]["variant"], "ordered")
        self.assertEqual(len(ast["blocks"][0]["items"]), 3)

    def test_source_block_attributes(self):
        source = "[source,python]\n----\ndef foo(): pass\n----\n"
        ast = parse_to_ast(source).to_dict()
        literal = ast["blocks"][0]
        self.assertEqual(literal["name"], "listing")
        self.assertEqual(
            literal["attributes"],
            {
                "style": "source",
                "language": "python",
                "1": "source",
                "2": "python",
                "positional": ["source", "python"],
            },
        )

    def test_listing_metadata_properties(self):
        # 1. Inline title and attributes
        source = '[#my-id,source,python,title="My Title",doctest=True]\n----\ndef foo(): pass\n----\n'
        ast = parse_to_ast(source)
        node = ast.blocks[0]

        # Verify block type
        from asciidoctrine.nodes import Listing

        self.assertTrue(isinstance(node, Listing))

        # Verify programmatic properties
        self.assertEqual(node.id, "my-id")
        self.assertEqual(node.language, "python")
        self.assertEqual(node.style, "source")
        self.assertEqual(node.listing_title, "My Title")
        self.assertEqual(node.attributes.get("doctest"), "True")

        # 2. Block-level title line style
        source_with_title_line = (
            ".Line Title\n[#my-id,source,python]\n----\ndef foo(): pass\n----\n"
        )
        ast_with_title_line = parse_to_ast(source_with_title_line)
        node_with_title_line = ast_with_title_line.blocks[0]
        self.assertEqual(node_with_title_line.listing_title, "Line Title")

        # 3. Mutability of properties
        node.id = "new-id"
        node.language = "ruby"
        node.style = "listing"
        self.assertEqual(node.attributes.get("id"), "new-id")
        self.assertEqual(node.attributes.get("language"), "ruby")
        self.assertEqual(node.attributes.get("style"), "listing")

    def test_section_parsing(self):
        source = "== Section 1\n\nThis is the first section.\n"
        ast = parse_to_ast(source).to_dict()
        section = ast["blocks"][0]
        self.assertEqual(section["name"], "section")
        self.assertEqual(section["title"][0]["value"], "Section 1")

    def test_nested_lists(self):
        source = "* level 1\n** level 2\n* back to 1\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "list")

    def test_admonitions_parameterized(self):
        cases = [
            ("NOTE", "note", "This is a note."),
            ("TIP", "tip", "Here's a helpful tip."),
            ("IMPORTANT", "important", "Pay attention to this."),
            ("WARNING", "warning", "Be careful here."),
            ("CAUTION", "caution", "Proceed with caution."),
            ("  NOTE  ", "note", "Content with whitespace in label."),
        ]
        for label, variant, content in cases:
            with self.subTest(variant=variant):
                source = f"[{label}]\n====\n{content}\n====\n"
                ast = parse_to_ast(source).to_dict()
                self.assertEqual(ast["blocks"][0]["name"], "admonition")
                self.assertEqual(ast["blocks"][0]["variant"], variant)

    def test_admonition_with_list(self):
        source = (
            "[NOTE]\n====\nConsider these points:\n\n"
            "- First point\n- Second point\n====\n"
        )
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        child_names = [c["name"] for c in admonition["blocks"]]
        self.assertIn("paragraph", child_names)
        self.assertIn("list", child_names)

    def test_admonition_empty(self):
        source = "[NOTE]\n====\n====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "admonition")

    def test_admonition_nesting_parameterized(self):
        cases = [
            (
                "paragraphs",
                "[NOTE]\n====\nFirst paragraph.\n\nSecond paragraph.\n====\n",
                lambda self, ast: self.assertGreaterEqual(
                    len(
                        [
                            c
                            for c in ast["blocks"][0]["blocks"]
                            if c["name"] == "paragraph"
                        ]
                    ),
                    2,
                ),
            ),
            (
                "multiple",
                "[NOTE]\n====\nFirst note.\n====\n\n[WARNING]\n====\nA warning.\n====\n",
                lambda self, ast: self.assertEqual(
                    len([c for c in ast["blocks"] if c["name"] == "admonition"]), 2
                ),
            ),
            (
                "nested_admonition",
                "****\n[NOTE]\n====\nNote inside sidebar\n====\n****\n",
                lambda self, ast: self.assertEqual(
                    ast["blocks"][0]["blocks"][0]["name"], "admonition"
                ),
            ),
            (
                "nested_sidebar",
                "[TIP]\n====\n****\nSidebar inside tip\n****\n====\n",
                lambda self, ast: self.assertEqual(
                    ast["blocks"][0]["blocks"][0]["name"], "sidebar"
                ),
            ),
        ]
        for name, source, validator in cases:
            with self.subTest(case=name):
                ast = parse_to_ast(source).to_dict()
                validator(self, ast)

    def test_admonition_with_literal_block(self):
        source = (
            "[TIP]\n====\nHere's some code:\n\n----\ndef hello():\n"
            '    print("world")\n----\n====\n'
        )
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        child_names = [c["name"] for c in admonition["blocks"]]
        self.assertIn("paragraph", child_names)
        self.assertIn("listing", child_names)

    def test_admonition_in_section(self):
        source = "== Section Title\n\n[NOTE]\n====\nNote in a section.\n====\n"
        ast = parse_to_ast(source).to_dict()
        section = ast["blocks"][0]
        admonitions = [c for c in section["blocks"] if c["name"] == "admonition"]
        self.assertGreaterEqual(len(admonitions), 1)

    def test_sidebar_basic(self):
        source = "****\nThis is a sidebar.\n****\n"
        ast = parse_to_ast(source).to_dict()
        sidebar = ast["blocks"][0]
        self.assertEqual(sidebar["name"], "sidebar")
        self.assertEqual(
            sidebar["blocks"][0]["inlines"][0]["value"], "This is a sidebar."
        )

    def test_sidebar_nested_content(self):
        source = "****\nSidebar paragraph.\n\n- List item\n\n----\ncode\n----\n****\n"
        ast = parse_to_ast(source).to_dict()
        sidebar = ast["blocks"][0]
        self.assertEqual(sidebar["name"], "sidebar")
        child_names = [c["name"] for c in sidebar["blocks"]]
        self.assertIn("paragraph", child_names)
        self.assertIn("list", child_names)
        self.assertIn("listing", child_names)

    def test_sidebar_empty(self):
        source = "****\n****\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "sidebar")

    def test_sidebar_multiple(self):
        source = "****\nContent 1\n****\n\n****\nContent 2\n****\n"
        ast = parse_to_ast(source).to_dict()
        sidebars = [c for c in ast["blocks"] if c["name"] == "sidebar"]
        self.assertEqual(len(sidebars), 2)

    def test_example_block_basic(self):
        source = "====\nThis is an example block.\n====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "example")

    def test_example_block_nesting(self):
        source = "====\n****\nSidebar in example\n****\n====\n"
        ast = parse_to_ast(source).to_dict()
        example = ast["blocks"][0]
        self.assertEqual(example["blocks"][0]["name"], "sidebar")

    def test_nested_examples_variable_length(self):
        source = "=====\n====\nnested\n====\n=====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "example")
        self.assertEqual(ast["blocks"][0]["blocks"][0]["name"], "example")

    def test_admonition_vs_example(self):
        source_adm = "[NOTE]\n====\nNote content\n====\n"
        ast_adm = parse_to_ast(source_adm).to_dict()
        self.assertEqual(ast_adm["blocks"][0]["name"], "admonition")

        source_ex = "====\nExample content\n====\n"
        ast_ex = parse_to_ast(source_ex).to_dict()
        self.assertEqual(ast_ex["blocks"][0]["name"], "example")

    def test_attribute_entry(self):
        source = ":author: Michael Bernstein\n\n"
        ast = parse_to_ast(source).to_dict()
        attr = ast["blocks"][0]
        self.assertEqual(attr["name"], "attribute_entry")
        self.assertEqual(attr["attribute_name"], "author")
        self.assertEqual(attr["value"], "Michael Bernstein")

    def test_attribute_entry_empty(self):
        source = ":myattr:\n\n"
        ast = parse_to_ast(source).to_dict()
        attr = ast["blocks"][0]
        self.assertEqual(attr["name"], "attribute_entry")
        self.assertEqual(attr["attribute_name"], "myattr")
        self.assertEqual(attr["value"], "")

    def test_nested_description_list(self):
        source = "Operating Systems::\n  Linux:::\n    Fedora::\n      Desktop\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        expected = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "descriptionList",
                    "type": "block",
                    "items": [
                        {
                            "name": "descriptionListItem",
                            "type": "block",
                            "terms": [
                                {
                                    "name": "descriptionListTerm",
                                    "type": "inline",
                                    "inlines": [
                                        {
                                            "name": "text",
                                            "type": "string",
                                            "value": "Operating Systems",
                                        }
                                    ],
                                }
                            ],
                            "blocks": [
                                {
                                    "name": "descriptionList",
                                    "type": "block",
                                    "items": [
                                        {
                                            "name": "descriptionListItem",
                                            "type": "block",
                                            "terms": [
                                                {
                                                    "name": "descriptionListTerm",
                                                    "type": "inline",
                                                    "inlines": [
                                                        {
                                                            "name": "text",
                                                            "type": "string",
                                                            "value": "Linux",
                                                        }
                                                    ],
                                                }
                                            ],
                                            "blocks": [
                                                {
                                                    "name": "descriptionList",
                                                    "type": "block",
                                                    "items": [
                                                        {
                                                            "name": "descriptionListItem",
                                                            "type": "block",
                                                            "terms": [
                                                                {
                                                                    "name": "descriptionListTerm",
                                                                    "type": "inline",
                                                                    "inlines": [
                                                                        {
                                                                            "name": "text",
                                                                            "type": "string",
                                                                            "value": "Fedora",
                                                                        }
                                                                    ],
                                                                }
                                                            ],
                                                            "blocks": [
                                                                {
                                                                    "name": "paragraph",
                                                                    "type": "block",
                                                                    "inlines": [
                                                                        {
                                                                            "name": "text",
                                                                            "type": "string",
                                                                            "value": "Desktop",
                                                                        }
                                                                    ],
                                                                }
                                                            ],
                                                        }
                                                    ],
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected)

    def test_advanced_table_cells(self):
        source = """
[cols="1,1"]
|===
| cell 1 | cell 2
2+^s| merged bold
|===
"""
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        table = ast["blocks"][0]
        self.assertEqual(table["name"], "table")

        # Row 1
        row1 = table["rows"][0]
        self.assertEqual(len(row1["cells"]), 2)
        cell1 = row1["cells"][0]
        self.assertEqual(cell1.get("colspan", 1), 1)
        self.assertEqual(cell1.get("rowspan", 1), 1)

        # Row 2
        row2 = table["rows"][1]
        self.assertEqual(len(row2["cells"]), 1)
        merged_cell = row2["cells"][0]
        self.assertEqual(merged_cell["colspan"], 2)
        self.assertEqual(merged_cell.get("rowspan", 1), 1)
        self.assertEqual(merged_cell["align"], "center")
        self.assertEqual(merged_cell["align"], "center")
        self.assertEqual(merged_cell["style"], "s")

    def test_block_positional_attributes(self):
        source = """
[source,python,my-custom-test]
----
print("hello")
----
"""
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "listing")
        # Legacy mappings
        self.assertEqual(block["attributes"]["style"], "source")
        self.assertEqual(block["attributes"]["language"], "python")
        # 1-based string keys
        self.assertEqual(block["attributes"]["1"], "source")
        self.assertEqual(block["attributes"]["2"], "python")
        self.assertEqual(block["attributes"]["3"], "my-custom-test")
        # Positional list key
        self.assertEqual(
            block["attributes"]["positional"], ["source", "python", "my-custom-test"]
        )

    def test_block_positional_attributes_with_empty_slots(self):
        source = """
[, ,third-val]
====
Empty slots test
====
"""
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        block = ast["blocks"][0]
        self.assertEqual(block["attributes"]["3"], "third-val")
        self.assertNotIn("1", block["attributes"])
        self.assertNotIn("2", block["attributes"])
        self.assertEqual(block["attributes"]["positional"], ["third-val"])

    def test_block_positional_attributes_mixed(self):
        source = """
[source,foo=bar,python]
----
print("mixed")
----
"""
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        block = ast["blocks"][0]
        self.assertEqual(block["attributes"]["1"], "source")
        self.assertEqual(block["attributes"]["foo"], "bar")
        self.assertEqual(block["attributes"]["3"], "python")
        self.assertNotIn("2", block["attributes"])
        self.assertEqual(block["attributes"]["positional"], ["source", "python"])

    def test_consecutive_block_attributes_merging(self):
        source = """
[.role-one]
[source,python]
----
print("test")
----
"""
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "listing")
        self.assertEqual(block["attributes"]["role"], "role-one")
        self.assertEqual(block["attributes"]["style"], "source")
        self.assertEqual(block["attributes"]["language"], "python")

    def test_consecutive_block_attributes_merging_three_lines(self):
        source = """
[#my-id]
[.role-one]
[source,python]
----
print("test")
----
"""
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "listing")
        self.assertEqual(block["attributes"]["id"], "my-id")
        self.assertEqual(block["attributes"]["role"], "role-one")
        self.assertEqual(block["attributes"]["style"], "source")
        self.assertEqual(block["attributes"]["language"], "python")

    def test_missing_trailing_newline(self):
        # Paragraph lacking trailing newline
        source1 = "= Document\n\nParagraph content"
        ast1 = self._strip_locations(parse_to_ast(source1).to_dict())
        self.assertEqual(ast1["blocks"][0]["name"], "paragraph")
        self.assertEqual(ast1["blocks"][0]["inlines"][0]["value"], "Paragraph content")

        # Listing block lacking trailing newline
        source2 = "= Document\n\n[source,python]\n----\nx = 1\n----"
        ast2 = self._strip_locations(parse_to_ast(source2).to_dict())
        self.assertEqual(ast2["blocks"][0]["name"], "listing")

    def test_invalid_syntax_raises_asciidoc_syntax_error(self):
        from unittest.mock import patch

        from lark.exceptions import UnexpectedInput

        from asciidoctrine import AsciiDocSyntaxError, parse_to_ast

        # Create a mock UnexpectedInput exception
        class MockUnexpectedInput(UnexpectedInput):
            def __init__(self):
                self.line = 5
                self.column = 10

            def get_context(self, text, span=40):
                return "mock_context_info"

        with patch("lark.Lark.parse", side_effect=MockUnexpectedInput()):
            with self.assertRaises(AsciiDocSyntaxError) as context:
                parse_to_ast("dummy source")

        err = context.exception
        self.assertEqual(err.line, 5)
        self.assertEqual(err.column, 10)
        self.assertEqual(err.context, "mock_context_info")
        self.assertIn("Syntax error at line 5, column 10", str(err))


if __name__ == "__main__":
    unittest.main()
