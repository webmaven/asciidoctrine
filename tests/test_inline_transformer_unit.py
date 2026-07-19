"""
Unit tests for InlineTransformer in asciidoctrine.
"""

import unittest
from unittest.mock import patch

from lark import Token

from asciidoctrine.lark_parser import AsciiDocTransformer
from asciidoctrine.nodes import Break, Span, Text


class TestInlineTransformerUnit(unittest.TestCase):
    def setUp(self):
        self.transformer = AsciiDocTransformer()
        self.transformer.attributes = {}

    def test_attribute_reference_found(self):
        self.transformer.attributes = {"my-attr": [Text("resolved-value")]}
        token = Token("ATTR_NAME", "my-attr")
        result = self.transformer.attribute_reference(None, [token])
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Text)
        self.assertEqual(result[0].value, "resolved-value")

    def test_attribute_reference_not_found(self):
        self.transformer.attributes = {}
        token = Token("ATTR_NAME", "missing")
        result = self.transformer.attribute_reference(None, [token])
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Text)
        self.assertEqual(result[0].value, "{missing}")

    def test_text_content_pending_attrs_role(self):
        token = Token("WORD", "hello")
        attrs = {"role": "blue", "foo": "bar"}
        result = self.transformer.text_content(None, [attrs, token])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, "hello")
        self.assertEqual(result[0].attributes["role"], "blue")
        self.assertEqual(result[0].attributes["foo"], "bar")

    def test_text_content_pending_attrs_append_role(self):
        span = Span(variant="strong", inlines=[Text("bold")])
        span.attributes["role"] = "red"
        result = self.transformer.text_content(None, [{"role": "blue"}, span])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].attributes["role"], "red blue")

    def test_text_content_nested_lists(self):
        token = Token("WORD", "hello")
        result = self.transformer.text_content(None, [[token]])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, "hello")

    def test_bold_content_and_variants(self):
        # bold_content
        result = self.transformer.bold_content(None, [Token("WORD", "boldtext")])
        self.assertEqual(result[0].value, "boldtext")

        # bold
        res = self.transformer.bold(None, [[Text("bold")]])
        self.assertEqual(res.variant, "strong")
        self.assertEqual(res.form, "constrained")
        self.assertEqual(res.inlines[0].value, "bold")

        # unconstrained_bold
        res = self.transformer.unconstrained_bold(None, [[Text("ubold")]])
        self.assertEqual(res.variant, "strong")
        self.assertEqual(res.form, "unconstrained")

    def test_italic_content_and_variants(self):
        # italic_content
        result = self.transformer.italic_content(None, [Token("WORD", "italictext")])
        self.assertEqual(result[0].value, "italictext")

        # italic
        res = self.transformer.italic(None, [[Text("italic")]])
        self.assertEqual(res.variant, "emphasis")
        self.assertEqual(res.form, "constrained")

        # unconstrained_italic
        res = self.transformer.unconstrained_italic(None, [[Text("uitalic")]])
        self.assertEqual(res.variant, "emphasis")
        self.assertEqual(res.form, "unconstrained")

    def test_marked_content_and_variants(self):
        # marked_content
        result = self.transformer.marked_content(None, [Token("WORD", "markedtext")])
        self.assertEqual(result[0].value, "markedtext")

        # marked
        res = self.transformer.marked(None, [[Text("marked")]])
        self.assertEqual(res.variant, "mark")

    def test_superscript_content_and_variants(self):
        # superscript_content
        result = self.transformer.superscript_content(
            None, [Token("WORD", "supertext")]
        )
        self.assertEqual(result[0].value, "supertext")

        # superscript
        res = self.transformer.superscript(None, [[Text("super")]])
        self.assertEqual(res.variant, "superscript")

    def test_subscript_content_and_variants(self):
        # subscript_content
        result = self.transformer.subscript_content(None, [Token("WORD", "subtext")])
        self.assertEqual(result[0].value, "subtext")

        # subscript
        res = self.transformer.subscript(None, [[Text("sub")]])
        self.assertEqual(res.variant, "subscript")

    def test_footnote_text_content_and_variants(self):
        # footnote_text_content
        result = self.transformer.footnote_text_content(
            None, [Token("WORD", "footnotetext")]
        )
        self.assertEqual(result[0].value, "footnotetext")

        # footnote
        res = self.transformer.footnote(None, [[Text("note text")]])
        self.assertEqual(res.variant, "footnote")
        self.assertEqual(res.target, "")
        self.assertEqual(res.inlines[0].value, "note text")

        # footnoteref with target FN_ID and inlines
        fn_id = Token("FN_ID", "fn-1")
        res = self.transformer.footnoteref(None, [fn_id, [Text("note text")]])
        self.assertEqual(res.variant, "footnote")
        self.assertEqual(res.target, "fn-1")
        self.assertEqual(res.inlines[0].value, "note text")

        # footnoteref with target WORD
        fn_word = Token("WORD", "fn-2")
        res = self.transformer.footnoteref(None, [fn_word])
        self.assertEqual(res.variant, "footnote")
        self.assertEqual(res.target, "fn-2")
        self.assertEqual(res.inlines, [])

    def test_literal_content_and_monospace_variants(self):
        # literal_content
        res_str = self.transformer.literal_content(None, [Token("WORD", "literaltext")])
        self.assertEqual(res_str, "literaltext")

        # monospace_content
        result = self.transformer.monospace_content(None, [Token("WORD", "monotext")])
        self.assertEqual(result[0].value, "monotext")

        # unconstrained_monospace_content
        result = self.transformer.unconstrained_monospace_content(
            None, [Token("WORD", "umonotext")]
        )
        self.assertEqual(result[0].value, "umonotext")

        # monospace
        res = self.transformer.monospace(None, [[Text("mono")]])
        self.assertEqual(res.variant, "code")
        self.assertEqual(res.form, "constrained")

        # unconstrained_monospace
        res = self.transformer.unconstrained_monospace(None, [[Text("umono")]])
        self.assertEqual(res.variant, "code")
        self.assertEqual(res.form, "unconstrained")

    def test_quotes(self):
        # double_quoted
        res = self.transformer.double_quoted(None, [[Text("double text")]])
        self.assertEqual(res.variant, "double")
        self.assertEqual(res.inlines[0].value, "double text")

        # single_quoted
        res = self.transformer.single_quoted(None, [[Text("single text")]])
        self.assertEqual(res.variant, "single")
        self.assertEqual(res.inlines[0].value, "single text")

    def test_images_and_icons(self):
        # inline_image
        target = Token("TARGET", "logo.png")
        attrs = {"style": "Logo Image", "width": "100"}
        res = self.transformer.inline_image(None, [target, attrs])
        self.assertEqual(res.target, "logo.png")
        self.assertEqual(res.attributes["alt"], "Logo Image")
        self.assertEqual(res.attributes["width"], "100")
        self.assertEqual(res.form, "macro")
        self.assertEqual(res.type, "inline")

        # icon_inline
        target = Token("TARGET", "heart")
        attrs = {"size": "lg"}
        res = self.transformer.icon_inline(None, [target, attrs])
        self.assertEqual(res.target, "heart")
        self.assertEqual(res.name, "icon")
        self.assertEqual(res.attributes["size"], "lg")

    def test_inline_anchors_and_xrefs(self):
        # inline_anchor with TARGET token
        target = Token("TARGET", "my-target")
        attrs = {"style": "My Label"}
        res = self.transformer.inline_anchor(None, [target, attrs])
        self.assertEqual(res.variant, "anchor")
        self.assertEqual(res.target, "my-target")
        self.assertEqual(res.inlines[0].value, "My Label")

        # inline_anchor with nodes (split on comma)
        nodes = [Text("my-target,Other label")]
        res = self.transformer.inline_anchor(None, [nodes])
        self.assertEqual(res.variant, "anchor")
        self.assertEqual(res.target, "my-target")

        # inline_xref with TARGET token
        target = Token("TARGET", "my-target")
        attrs = {"style": "My Label"}
        res = self.transformer.inline_xref(None, [target, attrs])
        self.assertEqual(res.variant, "xref")
        self.assertEqual(res.target, "my-target")
        self.assertEqual(res.inlines[0].value, "My Label")

        # inline_xref with nodes (split on comma)
        nodes = [Text("my-target,Label Text")]
        res = self.transformer.inline_xref(None, [nodes])
        self.assertEqual(res.variant, "xref")
        self.assertEqual(res.target, "my-target")
        self.assertEqual(res.inlines[0].value, "Label Text")

    def test_inline_link_try_except_coverage(self):
        # Force parse_inlines to raise exception
        with patch(
            "asciidoctrine.lark_parser.parse_inlines",
            side_effect=Exception("mocked error"),
        ):
            target = Token("TARGET", "https://google.com")
            attrs = {"style": "Google"}
            res = self.transformer.inline_link(None, [target, attrs])
            self.assertEqual(res.variant, "link")
            self.assertEqual(res.target, "https://google.com")
            self.assertEqual(res.inlines[0].value, "Google")

    def test_inline_bibref(self):
        # inline_bibref with comma
        nodes = [Text("my-bib,Extra Label")]
        res = self.transformer.inline_bibref(None, [nodes])
        self.assertEqual(res.variant, "bibref")
        self.assertEqual(res.target, "my-bib")

    def test_miscellaneous_inlines(self):
        # inline_break
        res = self.transformer.inline_break(None, [])
        self.assertIsInstance(res, Break)

        # inline_kbd
        content = Token("KBD_CONTENT", "Ctrl+Alt+Del")
        res = self.transformer.inline_kbd(None, [content])
        self.assertEqual(res.value, ["Ctrl", "Alt", "Del"])

        # inline_button
        btn = Token("BTN_CONTENT", "Save")
        res = self.transformer.inline_button(None, [btn])
        self.assertEqual(res.value, "Save")

        # inline_menu with items
        menu = Token("MENU_NAME", "File")
        items = Token("MENU_ITEMS", "New > Project")
        res = self.transformer.inline_menu(None, [menu, items])
        self.assertEqual(res.menu, "File")
        self.assertEqual(res.items, ["New", "Project"])

        # inline_callout
        co = Token("CALLOUT", "3")
        res = self.transformer.inline_callout(None, [co])
        self.assertEqual(res.value, 3)

    def test_stem_variants(self):
        # inline_stem with attribute 'stem'
        self.transformer.attributes = {"stem": [Text("latexmath")]}
        content = Token("STEM_CONTENT", "e=mc^2")
        res = self.transformer.inline_stem(None, [content])
        self.assertEqual(res.variant, "latexmath")
        self.assertEqual(res.value, "e=mc^2")

        # inline_asciimath()
        res = self.transformer.inline_asciimath(None, [content])
        self.assertEqual(res.variant, "asciimath")
        self.assertEqual(res.value, "e=mc^2")

        # inline_latexmath()
        res = self.transformer.inline_latexmath(None, [content])
        self.assertEqual(res.variant, "latexmath")
        self.assertEqual(res.value, "e=mc^2")


if __name__ == "__main__":
    unittest.main()
