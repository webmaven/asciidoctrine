"""
Tests for inline-level parsing in AsciiDoc.
"""

import unittest

from asciidoctrine.lark_parser import parse_to_ast


class TestInlines(unittest.TestCase):
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

    def test_bold(self):
        source = "This is *bold* text.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        self.assertEqual(paragraph["inlines"][1]["variant"], "strong")

    def test_italic(self):
        source = "This is _italic_ text.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        self.assertEqual(paragraph["inlines"][1]["variant"], "emphasis")

    def test_monospace(self):
        source = "This is `monospace` text.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        self.assertEqual(paragraph["inlines"][1]["variant"], "code")

    def test_symbols_in_word(self):
        source = "Hello, world! (tested)\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        self.assertEqual(
            ast["blocks"][0]["inlines"][0]["value"], "Hello, world! (tested)"
        )

    def test_list_item_with_formatting(self):
        source = "* basic item\n* item with *bold* and _italic_\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        second_item = ast["blocks"][0]["items"][1]
        content_nodes = second_item["principal"]
        names = [n["name"] for n in content_nodes]
        self.assertEqual(names.count("span"), 2)

    def test_attribute_substitution(self):
        source = ":author: Michael\n\nHello {author}!\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][1]
        text_node = paragraph["inlines"][0]
        self.assertEqual(text_node["value"], "Hello Michael!")

    def test_attribute_substitution_not_found(self):
        source = "Hello {unknown}!\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        text_node = paragraph["inlines"][0]
        self.assertEqual(text_node["value"], "Hello {unknown}!")

    def test_attribute_substitution_in_title(self):
        source = ":project: AsciiDocParser\n\n== {project} Documentation\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        section = ast["blocks"][1]
        actual_title = "".join([n["value"] for n in section["title"]])
        self.assertEqual(actual_title, "AsciiDocParser Documentation")

    def test_attribute_substitution_nested(self):
        source = ":project: AsciiDoc\n:tool: {project}Parser\n\nThis is {tool}.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][2]
        text_node = paragraph["inlines"][0]
        self.assertEqual(text_node["value"], "This is AsciiDocParser.")

    def test_attribute_with_inline_formatting(self):
        source = ":author: *Jane* _Smith_\n\nHello {author}!\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][1]
        self.assertEqual(paragraph["inlines"][1]["name"], "span")
        self.assertEqual(paragraph["inlines"][1]["inlines"][0]["value"], "Jane")

    def test_deeply_nested_attribute_substitution(self):
        source = ":a: 1\n:b: {a}{a}\n:c: {b}{b}\n\nResult is {c}.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][3]
        self.assertEqual(paragraph["inlines"][0]["value"], "Result is 1111.")

    def test_recursive_attribute_substitution(self):
        source = (
            ":project_name: Cool Project\n"
            ":doc_title: {project_name} Docs\n\n"
            "== {doc_title}\n"
        )
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        section = ast["blocks"][2]
        title_node = section["title"]
        text_node = title_node[0]
        self.assertEqual(text_node["value"], "Cool Project Docs")

    def test_inline_link_macro(self):
        source = "link:path/to/home.html[Go to Home]\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        link_node = paragraph["inlines"][0]
        self.assertEqual(link_node["name"], "ref")
        self.assertEqual(link_node["variant"], "link")
        self.assertEqual(link_node["target"], "path/to/home.html")
        self.assertEqual(link_node["inlines"][0]["value"], "Go to Home")

    def test_inline_url_macro(self):
        source = "https://example.com[example domain]\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        link_node = paragraph["inlines"][0]
        self.assertEqual(link_node["name"], "ref")
        self.assertEqual(link_node["variant"], "link")
        self.assertEqual(link_node["target"], "https://example.com")
        self.assertEqual(link_node["inlines"][0]["value"], "example domain")

    def test_inline_link_with_nested_formatting(self):
        source = "https://example.com[_example only_]\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        link_node = paragraph["inlines"][0]
        self.assertEqual(link_node["inlines"][0]["name"], "span")
        self.assertEqual(link_node["inlines"][0]["variant"], "emphasis")
        self.assertEqual(link_node["inlines"][0]["inlines"][0]["value"], "example only")

    def test_inline_link_with_window_caret(self):
        source = "https://example.com[example domain^]\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        link_node = paragraph["inlines"][0]
        self.assertEqual(link_node["attributes"]["window"], "_blank")
        self.assertEqual(link_node["inlines"][0]["value"], "example domain")

    def test_experimental_macros_standalone(self):
        # Test standalone kbd
        kbd_ast = self._strip_locations(parse_to_ast("kbd:[Ctrl+C]").to_dict())
        self.assertEqual(kbd_ast["blocks"][0]["inlines"][0]["name"], "kbd")
        self.assertEqual(kbd_ast["blocks"][0]["inlines"][0]["value"], ["Ctrl", "C"])

        # Test standalone btn
        btn_ast = self._strip_locations(parse_to_ast("btn:[Submit]").to_dict())
        self.assertEqual(btn_ast["blocks"][0]["inlines"][0]["name"], "button")
        self.assertEqual(btn_ast["blocks"][0]["inlines"][0]["value"], "Submit")

        # Test standalone menu
        menu_ast = self._strip_locations(parse_to_ast("menu:File[Save]").to_dict())
        self.assertEqual(menu_ast["blocks"][0]["inlines"][0]["name"], "menu")
        self.assertEqual(menu_ast["blocks"][0]["inlines"][0]["menu"], "File")
        self.assertEqual(menu_ast["blocks"][0]["inlines"][0]["items"], ["Save"])

    def test_experimental_macros_embedded_in_paragraph(self):
        source = "This is a kbd:[Ctrl+C] and btn:[Submit] inline macro test.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        inlines = ast["blocks"][0]["inlines"]

        # If parsed correctly, we should have 5 inline nodes:
        # 1. Text("This is a ")
        # 2. Kbd(["Ctrl", "C"])
        # 3. Text(" and ")
        # 4. Button("Submit")
        # 5. Text(" inline macro test.")
        self.assertEqual(len(inlines), 5)
        self.assertEqual(inlines[0]["value"], "This is a ")
        self.assertEqual(inlines[1]["name"], "kbd")
        self.assertEqual(inlines[1]["value"], ["Ctrl", "C"])
        self.assertEqual(inlines[2]["value"], " and ")
        self.assertEqual(inlines[3]["name"], "button")
        self.assertEqual(inlines[3]["value"], "Submit")
        self.assertEqual(inlines[4]["value"], " inline macro test.")


if __name__ == "__main__":
    unittest.main()
