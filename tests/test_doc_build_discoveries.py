import unittest

from asciidoctrine.lark_parser import parse_to_ast


class TestDocBuildDiscoveries(unittest.TestCase):
    def test_table_parsing(self):
        source = """
[cols="1,2"]
|===
| AST Node | ASG Structure
| `Document` | document
|===
"""
        # This currently raises a Lark error
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(ast["blocks"][0]["name"], "table")

    def test_monospace_with_underscores_no_nested_italics(self):
        """
        Monospace backticks should be literal and not allow nested formatting.
        This verifies the fix for the behavior discovered in index.adoc.
        """
        source = "own `asciidoctrine.sphinx_ext` plugin!\n"
        ast = parse_to_ast(source).to_dict()
        paragraph = ast["blocks"][0]
        span = paragraph["inlines"][1]
        self.assertEqual(span["variant"], "code")

        # Check that it DOES NOT have nested emphasis
        nested_variants = [n.get("variant") for n in span["inlines"] if "variant" in n]
        self.assertNotIn("emphasis", nested_variants)
        # The content should be a single text node
        self.assertEqual(len(span["inlines"]), 1)
        self.assertEqual(span["inlines"][0]["value"], "asciidoctrine.sphinx_ext")

    def test_unconstrained_monospace_literal(self):
        """
        Unconstrained monospace backticks (``) should also be literal.
        """
        source = "``*bold* _italic_``\n"
        ast = parse_to_ast(source).to_dict()
        paragraph = ast["blocks"][0]
        span = paragraph["inlines"][0]
        self.assertEqual(span["variant"], "code")
        self.assertEqual(span["form"], "unconstrained")

        # The content should be a single text node with literal content
        self.assertEqual(len(span["inlines"]), 1)
        self.assertEqual(span["inlines"][0]["value"], "*bold* _italic_")


    def test_nested_styles_inside_verbatim_listing_blocks(self):
        """
        Verbatim listing blocks should protect all nested characters (such as _to_
        or == Section Title) from being parsed as inline styling or sub-blocks.
        """
        source = """[source,python]
----
from asciidoctrine import parse_to_ast
from asciidoctrine.resolver import ASGResolver

source = \"\"\"
== Section Title
This is a *bold* word in a paragraph.
\"\"\"

# 1. Parse raw source to syntax-level AST
ast = parse_to_ast(source)
----
"""
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(len(ast["blocks"]), 1)
        block = ast["blocks"][0]
        self.assertEqual(block["name"], "listing")
        self.assertEqual(block["form"], "delimited")
        # Ensure that it was not split into multiple paragraphs/sections
        self.assertIn("== Section Title", block["inlines"][0]["value"])
        self.assertIn("parse_to_ast", block["inlines"][0]["value"])

    def test_inline_links_inside_table_cells(self):
        """
        Tables containing complex cell content (e.g. bold formatting and inline links)
        should be correctly parsed as table blocks, not normal paragraphs.
        """
        source = """
|===
| Feature | Language Spec Status

| *Document Header*
| link:vendor/asciidoc-lang/spec/outline.adoc[Standardized]
|===
"""
        ast = parse_to_ast(source).to_dict()
        self.assertEqual(len(ast["blocks"]), 1)
        self.assertEqual(ast["blocks"][0]["name"], "table")

    def test_link_inside_section_header(self):
        """
        Inline links with the link: prefix inside section headers should be
        fully parsed as a Ref inline node, with no leading plain text link: prefix.
        """
        source = "== link:https://pypi.org/project/asciidoctrine/0.1.0a3/[0.1.0a3] - 2026-07-11\n"
        ast = parse_to_ast(source).to_dict()
        header = ast["blocks"][0]
        self.assertEqual(header["name"], "section")
        
        # Verify the title contains the Ref link inline node and no plain text "link:"
        title_inlines = header["title"]
        inline_types = [n["name"] for n in title_inlines]
        self.assertIn("ref", inline_types)
        
        # Ensure there is no plain-text 'link:' string before the link
        plain_texts = [n["value"] for n in title_inlines if n["name"] == "text"]
        for t in plain_texts:
            self.assertNotIn("link:", t)


if __name__ == "__main__":
    unittest.main()
