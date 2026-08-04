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


def test_attribute_substitution() -> None:
    preprocessor = Preprocessor()
    preprocessor.attributes["backend"] = "html5"
    preprocessor.attributes["sectnumlevels"] = "3"

    assert preprocessor._evaluate_ifeval_condition('"{backend}" == "html5"') is True
    assert preprocessor._evaluate_ifeval_condition('{sectnumlevels} == 3') is True
    assert preprocessor._evaluate_ifeval_condition('"{unset_attr}" == ""') is True


def test_ifeval_preprocessor_integration() -> None:
    preprocessor = Preprocessor()
    input_text = """
:backend: html5
ifeval::["{backend}" == "html5"]
Included HTML line
endif::[]
ifeval::["{backend}" == "pdf"]
Excluded PDF line
endif::[]
"""
    result = preprocessor.process(input_text)
    assert "Included HTML line" in result
    assert "Excluded PDF line" not in result


def test_ifeval_nested_in_ifdef() -> None:
    preprocessor = Preprocessor()
    input_text = """
:backend: html5
ifdef::backend[]
ifeval::["{backend}" == "html5"]
Nested ifeval included
endif::[]
endif::[]
"""
    result = preprocessor.process(input_text)
    assert "Nested ifeval included" in result


def test_ifeval_anonymous_endif() -> None:
    preprocessor = Preprocessor()
    input_text = """
:backend: html5
ifeval::["{backend}" == "html5"]
Line 1
ifeval::["{backend}" == "html5"]
Line 2
endif::[]
Line 3
endif::[]
"""
    result = preprocessor.process(input_text)
    assert "Line 1" in result
    assert "Line 2" in result
    assert "Line 3" in result
