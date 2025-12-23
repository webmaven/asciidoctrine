"""
Tests for the AsciiDoc parser.
"""

import unittest
from asciidoc_parser.lark_parser import parse_to_ast

class ParserTest(unittest.TestCase):

    def test_paragraph(self):
        source = "Hello, world.\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'paragraph',
                    'children': [
                        {'type': 'text', 'text': 'Hello, world.'}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_bold(self):
        source = "This is *bold* text.\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'paragraph',
                    'children': [
                        {'type': 'text', 'text': 'This is '},
                        {'type': 'strong', 'children': [{'type': 'text', 'text': 'bold'}]},
                        {'type': 'text', 'text': ' text.'}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_italic(self):
        source = "This is _italic_ text.\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'paragraph',
                    'children': [
                        {'type': 'text', 'text': 'This is '},
                        {'type': 'emphasis', 'children': [{'type': 'text', 'text': 'italic'}]},
                        {'type': 'text', 'text': ' text.'}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_monospace(self):
        source = "This is `monospace` text.\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'paragraph',
                    'children': [
                        {'type': 'text', 'text': 'This is '},
                        {'type': 'literal', 'children': [{'type': 'text', 'text': 'monospace'}]},
                        {'type': 'text', 'text': ' text.'}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_ulist(self):
        source = "* one\n* two\n* three\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'bullet_list',
                    'children': [
                        {'type': 'list_item', 'children': [{'type': 'text', 'text': 'one'}]},
                        {'type': 'list_item', 'children': [{'type': 'text', 'text': 'two'}]},
                        {'type': 'list_item', 'children': [{'type': 'text', 'text': 'three'}]}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_olist(self):
        source = "1. one\n2. two\n3. three\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'enumerated_list',
                    'children': [
                        {'type': 'list_item', 'children': [{'type': 'text', 'text': 'one'}]},
                        {'type': 'list_item', 'children': [{'type': 'text', 'text': 'two'}]},
                        {'type': 'list_item', 'children': [{'type': 'text', 'text': 'three'}]}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_literal_block(self):
        source = "----\nThis is a literal block.\n----\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'literal_block',
                    'text': 'This is a literal block.\n'
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_section(self):
        source = "== Section 1\n\nThis is the first section.\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'section',
                    'level': 1,
                    'title': {'type': 'title', 'children': [{'type': 'text', 'text': 'Section 1'}]},
                    'children': [
                        {
                            'type': 'paragraph',
                            'children': [
                                {'type': 'text', 'text': 'This is the first section.'}
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_symbols_in_word(self):
        # Ensure that characters like commas, periods, etc. don't break WORD
        source = "Hello, world! (tested)\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'paragraph',
                    'children': [
                        {'type': 'text', 'text': 'Hello, world! (tested)'}
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_nested_lists(self):
        source = "* level 1\n** level 2\n* back to 1\n"
        ast = parse_to_ast(source)
        # Verify structure via dict conversion
        self.assertEqual(ast['type'], 'document')
        self.assertEqual(ast['children'][0]['type'], 'bullet_list')

    def test_list_item_with_formatting(self):
        source = "* basic item\n* item with *bold* and _italic_\n"
        ast = parse_to_ast(source)
        # Verify that the second item has children including bold and italic
        second_item = ast['children'][0]['children'][1]
        self.assertEqual(second_item['type'], 'list_item')
        content_nodes = second_item['children']
        
        # Types: 'item with ', 'strong', ' and ', 'emphasis'
        types = [n['type'] for n in content_nodes]
        self.assertIn('strong', types)
        self.assertIn('emphasis', types)

if __name__ == '__main__':
    unittest.main()
