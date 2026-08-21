"""
Tests for consecutive list parsing with distinct attributes, titles, and styles (Issue #96).
"""

import unittest

from asciidoctrine.lark_parser import parse_to_ast
from asciidoctrine.nodes import DescriptionList, List, Sidebar
from asciidoctrine.resolver import ASGResolver
from asciidoctrine.serializer import serialize_to_asciidoc


class TestConsecutiveLists(unittest.TestCase):
    def test_consecutive_description_lists_with_styles(self):
        src = """[parameters]
`x`:: (`int`) The initial count.
`y`:: (`str`, optional) Name prefix.

[returns]
`bool`:: True if successful.
"""
        doc = parse_to_ast(src)
        self.assertEqual(len(doc.blocks), 2)
        self.assertIsInstance(doc.blocks[0], DescriptionList)
        self.assertIsInstance(doc.blocks[1], DescriptionList)

        self.assertEqual(doc.blocks[0].attributes.get("style"), "parameters")
        self.assertEqual(len(doc.blocks[0].items), 2)

        self.assertEqual(doc.blocks[1].attributes.get("style"), "returns")
        self.assertEqual(len(doc.blocks[1].items), 1)

        # ASG resolution check
        resolver = ASGResolver(doc)
        asg = resolver.resolve(doc)
        self.assertEqual(len(asg.get("blocks", [])), 2)
        self.assertEqual(
            asg["blocks"][0].get("attributes", {}).get("style"), "parameters"
        )
        self.assertEqual(asg["blocks"][1].get("attributes", {}).get("style"), "returns")

    def test_consecutive_description_lists_with_titles(self):
        src = """.Inputs
term 1:: def 1

.Outputs
term 2:: def 2
"""
        doc = parse_to_ast(src)
        self.assertEqual(len(doc.blocks), 2)
        self.assertIsInstance(doc.blocks[0], DescriptionList)
        self.assertIsInstance(doc.blocks[1], DescriptionList)
        self.assertIsNotNone(doc.blocks[0].title)
        self.assertIsNotNone(doc.blocks[1].title)

    def test_consecutive_unordered_lists_with_roles_and_titles(self):
        src = """.First List
[.role-a]
* a
* b

.Second List
[.role-b]
* c
* d
"""
        doc = parse_to_ast(src)
        self.assertEqual(len(doc.blocks), 2)
        self.assertIsInstance(doc.blocks[0], List)
        self.assertIsInstance(doc.blocks[1], List)
        self.assertEqual(len(doc.blocks[0].items), 2)
        self.assertEqual(len(doc.blocks[1].items), 2)
        self.assertEqual(doc.blocks[0].attributes.get("role"), "role-a")
        self.assertEqual(doc.blocks[1].attributes.get("role"), "role-b")

    def test_consecutive_lists_nested_in_sidebar(self):
        src = """****
[parameters]
`a`:: description a

[returns]
`b`:: description b
****
"""
        doc = parse_to_ast(src)
        self.assertEqual(len(doc.blocks), 1)
        sidebar = doc.blocks[0]
        self.assertIsInstance(sidebar, Sidebar)
        self.assertEqual(len(sidebar.blocks), 2)
        self.assertIsInstance(sidebar.blocks[0], DescriptionList)
        self.assertIsInstance(sidebar.blocks[1], DescriptionList)
        self.assertEqual(sidebar.blocks[0].attributes.get("style"), "parameters")
        self.assertEqual(sidebar.blocks[1].attributes.get("style"), "returns")

    def test_unattributed_loose_lists_continue_to_merge(self):
        src = """* item 1

* item 2
"""
        doc = parse_to_ast(src)
        self.assertEqual(len(doc.blocks), 1)
        self.assertIsInstance(doc.blocks[0], List)
        self.assertEqual(len(doc.blocks[0].items), 2)

    def test_round_trip_serialization_of_consecutive_attributed_dlists(self):
        src = """[parameters]
`x`:: (`int`) Count.

[returns]
`bool`:: True.
"""
        doc = parse_to_ast(src)
        serialized = serialize_to_asciidoc(doc)
        self.assertIn("[parameters]", serialized)
        self.assertIn("[returns]", serialized)
        self.assertIn("`x`::", serialized)
        self.assertIn("`bool`::", serialized)


if __name__ == "__main__":
    unittest.main()
