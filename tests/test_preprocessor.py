"""
Tests for the AsciiDoc preprocessor.
"""

import os
import tempfile
import unittest

import pytest

from asciidoctrine.preprocessor import Preprocessor, PreprocessorError

pytestmark = pytest.mark.unit


class PreprocessorTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test fixtures using tempfile.TemporaryDirectory
        self._temp_dir_obj = tempfile.TemporaryDirectory()
        self.base_dir = self._temp_dir_obj.name

        # Create some sample files
        with open(os.path.join(self.base_dir, "main.adoc"), "w") as f:
            f.write("= Main Document\n\ninclude::paragraph.adoc[]")
        with open(os.path.join(self.base_dir, "paragraph.adoc"), "w") as f:
            f.write("This is an included paragraph.")

        # For nested includes
        with open(os.path.join(self.base_dir, "nested_main.adoc"), "w") as f:
            f.write("Level 1\ninclude::nested_child.adoc[]")
        with open(os.path.join(self.base_dir, "nested_child.adoc"), "w") as f:
            f.write("Level 2\ninclude::nested_grandchild.adoc[]")
        with open(os.path.join(self.base_dir, "nested_grandchild.adoc"), "w") as f:
            f.write("Level 3")

        # For circular includes
        with open(os.path.join(self.base_dir, "circular_a.adoc"), "w") as f:
            f.write("Circular A\ninclude::circular_b.adoc[]")
        with open(os.path.join(self.base_dir, "circular_b.adoc"), "w") as f:
            f.write("Circular B\ninclude::circular_a.adoc[]")

        # For security tests
        self._outside_dir_obj = tempfile.TemporaryDirectory()
        self.outside_dir = self._outside_dir_obj.name
        with open(os.path.join(self.outside_dir, "secret.adoc"), "w") as f:
            f.write("This is a secret file.")

    def tearDown(self):
        # Clean up the temporary directories
        self._temp_dir_obj.cleanup()
        self._outside_dir_obj.cleanup()

    def test_basic_include(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::main.adoc[]"
        processed = preprocessor.process(source)
        expected = "= Main Document\n\nThis is an included paragraph."
        self.assertEqual(processed.strip(), expected.strip())

    def test_nested_include(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::nested_main.adoc[]"
        processed = preprocessor.process(source)
        expected = "Level 1\nLevel 2\nLevel 3"
        self.assertEqual(processed.strip(), expected.strip())

    def test_file_not_found(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::nonexistent.adoc[]"
        with self.assertRaises(PreprocessorError) as context:
            preprocessor.process(source)
        self.assertIn("Include file not found", str(context.exception))

    def test_circular_include(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::circular_a.adoc[]"
        with self.assertRaises(PreprocessorError) as context:
            preprocessor.process(source)
        self.assertIn("Circular include detected", str(context.exception))

    def test_security_path_traversal(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        # Attempt to access a file outside the base_dir
        source = "include::../outside_fixtures/secret.adoc[]"
        with self.assertRaises(PreprocessorError) as context:
            preprocessor.process(source)
        self.assertIn(
            "attempts to access files outside the base directory",
            str(context.exception),
        )

    def test_include_with_leveloffset_relative(self):
        # Create a file with heading titles
        with open(os.path.join(self.base_dir, "headings.adoc"), "w") as f:
            f.write("= Title\n\n== Section 1\n\n=== Section 1.1")

        preprocessor = Preprocessor(base_dir=self.base_dir)

        # Test shift up (+1)
        source = "include::headings.adoc[leveloffset=+1]"
        processed = preprocessor.process(source)
        expected = "== Title\n\n=== Section 1\n\n==== Section 1.1"
        self.assertEqual(processed.strip(), expected.strip())

        # Test shift down (-1)
        source = "include::headings.adoc[leveloffset=-1]"
        processed = preprocessor.process(source)
        expected = "Title\n\n= Section 1\n\n== Section 1.1"
        self.assertEqual(processed.strip(), expected.strip())

    def test_include_with_leveloffset_absolute(self):
        with open(os.path.join(self.base_dir, "headings.adoc"), "w") as f:
            f.write("= Title\n\n== Section 1")

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::headings.adoc[leveloffset=2]"
        processed = preprocessor.process(source)
        # Shifted by +2
        expected = "=== Title\n\n==== Section 1"
        self.assertEqual(processed.strip(), expected.strip())

    def test_include_with_lines_single_range(self):
        with open(os.path.join(self.base_dir, "lines.txt"), "w") as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::lines.txt[lines=2..4]"
        processed = preprocessor.process(source)
        expected = "Line 2\nLine 3\nLine 4"
        self.assertEqual(processed.strip(), expected.strip())

    def test_include_with_lines_multiple_ranges(self):
        with open(os.path.join(self.base_dir, "lines.txt"), "w") as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

        preprocessor = Preprocessor(base_dir=self.base_dir)

        # Semicolon separated
        source = "include::lines.txt[lines=1..2;4..5]"
        processed = preprocessor.process(source)
        expected = "Line 1\nLine 2\nLine 4\nLine 5"
        self.assertEqual(processed.strip(), expected.strip())

        # Comma separated (quoted)
        source = 'include::lines.txt[lines="1..2,4..5"]'
        processed = preprocessor.process(source)
        expected = "Line 1\nLine 2\nLine 4\nLine 5"
        self.assertEqual(processed.strip(), expected.strip())

    def test_include_with_tag(self):
        with open(os.path.join(self.base_dir, "tagged.txt"), "w") as f:
            f.write(
                "Before tag\n// tag::snippet[]\nInside 1\nInside 2\n// end::snippet[]\nAfter tag\n"
            )

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::tagged.txt[tag=snippet]"
        processed = preprocessor.process(source)
        expected = "Inside 1\nInside 2"
        self.assertEqual(processed.strip(), expected.strip())

    def test_include_with_tags(self):
        with open(os.path.join(self.base_dir, "tagged_multiple.txt"), "w") as f:
            f.write(
                "Before\n"
                "// tag::first[]\n"
                "One\n"
                "// end::first[]\n"
                "Middle\n"
                "// tag::second[]\n"
                "Two\n"
                "// end::second[]\n"
                "After\n"
            )

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::tagged_multiple.txt[tags=first;second]"
        processed = preprocessor.process(source)
        expected = "One\nTwo"
        self.assertEqual(processed.strip(), expected.strip())

    def test_include_with_combined_attributes(self):
        with open(os.path.join(self.base_dir, "combined.adoc"), "w") as f:
            f.write(
                "= Main Title\n"
                "// tag::content[]\n"
                "== Subtitle\n"
                "Paragraph\n"
                "// end::content[]\n"
                "Other content\n"
            )

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::combined.adoc[tag=content,leveloffset=+1]"
        processed = preprocessor.process(source)
        expected = "=== Subtitle\nParagraph"
        self.assertEqual(processed.strip(), expected.strip())

    def test_unbalanced_block_delimiter_warning(self):
        # Create a child include file that opens a listing block with ---- but never closes it.
        with open(os.path.join(self.base_dir, "unbalanced.adoc"), "w") as f:
            f.write("Some text\n----\nListing text\n")

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::unbalanced.adoc[]"

        import warnings

        from asciidoctrine.preprocessor import PreprocessorWarning

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            processed = preprocessor.process(source)
            # Ensure the preprocessor ran to completion despite the warning
            self.assertIn("Some text\n----\nListing text", processed)

            # Verify that the PreprocessorWarning was raised
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, PreprocessorWarning))
            self.assertIn("unbalanced block delimiters", str(w[0].message))

    def test_balanced_block_delimiters_no_warning(self):
        # Create a child include file that cleanly opens and closes a listing block.
        with open(os.path.join(self.base_dir, "balanced.adoc"), "w") as f:
            f.write("Some text\n----\nListing text\n----\n")

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::balanced.adoc[]"

        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            processed = preprocessor.process(source)
            self.assertIn("Some text\n----\nListing text\n----", processed)

            # Verify that no warnings were raised
            self.assertEqual(len(w), 0)

    def test_parse_attributes_edge_cases(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        # 1. Single quotes inside and double quotes
        attrs = preprocessor._parse_attributes(
            "title='single quote',author=\"Double Quote\""
        )
        self.assertEqual(attrs.get("title"), "single quote")
        self.assertEqual(attrs.get("author"), "Double Quote")

        # 2. Empty attribute chunks
        attrs = preprocessor._parse_attributes(",,tag=snippet,,")
        self.assertEqual(attrs.get("tag"), "snippet")

        # 3. Attribute key with no value
        attrs = preprocessor._parse_attributes("some_option")
        self.assertIn("some_option", attrs)
        self.assertEqual(attrs.get("some_option"), "")

    def test_unfiltered_tag_stripping(self):
        # When tag/end comments are present in an include, but no tag/tags attribute is provided,
        # those comment tag lines must be automatically stripped out of the output.
        with open(os.path.join(self.base_dir, "tagged_comments.adoc"), "w") as f:
            f.write("Start\n// tag::my-tag[]\nMiddle\n// end::my-tag[]\nEnd\n")

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::tagged_comments.adoc[]"
        processed = preprocessor.process(source)
        expected = "Start\nMiddle\nEnd"
        self.assertEqual(processed.strip(), expected.strip())

    def test_lines_slicing_edge_cases(self):
        with open(os.path.join(self.base_dir, "many_lines.txt"), "w") as f:
            f.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")

        preprocessor = Preprocessor(base_dir=self.base_dir)

        # 1. Empty lines slices (semicolons/commas with no value in between)
        source = 'include::many_lines.txt[lines="1..2;;4..5"]'
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Line 1\nLine 2\nLine 4\nLine 5")

        # 2. Slices with single lines (e.g. lines="1,3,5")
        source = 'include::many_lines.txt[lines="1,3,5"]'
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Line 1\nLine 3\nLine 5")

        # 3. Handling invalid line entries (e.g., abc) cleanly by raising ValueError and ignoring them
        source = 'include::many_lines.txt[lines="1..2,abc,4..5"]'
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Line 1\nLine 2\nLine 4\nLine 5")

        # 4. Slices with no end value (e.g., lines="3..")
        source = 'include::many_lines.txt[lines="3.."]'
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Line 3\nLine 4\nLine 5")


if __name__ == "__main__":
    unittest.main()
