import os

import pytest

from asciidoctrine.lark_parser import parse_to_ast


def get_example_files():
    examples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")
    if not os.path.exists(examples_dir):
        return []
    return [
        os.path.join(examples_dir, f)
        for f in os.listdir(examples_dir)
        if f.endswith(".adoc")
    ]


@pytest.mark.parametrize("filepath", get_example_files())
def test_example_file_parses(filepath):
    """Data-driven test that ensures every .adoc file in the examples directory
    parses without error."""
    with open(filepath, "r") as f:
        source = f.read()

    # We just want to ensure it doesn't raise an exception
    ast = parse_to_ast(source).to_dict()
    assert ast is not None
    assert "name" in ast
    assert ast["name"] == "document"
