import fnmatch

import pytest

from asciidoc_parser import parse_to_ast
from tests.conftest import get_all_doctest_examples

# List of example groups or specific examples known to be unsupported currently
# to avoid failing the whole suite.
KNOWN_UNSUPPORTED = {
    "audio:*",
    "video:*",
    "table:*",
    "stem:*",
    "colist:*",
    "dlist:*",
    "inline_break:*",
    "inline_button:*",
    "inline_callout:*",
    "inline_kbd:*",
    "inline_menu:*",
    "pass:*",
    "preamble:*",
    "quote:*",
    "verse:*",
    "open:*",
    "outline:*",
    "page_break:*",
    "thematic_break:*",
    "toc:*",
    "floating_title:*",
    "embedded:*",
    "inline_quoted:asciimath",
    "inline_quoted:latexmath",
    "*:book-part-title",
}


@pytest.mark.parametrize("example_id,content", get_all_doctest_examples())
def test_doctest_example_parses(example_id: str, content: str):
    """Verify each doctest example parses without errors."""
    if any(fnmatch.fnmatch(example_id, p) for p in KNOWN_UNSUPPORTED):
        pytest.skip(f"Not yet implemented: {example_id}")

    try:
        ast = parse_to_ast(content)
        assert ast is not None
        assert ast.name == "document"
    except Exception as e:
        pytest.fail(f"Failed to parse {example_id}: {e}\nContent:\n{content}")
