"""
Tests for the AsciiDoc preprocessor.
"""

import os
import shutil
import unittest

from asciidoc_parser.preprocessor import Preprocessor, PreprocessorError


class PreprocessorTest(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test fixtures
        self.base_dir = os.path.join(os.path.dirname(__file__), "temp_fixtures")
        os.makedirs(self.base_dir, exist_ok=True)

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
        self.outside_dir = os.path.join(os.path.dirname(__file__), "outside_fixtures")
        os.makedirs(self.outside_dir, exist_ok=True)
        with open(os.path.join(self.outside_dir, "secret.adoc"), "w") as f:
            f.write("This is a secret file.")

    def tearDown(self):
        # Clean up the temporary directories
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
        if os.path.exists(self.outside_dir):
            shutil.rmtree(self.outside_dir)

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


if __name__ == "__main__":
    unittest.main()
