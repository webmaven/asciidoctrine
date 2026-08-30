from __future__ import annotations

from asciidoctrine.columns import parse_cols


def test_parse_cols_simple_ratios():
    result = parse_cols("1,3,1")
    assert result == [
        {
            "index": 0,
            "width": "20%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "60%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 2,
            "width": "20%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
    ]


def test_parse_cols_multipliers():
    result = parse_cols("2*")
    assert result == [
        {
            "index": 0,
            "width": "50%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "50%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
    ]

    result2 = parse_cols("3*^.<20%s")
    assert result2 == [
        {
            "index": 0,
            "width": "20%",
            "halign": "center",
            "valign": "top",
            "style": "strong",
        },
        {
            "index": 1,
            "width": "20%",
            "halign": "center",
            "valign": "top",
            "style": "strong",
        },
        {
            "index": 2,
            "width": "20%",
            "halign": "center",
            "valign": "top",
            "style": "strong",
        },
    ]


def test_parse_cols_alignments():
    result = parse_cols("<,^,>")
    assert result == [
        {
            "index": 0,
            "width": "33.3333%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "33.3333%",
            "halign": "center",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 2,
            "width": "33.3333%",
            "halign": "right",
            "valign": "top",
            "style": "default",
        },
    ]

    result_valign = parse_cols(".<,.^,.>")
    assert result_valign == [
        {
            "index": 0,
            "width": "33.3333%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "33.3333%",
            "halign": "left",
            "valign": "middle",
            "style": "default",
        },
        {
            "index": 2,
            "width": "33.3333%",
            "halign": "left",
            "valign": "bottom",
            "style": "default",
        },
    ]


def test_parse_cols_styles():
    result = parse_cols("d,e,s,l,m,h,a")
    expected_styles = [
        "default",
        "emphasis",
        "strong",
        "literal",
        "monospace",
        "header",
        "asciidoc",
    ]
    assert len(result) == 7
    for i, expected_style in enumerate(expected_styles):
        assert result[i]["style"] == expected_style
        assert result[i]["index"] == i
        assert result[i]["halign"] == "left"
        assert result[i]["valign"] == "top"


def test_parse_cols_explicit_percentages():
    result = parse_cols("20%,80%")
    assert result == [
        {
            "index": 0,
            "width": "20%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "80%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
    ]


def test_parse_cols_combined_tokens():
    result = parse_cols("1,3,>1s")
    assert result == [
        {
            "index": 0,
            "width": "20%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "60%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 2,
            "width": "20%",
            "halign": "right",
            "valign": "top",
            "style": "strong",
        },
    ]

    result2 = parse_cols("2*^.<20%a,>80%")
    assert result2 == [
        {
            "index": 0,
            "width": "20%",
            "halign": "center",
            "valign": "top",
            "style": "asciidoc",
        },
        {
            "index": 1,
            "width": "20%",
            "halign": "center",
            "valign": "top",
            "style": "asciidoc",
        },
        {
            "index": 2,
            "width": "80%",
            "halign": "right",
            "valign": "top",
            "style": "default",
        },
    ]


def test_parse_cols_empty_and_fallback():
    assert parse_cols(None, fallback_col_count=0) == []
    assert parse_cols("", fallback_col_count=0) == []
    assert parse_cols("   ", fallback_col_count=0) == []

    fallback_3 = parse_cols(None, fallback_col_count=3)
    assert fallback_3 == [
        {
            "index": 0,
            "width": "33.3333%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "33.3333%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 2,
            "width": "33.3333%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
    ]

    fallback_2 = parse_cols("", fallback_col_count=2)
    assert fallback_2 == [
        {
            "index": 0,
            "width": "50%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "50%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
    ]


def test_parse_cols_mixed_sparse_ratios():
    result = parse_cols("^,2,>")
    assert result == [
        {
            "index": 0,
            "width": "25%",
            "halign": "center",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 1,
            "width": "50%",
            "halign": "left",
            "valign": "top",
            "style": "default",
        },
        {
            "index": 2,
            "width": "25%",
            "halign": "right",
            "valign": "top",
            "style": "default",
        },
    ]
