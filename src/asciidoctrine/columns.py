from __future__ import annotations

import re
from typing import Any, Optional

"""
AsciiDoc column attribute DSL parser for tables.
"""

# Regex matching: [<multiplier>*][<align>][<width>][<style>]
# where align can be <halign>[.<valign>] or .<valign> or <halign>
# halign: [<|^|>]
# valign: .[<|^|>]
# width: \d+%?
# style: [deslmha]
# Multiplier: \d+\*
COL_SPEC_REGEX = re.compile(
    r"^(?:(?P<multiplier>\d+)\*)?"
    r"(?:(?P<halign>[<^>])?(?:\.(?P<valign>[<^>]))?)?"
    r"(?P<width>\d+%?)?"
    r"(?:(?:\.(?P<valign_after>[<^>]))?"
    r"(?P<style>[deslmha])?)?$"
)

ALIGN_MAP = {
    "<": "left",
    "^": "center",
    ">": "right",
}

VALIGN_MAP = {
    "<": "top",
    "^": "middle",
    ">": "bottom",
}

STYLE_MAP = {
    "d": "default",
    "e": "emphasis",
    "s": "strong",
    "l": "literal",
    "m": "monospace",
    "h": "header",
    "a": "asciidoc",
}


def _format_percentage(val: float) -> str:
    """Format a percentage cleanly, e.g. 20% or 33.3333%."""
    if val.is_integer():
        return f"{int(val)}%"
    formatted = f"{val:.4f}".rstrip("0").rstrip(".")
    return f"{formatted}%"


def parse_cols(
    cols_str: Optional[str], fallback_col_count: int = 0
) -> list[dict[str, Any]]:
    """
    Parse an AsciiDoc `cols` attribute string into structured column definitions.

    Parameters
    ----------
    cols_str : Optional[str]
        The raw `cols` string from block attributes (e.g. "1,3,>1s" or "2*^.<20%a,>80%").
    fallback_col_count : int, optional
        Number of default columns to generate if `cols_str` is empty or None.

    Returns
    -------
    list[dict[str, Any]]
        List of column metadata dictionaries with keys:
        'index', 'width', 'halign', 'valign', 'style'.
    """
    if not cols_str or not cols_str.strip():
        if fallback_col_count <= 0:
            return []
        equal_pct = _format_percentage(100.0 / fallback_col_count)
        return [
            {
                "index": i,
                "width": equal_pct,
                "halign": "left",
                "valign": "top",
                "style": "default",
            }
            for i in range(fallback_col_count)
        ]

    tokens = [t.strip() for t in cols_str.split(",") if t.strip()]
    if not tokens:
        if fallback_col_count <= 0:
            return []
        equal_pct = _format_percentage(100.0 / fallback_col_count)
        return [
            {
                "index": i,
                "width": equal_pct,
                "halign": "left",
                "valign": "top",
                "style": "default",
            }
            for i in range(fallback_col_count)
        ]

    raw_cols: list[dict[str, Any]] = []
    for token in tokens:
        match = COL_SPEC_REGEX.match(token)
        if not match:
            # Fallback for unrecognized token: 1 default col
            raw_cols.append(
                {
                    "raw_width": None,
                    "halign": "left",
                    "valign": "top",
                    "style": "default",
                }
            )
            continue

        groups = match.groupdict()
        mult_val = groups.get("multiplier")
        multiplier = int(mult_val) if mult_val else 1
        halign_char = groups.get("halign")
        halign = ALIGN_MAP.get(halign_char or "", "left")
        valign_char = groups.get("valign") or groups.get("valign_after")
        valign = VALIGN_MAP.get(valign_char or "", "top")
        style_char = groups.get("style")
        style = STYLE_MAP.get(style_char or "", "default")
        raw_width = groups.get("width")

        for _ in range(multiplier):
            raw_cols.append(
                {
                    "raw_width": raw_width,
                    "halign": halign,
                    "valign": valign,
                    "style": style,
                }
            )

    total_cols = len(raw_cols)
    if total_cols == 0:
        return []

    # Determine width calculation strategy:
    # 1. If explicit percentage strings (e.g. '20%') are used, pass through or normalize
    # 2. If integer ratios (e.g. 1, 3, 1), compute ratio / sum(ratios) * 100%
    # 3. If no width specified across all columns, equal distribution (100 / N)%
    has_numeric_ratio = any(
        col["raw_width"]
        and not col["raw_width"].endswith("%")
        and col["raw_width"].isdigit()
        for col in raw_cols
    )

    ratio_sum = sum(
        int(col["raw_width"])
        for col in raw_cols
        if col["raw_width"]
        and not col["raw_width"].endswith("%")
        and col["raw_width"].isdigit()
    )

    result: list[dict[str, Any]] = []
    for i, col in enumerate(raw_cols):
        rw = col["raw_width"]
        if rw and rw.endswith("%"):
            width_str = rw
        elif has_numeric_ratio and ratio_sum > 0:
            val = int(rw) if (rw and rw.isdigit()) else 1
            width_str = _format_percentage((val / ratio_sum) * 100.0)
        else:
            width_str = _format_percentage(100.0 / total_cols)

        result.append(
            {
                "index": i,
                "width": width_str,
                "halign": col["halign"],
                "valign": col["valign"],
                "style": col["style"],
            }
        )

    return result
