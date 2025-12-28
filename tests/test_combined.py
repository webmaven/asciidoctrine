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
            'type': 'document',
            'children': [
                {
                    'type': 'section',
                    'level': 1,
                    'title': {'type': 'title', 'children': [{'type': 'text', 'text': 'Section Title'}]},
                    'children': [
                        {
                            'type': 'bullet_list',
                            'children': [
                                {
                                    'type': 'list_item',
                                    'children': [
                                        {'type': 'text', 'text': 'This is a list item with '},
                                        {'type': 'strong', 'children': [{'type': 'text', 'text': 'bold'}]},
                                        {'type': 'text', 'text': ' text.'},
                                    ]
                                },
                                {
                                    'type': 'list_item',
                                    'children': [
                                        {'type': 'text', 'text': 'And this one has '},
                                        {'type': 'literal', 'children': [{'type': 'text', 'text': 'monospace'}]},
                                        {'type': 'text', 'text': '.'},
                                    ]
                                }
                            ]
                        },
                        {
                            'type': 'paragraph',
                            'children': [
                                {'type': 'text', 'text': 'Another paragraph.'}
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

if __name__ == '__main__':
    unittest.main()
