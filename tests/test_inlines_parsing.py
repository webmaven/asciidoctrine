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

    def test_inline_passthroughs(self):
        # 1. Test pass:[] macro
        ast_pass = self._strip_locations(parse_to_ast("pass:[_not_italic_]").to_dict())
        node_pass = ast_pass["blocks"][0]["inlines"][0]
        self.assertEqual(node_pass["name"], "passthrough")
        self.assertEqual(node_pass["type"], "inline")
        self.assertEqual(node_pass["value"], "_not_italic_")
        # Ensure no nested styling span is parsed
        self.assertNotIn("inlines", node_pass)

        # 2. Test triple plus +++
        ast_plus = self._strip_locations(parse_to_ast("+++<b>html</b>+++").to_dict())
        node_plus = ast_plus["blocks"][0]["inlines"][0]
        self.assertEqual(node_plus["name"], "passthrough")
        self.assertEqual(node_plus["type"], "inline")
        self.assertEqual(node_plus["value"], "<b>html</b>")
        self.assertNotIn("inlines", node_plus)

    def test_indexterms_parsing(self) -> None:
        # 1. Macro index term: indexterm:[primary,secondary,tertiary]
        macro_ast = self._strip_locations(
            parse_to_ast(
                "Some text indexterm:[primary, secondary, tertiary] rest of text."
            ).to_dict()
        )
        it_node = macro_ast["blocks"][0]["inlines"][1]
        self.assertEqual(it_node["name"], "indexterm")
        self.assertEqual(it_node["type"], "inline")
        self.assertEqual(it_node["variant"], "macro")
        self.assertEqual(it_node["terms"], ["primary", "secondary", "tertiary"])

        # 2. Flow double index term: ((term))
        double_ast = self._strip_locations(
            parse_to_ast("See ((single index entry)) inside paragraph.").to_dict()
        )
        it_node2 = double_ast["blocks"][0]["inlines"][1]
        self.assertEqual(it_node2["name"], "indexterm")
        self.assertEqual(it_node2["type"], "inline")
        self.assertEqual(it_node2["variant"], "flow_double")
        self.assertEqual(it_node2["terms"], ["single index entry"])
        self.assertEqual(it_node2["inlines"][0]["value"], "single index entry")

        # 3. Flow triple index term: (((term1, term2)))
        triple_ast = self._strip_locations(
            parse_to_ast(
                "See (((primary, secondary, tertiary))) nested inside flow."
            ).to_dict()
        )
        it_node3 = triple_ast["blocks"][0]["inlines"][1]
        self.assertEqual(it_node3["name"], "indexterm")
        self.assertEqual(it_node3["type"], "inline")
        self.assertEqual(it_node3["variant"], "flow_triple")
        self.assertEqual(it_node3["terms"], ["primary", "secondary", "tertiary"])
        self.assertEqual(
            it_node3["inlines"][0]["value"], "primary, secondary, tertiary"
        )

    def test_bare_url_links(self) -> None:
        # 1. Parse bare URL
        ast = self._strip_locations(
            parse_to_ast("Visit https://google.com for info.").to_dict()
        )
        p_inlines = ast["blocks"][0]["inlines"]
        self.assertEqual(len(p_inlines), 3)
        self.assertEqual(p_inlines[0]["value"], "Visit ")

        link_node = p_inlines[1]
        self.assertEqual(link_node["name"], "ref")
        self.assertEqual(link_node["variant"], "link")
        self.assertEqual(link_node["target"], "https://google.com")
        self.assertEqual(link_node["inlines"], [])

        self.assertEqual(p_inlines[2]["value"], " for info.")

        # 2. Serialize bare URL
        from asciidoctrine.serializer import AsciiDocSerializerVisitor

        doc = parse_to_ast("Visit https://google.com for info.")
        serialized = AsciiDocSerializerVisitor().serialize(doc)
        self.assertEqual(serialized.strip(), "Visit https://google.com for info.")

        # 3. Render to docutils
        from asciidoctrine.docutils_backend import asciidoc_to_docutils

        docutils_root = asciidoc_to_docutils("Visit https://google.com for info.")
        # Search for reference node
        import docutils.nodes as docutils_nodes

        ref_nodes = list(docutils_root.findall(docutils_nodes.reference))
        self.assertEqual(len(ref_nodes), 1)
        self.assertEqual(ref_nodes[0]["refuri"], "https://google.com")
        self.assertEqual(ref_nodes[0].astext(), "https://google.com")

        # 4. Standard link with attributes takes priority over bare URL
        ast2 = self._strip_locations(
            parse_to_ast("Visit https://google.com[Google] today.").to_dict()
        )
        p_inlines2 = ast2["blocks"][0]["inlines"]
        link_node2 = p_inlines2[1]
        self.assertEqual(link_node2["name"], "ref")
        self.assertEqual(link_node2["variant"], "link")
        self.assertEqual(link_node2["target"], "https://google.com")
        self.assertEqual(link_node2["inlines"][0]["value"], "Google")


if __name__ == "__main__":
    unittest.main()
