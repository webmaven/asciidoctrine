import unittest
from asciidoc_parser.nodes import Text, Span, Paragraph
from asciidoc_parser.attributes import (
    substitute_attributes,
    resolve_node_to_string,
    resolve_attribute_map,
)

class TestAttributes(unittest.TestCase):
    def test_substitute_attributes(self):
        attrs = {"name": "Jules", "version": "1.0"}
        text = "Hello {name}, version {version}."
        expected = "Hello Jules, version 1.0."
        self.assertEqual(substitute_attributes(text, attrs), expected)

    def test_substitute_unresolved(self):
        attrs = {"name": "Jules"}
        text = "Hello {name}, {unknown}."
        expected = "Hello Jules, {unknown}."
        self.assertEqual(substitute_attributes(text, attrs), expected)

    def test_resolve_node_to_string_basic(self):
        node = Text("plain text")
        self.assertEqual(resolve_node_to_string(node), "plain text")

    def test_resolve_node_to_string_nested(self):
        # Span(variant="strong", inlines=[Text("bold")])
        node = Span(variant="strong", inlines=[Text("bold")])
        self.assertEqual(resolve_node_to_string(node), "bold")

    def test_resolve_attribute_map(self):
        rich_attrs = {
            "author": [Text("John "), Span(variant="emphasis", inlines=[Text("Doe")])],
            "simple": "string",
        }
        expected = {"author": "John Doe", "simple": "string"}
        self.assertEqual(resolve_attribute_map(rich_attrs), expected)

if __name__ == "__main__":
    unittest.main()
