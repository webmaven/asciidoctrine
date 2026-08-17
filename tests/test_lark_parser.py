import pytest

from asciidoctrine import parse_to_ast

pytestmark = pytest.mark.integration


def test_parse_to_ast_attaches_base_dir_and_safe_mode():
    doc = parse_to_ast("Hello World\n", base_dir="/custom/path", safe_mode=2)
    assert doc.base_dir == "/custom/path"
    assert doc.safe_mode == 2


def test_parse_to_ast_default_base_dir_and_safe_mode():
    doc = parse_to_ast("Hello World\n")
    assert doc.base_dir is None
    assert doc.safe_mode == 0
