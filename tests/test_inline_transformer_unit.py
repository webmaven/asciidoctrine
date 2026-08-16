import pytest
"""
Unit tests for InlineTransformer in asciidoctrine.
"""

import unittest
from unittest.mock import patch

from lark import Token

from asciidoctrine.lark_parser import AsciiDocTransformer
from asciidoctrine.nodes import Break, Span, Text



pytestmark = pytest.mark.unit
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


    def test_inline_pass_macro_and_triple_plus(self):
        """inline_pass_macro and inline_triple_plus must produce InlinePassthrough nodes."""
        from asciidoctrine.nodes import InlinePassthrough

        content = Token("PASS_CONTENT", "<b>raw</b>")
        res = self.transformer.inline_pass_macro(None, [content])
        self.assertIsInstance(res, InlinePassthrough)
        self.assertEqual(res.value, "<b>raw</b>")
        self.assertEqual(res.form, "macro")

        res2 = self.transformer.inline_triple_plus(None, [content])
        self.assertIsInstance(res2, InlinePassthrough)
        self.assertEqual(res2.value, "<b>raw</b>")
        self.assertEqual(res2.form, "triple_plus")

        # Empty children edge case
        res3 = self.transformer.inline_pass_macro(None, [None])
        self.assertEqual(res3.value, "")
        res4 = self.transformer.inline_triple_plus(None, [None])
        self.assertEqual(res4.value, "")

    def test_bare_url_link_with_trailing_punctuation(self):
        """bare_url_link must strip trailing punctuation and return it as a separate Text."""
        from asciidoctrine.nodes import Ref, Text

        # URL with trailing period and comma
        uri = Token("URI", "https://example.com,")
        result = self.transformer.bare_url_link(None, [uri])
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Ref)
        self.assertEqual(result[0].target, "https://example.com")
        self.assertIsInstance(result[1], Text)
        self.assertEqual(result[1].value, ",")

        # URL with no trailing punctuation — only the Ref is returned
        uri2 = Token("URI", "https://example.com")
        result2 = self.transformer.bare_url_link(None, [uri2])
        self.assertEqual(len(result2), 1)
        self.assertIsInstance(result2[0], Ref)
        self.assertEqual(result2[0].target, "https://example.com")
        self.assertEqual(result2[0].attributes.get("role"), "bare")

    def test_bare_email_link(self):
        """bare_email_link must return a Ref with mailto: scheme."""
        from asciidoctrine.nodes import Ref

        email_tok = Token("EMAIL", "user@example.com")
        res = self.transformer.bare_email_link(None, [email_tok])
        self.assertIsInstance(res, Ref)
        self.assertEqual(res.variant, "link")
        self.assertEqual(res.target, "mailto:user@example.com")
        self.assertEqual(res.inlines[0].value, "user@example.com")
        self.assertEqual(res.attributes.get("role"), "bare")

    def test_inline_image_with_image_prefix_token(self):
        """inline_image must skip a leading IMAGE_PREFIX token."""
        prefix = Token("IMAGE_PREFIX", "image:")
        target = Token("TARGET", "photo.jpg")
        attrs = {"style": "A photo", "width": "200"}
        res = self.transformer.inline_image(None, [prefix, target, attrs])
        self.assertEqual(res.target, "photo.jpg")
        self.assertEqual(res.attributes.get("alt"), "A photo")
        self.assertEqual(res.attributes.get("width"), "200")

    def test_icon_inline_with_icon_prefix_token(self):
        """icon_inline must skip a leading ICON_PREFIX token."""
        prefix = Token("ICON_PREFIX", "icon:")
        target = Token("TARGET", "star")
        attrs = {"size": "2x"}
        res = self.transformer.icon_inline(None, [prefix, target, attrs])
        self.assertEqual(res.target, "star")
        self.assertEqual(res.name, "icon")
        self.assertEqual(res.attributes.get("size"), "2x")

    def test_inline_anchor_with_anchor_prefix_and_uri_type(self):
        """inline_anchor must handle ANCHOR_PREFIX + URI token."""
        prefix = Token("ANCHOR_PREFIX", "[[")
        uri = Token("URI", "my-anchor-id")
        res = self.transformer.inline_anchor(None, [prefix, uri, {}])
        self.assertEqual(res.variant, "anchor")
        self.assertEqual(res.target, "my-anchor-id")

    def test_inline_xref_with_xref_prefix_and_uri_type(self):
        """inline_xref must handle XREF_PREFIX + URI token."""
        prefix = Token("XREF_PREFIX", "xref:")
        uri = Token("URI", "other-doc.adoc")
        attrs = {"style": "Other Doc"}
        res = self.transformer.inline_xref(None, [prefix, uri, attrs])
        self.assertEqual(res.variant, "xref")
        self.assertEqual(res.target, "other-doc.adoc")
        self.assertEqual(res.inlines[0].value, "Other Doc")

    def test_inline_link_link_prefix_branch(self):
        """inline_link must handle LINK_PREFIX + URI children."""
        from asciidoctrine.nodes import Ref

        prefix = Token("LINK_PREFIX", "link:")
        target = Token("TARGET", "https://docs.example.com")
        attrs = {"style": "Docs"}
        res = self.transformer.inline_link(None, [prefix, target, attrs])
        self.assertIsInstance(res, Ref)
        self.assertEqual(res.target, "https://docs.example.com")
        self.assertEqual(res.inlines[0].value, "Docs")

    def test_inline_link_link_prefix_no_attrs(self):
        """inline_link LINK_PREFIX branch without attribute dict."""
        prefix = Token("LINK_PREFIX", "link:")
        target = Token("TARGET", "https://no-attrs.com")
        res = self.transformer.inline_link(None, [prefix, target])
        self.assertEqual(res.target, "https://no-attrs.com")
        self.assertEqual(res.inlines, [])

    def test_inline_link_new_window_caret(self):
        """inline_link must set window=_blank when label ends with '^'."""
        target = Token("TARGET", "https://example.com")
        attrs = {"style": "Open^"}
        res = self.transformer.inline_link(None, [target, attrs])
        self.assertEqual(res.attributes.get("window"), "_blank")
        self.assertEqual(res.inlines[0].value, "Open")

    def test_inline_link_bare_uri_no_attrs(self):
        """inline_link bare URI branch with no attributes."""
        target = Token("URI", "https://bare.example.com")
        res = self.transformer.inline_link(None, [target])
        self.assertEqual(res.target, "https://bare.example.com")
        self.assertEqual(res.inlines, [])

    def test_inline_stem_default_asciimath(self):
        """inline_stem defaults to asciimath when stem attribute is not set."""
        self.transformer.attributes = {}
        content = Token("STEM_CONTENT", "x^2")
        res = self.transformer.inline_stem(None, [content])
        self.assertEqual(res.variant, "asciimath")
        self.assertEqual(res.value, "x^2")

    def test_inline_stem_empty_children(self):
        """inline_stem with empty/None children produces empty value."""
        self.transformer.attributes = {}
        res = self.transformer.inline_stem(None, [None])
        self.assertEqual(res.value, "")

    def test_inline_asciimath_empty_children(self):
        res = self.transformer.inline_asciimath(None, [None])
        self.assertEqual(res.variant, "asciimath")
        self.assertEqual(res.value, "")

    def test_inline_latexmath_empty_children(self):
        res = self.transformer.inline_latexmath(None, [None])
        self.assertEqual(res.variant, "latexmath")
        self.assertEqual(res.value, "")

    def test_inline_menu_no_items(self):
        """inline_menu with only one child produces empty items list."""
        menu_name = Token("MENU_NAME", "View")
        res = self.transformer.inline_menu(None, [menu_name])
        self.assertEqual(res.menu, "View")
        self.assertEqual(res.items, [])

    def test_inline_menu_none_items_child(self):
        """inline_menu where second child is None produces empty items."""
        menu_name = Token("MENU_NAME", "Edit")
        res = self.transformer.inline_menu(None, [menu_name, None])
        self.assertEqual(res.menu, "Edit")
        self.assertEqual(res.items, [])

    def test_indexterm_flow_double_empty_children(self):
        """inline_indexterm_flow_double with empty children list."""
        from asciidoctrine.nodes import IndexTerm

        res = self.transformer.inline_indexterm_flow_double(None, [])
        self.assertIsInstance(res, IndexTerm)
        self.assertEqual(res.terms, [])
        self.assertEqual(res.variant, "flow_double")

    def test_indexterm_flow_triple(self):
        """inline_indexterm_flow_triple must split comma-separated terms."""
        from asciidoctrine.nodes import IndexTerm, Text

        nodes_list = [Text("primary, secondary")]
        res = self.transformer.inline_indexterm_flow_triple(None, [nodes_list])
        self.assertIsInstance(res, IndexTerm)
        self.assertEqual(res.variant, "flow_triple")
        self.assertEqual(res.terms, ["primary", "secondary"])

    def test_indexterm_flow_triple_empty_children(self):
        """inline_indexterm_flow_triple with empty children."""
        from asciidoctrine.nodes import IndexTerm

        res = self.transformer.inline_indexterm_flow_triple(None, [])
        self.assertIsInstance(res, IndexTerm)
        self.assertEqual(res.terms, [])

    def test_text_content_backslash_escaped_bare_url(self):
        """text_content must convert a backslash-escaped bare Ref to plain Text."""
        from asciidoctrine.nodes import Ref, Text

        # Simulate: prev text node ending in '\', followed by a bare Ref
        escaped_text = Text("Visit \\")
        bare_ref = Ref(
            variant="link",
            target="https://example.com",
            inlines=[Text("https://example.com")],
        )
        bare_ref.attributes["role"] = "bare"
        result = self.transformer.text_content(None, [escaped_text, bare_ref])
        # The backslash should be stripped and the Ref converted to plain Text
        full_text = "".join(n.value for n in result if isinstance(n, Text))
        self.assertIn("https://example.com", full_text)
        self.assertNotIn("\\", full_text)
        # No Ref should survive
        for n in result:
            self.assertNotIsInstance(n, Ref)

    def test_text_content_backslash_escaped_mailto(self):
        """text_content backslash escape strips 'mailto:' prefix for email display."""
        from asciidoctrine.nodes import Ref, Text

        escaped_text = Text("Email \\")
        bare_ref = Ref(
            variant="link",
            target="mailto:user@example.com",
            inlines=[Text("user@example.com")],
        )
        bare_ref.attributes["role"] = "bare"
        result = self.transformer.text_content(None, [escaped_text, bare_ref])
        full_text = "".join(n.value for n in result if isinstance(n, Text))
        # Should display the bare email address, not the mailto: form
        self.assertIn("user@example.com", full_text)
        self.assertNotIn("mailto:", full_text)

    def test_text_content_pending_attrs_no_following_node(self):
        """pending_attrs with no following node must be emitted as literal [key=val] text."""
        from asciidoctrine.nodes import Text

        # An attrs dict with no following node — hits the trailing pending_attrs path
        attrs = {"role": "special", "id": "sec1"}
        result = self.transformer.text_content(None, [attrs])
        # Should produce a single Text node with the attrs serialised
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Text)
        self.assertIn("[", result[0].value)

    def test_text_content_merge_consecutive_text_nodes(self):
        """Adjacent Text nodes with same attributes must be merged."""
        from asciidoctrine.nodes import Text

        t1 = Token("WORD", "Hello")
        t2 = Token("WORD", " World")
        result = self.transformer.text_content(None, [t1, t2])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, "Hello World")

    def test_unconstrained_marked_content(self):
        """unconstrained_marked_content delegates to text_content."""
        result = self.transformer.unconstrained_marked_content(
            None, [Token("WORD", "highlight")]
        )
        self.assertEqual(result[0].value, "highlight")

    def test_unconstrained_marked(self):
        """unconstrained_marked produces a mark Span with unconstrained form."""
        res = self.transformer.unconstrained_marked(None, [[Text("hi")]])
        self.assertEqual(res.variant, "mark")
        self.assertEqual(res.form, "unconstrained")

    def test_double_and_single_quoted_empty(self):
        """double_quoted/single_quoted with no children produce empty Spans."""
        res_d = self.transformer.double_quoted(None, [])
        self.assertEqual(res_d.variant, "double")
        self.assertEqual(res_d.inlines, [])

        res_s = self.transformer.single_quoted(None, [])
        self.assertEqual(res_s.variant, "single")
        self.assertEqual(res_s.inlines, [])

    def test_inline_indexterm_macro_with_quotes(self):
        """inline_indexterm_macro must strip quotes from term strings."""
        from asciidoctrine.nodes import IndexTerm

        content = Token("INDEX_CONTENT", '"primary", \'secondary\'')
        res = self.transformer.inline_indexterm_macro(None, [content])
        self.assertIsInstance(res, IndexTerm)
        self.assertEqual(res.terms, ["primary", "secondary"])

    def test_inline_indexterm_macro_empty(self):
        """inline_indexterm_macro with None child produces empty terms."""
        from asciidoctrine.nodes import IndexTerm

        res = self.transformer.inline_indexterm_macro(None, [None])
        self.assertIsInstance(res, IndexTerm)
        self.assertEqual(res.terms, [])

    def test_inline_bibref_no_comma(self):
        """inline_bibref with no comma keeps full target."""
        from asciidoctrine.nodes import Ref, Text

        nodes_list = [Text("my-ref")]
        res = self.transformer.inline_bibref(None, [nodes_list])
        self.assertIsInstance(res, Ref)
        self.assertEqual(res.variant, "bibref")
        self.assertEqual(res.target, "my-ref")


if __name__ == "__main__":
    unittest.main()
