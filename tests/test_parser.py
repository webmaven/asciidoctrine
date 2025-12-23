"""
Tests for the AsciiDoc parser.
"""

import unittest
import os
import shutil
from asciidoc_parser.lark_parser import parse_to_ast

class ParserTest(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test fixtures
        self.base_dir = os.path.join(os.path.dirname(__file__), 'temp_fixtures')
        os.makedirs(self.base_dir, exist_ok=True)
        with open(os.path.join(self.base_dir, 'included.adoc'), 'w') as f:
            f.write("This is an *included* file.\n\n* With a list item.\n")

    def tearDown(self):
        # Clean up the temporary directory
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)

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
        literal = ast['children'][0]
        self.assertEqual(literal['type'], 'literal_block')
        # Content regex might capture newlines
        self.assertIn('This is a literal block.', literal['content'])
        self.assertEqual(literal.get('attributes', {}), {})

    def test_source_block_attributes(self):
        source = "[source,python]\n----\ndef foo(): pass\n----\n"
        ast = parse_to_ast(source)
        literal = ast['children'][0]
        self.assertEqual(literal['type'], 'literal_block')
        self.assertEqual(literal['attributes'], {'style': 'source', 'language': 'python'})
        self.assertIn('def foo(): pass', literal['content'])

    def test_section_parsing(self):
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

    def test_example_block_basic(self):
        source = "====\nThis is an example block.\n====\n"
        ast = parse_to_ast(source)
        example = ast['children'][0]
        self.assertEqual(example['type'], 'example_block')
        self.assertEqual(len(example['children']), 1)
        self.assertEqual(example['children'][0]['type'], 'paragraph')

    def test_example_block_nesting(self):
        source = "====\n****\nSidebar in example\n****\n====\n"
        ast = parse_to_ast(source)
        example = ast['children'][0]
        self.assertEqual(example['type'], 'example_block')
        sidebar = example['children'][0]
        self.assertEqual(sidebar['type'], 'sidebar')

    def test_admonition_vs_example(self):
        # NOTE + ==== -> Admonition
        source_adm = "[NOTE]\n====\nNote content\n====\n"
        ast_adm = parse_to_ast(source_adm)
        self.assertEqual(ast_adm['children'][0]['type'], 'admonition')
        
        # ==== alone -> Example
        source_ex = "====\nExample content\n====\n"
        ast_ex = parse_to_ast(source_ex)
        self.assertEqual(ast_ex['children'][0]['type'], 'example_block')

    def test_attribute_entry(self):
        source = ":author: Michael Bernstein\n"
        ast = parse_to_ast(source)
        attr = ast['children'][0]
        self.assertEqual(attr['type'], 'attribute_entry')
        self.assertEqual(attr['name'], 'author')
        self.assertEqual(attr['value'], 'Michael Bernstein')

    def test_attribute_entry_empty(self):
        source = ":myattr:\n"
        ast = parse_to_ast(source)
        attr = ast['children'][0]
        self.assertEqual(attr['type'], 'attribute_entry')
        self.assertEqual(attr['name'], 'myattr')
        self.assertEqual(attr['value'], '')

    def test_attribute_substitution(self):
        source = ":author: Michael\nHello {author}!\n"
        ast = parse_to_ast(source)
        # children: [AttributeEntry, Paragraph]
        paragraph = ast['children'][1]
        self.assertEqual(paragraph['type'], 'paragraph')
        text_node = paragraph['children'][0]
        self.assertEqual(text_node['text'], 'Hello Michael!')

    def test_attribute_substitution_not_found(self):
        source = "Hello {unknown}!\n"
        ast = parse_to_ast(source)
        paragraph = ast['children'][0]
        text_node = paragraph['children'][0]
        self.assertEqual(text_node['text'], 'Hello {unknown}!')

    def test_attribute_substitution_in_title(self):
        source = ":project: AsciiDocParser\n== {project} Documentation\n"
        ast = parse_to_ast(source)
        # children: [AttributeEntry, Section]
        section = ast['children'][1]
        self.assertEqual(section['type'], 'section')
        title_node = section['title']
        text_node = title_node['children'][0]
        self.assertEqual(text_node['text'], 'AsciiDocParser Documentation')

    def test_attribute_substitution_nested(self):
        source = ":project: AsciiDoc\n:tool: {project}Parser\nThis is {tool}.\n"
        ast = parse_to_ast(source)
        # children: [Attr, Attr, Paragraph]
        paragraph = ast['children'][2]
        text_node = paragraph['children'][0]
        self.assertEqual(text_node['text'], 'This is AsciiDocParser.')

    def test_attribute_with_inline_formatting(self):
        source = ":author: *Jane* _Smith_\nHello {author}!\n"
        ast = parse_to_ast(source)
        paragraph = ast['children'][1]
        self.assertEqual(paragraph['type'], 'paragraph')
        # Expected: Hello *Jane* _Smith_! -> Text, Strong, Text, Emphasis, Text
        self.assertEqual(len(paragraph['children']), 5)
        self.assertEqual(paragraph['children'][0]['text'], 'Hello ')
        self.assertEqual(paragraph['children'][1]['type'], 'strong')
        self.assertEqual(paragraph['children'][1]['children'][0]['text'], 'Jane')
        self.assertEqual(paragraph['children'][2]['text'], ' ')
        self.assertEqual(paragraph['children'][3]['type'], 'emphasis')
        self.assertEqual(paragraph['children'][3]['children'][0]['text'], 'Smith')
        self.assertEqual(paragraph['children'][4]['text'], '!')

    def test_deeply_nested_attribute_substitution(self):
        source = ":a: 1\n:b: {a}{a}\n:c: {b}{b}\nResult is {c}.\n"
        ast = parse_to_ast(source)
        paragraph = ast['children'][3]
        self.assertEqual(paragraph['children'][0]['text'], 'Result is 1111.')

    def test_recursive_attribute_substitution(self):
        source = ":project_name: Cool Project\n:doc_title: {project_name} Docs\n== {doc_title}\n"
        ast = parse_to_ast(source)
        section = ast['children'][2]
        title_node = section['title']
        text_node = title_node['children'][0]
        self.assertEqual(text_node['text'], 'Cool Project Docs')


    def test_preprocessor_integration(self):
        source = "include::included.adoc[]"
        ast = parse_to_ast(source, base_dir=self.base_dir)
        expected_ast = {
            'type': 'document',
            'children': [
                {
                    'type': 'paragraph',
                    'children': [
                        {'type': 'text', 'text': 'This is an '},
                        {'type': 'strong', 'children': [{'type': 'text', 'text': 'included'}]},
                        {'type': 'text', 'text': ' file.'}
                    ]
                },
                {
                    'type': 'bullet_list',
                    'children': [
                        {
                            'type': 'list_item',
                            'children': [
                                {'type': 'text', 'text': 'With a list item.'}
                            ]
                        }
                    ]
                }
            ]
        }
        self.assertEqual(ast, expected_ast)


if __name__ == '__main__':
    unittest.main()
