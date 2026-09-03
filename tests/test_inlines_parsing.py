"""
Tests for inline-level parsing in AsciiDoc.
"""

import unittest

import pytest

from asciidoctrine.lark_parser import parse_to_ast
from asciidoctrine.nodes import Span

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

    def test_list_item_starting_with_formatting(self):
        source = "* *PyPI Package*: https://pypi.org/project/asciidoctrine/\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        item = ast["blocks"][0]["items"][0]
        content_nodes = item["principal"]
        self.assertEqual(content_nodes[0]["name"], "span")
        self.assertEqual(content_nodes[0]["variant"], "strong")
        self.assertEqual(content_nodes[0]["inlines"][0]["value"], "PyPI Package")

    def test_list_item_with_link_macro(self):
        """link:URL[text] in a list item: the 'link:' prefix must be consumed
        by the inline_link rule, not left as literal text."""
        source = "* *PyPI Package*: link:https://pypi.org/project/asciidoctrine/[asciidoctrine on PyPI]\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        item = ast["blocks"][0]["items"][0]
        content_nodes = item["principal"]
        # The text between bold span and link should be ': ' only.
        self.assertEqual(content_nodes[1]["value"], ": ")
        ref_node = content_nodes[2]
        self.assertEqual(ref_node["name"], "ref")
        self.assertEqual(ref_node["variant"], "link")
        self.assertEqual(ref_node["target"], "https://pypi.org/project/asciidoctrine/")
        self.assertEqual(ref_node["inlines"][0]["value"], "asciidoctrine on PyPI")

    def test_explicit_link_macro_with_link_prefix(self):
        """link:URL[text] in a paragraph: the 'link:' prefix must be consumed
        by the inline_link rule, making the preceding text 'See '."""
        source = "See link:https://asciidoc.org/[AsciiDoc] for details.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        # The preceding text should be 'See ', not 'See link:'
        self.assertEqual(paragraph["inlines"][0]["value"], "See ")
        ref = paragraph["inlines"][1]
        self.assertEqual(ref["name"], "ref")
        self.assertEqual(ref["variant"], "link")
        self.assertEqual(ref["target"], "https://asciidoc.org/")
        self.assertEqual(ref["inlines"][0]["value"], "AsciiDoc")

    def test_inline_image_with_url_target(self):
        source = "See image:https://example.com/logo.png[Logo] for details.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        self.assertEqual(paragraph["inlines"][0]["value"], "See ")
        img = paragraph["inlines"][1]
        self.assertEqual(img["name"], "image")
        self.assertEqual(img["target"], "https://example.com/logo.png")

    def test_icon_inline_with_url_target(self):
        source = "See icon:https://example.com/icon.png[Icon] for details.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        self.assertEqual(paragraph["inlines"][0]["value"], "See ")
        icon = paragraph["inlines"][1]
        self.assertEqual(icon["name"], "icon")
        self.assertEqual(icon["target"], "https://example.com/icon.png")

    def test_xref_inline_with_url_target(self):
        source = "See xref:https://example.com/doc.html[Doc] for details.\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        paragraph = ast["blocks"][0]
        self.assertEqual(paragraph["inlines"][0]["value"], "See ")
        ref = paragraph["inlines"][1]
        self.assertEqual(ref["name"], "ref")
        self.assertEqual(ref["variant"], "xref")
        self.assertEqual(ref["target"], "https://example.com/doc.html")

    def test_bold_bare_link_parsing(self):
        source = "* *https://example.com*\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        item = ast["blocks"][0]["items"][0]
        span = item["principal"][0]
        self.assertEqual(span["name"], "span")
        self.assertEqual(span["variant"], "strong")
        ref = span["inlines"][0]
        self.assertEqual(ref["name"], "ref")
        self.assertEqual(ref["target"], "https://example.com")
        self.assertEqual(ref["attributes"]["role"], "bare")

    def test_nested_formatting_around_inline_link(self):
        source = "* *_link:https://example.com[https://example.com]_*\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        item = ast["blocks"][0]["items"][0]
        strong_span = item["principal"][0]
        self.assertEqual(strong_span["variant"], "strong")
        italic_span = strong_span["inlines"][0]
        self.assertEqual(italic_span["variant"], "emphasis")
        ref = italic_span["inlines"][0]
        self.assertEqual(ref["name"], "ref")
        self.assertEqual(ref["variant"], "link")
        self.assertEqual(ref["target"], "https://example.com")
        self.assertEqual(ref["inlines"][0]["value"], "https://example.com")

    def test_internationalized_and_advanced_urls(self):
        cases = [
            (
                "https://xn--bcher-kva.ch/search?q=test",
                "https://xn--bcher-kva.ch/search?q=test",
            ),
            (
                "https://münchen.de/stefan",
                "https://münchen.de/stefan",
            ),
            (
                "https://example.com/🍕/page",
                "https://example.com/🍕/page",
            ),
            (
                "data:text/plain;utf8,Hello%20World",
                "data:text/plain;utf8,Hello%20World",
            ),
            (
                "https://example.com/page.html?arg=value",
                "https://example.com/page.html?arg=value",
            ),
            (
                "tel:+1-555-0199",
                "tel:+1-555-0199",
            ),
            (
                "sms:+1-555-0199?body=Hello",
                "sms:+1-555-0199?body=Hello",
            ),
            (
                "wss://stream.example.com/socket",
                "wss://stream.example.com/socket",
            ),
            (
                "file:///path/to/doc.pdf",
                "file:///path/to/doc.pdf",
            ),
            (
                "git://github.com/webmaven/asciidoctrine.git",
                "git://github.com/webmaven/asciidoctrine.git",
            ),
        ]
        for src_url, expected_target in cases:
            source = f"See {src_url} for details.\n"
            ast = self._strip_locations(parse_to_ast(source).to_dict())
            paragraph = ast["blocks"][0]
            self.assertEqual(paragraph["inlines"][0]["value"], "See ")
            ref = paragraph["inlines"][1]
            self.assertEqual(ref["name"], "ref")
            self.assertEqual(ref["variant"], "link")
            self.assertEqual(ref["target"], expected_target)

    def test_custom_scheme_registration(self):
        source = "Join slack://channel/general or call zoommtg://zoom.us/join?id=123 for details.\n"
        ast = self._strip_locations(
            parse_to_ast(
                source,
                extra_authority_schemes=["slack", "zoommtg"],
            ).to_dict()
        )
        inlines = ast["blocks"][0]["inlines"]
        self.assertEqual(inlines[0]["value"], "Join ")
        self.assertEqual(inlines[1]["name"], "ref")
        self.assertEqual(inlines[1]["target"], "slack://channel/general")
        self.assertEqual(inlines[2]["value"], " or call ")
        self.assertEqual(inlines[3]["name"], "ref")
        self.assertEqual(inlines[3]["target"], "zoommtg://zoom.us/join?id=123")

    def test_custom_scheme_validation_errors(self):
        blacklisted = [
            "note",
            "to",
            "cc",
            "bcc",
            "date",
            "time",
            "ssn",
            "id",
            "link",
            "http",
            "image",
        ]
        for bad_scheme in blacklisted:
            with self.assertRaises(ValueError):
                parse_to_ast("test", extra_authority_schemes=[bad_scheme])

        # Test length limits
        with self.assertRaises(ValueError):
            parse_to_ast("test", extra_authority_schemes=["a"])  # Too short (<2)
        with self.assertRaises(ValueError):
            parse_to_ast(
                "test", extra_authority_schemes=["verylongschemename"]
            )  # Too long (>10)

        # Test invalid characters
        with self.assertRaises(ValueError):
            parse_to_ast("test", extra_authority_schemes=["bad_scheme!"])

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
        # 1. Parse bare URL (with role='bare' and inlines containing URL text)
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
        self.assertEqual(link_node["attributes"], {"role": "bare"})
        self.assertEqual(link_node["inlines"][0]["value"], "https://google.com")

        self.assertEqual(p_inlines[2]["value"], " for info.")

        # 2. Trailing punctuation stripping (dot must be separated)
        ast_punc = self._strip_locations(
            parse_to_ast("Go to https://google.com.").to_dict()
        )
        punc_inlines = ast_punc["blocks"][0]["inlines"]
        self.assertEqual(len(punc_inlines), 3)
        self.assertEqual(punc_inlines[1]["target"], "https://google.com")
        self.assertEqual(punc_inlines[2]["value"], ".")

        # 3. Angle brackets delineation stripping
        ast_bracket = self._strip_locations(
            parse_to_ast("See <https://google.com> here.").to_dict()
        )
        bracket_inlines = ast_bracket["blocks"][0]["inlines"]
        self.assertEqual(len(bracket_inlines), 3)
        self.assertEqual(bracket_inlines[0]["value"], "See ")
        self.assertEqual(bracket_inlines[1]["target"], "https://google.com")
        self.assertEqual(bracket_inlines[2]["value"], " here.")

        # 4. Escaping behavior (preceding backslash makes it plain text, and
        #    the result merges with surrounding text)
        ast_escape = self._strip_locations(
            parse_to_ast("Go to \\https://google.com").to_dict()
        )
        escape_inlines = ast_escape["blocks"][0]["inlines"]
        # After escaping, 'Go to ' and 'https://google.com' merge into one Text
        self.assertEqual(len(escape_inlines), 1)
        self.assertEqual(escape_inlines[0]["value"], "Go to https://google.com")

        # 5. Bare Email autolinks
        ast_email = self._strip_locations(
            parse_to_ast("Contact user@example.com for help.").to_dict()
        )
        email_inlines = ast_email["blocks"][0]["inlines"]
        self.assertEqual(len(email_inlines), 3)
        self.assertEqual(email_inlines[0]["value"], "Contact ")
        email_node = email_inlines[1]
        self.assertEqual(email_node["name"], "ref")
        self.assertEqual(email_node["variant"], "link")
        self.assertEqual(email_node["target"], "mailto:user@example.com")
        self.assertEqual(email_node["attributes"], {"role": "bare"})
        self.assertEqual(email_node["inlines"][0]["value"], "user@example.com")
        self.assertEqual(email_inlines[2]["value"], " for help.")

        # 6. Escaped Email
        ast_esc_email = self._strip_locations(
            parse_to_ast("Send to \\user@example.com").to_dict()
        )
        esc_email_inlines = ast_esc_email["blocks"][0]["inlines"]
        # After escaping, 'Send to ' and 'user@example.com' merge into one Text
        self.assertEqual(len(esc_email_inlines), 1)
        self.assertEqual(esc_email_inlines[0]["value"], "Send to user@example.com")

        # 7. Serialize bare URL
        from asciidoctrine.serializer import AsciiDocSerializerVisitor

        doc = parse_to_ast("Visit https://google.com for info.")
        serialized = AsciiDocSerializerVisitor().serialize(doc)
        self.assertEqual(serialized.strip(), "Visit https://google.com for info.")

        # 8. Render to docutils
        from asciidoctrine.docutils_backend import asciidoc_to_docutils

        docutils_root = asciidoc_to_docutils("Visit https://google.com for info.")
        # Search for reference node
        import docutils.nodes as docutils_nodes

        ref_nodes = list(docutils_root.findall(docutils_nodes.reference))
        self.assertEqual(len(ref_nodes), 1)
        self.assertEqual(ref_nodes[0]["refuri"], "https://google.com")
        self.assertEqual(ref_nodes[0].astext(), "https://google.com")

        # 9. Standard link with attributes takes priority over bare URL
        ast2 = self._strip_locations(
            parse_to_ast("Visit https://google.com[Google] today.").to_dict()
        )
        p_inlines2 = ast2["blocks"][0]["inlines"]
        link_node2 = p_inlines2[1]
        self.assertEqual(link_node2["name"], "ref")
        self.assertEqual(link_node2["variant"], "link")
        self.assertEqual(link_node2["target"], "https://google.com")
        self.assertEqual(link_node2["inlines"][0]["value"], "Google")

    def test_inline_passthrough_serialization(self) -> None:
        from asciidoctrine.nodes import InlinePassthrough
        from asciidoctrine.serializer import AsciiDocSerializerVisitor

        # 1. Macro form
        node_macro = InlinePassthrough(value="raw_html_macro")
        node_macro.form = "macro"
        serialized_macro = AsciiDocSerializerVisitor().serialize(node_macro)
        self.assertEqual(serialized_macro, "pass:[raw_html_macro]")

        # 2. Triple plus form
        node_triple = InlinePassthrough(value="raw_html_triple")
        node_triple.form = "triple_plus"
        serialized_triple = AsciiDocSerializerVisitor().serialize(node_triple)
        self.assertEqual(serialized_triple, "+++raw_html_triple+++")

    def test_marked_and_span_roles(self) -> None:
        # 1. Bare marked text
        source = "#text#\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        span = ast["blocks"][0]["inlines"][0]
        self.assertEqual(span["name"], "span")
        self.assertEqual(span["variant"], "mark")
        self.assertEqual(span["form"], "constrained")
        self.assertEqual(span["inlines"][0]["value"], "text")

        # 2. Single role on marked text
        source = "[.underline]#text#\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        span = ast["blocks"][0]["inlines"][0]
        self.assertEqual(span["name"], "span")
        self.assertEqual(span["variant"], "mark")
        self.assertEqual(span["attributes"]["role"], "underline")
        self.assertEqual(span["inlines"][0]["value"], "text")

        # 3. Multiple roles on marked text
        source = "[.role1.role2]#text#\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        span = ast["blocks"][0]["inlines"][0]
        self.assertEqual(span["attributes"]["role"], "role1 role2")

        # 4. Role + ID on marked text
        source = "[#myid.highlight]#text#\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        span = ast["blocks"][0]["inlines"][0]
        self.assertEqual(span["attributes"]["id"], "myid")
        self.assertEqual(span["attributes"]["role"], "highlight")

        # 5. Unconstrained marked text
        source = "##text##\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        span = ast["blocks"][0]["inlines"][0]
        self.assertEqual(span["name"], "span")
        self.assertEqual(span["variant"], "mark")
        self.assertEqual(span["form"], "unconstrained")
        self.assertEqual(span["inlines"][0]["value"], "text")

        # 6. Unconstrained marked text with role
        source = "[.line-through]##struck##\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        span = ast["blocks"][0]["inlines"][0]
        self.assertEqual(span["name"], "span")
        self.assertEqual(span["variant"], "mark")
        self.assertEqual(span["form"], "unconstrained")
        self.assertEqual(span["attributes"]["role"], "line-through")

        # 7. Role on bold
        source = "[.important]*bold*\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        span = ast["blocks"][0]["inlines"][0]
        self.assertEqual(span["variant"], "strong")
        self.assertEqual(span["attributes"]["role"], "important")

        # 8. Role on italic
        source = "[.cite]_italic_\n"
        ast = self._strip_locations(parse_to_ast(source).to_dict())
        span = ast["blocks"][0]["inlines"][0]
        self.assertEqual(span["variant"], "emphasis")
        self.assertEqual(span["attributes"]["role"], "cite")

        # 9. Docutils backend role class mapping
        from asciidoctrine.docutils_backend import asciidoc_to_docutils

        # 9a. Marked text with role -> inline node with CSS class
        doc1 = asciidoc_to_docutils("[.line-through]##struck##\n")
        para1 = doc1[0]
        span1 = para1[0]
        self.assertIn("line-through", span1["classes"])

        # 9b. Bold with role -> strong node with CSS class
        doc2 = asciidoc_to_docutils("[.important]*bold*\n")
        para2 = doc2[0]
        span2 = para2[0]
        self.assertIn("important", span2["classes"])

    def test_footnote_resolution_and_catalog(self):
        from asciidoctrine.resolver import ASGResolver

        source = (
            "First footnote:[first note]. "
            "Second footnoteref:[fn1, second note]. "
            "Third footnoteref:[fn1].\n"
        )
        ast = parse_to_ast(source)
        resolved = ASGResolver(ast).resolve(ast)

        # Check inlines and ref indices
        inlines = resolved["blocks"][0]["inlines"]
        refs = [
            n
            for n in inlines
            if n.get("name") == "ref" and n.get("variant") == "footnote"
        ]
        self.assertEqual(len(refs), 3)
        self.assertEqual(refs[0]["index"], 1)
        self.assertEqual(refs[1]["index"], 2)
        self.assertEqual(refs[2]["index"], 2)

        # Check footnotes catalog on resolved Document ASG
        self.assertIn("footnotes", resolved)
        footnotes = resolved["footnotes"]
        self.assertEqual(len(footnotes), 2)

        # First footnote entry
        self.assertEqual(footnotes[0]["index"], 1)
        self.assertIsNone(footnotes[0]["id"])
        self.assertEqual(footnotes[0]["text"], "first note")
        self.assertEqual(footnotes[0]["inlines"][0]["value"], "first note")

        # Second footnote entry
        self.assertEqual(footnotes[1]["index"], 2)
        self.assertEqual(footnotes[1]["id"], "fn1")
        self.assertEqual(footnotes[1]["text"], "second note")
        self.assertEqual(footnotes[1]["inlines"][0]["value"], "second note")

    def test_footnote_nested_formatting_and_attributes(self):
        from asciidoctrine.resolver import ASGResolver

        source = (
            ":author: John Doe\n\n"
            "This footnote:[A note by {author} with *bold* text].\n"
        )
        ast = parse_to_ast(source)
        resolved = ASGResolver(ast).resolve(ast)

        self.assertIn("footnotes", resolved)
        fn = resolved["footnotes"][0]
        self.assertEqual(fn["index"], 1)
        self.assertIsNone(fn["id"])
        self.assertEqual(fn["text"], "A note by John Doe with bold text")
        # Inlines check: Text("A note by John Doe with "), Span(variant="strong", inlines=[Text("bold")]), Text(" text")
        self.assertEqual(len(fn["inlines"]), 3)
        self.assertEqual(fn["inlines"][0]["value"], "A note by John Doe with ")
        self.assertEqual(fn["inlines"][1]["name"], "span")
        self.assertEqual(fn["inlines"][1]["variant"], "strong")
        self.assertEqual(fn["inlines"][1]["inlines"][0]["value"], "bold")
        self.assertEqual(fn["inlines"][2]["value"], " text")

    def test_footnote_forward_reference(self):
        from asciidoctrine.resolver import ASGResolver

        source = (
            "Ref first footnoteref:[fn-fwd], "
            "then define footnoteref:[fn-fwd, Forward defined note].\n"
        )
        ast = parse_to_ast(source)
        resolved = ASGResolver(ast).resolve(ast)

        inlines = resolved["blocks"][0]["inlines"]
        refs = [
            n
            for n in inlines
            if n.get("name") == "ref" and n.get("variant") == "footnote"
        ]
        self.assertEqual(len(refs), 2)
        self.assertEqual(refs[0]["index"], 1)
        self.assertEqual(refs[1]["index"], 1)

        self.assertIn("footnotes", resolved)
        self.assertEqual(len(resolved["footnotes"]), 1)
        fn = resolved["footnotes"][0]
        self.assertEqual(fn["id"], "fn-fwd")
        self.assertEqual(fn["index"], 1)
        self.assertEqual(fn["text"], "Forward defined note")

    def test_document_without_footnotes(self):
        from asciidoctrine.resolver import ASGResolver

        source = "Just a regular paragraph.\n"
        ast = parse_to_ast(source)
        resolved = ASGResolver(ast).resolve(ast)

        self.assertNotIn("footnotes", resolved)

    def test_mid_identifier_underscores_plain_text(self):
        source = "The function `some_function_name` or plain some_function_name and var_name_2.\n"
        doc = parse_to_ast(source)
        p = doc.blocks[0]
        # Inlines: "The function ", `some_function_name` (code span), " or plain some_function_name and var_name_2."
        text_nodes = [node for node in p.inlines if node.name == "text"]
        full_text = "".join(n.value for n in text_nodes)
        assert "some_function_name" in full_text
        assert "var_name_2" in full_text
        # Ensure no italic span was generated from some_function_name
        span_variants = [node.variant for node in p.inlines if node.name == "span"]
        assert "emphasis" not in span_variants

    def test_constrained_italic_with_punctuation_boundaries(self):
        source = (
            'This is (_italic_), "_quoted italic_", and _italic_ at word boundaries.\n'
        )
        doc = parse_to_ast(source)
        p = doc.blocks[0]
        spans = [
            node
            for node in p.inlines
            if node.name == "span" and node.variant == "emphasis"
        ]
        assert len(spans) == 3
        assert spans[0].inlines[0].value == "italic"
        assert spans[1].inlines[0].value == "quoted italic"
        assert spans[2].inlines[0].value == "italic"

    def test_unconstrained_italic_inside_words(self):
        source = "This is un__doubt__edly unconstrained.\n"
        doc = parse_to_ast(source)
        p = doc.blocks[0]
        spans = [
            node
            for node in p.inlines
            if node.name == "span" and node.variant == "emphasis"
        ]
        assert len(spans) == 1
        assert spans[0].form == "unconstrained"
        assert spans[0].inlines[0].value == "doubt"

    def test_consecutive_comma_separated_backtick_spans(self):
        content = "hooks (`hook_0`, `hook_1`, `hook_2`, `hook_3`) end."
        doc = parse_to_ast(content)
        para = doc.blocks[0]
        # Check that inlines contain 4 separate code spans with comma/space separators
        code_spans = [
            span
            for span in para.inlines
            if isinstance(span, Span) and span.variant == "code"
        ]
        assert len(code_spans) == 4
        for i, span in enumerate(code_spans):
            assert span.inlines[0].value == f"hook_{i}"

    def test_constrained_monospace_with_punctuation_boundaries(self):
        source = 'This is (`code`), "`quoted code`", and `code` at word boundaries.\n'
        doc = parse_to_ast(source)
        p = doc.blocks[0]
        spans = [
            node for node in p.inlines if node.name == "span" and node.variant == "code"
        ]
        assert len(spans) == 3
        assert spans[0].inlines[0].value == "code"
        assert spans[1].inlines[0].value == "quoted code"
        assert spans[2].inlines[0].value == "code"

    def test_unconstrained_monospace_inside_words(self):
        source = "This is un``doubt``edly unconstrained.\n"
        doc = parse_to_ast(source)
        p = doc.blocks[0]
        spans = [
            node for node in p.inlines if node.name == "span" and node.variant == "code"
        ]
        assert len(spans) == 1
        assert spans[0].form == "unconstrained"
        assert spans[0].inlines[0].value == "doubt"

    def test_monospace_whitespace_boundary_non_match(self):
        # Leading or trailing whitespace within constrained backticks should not produce code spans
        source1 = "Not a ` code` span.\n"
        doc1 = parse_to_ast(source1)
        spans1 = [
            node
            for node in doc1.blocks[0].inlines
            if node.name == "span" and node.variant == "code"
        ]
        assert len(spans1) == 0

        source2 = "Not a `code ` span.\n"
        doc2 = parse_to_ast(source2)
        spans2 = [
            node
            for node in doc2.blocks[0].inlines
            if node.name == "span" and node.variant == "code"
        ]
        assert len(spans2) == 0


class TestInlineMacroAttachedToPunctuation(TestInlines):
    """Tests for issue #120: inline macros attached directly to preceding words/punctuation."""

    def _inlines(self, source: str):
        return parse_to_ast(source).blocks[0].inlines

    # ── footnote ──────────────────────────────────────────────────────────────

    def test_footnote_attached_to_period(self):
        """statement.footnote:[Note] → text("statement.") + ref(footnote)"""
        nodes = self._inlines("This is a statement.footnote:[Note text]\n")
        ref_nodes = [n for n in nodes if n.name == "ref" and n.variant == "footnote"]
        self.assertEqual(len(ref_nodes), 1)
        text_nodes = [n for n in nodes if n.name == "text"]
        combined = "".join(n.value for n in text_nodes)
        self.assertIn("statement", combined)
        self.assertNotIn("footnote", combined)

    def test_footnote_attached_to_word(self):
        """word directly followed by footnote: (lowercase, no punctuation gap) → text + ref.
        Note: macro names are case-sensitive; 'Footnote:' is not a macro."""
        nodes = self._inlines("wordfootnote:[Note text]\n")
        # 'footnote' is reached as an inline macro; 'word' remains as text
        ref_nodes = [n for n in nodes if n.name == "ref" and n.variant == "footnote"]
        self.assertEqual(len(ref_nodes), 1)
        text_nodes = [n for n in nodes if n.name == "text"]
        combined = "".join(n.value for n in text_nodes)
        self.assertIn("word", combined)

    def test_footnoteref_attached_to_period(self):
        """statement.footnoteref:[id,text] → text + ref(footnote)"""
        nodes = self._inlines("See statement.footnoteref:[fn1, Some text]\n")
        ref_nodes = [n for n in nodes if n.name == "ref" and n.variant == "footnote"]
        self.assertEqual(len(ref_nodes), 1)

    # ── indexterm ─────────────────────────────────────────────────────────────

    def test_indexterm_attached_to_word(self):
        """term.indexterm:[primary] → text + indexterm node"""
        nodes = self._inlines("IndexTermindexterm:[primary term]\n")
        idx_nodes = [n for n in nodes if n.name == "indexterm"]
        self.assertEqual(len(idx_nodes), 1)

    # ── preceded by space (regression: these must still work) ─────────────────

    def test_footnote_preceded_by_space_still_works(self):
        """Whitespace-separated footnote must continue to parse correctly."""
        nodes = self._inlines("This is a statement. footnote:[Note text]\n")
        ref_nodes = [n for n in nodes if n.name == "ref" and n.variant == "footnote"]
        self.assertEqual(len(ref_nodes), 1)

    def test_footnoteref_preceded_by_space_still_works(self):
        nodes = self._inlines("See this. footnoteref:[fn1, Some text]\n")
        ref_nodes = [n for n in nodes if n.name == "ref" and n.variant == "footnote"]
        self.assertEqual(len(ref_nodes), 1)

    def test_word_tokenizer_with_uri_scheme_suffixes(self):
        # Metadata ends in data:
        text1 = "* *Metadata:*"
        ast1 = self._strip_locations(parse_to_ast(text1).to_dict())
        self.assertEqual(len(ast1["blocks"]), 1)

        text2 = "Subdata: something"
        ast2 = self._strip_locations(parse_to_ast(text2).to_dict())
        self.assertEqual(len(ast2["blocks"]), 1)

        # Control case
        text3 = "* *Metadat:*"
        ast3 = self._strip_locations(parse_to_ast(text3).to_dict())
        self.assertEqual(len(ast3["blocks"]), 1)

        # Additional URI schemes: tel:, sms:, mailto:
        text_tel = "* *Cartel:*"
        ast_tel = self._strip_locations(parse_to_ast(text_tel).to_dict())
        self.assertEqual(len(ast_tel["blocks"]), 1)

        text_sms = "* *Cosms:*"
        ast_sms = self._strip_locations(parse_to_ast(text_sms).to_dict())
        self.assertEqual(len(ast_sms["blocks"]), 1)

        text_mailto = "* *sendmailto:*"
        ast_mailto = self._strip_locations(parse_to_ast(text_mailto).to_dict())
        self.assertEqual(len(ast_mailto["blocks"]), 1)

        # Ensure valid URI schemes still match properly
        text_uri1 = "data:image/png;base64,iVBORw0KGgo= image"
        ast_uri1 = self._strip_locations(parse_to_ast(text_uri1).to_dict())
        ref1 = ast_uri1["blocks"][0]["inlines"][0]
        self.assertEqual(ref1["name"], "ref")
        self.assertEqual(ref1["variant"], "link")
        self.assertEqual(ref1["target"], "data:image/png;base64,iVBORw0KGgo=")

        text_uri2 = "Contact mailto:user@example.com for info"
        ast_uri2 = self._strip_locations(parse_to_ast(text_uri2).to_dict())
        ref2 = ast_uri2["blocks"][0]["inlines"][1]
        self.assertEqual(ref2["name"], "ref")
        self.assertEqual(ref2["variant"], "link")
        self.assertEqual(ref2["target"], "mailto:user@example.com")

        text_uri3 = "Call tel:+123456789 now"
        ast_uri3 = self._strip_locations(parse_to_ast(text_uri3).to_dict())
        ref3 = ast_uri3["blocks"][0]["inlines"][1]
        self.assertEqual(ref3["name"], "ref")
        self.assertEqual(ref3["variant"], "link")
        self.assertEqual(ref3["target"], "tel:+123456789")


class TestInlineParsing(TestInlines):
    """Tests for inline macro backslash escaping (#124, #113)."""

    def test_backslash_escaped_inline_macro(self):
        # 1. Plain paragraph with backslash-escaped xref macro
        source_plain = r"\xref:chapter-02.adoc#anchor[Chapter 2]" + "\n"
        doc_plain = parse_to_ast(source_plain)
        p_plain = doc_plain.blocks[0]
        # Must not contain any Ref nodes
        ref_nodes = [n for n in p_plain.inlines if n.name == "ref"]
        self.assertEqual(len(ref_nodes), 0)
        # Must emit literal text without leading backslash
        text_nodes = [n for n in p_plain.inlines if n.name == "text"]
        self.assertEqual(len(text_nodes), 1)
        self.assertEqual(text_nodes[0].value, "xref:chapter-02.adoc#anchor[Chapter 2]")

        # 2. Escaped xref preceded by text
        source_preceded = (
            r"See \xref:chapter-02.adoc#anchor[Chapter 2] for details." + "\n"
        )
        doc_preceded = parse_to_ast(source_preceded)
        p_preceded = doc_preceded.blocks[0]
        ref_nodes = [n for n in p_preceded.inlines if n.name == "ref"]
        self.assertEqual(len(ref_nodes), 0)
        text_nodes = [n for n in p_preceded.inlines if n.name == "text"]
        combined = "".join(n.value for n in text_nodes)
        self.assertEqual(
            combined, "See xref:chapter-02.adoc#anchor[Chapter 2] for details."
        )

        # 3. Escaped link macro
        source_link = r"\link:https://asciidoc.org[AsciiDoc Site]" + "\n"
        doc_link = parse_to_ast(source_link)
        p_link = doc_link.blocks[0]
        ref_nodes = [n for n in p_link.inlines if n.name == "ref"]
        self.assertEqual(len(ref_nodes), 0)
        text_nodes = [n for n in p_link.inlines if n.name == "text"]
        combined = "".join(n.value for n in text_nodes)
        self.assertEqual(combined, "link:https://asciidoc.org[AsciiDoc Site]")

        # 4. Monospace span with escaped xref macro
        source_mono = r"`\xref:chapter-02.adoc#anchor[Chapter 2]`" + "\n"
        doc_mono = parse_to_ast(source_mono)
        p_mono = doc_mono.blocks[0]

        def _get_all_refs(nodes):
            refs = []
            for n in nodes:
                if n.name == "ref":
                    refs.append(n)
                if hasattr(n, "inlines"):
                    refs.extend(_get_all_refs(n.inlines))
            return refs

        self.assertEqual(len(_get_all_refs(p_mono.inlines)), 0)
        code_spans = [
            n for n in p_mono.inlines if n.name == "span" and n.variant == "code"
        ]
        self.assertEqual(len(code_spans), 1)
        self.assertEqual(
            code_spans[0].inlines[0].value, "xref:chapter-02.adoc#anchor[Chapter 2]"
        )

        # 5. ASGResolver does not fail on escaped xref macros
        from asciidoctrine.resolver import ASGResolver

        resolver = ASGResolver(doc_plain)
        resolved = resolver.resolve(doc_plain)
        self.assertIsNotNone(resolved)

    def test_backslash_escaped_inline_macro_in_monospace_with_surrounding_text(self):
        source = (
            r"Refer to `\xref:chapter-02.adoc#anchor[Chapter 2]` in the manual." + "\n"
        )
        doc = parse_to_ast(source)
        p = doc.blocks[0]
        # No active Ref nodes
        refs = [n for n in p.inlines if n.name == "ref"]
        self.assertEqual(len(refs), 0)
        # Check inlines structure: text, code span, text
        self.assertEqual(len(p.inlines), 3)
        self.assertEqual(p.inlines[0].value, "Refer to ")
        self.assertEqual(p.inlines[1].name, "span")
        self.assertEqual(p.inlines[1].variant, "code")
        self.assertEqual(
            p.inlines[1].inlines[0].value, "xref:chapter-02.adoc#anchor[Chapter 2]"
        )
        self.assertEqual(p.inlines[2].value, " in the manual.")

    def test_backslash_escaped_inline_macro_other_types(self):
        # Image macro escaped
        doc_img = parse_to_ast(r"\image:sunset.png[Sunset]" + "\n")
        p_img = doc_img.blocks[0]
        images = [n for n in p_img.inlines if n.name == "image"]
        self.assertEqual(len(images), 0)
        self.assertEqual(p_img.inlines[0].value, "image:sunset.png[Sunset]")

        # Footnote macro escaped
        doc_fn = parse_to_ast(r"Text \footnote:[Footnote content] here." + "\n")
        p_fn = doc_fn.blocks[0]
        fn_refs = [
            n for n in p_fn.inlines if n.name == "ref" and n.variant == "footnote"
        ]
        self.assertEqual(len(fn_refs), 0)
        combined_fn = "".join(n.value for n in p_fn.inlines if n.name == "text")
        self.assertEqual(combined_fn, "Text footnote:[Footnote content] here.")

        # Kbd macro escaped
        doc_kbd = parse_to_ast(r"Press \kbd:[Ctrl+S] to save." + "\n")
        p_kbd = doc_kbd.blocks[0]
        kbds = [n for n in p_kbd.inlines if n.name == "kbd"]
        self.assertEqual(len(kbds), 0)
        combined_kbd = "".join(n.value for n in p_kbd.inlines if n.name == "text")
        self.assertEqual(combined_kbd, "Press kbd:[Ctrl+S] to save.")

    def test_double_backslash_preserves_active_macro(self):
        # Two backslashes: first escapes second, leaving active macro preceded by literal '\'
        source = r"\\xref:target[Label]" + "\n"
        doc = parse_to_ast(source)
        p = doc.blocks[0]
        ref_nodes = [n for n in p.inlines if n.name == "ref"]
        self.assertEqual(len(ref_nodes), 1)
        self.assertEqual(ref_nodes[0].variant, "xref")
        self.assertEqual(ref_nodes[0].target, "target")
        text_nodes = [n for n in p.inlines if n.name == "text"]
        self.assertEqual(len(text_nodes), 1)
        self.assertEqual(text_nodes[0].value, "\\")


if __name__ == "__main__":
    unittest.main()
