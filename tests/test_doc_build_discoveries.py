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


if __name__ == "__main__":
    unittest.main()
