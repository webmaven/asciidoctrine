"""
Local TCK Harness Runner.

Runs every *-input.adoc / *-output.json pair under tests/tck_harness/
against the parser's AST to_dict() output (with location fields stripped),
mirroring the structure of the official TCK tests in test_tck.py.

The expected output files include ``location`` data as a documentation aid;
they are removed before comparison so the test focuses on structural accuracy.
"""

import glob
import json
import os
from typing import Any

import pytest

from asciidoctrine import parse_to_ast

HARNESS_DIR = os.path.join("tests", "tck_harness", "tests")


def clean_asg_for_tck(obj: Any) -> Any:
    if isinstance(obj, dict):
        res = {}
        for k, v in obj.items():
            if k == "location":
                continue
            res[k] = clean_asg_for_tck(v)

        for key in ["blocks", "inlines", "items"]:
            if key in res and not res[key]:
                del res[key]
        return res
    elif isinstance(obj, list):
        return [clean_asg_for_tck(i) for i in obj]
    return obj


def get_local_tck_tests() -> list[str]:
    pattern = os.path.join(HARNESS_DIR, "**", "*-input.adoc")
    adoc_files = glob.glob(pattern, recursive=True)
    return sorted([os.path.relpath(f, HARNESS_DIR) for f in adoc_files])


@pytest.mark.parametrize("adoc_path", get_local_tck_tests())
def test_local_tck(adoc_path: str) -> None:
    input_path = os.path.join(HARNESS_DIR, adoc_path)
    output_path = input_path.replace("-input.adoc", "-output.json")
    config_path = input_path.replace("-input.adoc", "-config.json")

    parse_type = "block"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            parse_type = cfg.get("type", "block")
    elif "inline/" in adoc_path:
        parse_type = "inline"

    with open(input_path, "r", encoding="utf-8") as f:
        source = f.read()

    with open(output_path, "r", encoding="utf-8") as f:
        expected = clean_asg_for_tck(json.load(f))

    ast = parse_to_ast(source)
    from asciidoctrine.resolver import ASGResolver

    resolver = ASGResolver(ast)
    asg = resolver.resolve(ast)

    if parse_type == "inline":
        if asg.get("blocks") and asg["blocks"][0].get("name") == "paragraph":
            actual = clean_asg_for_tck(asg["blocks"][0].get("inlines", []))
        else:
            actual = []
    else:
        actual = clean_asg_for_tck(asg)

    assert actual == expected, (
        f"Local TCK test failed: {adoc_path}\n"
        f"Expected:\n{json.dumps(expected, indent=2)}\n"
        f"Actual:\n{json.dumps(actual, indent=2)}"
    )
