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

    def test_list_continuation_parsing(self):
        source = (
            "* List item 1\n"
            "+\n"
            "This paragraph is continued under list item 1\n"
            "+\n"
            "This second paragraph is also continued!\n"
            "* List item 2\n"
            "** Nested list item 2a\n"
            "+\n"
            "This paragraph continues under 2a\n"
        )
        doc = parse_to_ast(source)
        ast = doc.to_dict()

        blocks = ast["blocks"]
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["name"], "list")

        items = blocks[0]["items"]
        self.assertEqual(len(items), 2)

        item1 = items[0]
        self.assertEqual(len(item1["blocks"]), 2)
        self.assertEqual(item1["blocks"][0]["name"], "paragraph")
        self.assertEqual(
            item1["blocks"][0]["inlines"][0]["value"],
            "This paragraph is continued under list item 1",
        )
        self.assertEqual(item1["blocks"][1]["name"], "paragraph")
        self.assertEqual(
            item1["blocks"][1]["inlines"][0]["value"],
            "This second paragraph is also continued!",
        )

        item2 = items[1]
        self.assertEqual(len(item2["blocks"]), 1)
        nested_list = item2["blocks"][0]
        self.assertEqual(nested_list["name"], "list")
        nested_item = nested_list["items"][0]
        self.assertEqual(nested_item["marker"], "**")

        self.assertEqual(len(nested_item["blocks"]), 1)
        self.assertEqual(nested_item["blocks"][0]["name"], "paragraph")
        self.assertEqual(
            nested_item["blocks"][0]["inlines"][0]["value"],
            "This paragraph continues under 2a",
        )

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

    def test_inline_colons_not_dlist(self):
        source = "A node representing an `include::` directive.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
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
                            "value": "A node representing an ",
                        },
                        {
                            "name": "span",
                            "type": "inline",
                            "variant": "code",
                            "form": "constrained",
                            "inlines": [
                                {"name": "text", "type": "string", "value": "include::"}
                            ],
                        },
                        {"name": "text", "type": "string", "value": " directive."},
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)

    def test_open_blocks_parsing(self):
        import warnings

        # 1. Legacy open block
        legacy_source = "--\nLegacy open block content.\n--\n"
        with self.assertWarns(DeprecationWarning):
            legacy_ast = parse_to_ast(legacy_source).to_dict()
        self.assertEqual(legacy_ast["blocks"][0]["name"], "open")
        self.assertEqual(legacy_ast["blocks"][0]["delimiter"], "--")
        self.assertEqual(legacy_ast["blocks"][0]["blocks"][0]["name"], "paragraph")

        # 2. Standard SDR-1 open block (4 tildes)
        standard_source = "~~~~\nStandard open block content.\n~~~~\n"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            standard_ast = parse_to_ast(standard_source).to_dict()
            deprecation_warnings = [
                warn
                for warning in w
                if (warn := getattr(warning, "message", warning))
                and issubclass(warning.category, DeprecationWarning)
            ]
            self.assertEqual(len(deprecation_warnings), 0)
        self.assertEqual(standard_ast["blocks"][0]["name"], "open")
        self.assertEqual(standard_ast["blocks"][0]["delimiter"], "~~~~")

        # 3. Long SDR-1 open block (7 tildes)
        long_source = "~~~~~~~\nLong open block.\n~~~~~~~\n"
        long_ast = parse_to_ast(long_source).to_dict()
        self.assertEqual(long_ast["blocks"][0]["name"], "open")
        self.assertEqual(long_ast["blocks"][0]["delimiter"], "~~~~~~~")

        # 4. Nested open blocks of varying length
        nested_source = "~~~~~~\n~~~~\nNested content\n~~~~\n~~~~~~\n"
        nested_ast = parse_to_ast(nested_source).to_dict()
        self.assertEqual(nested_ast["blocks"][0]["name"], "open")
        self.assertEqual(nested_ast["blocks"][0]["delimiter"], "~~~~~~")
        inner_open = nested_ast["blocks"][0]["blocks"][0]
        self.assertEqual(inner_open["name"], "open")
        self.assertEqual(inner_open["delimiter"], "~~~~")
        self.assertEqual(inner_open["blocks"][0]["name"], "paragraph")

        # 5. Nesting legacy inside standard and vice-versa
        mixed_nest_source = "~~~~\n--\nMixed nesting\n--\n~~~~\n"
        mixed_nest_ast = parse_to_ast(mixed_nest_source).to_dict()
        self.assertEqual(mixed_nest_ast["blocks"][0]["name"], "open")
        self.assertEqual(mixed_nest_ast["blocks"][0]["delimiter"], "~~~~")
        self.assertEqual(mixed_nest_ast["blocks"][0]["blocks"][0]["name"], "open")
        self.assertEqual(mixed_nest_ast["blocks"][0]["blocks"][0]["delimiter"], "--")

    def test_complex_code_listing_block(self):
        """
        Verify that a listing block containing complex python code with backticks,
        underscores, and asterisks is parsed as a single listing block,
        and is NOT split into normal paragraph/literal blocks.
        """
        source = """[source,python]
----
import sys
from typing import Dict, List, Any
from asciidoctrine import parse_to_ast
from asciidoctrine.resolver import ASGResolver

class MarkdownRenderer:
    \"\"\"
    A custom visitor class that traverses an AsciiDoctrine ASG dictionary
    and compiles it into standard Markdown.
    \"\"\"

    def render(self, node: Dict[str, Any]) -> str:
        if not node:
            return ""

        node_name = node.get("name", "")
        # Dynamically dispatch to render_<node_name> if it exists
        method_name = f"render_{node_name}"
        visitor = getattr(self, method_name, self.generic_render)
        return visitor(node)

    def generic_render(self, node: Dict[str, Any]) -> str:
        # Fallback for unhandled nodes: render child blocks if present
        result = []
        for block in node.get("blocks", []):
            result.append(self.render(block))
        return "\\n\\n".join(result)

    def render_document(self, node: Dict[str, Any]) -> str:
        # Render all children blocks in the document
        blocks = [self.render(b) for b in node.get("blocks", [])]
        return "\\n\\n".join(b for b in blocks if b)

    def render_section(self, node: Dict[str, Any]) -> str:
        # ASG sections have a "level" integer and a "title" list of inline nodes
        level = node.get("level", 1)
        # Markdown headings use '#' prefixes matching the level
        header_prefix = "#" * level

        # Render the section title inlines
        title_inlines = node.get("title", [])
        title_text = "".join(self.render(inline) for inline in title_inlines)

        # Render child blocks of this section
        child_blocks = [self.render(b) for b in node.get("blocks", [])]
        rendered_children = "\\n\\n".join(b for b in child_blocks if b)

        return f"{header_prefix} {title_text}\\n\\n{rendered_children}".strip()

    def render_paragraph(self, node: Dict[str, Any]) -> str:
        # Render all inline children inside the paragraph
        inlines = [self.render(i) for i in node.get("inlines", [])]
        return "".join(inlines)

    def render_text(self, node: Dict[str, Any]) -> str:
        # Simple leaf text node
        return node.get("value", "")

    def render_span(self, node: Dict[str, Any]) -> str:
        # Spans represent formatting wraps like bold, italic, or monospace
        variant = node.get("variant", "text")
        inlines = [self.render(i) for i in node.get("inlines", [])]
        content = "".join(inlines)

        if variant == "strong":
            return f"**{content}**"
        elif variant == "emphasis":
            return f"*{content}*"
        elif variant == "code":
            return f"`{content}`"
        return content

    def render_listing(self, node: Dict[str, Any]) -> str:
        # Listing/source block representation
        lang = node.get("attributes", {}).get("language", "")
        # Listing contents are list of inline text nodes
        inlines = [self.render(i) for i in node.get("inlines", [])]
        code_content = "".join(inlines).strip()
        return f"```{lang}\\n{code_content}\\n```"

    def render_list(self, node: Dict[str, Any]) -> str:
        # Unordered or ordered list container
        variant = node.get("variant", "unordered")
        items = [self.render_list_item(item, variant, i) for i, item in enumerate(node.get("items", []))]
        return "\\n".join(items)

    def render_list_item(self, item: Dict[str, Any], variant: str, index: int) -> str:
        # Render principal text content of list item
        principal_nodes = item.get("principal", [])
        principal_text = "".join(self.render(p) for principal_nodes in principal_nodes for p in (principal_nodes if isinstance(principal_nodes, list) else [principal_nodes]))
        
        # Render any nested sub-blocks inside list item
        sub_blocks = [self.render(b) for b in item.get("blocks", [])]
        rendered_sub = "\\n  ".join(b for b in sub_blocks if b)
        
        prefix = "1." if variant == "ordered" else "*"
        item_text = f"{prefix} {principal_text}"
        if rendered_sub:
            item_text += f"\\n  {rendered_sub}"
        return item_text
----
"""
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(len(ast["blocks"]), 1)
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "listing")
        self.assertEqual(block["form"], "delimited")
        self.assertEqual(block["attributes"]["language"], "python")

    def test_nested_listing_different_lengths(self) -> None:
        source = """[source,asciidoc]
-----
[source,python]
----
print("inner")
----
-----"""
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(len(ast["blocks"]), 1)
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "listing")
        self.assertEqual(block["attributes"]["style"], "source")
        self.assertEqual(block["attributes"]["language"], "asciidoc")
        self.assertEqual(block["delimiter"], "-----")
        self.assertIn(
            '[source,python]\n----\nprint("inner")\n----', block["inlines"][0]["value"]
        )

    def test_nested_literal_different_lengths(self) -> None:
        source = """[style=literal]
.....
[style=another]
....
inner literal
....
....."""
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(len(ast["blocks"]), 1)
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "literal")
        self.assertEqual(block["delimiter"], ".....")
        self.assertIn(
            "[style=another]\n....\ninner literal\n....", block["inlines"][0]["value"]
        )

    def test_nested_passthrough_different_lengths(self) -> None:
        source = """+++++
++++
inner passthrough
++++
+++++"""
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(len(ast["blocks"]), 1)
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "passthrough")
        self.assertEqual(block["delimiter"], "+++++")
        self.assertIn("++++\ninner passthrough\n++++", block["inlines"][0]["value"])

    def test_delimited_comments(self) -> None:
        # 1. Basic parsing
        source = """////
This is a comment.
It should be parsed.
////"""
        doc = parse_to_ast(source)
        ast = doc.to_dict()
        self.assertEqual(len(ast["blocks"]), 1)
        comment_block = ast["blocks"][0]
        self.assertEqual(comment_block["name"], "comment")
        self.assertEqual(comment_block["type"], "block")
        self.assertEqual(
            comment_block["value"], "This is a comment.\nIt should be parsed."
        )

        # 2. ASG resolution (comments should be filtered out)
        from asciidoctrine.resolver import ASGResolver

        resolved_ast = ASGResolver(doc).resolve(doc)
        self.assertEqual(len(resolved_ast["blocks"]), 0)

    def test_collapsible_block(self) -> None:
        source = """.Summary Title
[%collapsible]
====
This content is collapsible.
====
"""
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(len(ast["blocks"]), 1)
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "collapsible")
        self.assertEqual(block["type"], "block")
        self.assertEqual(block["title"]["name"], "title")
        self.assertEqual(block["title"]["inlines"][0]["value"], "Summary Title")
        self.assertEqual(block["blocks"][0]["name"], "paragraph")
        self.assertEqual(
            block["blocks"][0]["inlines"][0]["value"], "This content is collapsible."
        )

        # Test alternative syntax: style="collapsible"
        source2 = """[collapsible]
====
Alternative collapsible.
====
"""
        ast2 = parse_to_ast(source2).to_dict()
        self.assertEqual(ast2["blocks"][0]["name"], "collapsible")

    def test_extended_delimiters_parsing(self):
        source = """*****
Sidebar with 5 asterisks
*****

______
Quote with 6 underscores
______

~~~~~
Open block with 5 tildes
~~~~~
"""
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(len(ast["blocks"]), 3)

        sb = ast["blocks"][0]
        self.assertEqual(sb["name"], "sidebar")
        self.assertEqual(sb["delimiter"], "*****")

        q = ast["blocks"][1]
        self.assertEqual(q["name"], "quote")
        self.assertEqual(q["delimiter"], "______")

        op = ast["blocks"][2]
        self.assertEqual(op["name"], "open")
        self.assertEqual(op["delimiter"], "~~~~~")

    def test_page_break(self):
        source = """First paragraph.

<<<

Second paragraph.
"""
        doc = parse_to_ast(source)
        ast = self._strip_locations(doc.to_dict())
        self.assertEqual(len(ast["blocks"]), 3)
        self.assertEqual(ast["blocks"][0]["name"], "paragraph")
        self.assertEqual(ast["blocks"][1]["name"], "page_break")
        self.assertEqual(ast["blocks"][1]["type"], "block")
        self.assertEqual(ast["blocks"][2]["name"], "paragraph")

        # Standalone page break
        source_standalone = "<<<\n"
        doc_standalone = parse_to_ast(source_standalone)
        ast_standalone = self._strip_locations(doc_standalone.to_dict())
        self.assertEqual(len(ast_standalone["blocks"]), 1)
        self.assertEqual(ast_standalone["blocks"][0]["name"], "page_break")
        self.assertEqual(ast_standalone["blocks"][0]["type"], "block")

        # Page break with longer delimiter (e.g. <<<<)
        source_long = "Para 1\n\n<<<<\n\nPara 2\n"
        doc_long = parse_to_ast(source_long)
        ast_long = self._strip_locations(doc_long.to_dict())
        self.assertEqual(len(ast_long["blocks"]), 3)
        self.assertEqual(ast_long["blocks"][1]["name"], "page_break")

        # Page break location tracking
        pb_node = doc.blocks[1]
        self.assertIsNotNone(pb_node.location)
        self.assertEqual(pb_node.location[0]["line"], 3)

        # ASG Resolver preserves page break
        from asciidoctrine.resolver import ASGResolver

        resolved = ASGResolver(doc).resolve(doc)
        self.assertEqual(len(resolved["blocks"]), 3)
        self.assertEqual(resolved["blocks"][1]["name"], "page_break")

    def test_quote_and_verse_attribution_and_citetitle(self):
        from asciidoctrine.resolver import ASGResolver

        # 1. Delimited quote with positional attributes [quote, author, title]
        source_quote_pos = (
            '[quote, Antoine de Saint-Exupéry, "Airman\'s Odyssey"]\n'
            "____\n"
            "It is in the compelling zest of high adventure...\n"
            "____\n"
        )
        doc = parse_to_ast(source_quote_pos)
        ast = self._strip_locations(doc.to_dict())
        quote_node = ast["blocks"][0]
        self.assertEqual(quote_node["name"], "quote")
        self.assertEqual(quote_node["attribution"], "Antoine de Saint-Exupéry")
        self.assertEqual(quote_node["citetitle"], "Airman's Odyssey")

        asg = ASGResolver(doc).resolve(doc)
        asg_quote = asg["blocks"][0]
        self.assertEqual(asg_quote["name"], "quote")
        self.assertEqual(asg_quote["attribution"], "Antoine de Saint-Exupéry")
        self.assertEqual(asg_quote["citetitle"], "Airman's Odyssey")

        # 2. Delimited quote with named attributes [attribution="...", citetitle="..."]
        source_quote_named = (
            '[attribution="Albert Einstein", citetitle="Relativity"]\n'
            "____\n"
            "Imagination is more important than knowledge.\n"
            "____\n"
        )
        doc_named = parse_to_ast(source_quote_named)
        asg_named = ASGResolver(doc_named).resolve(doc_named)
        quote_named = asg_named["blocks"][0]
        self.assertEqual(quote_named["name"], "quote")
        self.assertEqual(quote_named["attribution"], "Albert Einstein")
        self.assertEqual(quote_named["citetitle"], "Relativity")

        # 3. Delimited verse with positional attributes [verse, author, title]
        source_verse_pos = (
            '[verse, Carl Sandburg, "Fog"]\n'
            "____\n"
            "The fog comes\n"
            "on little cat feet.\n"
            "____\n"
        )
        doc_verse = parse_to_ast(source_verse_pos)
        asg_verse = ASGResolver(doc_verse).resolve(doc_verse)
        verse_node = asg_verse["blocks"][0]
        self.assertEqual(verse_node["name"], "verse")
        self.assertEqual(verse_node["attribution"], "Carl Sandburg")
        self.assertEqual(verse_node["citetitle"], "Fog")

        # 4. Paragraph quote with positional attributes
        source_para_quote = (
            "[quote, Douglas Adams, The Hitchhiker's Guide to the Galaxy]\n"
            "Don't Panic.\n"
        )
        doc_pq = parse_to_ast(source_para_quote)
        asg_pq = ASGResolver(doc_pq).resolve(doc_pq)
        pq_node = asg_pq["blocks"][0]
        self.assertEqual(pq_node["name"], "quote")
        self.assertEqual(pq_node["attribution"], "Douglas Adams")
        self.assertEqual(pq_node["citetitle"], "The Hitchhiker's Guide to the Galaxy")

    def test_dlist_continuation_multiple_blocks(self):
        source = (
            "AST (Abstract Syntax Tree)::\n"
            "Raw hierarchical parse tree generated directly by Lark grammar rules.\n"
            "+\n"
            "It preserves concrete syntax tokens and source offsets before resolution.\n"
        )
        doc = parse_to_ast(source)
        ast = doc.to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "descriptionList")
        item = ast["blocks"][0]["items"][0]
        self.assertEqual(len(item["blocks"]), 2)
        self.assertEqual(item["blocks"][0]["name"], "paragraph")
        self.assertEqual(
            item["blocks"][0]["inlines"][0]["value"],
            "Raw hierarchical parse tree generated directly by Lark grammar rules.",
        )
        self.assertEqual(item["blocks"][1]["name"], "paragraph")
        self.assertEqual(
            item["blocks"][1]["inlines"][0]["value"],
            "It preserves concrete syntax tokens and source offsets before resolution.",
        )

    def test_listing_block_inline_callouts_explicit(self):
        source = "[source,python]\n----\nimport os # <1>\nsys.exit(0) # <2> <3>\n----\n"
        doc = parse_to_ast(source)
        ast = self._strip_locations(doc.to_dict())
        listing = ast["blocks"][0]
        self.assertEqual(listing["name"], "listing")
        expected_inlines = [
            {"name": "text", "type": "string", "value": "import os"},
            {"name": "callout", "type": "inline", "value": 1},
            {"name": "text", "type": "string", "value": "\nsys.exit(0)"},
            {"name": "callout", "type": "inline", "value": 2},
            {"name": "callout", "type": "inline", "value": 3},
        ]
        self.assertEqual(listing["inlines"], expected_inlines)

    def test_listing_block_inline_callouts_auto_and_comments(self):
        source = (
            "----\n"
            "line 1 // <.>\n"
            "line 2 /* <5> */\n"
            "line 3 <!-- <.> -->\n"
            "line 4 <!--7-->\n"
            "----\n"
        )
        doc = parse_to_ast(source)
        ast = self._strip_locations(doc.to_dict())
        listing = ast["blocks"][0]
        self.assertEqual(listing["name"], "listing")
        expected_inlines = [
            {"name": "text", "type": "string", "value": "line 1"},
            {"name": "callout", "type": "inline", "value": 1},
            {"name": "text", "type": "string", "value": "\nline 2"},
            {"name": "callout", "type": "inline", "value": 5},
            {"name": "text", "type": "string", "value": "\nline 3"},
            {"name": "callout", "type": "inline", "value": 6},
            {"name": "text", "type": "string", "value": "\nline 4"},
            {"name": "callout", "type": "inline", "value": 7},
        ]
        self.assertEqual(listing["inlines"], expected_inlines)

    def test_table_with_asciidoc_cells_containing_listing_blocks(self):
        source = """[cols="1,1"]
|===
| Problematic | Correct

a|
[source,python]
----
def foo():
    pass
----

a|
[source,python]
----
def bar():
    pass
----
|===
"""
        doc = parse_to_ast(source)
        ast = self._strip_locations(doc.to_dict())
        self.assertEqual(len(ast["blocks"]), 1)
        table = ast["blocks"][0]
        self.assertEqual(table["name"], "table")
        self.assertEqual(len(table["rows"]), 2)
        # Row 1 has 2 header/text cells
        row1 = table["rows"][0]
        self.assertEqual(len(row1["cells"]), 2)
        # Row 2 has 2 AsciiDoc cells containing listing blocks
        row2 = table["rows"][1]
        self.assertEqual(len(row2["cells"]), 2)
        cell1 = row2["cells"][0]
        self.assertEqual(cell1["style"], "a")
        self.assertEqual(len(cell1["blocks"]), 1)
        self.assertEqual(cell1["blocks"][0]["name"], "listing")
        cell2 = row2["cells"][1]
        self.assertEqual(cell2["style"], "a")
        self.assertEqual(len(cell2["blocks"]), 1)
        self.assertEqual(cell2["blocks"][0]["name"], "listing")


if __name__ == "__main__":
    unittest.main()


def test_parsed_listing_block_callouts():
    """Integration: callout markers inside a real parsed listing block are correctly split."""
    source = (
        "[source,ruby]\n"
        "----\n"
        "require 'json' # <1>\n"
        "puts JSON.generate({ok: true}) # <2>\n"
        "----\n"
    )
    doc = parse_to_ast(source)
    listing = doc.blocks[0]
    assert len(listing.inlines) == 4
    assert listing.inlines[0].value == "require 'json'"
    assert listing.inlines[1].value == 1
    assert listing.inlines[2].value == "\nputs JSON.generate({ok: true})"
    assert listing.inlines[3].value == 2
    assert listing.callouts == {1: [1], 2: [2]}
    assert listing.stripped_code == "require 'json'\nputs JSON.generate({ok: true})"


def test_table_inside_listing_block_remains_literal():
    from asciidoctrine.nodes import Listing

    content = """[source,asciidoc]
----
[cols="1,2"]
|===
| A | B
| 1 | 2
|===
----"""
    doc = parse_to_ast(content)
    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Listing)
    assert "|===" in doc.blocks[0].code
    assert "ASCIIDOCTRINE_OUTER" not in doc.blocks[0].code


def test_table_inside_literal_block_remains_literal():
    from asciidoctrine.nodes import Literal

    content = """....
|===
| A | B
|===
...."""
    doc = parse_to_ast(content)
    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Literal)
    assert "|===" in doc.blocks[0].code
    assert "ASCIIDOCTRINE_OUTER" not in doc.blocks[0].code


def test_table_inside_passthrough_block_remains_literal():
    from asciidoctrine.nodes import Passthrough

    content = """++++
|===
| A | B
|===
++++"""
    doc = parse_to_ast(content)
    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Passthrough)
    assert "|===" in doc.blocks[0].inlines[0].value
    assert "ASCIIDOCTRINE_OUTER" not in doc.blocks[0].inlines[0].value


