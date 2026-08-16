import os
import re

import pytest

try:
    from pytest_pyodide import run_in_pyodide

    HAS_PYODIDE = True
except ImportError:
    HAS_PYODIDE = False



pytestmark = pytest.mark.functional
def _get_wheel_name():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pyproject_path = os.path.join(base_dir, "pyproject.toml")
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return f"asciidoctrine-{match.group(1)}-py3-none-any.whl"
    except Exception:
        pass
    return "asciidoctrine-0.1.0-py3-none-any.whl"


def run_if_pyodide(func):
    if HAS_PYODIDE:
        return run_in_pyodide(
            packages=[
                "lark-1.3.1-py3-none-any.whl",
                _get_wheel_name(),
            ]
        )(func)
    return pytest.mark.skip(reason="pytest-pyodide not installed")(func)


@run_if_pyodide
def test_unconstrained_bold_functional(selenium):
    from asciidoctrine.lark_parser import parse_to_ast

    source = "**bold**anywhere\n"
    ast = parse_to_ast(source).to_dict()

    para = ast["blocks"][0]
    # Should have 2 inlines: span(bold) and text("anywhere")
    assert len(para["inlines"]) == 2
    assert para["inlines"][0]["variant"] == "strong"
    assert para["inlines"][0]["form"] == "unconstrained"
    assert para["inlines"][1]["value"] == "anywhere"


@run_if_pyodide
def test_indented_literal_block_functional(selenium):
    from asciidoctrine.lark_parser import parse_to_ast

    source = "  indented literal\n"
    ast = parse_to_ast(source).to_dict()

    # Should be a literal block, not a paragraph
    block = ast["blocks"][0]
    assert block["name"] == "literal"
    assert block["inlines"][0]["value"] == "indented literal"


@run_if_pyodide
def test_admonition_shorthand_functional(selenium):
    from asciidoctrine.lark_parser import parse_to_ast

    source = "NOTE: This is a note.\n"
    ast = parse_to_ast(source).to_dict()

    block = ast["blocks"][0]
    assert block["name"] == "admonition"
    assert block["variant"] == "note"


@run_if_pyodide
def test_advanced_table_cells_functional(selenium):
    from asciidoctrine.lark_parser import parse_to_ast

    source = """
[cols="1,1"]
|===
| cell 1 | cell 2
2+^s| merged bold
|===
"""
    ast = parse_to_ast(source).to_dict()
    table = ast["blocks"][0]
    assert table["name"] == "table"

    # Row 1
    row1 = table["rows"][0]
    assert len(row1["cells"]) == 2
    cell1 = row1["cells"][0]
    assert cell1.get("colspan", 1) == 1
    assert cell1.get("rowspan", 1) == 1

    # Row 2 (merged cell)
    row2 = table["rows"][1]
    assert len(row2["cells"]) == 1
    merged_cell = row2["cells"][0]
    assert merged_cell["colspan"] == 2
    assert merged_cell.get("rowspan", 1) == 1
    assert merged_cell["align"] == "center"
    assert merged_cell["style"] == "s"


@run_if_pyodide
def test_node_transformer_functional(selenium):
    from asciidoctrine.lark_parser import parse_to_ast
    from asciidoctrine.nodes import NodeTransformer

    class CapitalizeTransformer(NodeTransformer):
        def visit_text(self, node):
            node.value = node.value.upper()
            return node

    source = "Hello world\n"
    ast = parse_to_ast(source)
    transformed_ast = CapitalizeTransformer().visit(ast)
    transformed_dict = transformed_ast.to_dict()

    text_node = transformed_dict["blocks"][0]["inlines"][0]
    assert text_node["value"] == "HELLO WORLD"


@run_if_pyodide
def test_serializer_functional(selenium):
    from asciidoctrine.lark_parser import parse_to_ast
    from asciidoctrine.serializer import serialize_to_asciidoc

    source = "A paragraph with *bold* formatting.\n"
    ast = parse_to_ast(source)
    serialized = serialize_to_asciidoc(ast)
    assert "*bold*" in serialized
