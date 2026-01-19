import unittest

from asciidoc_parser.lark_parser import parse_to_ast


class CombinedFeaturesTest(unittest.TestCase):
    def test_section_with_list_and_inline_formatting(self):
        source = """== Section Title

* This is a list item with **bold** text.
* And this one has `monospace`.

Another paragraph.
"""
        ast = parse_to_ast(source).to_dict()
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
                                            "form": "constrained",
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
