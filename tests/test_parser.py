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

    def test_admonition_note(self):
        source = "[NOTE]\n====\nThis is a note.\n====\n"
        ast = parse_to_ast(source)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'admonition',
                    'flavor': 'note',
                    'children': [
                        {
                            'type': 'paragraph',
                            'children': [
                                {'type': 'text', 'text': 'This is a note.'}
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)

    def test_admonition_tip(self):
        source = "[TIP]\n====\nHere's a helpful tip.\n====\n"
        ast = parse_to_ast(source)
        self.assertEqual(ast['children'][0]['type'], 'admonition')
        self.assertEqual(ast['children'][0]['flavor'], 'tip')

    def test_admonition_important(self):
        source = "[IMPORTANT]\n====\nPay attention to this.\n====\n"
        ast = parse_to_ast(source)
        self.assertEqual(ast['children'][0]['type'], 'admonition')
        self.assertEqual(ast['children'][0]['flavor'], 'important')

    def test_admonition_warning(self):
        source = "[WARNING]\n====\nBe careful here.\n====\n"
        ast = parse_to_ast(source)
        self.assertEqual(ast['children'][0]['type'], 'admonition')
        self.assertEqual(ast['children'][0]['flavor'], 'warning')

    def test_admonition_caution(self):
        source = "[CAUTION]\n====\nProceed with caution.\n====\n"
        ast = parse_to_ast(source)
        self.assertEqual(ast['children'][0]['type'], 'admonition')
        self.assertEqual(ast['children'][0]['flavor'], 'caution')

    def test_admonition_with_list(self):
        source = "[NOTE]\n====\nConsider these points:\n\n- First point\n- Second point\n====\n"
        ast = parse_to_ast(source)
        admonition = ast['children'][0]
        self.assertEqual(admonition['type'], 'admonition')
        self.assertEqual(admonition['flavor'], 'note')
        # Should have paragraph and bullet list (may have blank lines between)
        child_types = [c['type'] for c in admonition['children']]
        self.assertIn('paragraph', child_types)
        self.assertIn('bullet_list', child_types)

    def test_admonition_with_formatting(self):
        source = "[TIP]\n====\nUse *bold* and _italic_ formatting.\n====\n"
        ast = parse_to_ast(source)
        admonition = ast['children'][0]
        paragraph = admonition['children'][0]
        # Check that formatting is preserved
        types = [n['type'] for n in paragraph['children']]
        self.assertIn('strong', types)
        self.assertIn('emphasis', types)

    def test_admonition_empty(self):
        source = "[NOTE]\n====\n====\n"
        ast = parse_to_ast(source)
        admonition = ast['children'][0]
        self.assertEqual(admonition['type'], 'admonition')
        self.assertEqual(admonition['flavor'], 'note')
        # Empty admonition should have no children key or empty children
        children = admonition.get('children', [])
        self.assertTrue(len(children) == 0 or all(c['type'] == 'blank_line' for c in children))


    def test_admonition_multiple_paragraphs(self):
        source = "[NOTE]\n====\nFirst paragraph.\n\nSecond paragraph.\n====\n"
        ast = parse_to_ast(source)
        admonition = ast['children'][0]
        paragraphs = [c for c in admonition['children'] if c['type'] == 'paragraph']
        self.assertGreaterEqual(len(paragraphs), 2)

    def test_admonition_with_literal_block(self):
        source = "[TIP]\n====\nHere's some code:\n\n----\ndef hello():\n    print(\"world\")\n----\n====\n"
        ast = parse_to_ast(source)
        admonition = ast['children'][0]
        child_types = [c['type'] for c in admonition['children']]
        self.assertIn('paragraph', child_types)
        self.assertIn('literal_block', child_types)

    def test_admonition_whitespace_in_label(self):
        source = "[  NOTE  ]\n====\nContent with whitespace in label.\n====\n"
        ast = parse_to_ast(source)
        admonition = ast['children'][0]
        self.assertEqual(admonition['type'], 'admonition')
        self.assertEqual(admonition['flavor'], 'note')

    def test_multiple_admonitions(self):
        source = "[NOTE]\n====\nFirst note.\n====\n\n[WARNING]\n====\nA warning.\n====\n"
        ast = parse_to_ast(source)
        admonitions = [c for c in ast['children'] if c['type'] == 'admonition']
        self.assertEqual(len(admonitions), 2)
        self.assertEqual(admonitions[0]['flavor'], 'note')
        self.assertEqual(admonitions[1]['flavor'], 'warning')

    def test_admonition_in_section(self):
        source = "== Section Title\n\n[NOTE]\n====\nNote in a section.\n====\n"
        ast = parse_to_ast(source)
        section = ast['children'][0]
        self.assertEqual(section['type'], 'section')
        admonitions = [c for c in section['children'] if c['type'] == 'admonition']
        self.assertGreaterEqual(len(admonitions), 1)
        self.assertEqual(admonitions[0]['flavor'], 'note')

    def test_sidebar_basic(self):
        source = "****\nThis is a sidebar.\n****\n"
        ast = parse_to_ast(source)
        sidebar = ast['children'][0]
        self.assertEqual(sidebar['type'], 'sidebar')
        self.assertEqual(len(sidebar['children']), 1)
        self.assertEqual(sidebar['children'][0]['type'], 'paragraph')
        self.assertEqual(sidebar['children'][0]['children'][0]['text'], 'This is a sidebar.')

    def test_sidebar_nested_content(self):
        source = "****\nSidebar paragraph.\n\n- List item\n\n----\ncode\n----\n****\n"
        ast = parse_to_ast(source)
        sidebar = ast['children'][0]
        child_types = [c['type'] for c in sidebar['children']]
        self.assertIn('paragraph', child_types)
        self.assertIn('bullet_list', child_types)
        self.assertIn('literal_block', child_types)

    def test_sidebar_empty(self):
        source = "****\n****\n"
        ast = parse_to_ast(source)
        sidebar = ast['children'][0]
        # Should be empty or have blank lines, handle missing 'children' key safely
        children = sidebar.get('children', [])
        self.assertTrue(len(children) == 0 or all(c['type'] == 'blank_line' for c in children))

    def test_sidebar_multiple(self):
        source = "****\nContent 1\n****\n\n****\nContent 2\n****\n"
        ast = parse_to_ast(source)
        sidebars = [c for c in ast['children'] if c['type'] == 'sidebar']
        self.assertEqual(len(sidebars), 2)

    def test_sidebar_nested_admonition(self):
        source = "****\n[NOTE]\n====\nNote inside sidebar\n====\n****\n"
        ast = parse_to_ast(source)
        sidebar = ast['children'][0]
        self.assertEqual(sidebar['type'], 'sidebar')
        admonition = sidebar['children'][0]
        self.assertEqual(admonition['type'], 'admonition')
        self.assertEqual(admonition['flavor'], 'note')

    def test_admonition_nested_sidebar(self):
        source = "[TIP]\n====\n****\nSidebar inside tip\n****\n====\n"
        ast = parse_to_ast(source)
        admonition = ast['children'][0]
        self.assertEqual(admonition['type'], 'admonition')
        sidebar = admonition['children'][0]
        self.assertEqual(sidebar['type'], 'sidebar')

if __name__ == '__main__':
    unittest.main()
