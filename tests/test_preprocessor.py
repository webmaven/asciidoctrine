"""
Tests for the AsciiDoc preprocessor.
"""

import os
import tempfile
import unittest
import warnings

import pytest

from asciidoctrine.preprocessor import (
    Preprocessor,
    PreprocessorError,
    PreprocessorWarning,
)

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
        from asciidoctrine.preprocessor import CircularIncludeError

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::circular_a.adoc[]"
        with self.assertRaises(CircularIncludeError) as context:
            preprocessor.process(source)

        err_str = str(context.exception)
        self.assertIn(
            "Circular include detected: circular_a.adoc -> circular_b.adoc -> circular_a.adoc",
            err_str,
        )

        # Assert location info and carets are present for both files in the loop
        self.assertIn('File "circular_a.adoc", line 2:', err_str)
        self.assertIn("include::circular_b.adoc[]", err_str)
        self.assertIn("^~~~~~~~~~~~~~~~~~~~~~~~~~", err_str)

        self.assertIn('File "circular_b.adoc", line 2:', err_str)
        self.assertIn("include::circular_a.adoc[]", err_str)
        self.assertIn("^~~~~~~~~~~~~~~~~~~~~~~~~~", err_str)

    def test_circular_include_diagnostic_formatting(self):
        from asciidoctrine.preprocessor import CircularIncludeError

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::circular_a.adoc[]"
        with self.assertRaises(CircularIncludeError) as context:
            preprocessor.process(source)

        err_str = str(context.exception)
        # Verify cycle arrow chain and header
        self.assertIn(
            "Circular include detected: circular_a.adoc -> circular_b.adoc -> circular_a.adoc",
            err_str,
        )
        # Verify file locations and caret pointers in diagnostic output
        self.assertIn(
            'File "circular_a.adoc", line 2:\n    include::circular_b.adoc[]\n    ^~~~~~~~~~~~~~~~~~~~~~~~~~',
            err_str,
        )
        self.assertIn(
            'File "circular_b.adoc", line 2:\n    include::circular_a.adoc[]\n    ^~~~~~~~~~~~~~~~~~~~~~~~~~',
            err_str,
        )

    def test_multiple_sibling_includes(self):
        # Create helper file
        helper_path = os.path.join(self.base_dir, "helper.adoc")
        with open(helper_path, "w") as f:
            f.write("helper content\n")

        # Create main file with two inclusions of helper
        main_path = os.path.join(self.base_dir, "multi_sibling.adoc")
        with open(main_path, "w") as f:
            f.write("include::helper.adoc[]\ninclude::helper.adoc[]")

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::multi_sibling.adoc[]"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "helper content\nhelper content")

    def test_complex_tangle_circular_includes(self):
        from asciidoctrine.preprocessor import CircularIncludeError

        # Create a three-file tangle with mutual includes
        with open(os.path.join(self.base_dir, "tangle_a.adoc"), "w") as f:
            f.write("include::tangle_b.adoc[]\ninclude::tangle_c.adoc[]")
        with open(os.path.join(self.base_dir, "tangle_b.adoc"), "w") as f:
            f.write("include::tangle_c.adoc[]\ninclude::tangle_a.adoc[]")
        with open(os.path.join(self.base_dir, "tangle_c.adoc"), "w") as f:
            f.write("include::tangle_a.adoc[]\ninclude::tangle_b.adoc[]")

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::tangle_a.adoc[]"
        with self.assertRaises(CircularIncludeError) as context:
            preprocessor.process(source)

        err_str = str(context.exception)
        # Assert that the cyclic loop trace is captured
        self.assertIn(
            "Circular include detected: tangle_a.adoc -> tangle_b.adoc -> tangle_c.adoc -> tangle_a.adoc",
            err_str,
        )

        # Assert all mutual includes across all three files in the cycle are listed
        self.assertIn('File "tangle_a.adoc", line 1:', err_str)
        self.assertIn("include::tangle_b.adoc[]", err_str)
        self.assertIn("^~~~~~~~~~~~~~~~~~~~~~~~", err_str)
        self.assertIn('File "tangle_a.adoc", line 2:', err_str)
        self.assertIn("include::tangle_c.adoc[]", err_str)
        self.assertIn("^~~~~~~~~~~~~~~~~~~~~~~~", err_str)

        self.assertIn('File "tangle_b.adoc", line 1:', err_str)
        self.assertIn("include::tangle_c.adoc[]", err_str)
        self.assertIn("^~~~~~~~~~~~~~~~~~~~~~~~", err_str)
        self.assertIn('File "tangle_b.adoc", line 2:', err_str)
        self.assertIn("include::tangle_a.adoc[]", err_str)
        self.assertIn("^~~~~~~~~~~~~~~~~~~~~~~~", err_str)

        self.assertIn('File "tangle_c.adoc", line 1:', err_str)
        self.assertIn("include::tangle_a.adoc[]", err_str)
        self.assertIn("^~~~~~~~~~~~~~~~~~~~~~~~", err_str)
        self.assertIn('File "tangle_c.adoc", line 2:', err_str)
        self.assertIn("include::tangle_b.adoc[]", err_str)
        self.assertIn("^~~~~~~~~~~~~~~~~~~~~~~~", err_str)

    def test_circular_include_file_read_failure(self):
        from unittest.mock import patch

        from asciidoctrine.preprocessor import CircularIncludeError

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::circular_a.adoc[]"

        # Mock open so that when circular_b.adoc is opened during static scanning, it raises OSError
        original_open = open
        open_counts = {}

        def side_effect(file, *args, **kwargs):
            file_str = str(file)
            if "circular_b.adoc" in file_str and args and args[0] == "r":
                open_counts[file_str] = open_counts.get(file_str, 0) + 1
                if open_counts[file_str] > 1:
                    raise OSError("Simulated read failure during static scan")
            return original_open(file, *args, **kwargs)

        with patch("builtins.open", side_effect):
            with self.assertRaises(CircularIncludeError) as context:
                preprocessor.process(source)

        err_str = str(context.exception)
        # Assert that circular_a.adoc's include is still shown, but circular_b.adoc's is skipped due to read failure
        self.assertIn('File "circular_a.adoc", line 2:', err_str)
        self.assertNotIn('File "circular_b.adoc", line 2:', err_str)

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

    def test_security_sibling_directory_traversal(self):
        # Create a sibling directory to base_dir
        sibling_dir = self.base_dir + "_sibling"
        os.makedirs(sibling_dir, exist_ok=True)
        secret_file = os.path.join(sibling_dir, "secret.adoc")
        try:
            with open(secret_file, "w") as f:
                f.write("sensitive content")

            # Formulate include path relative to base_dir pointing to sibling_dir
            relative_path = os.path.join(
                "..", os.path.basename(sibling_dir), "secret.adoc"
            )

            preprocessor = Preprocessor(base_dir=self.base_dir)
            source = f"include::{relative_path}[]"
            with self.assertRaises(PreprocessorError) as context:
                preprocessor.process(source)
            self.assertIn(
                "attempts to access files outside the base directory",
                str(context.exception),
            )
        finally:
            if os.path.exists(secret_file):
                os.remove(secret_file)
            if os.path.exists(sibling_dir):
                os.rmdir(sibling_dir)

    def test_security_commonpath_value_error(self):
        from unittest.mock import patch

        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = "include::paragraph.adoc[]"

        with patch("os.path.commonpath", side_effect=ValueError("mocked ValueError")):
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
            self.assertIn(
                "Some text\n--ASCIIDOCTRINE_OUTER_LISTING_START_4--\nListing text",
                processed,
            )

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
            self.assertIn(
                "Some text\n--ASCIIDOCTRINE_OUTER_LISTING_START_4--\nListing text\n--ASCIIDOCTRINE_OUTER_LISTING_END_4--",
                processed,
            )

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

    def test_same_length_listing_nesting_warning(self) -> None:
        source = """----
[source,python]
----
print("inner")
----
----"""
        preprocessor = Preprocessor(base_dir=self.base_dir)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            preprocessor.process(source)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, PreprocessorWarning))
            self.assertIn("same-length", str(w[0].message).lower())

    def test_same_length_literal_nesting_warning(self) -> None:
        source = """....
[style=literal]
....
inner
....
...."""
        preprocessor = Preprocessor(base_dir=self.base_dir)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            preprocessor.process(source)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, PreprocessorWarning))
            self.assertIn("same-length", str(w[0].message).lower())

    def test_is_metadata_relative_paths_no_warning(self) -> None:
        # Relative file or command paths starting with ./ or ../ or Windows counterparts
        # inside verbatim blocks should not be mistaken as metadata/block titles
        # and should not trigger false same-length nesting warnings on block close.
        source = """[source,bash]
----
./run-tck.sh
../run-tck-coverage.sh
.\\run.bat
----"""
        preprocessor = Preprocessor(base_dir=self.base_dir)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            preprocessor.process(source)
            self.assertEqual(len(w), 0)

    def test_block_title_is_metadata_edge_cases(self) -> None:
        # Test various edge cases for what should be recognized as block metadata vs what should be ignored.
        preprocessor = Preprocessor(base_dir=self.base_dir)

        # 1. A valid block title inside verbatim block preceding a same-length delimiter
        # SHOULD trigger a warning because it resembles a nested block opening.
        source_with_warning = """----
.Valid Title
----
print("inner")
----
----"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            preprocessor.process(source_with_warning)
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, PreprocessorWarning))
            self.assertIn("same-length", str(w[0].message).lower())

        # 2. File paths, decimal points, spaces, and single/multiple dots inside verbatim block
        # preceding a same-length delimiter should NOT trigger any warnings.
        source_no_warning = """----
./file.sh
../dir/file.py
.\\windows.bat
..\\windows_parent\\run
. 
.
..
...
----"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            preprocessor.process(source_no_warning)
            self.assertEqual(len(w), 0)

    def test_preprocess_directives_bypass(self) -> None:
        # Create a child include file that would be included if processed.
        with open(os.path.join(self.base_dir, "to_include.adoc"), "w") as f:
            f.write("Included text")

        source = "include::to_include.adoc[]\n\n----\nListing text\n----\n"

        # When preprocess_directives=False, the include directive should NOT be processed/replaced.
        # But standard outer listing block translation should still occur.
        preprocessor = Preprocessor(base_dir=self.base_dir, preprocess_directives=False)
        processed = preprocessor.process(source)

        self.assertIn("include::to_include.adoc[]", processed)
        self.assertNotIn("Included text", processed)
        self.assertIn(
            "--ASCIIDOCTRINE_OUTER_LISTING_START_4--\nListing text\n--ASCIIDOCTRINE_OUTER_LISTING_END_4--",
            processed,
        )

    def test_ifdef_defined(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {"show-content": "true"}
        source = "ifdef::show-content[]\nThis text should be visible.\nendif::[]"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "This text should be visible.")

    def test_ifdef_undefined(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {}
        source = "ifdef::show-content[]\nThis text should not be visible.\nendif::[]"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "")

    def test_ifdef_and_operator(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {"attr-a": "yes", "attr-b": "yes"}
        source = "ifdef::attr-a+attr-b[]\nVisible.\nendif::[]"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Visible.")

        # One missing
        preprocessor.attributes = {"attr-a": "yes"}
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "")

    def test_ifdef_or_operator(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {"attr-a": "yes"}
        source = "ifdef::attr-a,attr-b[]\nVisible.\nendif::[]"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Visible.")

        # Neither present
        preprocessor.attributes = {}
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "")

    def test_ifdef_negation(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {}
        source = "ifdef::!hidden-content[]\nVisible when not hidden.\nendif::[]"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Visible when not hidden.")

        # Hidden defined
        preprocessor.attributes = {"hidden-content": ""}
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "")

    def test_ifndef(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {}
        source = (
            "ifndef::some-attr[]\nVisible because some-attr is NOT defined.\nendif::[]"
        )
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Visible because some-attr is NOT defined.")

        # Defined
        preprocessor.attributes = {"some-attr": ""}
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "")

    def test_ifdef_single_line_shorthand(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {"show-it": "true"}
        source = "ifdef::show-it[This is single line text.]\nThis is always visible."
        processed = preprocessor.process(source)
        self.assertEqual(
            processed.strip(), "This is single line text.\nThis is always visible."
        )

        # Undefined
        preprocessor.attributes = {}
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "This is always visible.")

    def test_dynamic_attribute_definition(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = (
            ":my-dynamic-attr: hello\n"
            "ifdef::my-dynamic-attr[]\n"
            "Parsed dynamically.\n"
            "endif::[]\n"
            ":!my-dynamic-attr:\n"
            "ifdef::my-dynamic-attr[]\n"
            "Should not be parsed now.\n"
            "endif::[]"
        )
        processed = preprocessor.process(source)
        # Note: Attribute declarations themselves are preserved or kept as-is,
        # but the conditional blocks are evaluated.
        # Wait, does the preprocessor output the attribute declarations?
        # Yes, attribute entries can remain for the parser/resolver, or be stripped.
        # But wait! In standard AsciiDoc, attribute declarations on their own line are kept
        # in the output so the AST can parse them as attribute_entry nodes.
        # So we expect the output to preserve the attribute declarations.
        expected = ":my-dynamic-attr: hello\nParsed dynamically.\n:!my-dynamic-attr:"
        self.assertEqual(processed.strip(), expected.strip())

    def test_nested_ifdefs(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {"outer": "", "inner": ""}
        source = (
            "ifdef::outer[]\n"
            "Outer visible.\n"
            "ifdef::inner[]\n"
            "Inner visible.\n"
            "endif::[]\n"
            "Outer still visible.\n"
            "endif::[]"
        )
        processed = preprocessor.process(source)
        expected = "Outer visible.\nInner visible.\nOuter still visible."
        self.assertEqual(processed.strip(), expected.strip())

        # Inner disabled
        preprocessor.attributes = {"outer": ""}
        processed = preprocessor.process(source)
        expected = "Outer visible.\nOuter still visible."
        self.assertEqual(processed.strip(), expected.strip())

    def test_empty_condition_evaluation(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        # Empty condition inside ifdef or ifndef
        source = "ifdef::[]\nInside empty ifdef block.\nendif::[]"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "")

    def test_shorthand_ifndef_parsing(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {}
        # ifndef with shorthand body
        source = "ifndef::unset_attr[shorthand text for unset]"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "shorthand text for unset")

        # ifndef with shorthand body where attribute IS set
        preprocessor.attributes = {"unset_attr": "value"}
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "")

    def test_alternate_attribute_deletion(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        source = (
            ":my_attr: hello\n"
            "ifdef::my_attr[]\n"
            "Visible 1\n"
            "endif::[]\n"
            ":my_attr!:\n"
            "ifdef::my_attr[]\n"
            "Visible 2\n"
            "endif::[]"
        )
        processed = preprocessor.process(source)
        expected = ":my_attr: hello\nVisible 1\n:my_attr!:"
        self.assertEqual(processed.strip(), expected.strip())

    def test_include_inside_verbatim_block(self):
        # Create a file to include
        included_file = os.path.join(self.base_dir, "to_include.adoc")
        with open(included_file, "w") as f:
            f.write("content inside included file\n")

        try:
            preprocessor = Preprocessor(base_dir=self.base_dir)
            source = "----\ninclude::to_include.adoc[]\n----"
            processed = preprocessor.process(source)
            expected = (
                "--ASCIIDOCTRINE_OUTER_LISTING_START_4--\n"
                "content inside included file\n"
                "--ASCIIDOCTRINE_OUTER_LISTING_END_4--"
            )
            self.assertEqual(processed.strip(), expected.strip())
        finally:
            if os.path.exists(included_file):
                os.remove(included_file)

    def test_include_security_inside_verbatim_block(self):
        preprocessor = Preprocessor(base_dir=self.base_dir)
        # Attempt traversal include inside verbatim block
        source = "----\ninclude::../outside_fixtures/secret.adoc[]\n----"
        with self.assertRaises(PreprocessorError) as context:
            preprocessor.process(source)
        self.assertIn(
            "attempts to access files outside the base directory",
            str(context.exception),
        )

    def test_file_not_found_permissive(self):
        # In permissive mode (strict=False), missing include should emit PreprocessorWarning
        # and return an unresolved directive placeholder string
        preprocessor = Preprocessor(base_dir=self.base_dir, strict=False)
        source = "include::nonexistent_file.adoc[]"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            processed = preprocessor.process(source)

            # Assert warning was issued
            assert len(w) == 1
            assert issubclass(w[0].category, PreprocessorWarning)
            assert "Include file not found" in str(w[0].message)

            # Assert placeholder was returned
            expected = (
                "Unresolved directive in <root> - include::nonexistent_file.adoc[]"
            )
            assert processed.strip() == expected

    def test_named_endif_matching(self):
        """Named endif::backend[] should correctly close its matching ifdef::backend[]."""
        preprocessor = Preprocessor(base_dir=self.base_dir)
        preprocessor.attributes = {"backend": "html5"}
        source = "ifdef::backend[]\nVisible content\nendif::backend[]\n"
        processed = preprocessor.process(source)
        self.assertEqual(processed.strip(), "Visible content")

    def test_named_endif_mismatch_strict(self):
        """In strict mode, a mismatched named endif should raise PreprocessorError."""
        preprocessor = Preprocessor(base_dir=self.base_dir, strict=True)
        preprocessor.attributes = {"backend": "html5"}
        source = "ifdef::backend[]\nContent\nendif::wrong_name[]\n"
        with self.assertRaises(PreprocessorError) as context:
            preprocessor.process(source)
        self.assertIn("mismatch", str(context.exception).lower())

    def test_named_endif_mismatch_permissive(self):
        """In permissive mode, a mismatched named endif should still pop the stack (lenient)."""
        preprocessor = Preprocessor(base_dir=self.base_dir, strict=False)
        preprocessor.attributes = {"backend": "html5"}
        source = "ifdef::backend[]\nContent\nendif::wrong_name[]\nAfter endif\n"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            processed = preprocessor.process(source)
            # Should still work (pop the stack) but issue a warning
            self.assertIn("Content", processed)
            self.assertIn("After endif", processed)
            # Check that a warning was issued about the mismatch
            mismatch_warnings = [x for x in w if "mismatch" in str(x.message).lower()]
            self.assertGreater(len(mismatch_warnings), 0)

    def test_named_endif_with_ifeval(self):
        """Anonymous endif::[] should correctly close an ifeval block."""
        preprocessor = Preprocessor(base_dir=self.base_dir, strict=True)
        preprocessor.attributes = {"backend": "html5"}
        source = 'ifeval::["{backend}" == "html5"]\nHTML content\nendif::[]\n'
        processed = preprocessor.process(source)
        self.assertIn("HTML content", processed)

    def test_nested_named_endif_strict(self):
        """Named endifs in strict mode should match their corresponding openers in LIFO order."""
        preprocessor = Preprocessor(base_dir=self.base_dir, strict=True)
        preprocessor.attributes = {"outer": "", "inner": ""}
        source = (
            "ifdef::outer[]\n"
            "Outer\n"
            "ifdef::inner[]\n"
            "Inner\n"
            "endif::inner[]\n"
            "Still outer\n"
            "endif::outer[]\n"
        )
        processed = preprocessor.process(source)
        self.assertIn("Outer", processed)
        self.assertIn("Inner", processed)
        self.assertIn("Still outer", processed)


if __name__ == "__main__":
    unittest.main()


# ---------------------------------------------------------------------------
# ConditionalStack — is_active, __bool__
# ---------------------------------------------------------------------------


class TestConditionalStack:
    def test_is_active_empty_stack_returns_true(self):
        from asciidoctrine.preprocessor import ConditionalStack

        cs = ConditionalStack()
        assert cs.is_active() is True

    def test_is_active_all_active(self):
        from asciidoctrine.preprocessor import ConditionalStack

        cs = ConditionalStack()
        cs.push(True, "a", "ifdef")
        cs.push(True, "b", "ifdef")
        assert cs.is_active() is True

    def test_is_active_one_inactive(self):
        from asciidoctrine.preprocessor import ConditionalStack

        cs = ConditionalStack()
        cs.push(True, "a", "ifdef")
        cs.push(False, "b", "ifdef")
        assert cs.is_active() is False

    def test_bool_empty_is_false(self):
        from asciidoctrine.preprocessor import ConditionalStack

        cs = ConditionalStack()
        assert bool(cs) is False

    def test_bool_non_empty_is_true(self):
        from asciidoctrine.preprocessor import ConditionalStack

        cs = ConditionalStack()
        cs.push(True, "x", "ifdef")
        assert bool(cs) is True

    def test_pop_empty_returns_none(self):
        from asciidoctrine.preprocessor import ConditionalStack

        cs = ConditionalStack()
        assert cs.pop() is None

    def test_pop_named_mismatch_strict_raises(self):
        from asciidoctrine.preprocessor import ConditionalStack, PreprocessorError

        cs = ConditionalStack(strict=True)
        cs.push(True, "foo", "ifdef")
        with pytest.raises(PreprocessorError, match="Mismatched endif"):
            cs.pop("bar")

    def test_pop_named_mismatch_permissive_warns(self):
        from asciidoctrine.preprocessor import ConditionalStack, PreprocessorWarning

        cs = ConditionalStack(strict=False)
        cs.push(True, "foo", "ifdef")
        with pytest.warns(PreprocessorWarning, match="Mismatched"):
            cs.pop("bar")

    def test_pop_unnamed_target_no_check(self):
        from asciidoctrine.preprocessor import ConditionalStack

        cs = ConditionalStack(strict=True)
        cs.push(True, "foo", "ifdef")
        frame = cs.pop("")
        assert frame is not None
        assert frame.name == "foo"


# ---------------------------------------------------------------------------
# _parse_ifeval_operand — float, nil/null, unrecognised fallback
# ---------------------------------------------------------------------------


class TestParseIfevalOperand:
    def _preprocessor(self):
        import tempfile

        from asciidoctrine.preprocessor import Preprocessor

        return Preprocessor(base_dir=tempfile.mkdtemp())

    def test_float_operand(self):
        p = self._preprocessor()
        assert p._parse_ifeval_operand("3.14") == pytest.approx(3.14)

    def test_nil_operand(self):
        p = self._preprocessor()
        assert p._parse_ifeval_operand("nil") is None

    def test_null_operand(self):
        p = self._preprocessor()
        assert p._parse_ifeval_operand("null") is None

    def test_unrecognised_string_fallback(self):
        p = self._preprocessor()
        assert p._parse_ifeval_operand("html5") == "html5"

    def test_quoted_double(self):
        p = self._preprocessor()
        assert p._parse_ifeval_operand('"hello"') == "hello"

    def test_quoted_single(self):
        p = self._preprocessor()
        assert p._parse_ifeval_operand("'world'") == "world"


# ---------------------------------------------------------------------------
# _split_ifeval_expression — None return when no operator found
# ---------------------------------------------------------------------------


class TestSplitIfevalExpression:
    def _preprocessor(self):
        import tempfile

        from asciidoctrine.preprocessor import Preprocessor

        return Preprocessor(base_dir=tempfile.mkdtemp())

    def test_no_operator_returns_none(self):
        p = self._preprocessor()
        assert p._split_ifeval_expression("just-a-string") is None

    def test_operator_inside_quotes_ignored(self):
        p = self._preprocessor()
        # The == inside the quoted string should be ignored; the outer == should be found
        result = p._split_ifeval_expression('"a == b" == "a == b"')
        assert result is not None
        left, op, right = result
        assert op == "=="

    def test_all_two_char_operators(self):
        p = self._preprocessor()
        for op in ("==", "!=", "<=", ">="):
            result = p._split_ifeval_expression(f"1 {op} 2")
            assert result is not None
            assert result[1] == op


# ---------------------------------------------------------------------------
# _evaluate_ifeval_condition — attr substitution, TypeError catch
# ---------------------------------------------------------------------------


class TestEvaluateIfevalCondition:
    def _preprocessor(self, attrs=None):
        import tempfile

        from asciidoctrine.preprocessor import Preprocessor

        return Preprocessor(base_dir=tempfile.mkdtemp(), attributes=attrs or {})

    def test_attribute_substitution_in_expression(self):
        p = self._preprocessor({"revnumber": "2"})
        # {revnumber} should be substituted to "2"
        result = p._evaluate_ifeval_condition('"{revnumber}" == "2"')
        assert result is True

    def test_no_operator_returns_false(self):
        p = self._preprocessor()
        assert p._evaluate_ifeval_condition("no-operator-here") is False

    def test_type_error_caught_returns_false(self):
        p = self._preprocessor()
        # Comparing incompatible types (e.g. string < int after coercion) should
        # return False rather than propagating TypeError
        result = p._evaluate_ifeval_condition('"text" < 5')
        assert result is False

    def test_gt_operator(self):
        p = self._preprocessor()
        assert p._evaluate_ifeval_condition("10 > 5") is True

    def test_lt_operator(self):
        p = self._preprocessor()
        assert p._evaluate_ifeval_condition("3 < 10") is True

    def test_ne_operator(self):
        p = self._preprocessor()
        assert p._evaluate_ifeval_condition('"a" != "b"') is True


# ---------------------------------------------------------------------------
# _update_delimiter_stack
# ---------------------------------------------------------------------------


class TestUpdateDelimiterStack:
    def _preprocessor(self):
        import tempfile

        from asciidoctrine.preprocessor import Preprocessor

        return Preprocessor(base_dir=tempfile.mkdtemp())

    def test_pushes_new_delimiter(self):
        p = self._preprocessor()
        stack: list = []
        p._update_delimiter_stack("----\n", stack)
        assert stack == ["----"]

    def test_pops_matching_delimiter(self):
        p = self._preprocessor()
        stack = ["----"]
        p._update_delimiter_stack("----\n", stack)
        assert stack == []

    def test_non_delimiter_line_ignored(self):
        p = self._preprocessor()
        stack: list = []
        p._update_delimiter_stack("normal text\n", stack)
        assert stack == []

    def test_different_depth_does_not_pop(self):
        p = self._preprocessor()
        stack = ["----"]
        p._update_delimiter_stack("========\n", stack)
        assert "========" in stack
        assert "----" in stack


# ---------------------------------------------------------------------------
# _record_line — guard clause paths
# ---------------------------------------------------------------------------


class TestRecordLine:
    def _preprocessor(self):
        import tempfile

        from asciidoctrine.preprocessor import Preprocessor

        return Preprocessor(base_dir=tempfile.mkdtemp())

    def test_record_line_initialises_if_missing(self):
        p = self._preprocessor()
        p.process("")  # initialise state normally
        # Now delete so guard clauses in _record_line execute
        del p.line_map
        del p._global_line_counter
        p._record_line("<root>", 1)
        assert p.line_map == {1: ("<root>", 1)}
        assert p._global_line_counter == 2

    def test_record_line_increments_counter(self):
        p = self._preprocessor()
        p.process("")  # initialise state
        before = p._global_line_counter
        p._record_line("<root>", 5)
        assert p._global_line_counter == before + 1


# ---------------------------------------------------------------------------
# _process_source — passthrough, comment, and other-delimiter branches
# ---------------------------------------------------------------------------


class TestProcessSourceDelimiters:
    def _preprocessor(self, **kwargs):
        import tempfile

        from asciidoctrine.preprocessor import Preprocessor

        return Preprocessor(base_dir=tempfile.mkdtemp(), **kwargs)

    def test_passthrough_block_marked(self):
        p = self._preprocessor()
        src = "++++\nraw <html/>\n++++\n"
        result = p.process(src)
        assert "ASCIIDOCTRINE_OUTER_PASSTHROUGH_START" in result

    def test_comment_block_marked(self):
        p = self._preprocessor()
        src = "////\nthis is a comment\n////\n"
        result = p.process(src)
        assert "ASCIIDOCTRINE_OUTER_COMMENT_START" in result

    def test_other_delimiter_tracked(self):
        p = self._preprocessor()
        # ==== is a delimiter that goes through the _update_delimiter_stack path
        src = "====\nExample content.\n====\n"
        result = p.process(src)
        # Content preserved unchanged
        assert "Example content." in result

    def test_nested_passthrough_inside_listing_not_marked(self):
        """Passthrough inside a verbatim listing block is not re-processed."""
        p = self._preprocessor()
        src = "----\n++++\nnested\n++++\n----\n"
        result = p.process(src)
        # The inner ++++ lines are inside verbatim, should not be transformed
        assert "ASCIIDOCTRINE_OUTER_PASSTHROUGH_START" not in result


# ---------------------------------------------------------------------------
# Preprocessor gaps
# ---------------------------------------------------------------------------


class TestPreprocessorAdditionalGaps:
    def test_is_metadata_comment_line_returns_true(self):
        """is_metadata returns True for // comment lines (line 661)."""
        from asciidoctrine.preprocessor import Preprocessor

        # A comment line above a block should not absorb the block into a paragraph
        src = "// single-line comment\n= Doc Title\n"
        p = Preprocessor()
        result = p.process(src)
        # The comment line passes through and the title is preserved
        assert "= Doc Title" in result

    def test_is_metadata_comment_before_block(self):
        """Comment line acts as metadata — block content after it is preserved."""
        from asciidoctrine.preprocessor import Preprocessor

        src = "// a comment\n----\ncode block\n----\n"
        p = Preprocessor()
        result = p.process(src)
        # Preprocessor replaces ---- with internal sentinels; the content is preserved
        assert "code block" in result
        assert "// a comment" in result

    def test_evaluate_ifeval_condition_unknown_op_via_process(self):
        """ifeval with a type-incompatible comparison returns False (line 223 TypeError path)."""
        from asciidoctrine.preprocessor import Preprocessor

        # Comparing string to number raises TypeError internally → returns False
        src = 'ifeval::["{foo}" > 0]\nincluded\nendif::[]\n'
        p = Preprocessor()
        result = p.process(src)
        # foo is undefined (empty string); "" > 0 raises TypeError, so block is skipped
        assert "included" not in result
