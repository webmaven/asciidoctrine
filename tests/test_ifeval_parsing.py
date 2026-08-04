"""
Tests for ifeval directive parsing in the AsciiDoc preprocessor.
"""

import pytest
from asciidoctrine.preprocessor import Preprocessor

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "input_val, expected, expected_type",
    [
        # Quoted strings
        ('"html5"', "html5", str),
        ("'pdf'", "pdf", str),
        ('"42"', "42", str),
        ("'true'", "true", str),
        # Integers and floats
        ("42", 42, int),
        ("-10", -10, int),
        ("3.14", 3.14, float),
        ("-0.5", -0.5, float),
        # Booleans
        ("true", True, bool),
        ("false", False, bool),
        ("True", True, bool),
        ("False", False, bool),
        # nil and null
        ("nil", None, type(None)),
        ("null", None, type(None)),
    ],
)
def test_operand_parsing(input_val: str, expected: object, expected_type: type) -> None:
    preprocessor = Preprocessor()
    result = preprocessor._parse_ifeval_operand(input_val)
    assert result == expected
    assert type(result) is expected_type
