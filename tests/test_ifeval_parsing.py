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


@pytest.mark.parametrize(
    "expr, expected",
    [
        # Equality and inequality
        ('"html5" == "html5"', True),
        ('"html5" != "pdf"', True),
        ('"html5" == "pdf"', False),
        ('"html5" != "html5"', False),
        ("2 == 2", True),
        ("2 != 3", True),
        ("2 == 3", False),
        ("2 != 2", False),
        # Numeric comparisons
        ("5 > 3", True),
        ("5 > 5", False),
        ("10 <= 10", True),
        ("10 <= 9", False),
        ("3.14 < 3.15", True),
        ("3.15 < 3.14", False),
        ("-1 < 0", True),
        ("5 >= 5", True),
        ("4 >= 5", False),
        # Type mismatch safety
        ('"3" == 3', False),
        ('"3" != 3', True),
        ('"abc" < 10', False),
        ('"abc" > 10', False),
        ('"abc" <= 10', False),
        ('"abc" >= 10', False),
    ],
)
def test_expression_evaluation(expr: str, expected: bool) -> None:
    preprocessor = Preprocessor()
    assert preprocessor._evaluate_ifeval_condition(expr) is expected

