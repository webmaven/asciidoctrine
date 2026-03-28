import pytest

try:
    from pytest_pyodide import copy_files_to_pyodide, run_in_pyodide

    HAS_PYODIDE = True
except ImportError:
    HAS_PYODIDE = False


import os

def run_if_pyodide(func):
    if HAS_PYODIDE:
        cwd = os.getcwd()
        return copy_files_to_pyodide(
            file_list=[
                os.path.join(cwd, "pyodide", "lark-1.3.1-py3-none-any.whl"),
                os.path.join(cwd, "pyodide", "asciidoctrine-0.1.0-py3-none-any.whl"),
            ],
            install_wheels=True,
        )(run_in_pyodide(func))
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
