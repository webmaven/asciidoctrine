"""
Tests for the AsciiDoc parser.
"""

import os
import shutil
import unittest

from asciidoc_parser.lark_parser import parse_to_ast


class ParserTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test fixtures
        self.base_dir = os.path.join(os.path.dirname(__file__), "temp_fixtures")
        os.makedirs(self.base_dir, exist_ok=True)
        with open(os.path.join(self.base_dir, "included.adoc"), "w") as f:
            f.write("This is an *included* file.\n\n* With a list item.\n")

    def tearDown(self):
        # Clean up the temporary directory
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

    def test_bold(self):
        source = "This is *bold* text.\n"
        ast = parse_to_ast(source).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "paragraph",
                    "type": "block",
                    "inlines": [
                        {"name": "text", "type": "string", "value": "This is "},
                        {
                            "name": "span",
                            "type": "inline",
                            "variant": "strong",
                            "form": "constrained",
                            "inlines": [
                                {"name": "text", "type": "string", "value": "bold"}
                            ],
                        },
                        {"name": "text", "type": "string", "value": " text."},
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_italic(self):
        source = "This is _italic_ text.\n"
        ast = parse_to_ast(source).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "paragraph",
                    "type": "block",
                    "inlines": [
                        {"name": "text", "type": "string", "value": "This is "},
                        {
                            "name": "span",
                            "type": "inline",
                            "variant": "emphasis",
                            "form": "constrained",
                            "inlines": [
                                {"name": "text", "type": "string", "value": "italic"}
                            ],
                        },
                        {"name": "text", "type": "string", "value": " text."},
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_monospace(self):
        source = "This is `monospace` text.\n"
        ast = parse_to_ast(source).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "paragraph",
                    "type": "block",
                    "inlines": [
                        {"name": "text", "type": "string", "value": "This is "},
                        {
                            "name": "span",
                            "type": "inline",
                            "variant": "code",
                            "form": "constrained",
                            "inlines": [
                                {"name": "text", "type": "string", "value": "monospace"}
                            ],
                        },
                        {"name": "text", "type": "string", "value": " text."},
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_ulist(self):
        source = "* one\n* two\n* three\n"
        ast = parse_to_ast(source).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "list",
                    "type": "block",
                    "variant": "unordered",
                    "marker": "*",
                    "items": [
                        {
                            "name": "listItem",
                            "type": "block",
                            "marker": "*",
                            "principal": [
                                {"name": "text", "type": "string", "value": "one"}
                            ],
                            "blocks": [],
                        },
                        {
                            "name": "listItem",
                            "type": "block",
                            "marker": "*",
                            "principal": [
                                {"name": "text", "type": "string", "value": "two"}
                            ],
                            "blocks": [],
                        },
                        {
                            "name": "listItem",
                            "type": "block",
                            "marker": "*",
                            "principal": [
                                {"name": "text", "type": "string", "value": "three"}
                            ],
                            "blocks": [],
                        },
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_olist(self):
        source = "1. one\n2. two\n3. three\n"
        ast = parse_to_ast(source).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "list",
                    "type": "block",
                    "variant": "ordered",
                    "marker": "1.",
                    "items": [
                        {
                            "name": "listItem",
                            "type": "block",
                            "marker": "1.",
                            "principal": [
                                {"name": "text", "type": "string", "value": "one"}
                            ],
                            "blocks": [],
                        },
                        {
                            "name": "listItem",
                            "type": "block",
                            "marker": "2.",
                            "principal": [
                                {"name": "text", "type": "string", "value": "two"}
                            ],
                            "blocks": [],
                        },
                        {
                            "name": "listItem",
                            "type": "block",
                            "marker": "3.",
                            "principal": [
                                {"name": "text", "type": "string", "value": "three"}
                            ],
                            "blocks": [],
                        },
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_literal_block(self):
        source = "----\nThis is a literal block.\n----\n"
        ast = parse_to_ast(source).to_dict()
        literal = ast["blocks"][0]
        self.assertEqual(literal["name"], "listing")
        # Content regex might capture newlines
        content = literal["inlines"][0]["value"]
        self.assertIn("This is a literal block.", content)
        self.assertEqual(literal.get("attributes", {}), {})

    def test_source_block_attributes(self):
        source = "[source,python]\n----\ndef foo(): pass\n----\n"
        ast = parse_to_ast(source).to_dict()
        literal = ast["blocks"][0]
        self.assertEqual(literal["name"], "listing")
        self.assertEqual(
            literal["attributes"], {"style": "source", "language": "python"}
        )
        content = literal["inlines"][0]["value"]
        self.assertIn("def foo(): pass", content)

    def test_section_parsing(self):
        source = "== Section 1\n\nThis is the first section.\n"
        ast = parse_to_ast(source).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "section",
                    "type": "block",
                    "level": 1,
                    "title": [{"name": "text", "type": "string", "value": "Section 1"}],
                    "blocks": [
                        {
                            "name": "paragraph",
                            "type": "block",
                            "inlines": [
                                {
                                    "name": "text",
                                    "type": "string",
                                    "value": "This is the first section.",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_symbols_in_word(self):
        # Ensure that characters like commas, periods, etc. don't break WORD
        source = "Hello, world! (tested)\n"
        ast = parse_to_ast(source).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "paragraph",
                    "type": "block",
                    "inlines": [
                        {
                            "name": "text",
                            "type": "string",
                            "value": "Hello, world! (tested)",
                        }
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_nested_lists(self):
        source = "* level 1\n** level 2\n* back to 1\n"
        ast = parse_to_ast(source).to_dict()
        # Verify structure via dict conversion
        self.assertEqual(ast["name"], "document")
        self.assertEqual(ast["blocks"][0]["name"], "list")

    def test_list_item_with_formatting(self):
        source = "* basic item\n* item with *bold* and _italic_\n"
        ast = parse_to_ast(source).to_dict()
        # Verify that the second item has inlines including bold and italic
        second_item = ast["blocks"][0]["items"][1]
        self.assertEqual(second_item["name"], "listItem")
        content_nodes = second_item["principal"]

        # Names: 'item with ', 'span', ' and ', 'span'
        names = [n["name"] for n in content_nodes]
        self.assertEqual(names.count("span"), 2)

    def test_admonition_note(self):
        source = "[NOTE]\n====\nThis is a note.\n====\n"
        ast = parse_to_ast(source).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "admonition",
                    "type": "block",
                    "variant": "note",
                    "form": "delimited",
                    "delimiter": "====",
                    "blocks": [
                        {
                            "name": "paragraph",
                            "type": "block",
                            "inlines": [
                                {
                                    "name": "text",
                                    "type": "string",
                                    "value": "This is a note.",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

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
            "[NOTE]\n"
            "====\n"
            "Consider these points:\n\n"
            "- First point\n"
            "- Second point\n"
            "====\n"
        )
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        self.assertEqual(admonition["name"], "admonition")
        self.assertEqual(admonition["variant"], "note")
        # Should have paragraph and list (may have blank lines between)
        child_names = [c["name"] for c in admonition["blocks"]]
        self.assertIn("paragraph", child_names)
        self.assertIn("list", child_names)

    def test_admonition_with_formatting(self):
        source = "[TIP]\n====\nUse *bold* and _italic_ formatting.\n====\n"
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        paragraph = admonition["blocks"][0]
        # Check that formatting is preserved
        names = [n["name"] for n in paragraph["inlines"]]
        self.assertEqual(names.count("span"), 2)

    def test_admonition_empty(self):
        source = "[NOTE]\n====\n====\n"
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        self.assertEqual(admonition["name"], "admonition")
        self.assertEqual(admonition["variant"], "note")
        # Empty admonition should have no blocks key or empty blocks
        blocks = admonition.get("blocks", [])
        self.assertTrue(
            len(blocks) == 0 or all(c["name"] == "blank_line" for c in blocks)
        )

    def test_admonition_multiple_paragraphs(self):
        source = "[NOTE]\n====\nFirst paragraph.\n\nSecond paragraph.\n====\n"
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        paragraphs = [c for c in admonition["blocks"] if c["name"] == "paragraph"]
        self.assertGreaterEqual(len(paragraphs), 2)

    def test_admonition_with_literal_block(self):
        source = (
            "[TIP]\n"
            "====\n"
            "Here's some code:\n\n"
            '----\ndef hello():\n    print("world")\n----\n'
            "====\n"
        )
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        child_names = [c["name"] for c in admonition["blocks"]]
        self.assertIn("paragraph", child_names)
        self.assertIn("listing", child_names)

    def test_admonition_whitespace_in_label(self):
        source = "[  NOTE  ]\n====\nContent with whitespace in label.\n====\n"
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        self.assertEqual(admonition["name"], "admonition")
        self.assertEqual(admonition["variant"], "note")

    def test_multiple_admonitions(self):
        source = (
            "[NOTE]\n====\nFirst note.\n====\n\n[WARNING]\n====\nA warning.\n====\n"
        )
        ast = parse_to_ast(source).to_dict()
        admonitions = [c for c in ast["blocks"] if c["name"] == "admonition"]
        self.assertEqual(len(admonitions), 2)
        self.assertEqual(admonitions[0]["variant"], "note")
        self.assertEqual(admonitions[1]["variant"], "warning")

    def test_admonition_in_section(self):
        source = "== Section Title\n\n[NOTE]\n====\nNote in a section.\n====\n"
        ast = parse_to_ast(source).to_dict()
        section = ast["blocks"][0]
        self.assertEqual(section["name"], "section")
        admonitions = [c for c in section["blocks"] if c["name"] == "admonition"]
        self.assertGreaterEqual(len(admonitions), 1)
        self.assertEqual(admonitions[0]["variant"], "note")

    def test_sidebar_basic(self):
        source = "****\nThis is a sidebar.\n****\n"
        ast = parse_to_ast(source).to_dict()
        sidebar = ast["blocks"][0]
        self.assertEqual(sidebar["name"], "sidebar")
        self.assertEqual(len(sidebar["blocks"]), 1)
        self.assertEqual(sidebar["blocks"][0]["name"], "paragraph")
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
        sidebar = ast["blocks"][0]
        # Should be empty or have blank lines, handle missing 'blocks' key safely
        blocks = sidebar.get("blocks", [])
        self.assertTrue(
            len(blocks) == 0 or all(c["name"] == "blank_line" for c in blocks)
        )

    def test_sidebar_multiple(self):
        source = "****\nContent 1\n****\n\n****\nContent 2\n****\n"
        ast = parse_to_ast(source).to_dict()
        sidebars = [c for c in ast["blocks"] if c["name"] == "sidebar"]
        self.assertEqual(len(sidebars), 2)

    def test_sidebar_nested_admonition(self):
        source = "****\n[NOTE]\n====\nNote inside sidebar\n====\n****\n"
        ast = parse_to_ast(source).to_dict()
        sidebar = ast["blocks"][0]
        self.assertEqual(sidebar["name"], "sidebar")
        admonition = sidebar["blocks"][0]
        self.assertEqual(admonition["name"], "admonition")
        self.assertEqual(admonition["variant"], "note")

    def test_admonition_nested_sidebar(self):
        source = "[TIP]\n====\n****\nSidebar inside tip\n****\n====\n"
        ast = parse_to_ast(source).to_dict()
        admonition = ast["blocks"][0]
        self.assertEqual(admonition["name"], "admonition")
        sidebar = admonition["blocks"][0]
        self.assertEqual(sidebar["name"], "sidebar")

    def test_example_block_basic(self):
        source = "====\nThis is an example block.\n====\n"
        ast = parse_to_ast(source).to_dict()
        example = ast["blocks"][0]
        self.assertEqual(example["name"], "example")
        self.assertEqual(len(example["blocks"]), 1)
        self.assertEqual(example["blocks"][0]["name"], "paragraph")

    def test_example_block_nesting(self):
        source = "====\n****\nSidebar in example\n****\n====\n"
        ast = parse_to_ast(source).to_dict()
        example = ast["blocks"][0]
        self.assertEqual(example["name"], "example")
        sidebar = example["blocks"][0]
        self.assertEqual(sidebar["name"], "sidebar")

    def test_admonition_vs_example(self):
        # NOTE + ==== -> Admonition
        source_adm = "[NOTE]\n====\nNote content\n====\n"
        ast_adm = parse_to_ast(source_adm).to_dict()
        self.assertEqual(ast_adm["blocks"][0]["name"], "admonition")

        # ==== alone -> Example
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

    def test_attribute_substitution(self):
        source = ":author: Michael\n\nHello {author}!\n"
        ast = parse_to_ast(source).to_dict()
        # blocks: [AttributeEntry, Paragraph]
        paragraph = ast["blocks"][1]
        self.assertEqual(paragraph["name"], "paragraph")
        text_node = paragraph["inlines"][0]
        self.assertEqual(text_node["value"], "Hello Michael!")

    def test_attribute_substitution_not_found(self):
        source = "Hello {unknown}!\n"
        ast = parse_to_ast(source).to_dict()
        paragraph = ast["blocks"][0]
        text_node = paragraph["inlines"][0]
        self.assertEqual(text_node["value"], "Hello {unknown}!")

    def test_attribute_substitution_in_title(self):
        source = ":project: AsciiDocParser\n\n== {project} Documentation\n"
        ast = parse_to_ast(source).to_dict()
        # blocks: [AttributeEntry, Section]
        section = ast["blocks"][1]
        self.assertEqual(section["name"], "section")
        title_node = section["title"]
        text_node = title_node[0]
        self.assertEqual(text_node["value"], "AsciiDocParser Documentation")

    def test_attribute_substitution_nested(self):
        source = ":project: AsciiDoc\n:tool: {project}Parser\n\nThis is {tool}.\n"
        ast = parse_to_ast(source).to_dict()
        # blocks: [Attr, Attr, Paragraph]
        paragraph = ast["blocks"][2]
        text_node = paragraph["inlines"][0]
        self.assertEqual(text_node["value"], "This is AsciiDocParser.")

    def test_attribute_with_inline_formatting(self):
        source = ":author: *Jane* _Smith_\n\nHello {author}!\n"
        ast = parse_to_ast(source).to_dict()
        paragraph = ast["blocks"][1]
        self.assertEqual(paragraph["name"], "paragraph")
        # Expected: Hello *Jane* _Smith_! -> Text, Span, Text, Span, Text
        self.assertEqual(len(paragraph["inlines"]), 5)
        self.assertEqual(paragraph["inlines"][0]["value"], "Hello ")
        self.assertEqual(paragraph["inlines"][1]["name"], "span")
        self.assertEqual(paragraph["inlines"][1]["inlines"][0]["value"], "Jane")
        self.assertEqual(paragraph["inlines"][2]["value"], " ")
        self.assertEqual(paragraph["inlines"][3]["name"], "span")
        self.assertEqual(paragraph["inlines"][3]["inlines"][0]["value"], "Smith")
        self.assertEqual(paragraph["inlines"][4]["value"], "!")

    def test_deeply_nested_attribute_substitution(self):
        source = ":a: 1\n:b: {a}{a}\n:c: {b}{b}\n\nResult is {c}.\n"
        ast = parse_to_ast(source).to_dict()
        paragraph = ast["blocks"][3]
        self.assertEqual(paragraph["inlines"][0]["value"], "Result is 1111.")

    def test_recursive_attribute_substitution(self):
        source = (
            ":project_name: Cool Project\n"
            ":doc_title: {project_name} Docs\n\n"
            "== {doc_title}\n"
        )
        ast = parse_to_ast(source).to_dict()
        section = ast["blocks"][2]
        title_node = section["title"]
        text_node = title_node[0]
        self.assertEqual(text_node["value"], "Cool Project Docs")

    def test_preprocessor_integration(self):
        source = "include::included.adoc[]"
        ast = parse_to_ast(source, base_dir=self.base_dir).to_dict()
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "paragraph",
                    "type": "block",
                    "inlines": [
                        {"name": "text", "type": "string", "value": "This is an "},
                        {
                            "name": "span",
                            "type": "inline",
                            "variant": "strong",
                            "form": "constrained",
                            "inlines": [
                                {"name": "text", "type": "string", "value": "included"}
                            ],
                        },
                        {"name": "text", "type": "string", "value": " file."},
                    ],
                },
                {
                    "name": "list",
                    "type": "block",
                    "variant": "unordered",
                    "marker": "*",
                    "items": [
                        {
                            "name": "listItem",
                            "type": "block",
                            "marker": "*",
                            "principal": [
                                {
                                    "name": "text",
                                    "type": "string",
                                    "value": "With a list item.",
                                }
                            ],
                            "blocks": [],
                        }
                    ],
                },
            ],
        }
        self.assertEqual(ast, expected_ast)


if __name__ == "__main__":
    unittest.main()
