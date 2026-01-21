"""
Tests for block-level parsing in AsciiDoc.
"""

import os
import shutil
import unittest

from asciidoc_parser.lark_parser import parse_to_ast


class TestBlocks(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.join(os.path.dirname(__file__), "temp_fixtures_blocks")
        os.makedirs(self.base_dir, exist_ok=True)
        with open(os.path.join(self.base_dir, "included.adoc"), "w") as f:
            f.write("This is an *included* file.\n\n* With a list item.\n")

    def tearDown(self):
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)

    def test_paragraph(self):
        source = "Hello, world.\n"
        ast = parse_to_ast(source).to_dict()
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

    def test_variable_length_listing(self):
        source = "-----\nlisting\n-----\n"
        ast = parse_to_ast(source).to_dict()
        expected = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "listing",
                    "type": "block",
                    "form": "delimited",
                    "delimiter": "-----",
                    "inlines": [{"name": "text", "type": "string", "value": "listing"}],
                }
            ],
        }
        self.assertEqual(ast, expected)

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

    def test_literal_block(self):
        source = "----\nThis is a literal block.\n----\n"
        ast = parse_to_ast(source).to_dict()
        literal = ast["blocks"][0]
        self.assertEqual(literal["name"], "listing")
        self.assertIn("This is a literal block.", literal["inlines"][0]["value"])

    def test_source_block_attributes(self):
        source = "[source,python]\n----\ndef foo(): pass\n----\n"
        ast = parse_to_ast(source).to_dict()
        literal = ast["blocks"][0]
        self.assertEqual(literal["name"], "listing")
        self.assertEqual(
            literal["attributes"], {"style": "source", "language": "python"}
        )

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

    def test_admonition_note(self):
        source = "[NOTE]\n====\nThis is a note.\n====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "admonition")
        self.assertEqual(ast["blocks"][0]["variant"], "note")

    def test_admonition_tip(self):
        source = "[TIP]\n====\nHere's a helpful tip.\n====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "admonition")
        self.assertEqual(ast["blocks"][0]["variant"], "tip")

    def test_admonition_important(self):
        source = "[IMPORTANT]\n====\nPay attention to this.\n====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "admonition")
        self.assertEqual(ast["blocks"][0]["variant"], "important")

    def test_admonition_warning(self):
        source = "[WARNING]\n====\nBe careful here.\n====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "admonition")
        self.assertEqual(ast["blocks"][0]["variant"], "warning")

    def test_admonition_caution(self):
        source = "[CAUTION]\n====\nProceed with caution.\n====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "admonition")
        self.assertEqual(ast["blocks"][0]["variant"], "caution")

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

    def test_admonition_multiple_paragraphs(self):
        source = "[NOTE]\n====\nFirst paragraph.\n\nSecond paragraph.\n====\n"
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        paragraphs = [c for c in admonition["blocks"] if c["name"] == "paragraph"]
        self.assertGreaterEqual(len(paragraphs), 2)

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

    def test_admonition_whitespace_in_label(self):
        source = "[  NOTE  ]\n====\nContent with whitespace in label.\n====\n"
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "admonition")
        self.assertEqual(ast["blocks"][0]["variant"], "note")

    def test_multiple_admonitions(self):
        source = (
            "[NOTE]\n====\nFirst note.\n====\n\n[WARNING]\n====\nA warning.\n====\n"
        )
        ast = parse_to_ast(source).to_dict()
        admonitions = [c for c in ast["blocks"] if c["name"] == "admonition"]
        self.assertEqual(len(admonitions), 2)

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

    def test_sidebar_nested_admonition(self):
        source = "****\n[NOTE]\n====\nNote inside sidebar\n====\n****\n"
        ast = parse_to_ast(source).to_dict()
        sidebar = ast["blocks"][0]
        admonition = sidebar["blocks"][0]
        self.assertEqual(admonition["name"], "admonition")

    def test_admonition_nested_sidebar(self):
        source = "[TIP]\n====\n****\nSidebar inside tip\n****\n====\n"
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        sidebar = admonition["blocks"][0]
        self.assertEqual(sidebar["name"], "sidebar")

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

    def test_preprocessor_integration(self):
        source = "include::included.adoc[]"
        ast = parse_to_ast(source, base_dir=self.base_dir).to_dict()
        self.assertEqual(len(ast["blocks"]), 2)
        self.assertEqual(ast["blocks"][1]["name"], "list")


if __name__ == "__main__":
    unittest.main()
