import pytest
import unittest

from asciidoctrine.lark_parser import parse_to_ast



pytestmark = pytest.mark.integration
class CombinedFeaturesTest(unittest.TestCase):
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

    def test_section_with_list_and_inline_formatting(self):
        source = """== Section Title

* This is a list item with **bold** text.
* And this one has `monospace`.

Another paragraph.
"""
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        import json

        print(json.dumps(ast, indent=2))
        self.maxDiff = None
        expected_ast = {
            "name": "document",
            "type": "block",
            "blocks": [
                {
                    "name": "section",
                    "type": "block",
                    "level": 1,
                    "title": [
                        {"name": "text", "type": "string", "value": "Section Title"}
                    ],
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
                                        {
                                            "name": "text",
                                            "type": "string",
                                            "value": "This is a list item with ",
                                        },
                                        {
                                            "name": "span",
                                            "type": "inline",
                                            "variant": "strong",
                                            "form": "unconstrained",
                                            "inlines": [
                                                {
                                                    "name": "text",
                                                    "type": "string",
                                                    "value": "bold",
                                                }
                                            ],
                                        },
                                        {
                                            "name": "text",
                                            "type": "string",
                                            "value": " text.",
                                        },
                                    ],
                                    "blocks": [],
                                },
                                {
                                    "name": "listItem",
                                    "type": "block",
                                    "marker": "*",
                                    "principal": [
                                        {
                                            "name": "text",
                                            "type": "string",
                                            "value": "And this one has ",
                                        },
                                        {
                                            "name": "span",
                                            "type": "inline",
                                            "variant": "code",
                                            "form": "constrained",
                                            "inlines": [
                                                {
                                                    "name": "text",
                                                    "type": "string",
                                                    "value": "monospace",
                                                }
                                            ],
                                        },
                                        {
                                            "name": "text",
                                            "type": "string",
                                            "value": ".",
                                        },
                                    ],
                                    "blocks": [],
                                },
                            ],
                        },
                        {
                            "name": "paragraph",
                            "type": "block",
                            "inlines": [
                                {
                                    "name": "text",
                                    "type": "string",
                                    "value": "Another paragraph.",
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        self.assertEqual(ast, expected_ast)


if __name__ == "__main__":
    unittest.main()
