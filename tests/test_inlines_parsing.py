"""
Tests for inline-level parsing in AsciiDoc.
"""

import unittest

import pytest

from asciidoctrine.lark_parser import parse_to_ast

pytestmark = pytest.mark.integration


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

    def test_attribute_substitutions_parameterized(self):
        cases = [
            (
                ":author: Michael\n\nHello {author}!\n",
                1,
                "Hello Michael!",
            ),
            (
                ":project: AsciiDoc\n:tool: {project}Parser\n\nThis is {tool}.\n",
                2,
                "This is AsciiDocParser.",
            ),
            (
                ":a: 1\n:b: {a}{a}\n:c: {b}{b}\n\nResult is {c}.\n",
                3,
                "Result is 1111.",
            ),
        ]
        for source, block_idx, expected in cases:
            with self.subTest(expected=expected):
                ast = self._strip_locations(parse_to_ast(source).to_dict())
                paragraph = ast["blocks"][block_idx]
                text_node = paragraph["inlines"][0]
                self.assertEqual(text_node["value"], expected)

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

    def test_attribute_with_inline_formatting(self):
        source = ":author: *Jane* _Smith_\n\nHello {author}!\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][1]
        self.assertEqual(paragraph["inlines"][1]["name"], "span")
        self.assertEqual(paragraph["inlines"][1]["inlines"][0]["value"], "Jane")

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

    def test_inline_links_parameterized(self):
        cases = [
            (
                "link:path/to/home.html[Go to Home]\n",
                "path/to/home.html",
                "Go to Home",
                None,
                None,
            ),
            (
                "https://example.com[example domain]\n",
                "https://example.com",
                "example domain",
                None,
                None,
            ),
            (
                "https://example.com[_example only_]\n",
                "https://example.com",
                "example only",
                "emphasis",
                None,
            ),
            (
                "https://example.com[example domain^]\n",
                "https://example.com",
                "example domain",
                None,
                "_blank",
            ),
        ]
        for source, target, text, nested_variant, window in cases:
            with self.subTest(source=source):
                ast = self._strip_locations(parse_to_ast(source).to_dict())
                link_node = ast["blocks"][0]["inlines"][0]
                self.assertEqual(link_node["name"], "ref")
                self.assertEqual(link_node["variant"], "link")
                self.assertEqual(link_node["target"], target)

                if nested_variant:
                    nested = link_node["inlines"][0]
                    self.assertEqual(nested["name"], "span")
                    self.assertEqual(nested["variant"], nested_variant)
                    self.assertEqual(nested["inlines"][0]["value"], text)
                else:
                    self.assertEqual(link_node["inlines"][0]["value"], text)

                if window:
                    self.assertEqual(link_node["attributes"]["window"], window)

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

    def test_additional_inline_macros(self):
        # 1. Icon inline macro
        icon_ast = self._strip_locations(
            parse_to_ast("This is icon:heart[role=red] icon.").to_dict()
        )
        self.assertEqual(icon_ast["blocks"][0]["inlines"][1]["name"], "icon")
        self.assertEqual(icon_ast["blocks"][0]["inlines"][1]["target"], "heart")

        # 2. Inline anchor
        anchor_ast1 = self._strip_locations(
            parse_to_ast("This is [[my-target]] anchor.").to_dict()
        )
        self.assertEqual(anchor_ast1["blocks"][0]["inlines"][1]["name"], "ref")
        self.assertEqual(anchor_ast1["blocks"][0]["inlines"][1]["variant"], "anchor")
        self.assertEqual(anchor_ast1["blocks"][0]["inlines"][1]["target"], "my-target")

        # anchor:my-target[] form anchor
        anchor_ast2 = self._strip_locations(
            parse_to_ast("This is anchor:my-target[] anchor.").to_dict()
        )
        self.assertEqual(anchor_ast2["blocks"][0]["inlines"][1]["name"], "ref")
        self.assertEqual(anchor_ast2["blocks"][0]["inlines"][1]["variant"], "anchor")
        self.assertEqual(anchor_ast2["blocks"][0]["inlines"][1]["target"], "my-target")

        # 3. Inline xref
        xref_ast1 = self._strip_locations(parse_to_ast("See <<my-target>>.").to_dict())
        self.assertEqual(xref_ast1["blocks"][0]["inlines"][1]["name"], "ref")
        self.assertEqual(xref_ast1["blocks"][0]["inlines"][1]["variant"], "xref")
        self.assertEqual(xref_ast1["blocks"][0]["inlines"][1]["target"], "my-target")

        xref_ast2 = self._strip_locations(
            parse_to_ast("See <<my-target,My Label>>.").to_dict()
        )
        self.assertEqual(xref_ast2["blocks"][0]["inlines"][1]["name"], "ref")
        self.assertEqual(xref_ast2["blocks"][0]["inlines"][1]["variant"], "xref")
        self.assertEqual(xref_ast2["blocks"][0]["inlines"][1]["target"], "my-target")

        # 4. Inline link
        link_ast = self._strip_locations(
            parse_to_ast("Go to https://google.com[Google].").to_dict()
        )
        self.assertEqual(link_ast["blocks"][0]["inlines"][1]["name"], "ref")
        self.assertEqual(link_ast["blocks"][0]["inlines"][1]["variant"], "link")
        self.assertEqual(
            link_ast["blocks"][0]["inlines"][1]["target"], "https://google.com"
        )

        # 5. Bibliography reference
        bibref_ast = self._strip_locations(parse_to_ast("Ref [[[my-bib]]].").to_dict())
        self.assertEqual(bibref_ast["blocks"][0]["inlines"][1]["name"], "ref")
        self.assertEqual(bibref_ast["blocks"][0]["inlines"][1]["variant"], "bibref")
        self.assertEqual(bibref_ast["blocks"][0]["inlines"][1]["target"], "my-bib")

        # 6. Forced line break
        break_ast = self._strip_locations(
            parse_to_ast("Line one +\nLine two.\n").to_dict()
        )
        self.assertEqual(break_ast["blocks"][0]["inlines"][1]["name"], "break")

        # 7. Inline STEM / asciimath / latexmath
        math_ast1 = self._strip_locations(parse_to_ast("asciimath:[x^2]").to_dict())
        self.assertEqual(math_ast1["blocks"][0]["inlines"][0]["name"], "stem")
        self.assertEqual(math_ast1["blocks"][0]["inlines"][0]["variant"], "asciimath")
        self.assertEqual(math_ast1["blocks"][0]["inlines"][0]["value"], "x^2")

        math_ast2 = self._strip_locations(
            parse_to_ast("latexmath:[e^{i\\pi}]").to_dict()
        )
        self.assertEqual(math_ast2["blocks"][0]["inlines"][0]["name"], "stem")
        self.assertEqual(math_ast2["blocks"][0]["inlines"][0]["variant"], "latexmath")
        self.assertEqual(math_ast2["blocks"][0]["inlines"][0]["value"], "e^{i\\pi}")


if __name__ == "__main__":
    unittest.main()
