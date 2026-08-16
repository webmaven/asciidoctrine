import fnmatch
import os

import pytest

from asciidoctrine import parse_to_ast
from tests.conftest import get_all_doctest_examples


pytestmark = pytest.mark.integration
# List of example groups or specific examples known to be unsupported currently
# to avoid failing the whole suite.
KNOWN_UNSUPPORTED: set[str] = set()


@pytest.mark.parametrize("example_id,content", get_all_doctest_examples())
def test_doctest_example_parses(example_id: str, content: str):
    """Verify each doctest example parses without errors."""
    if not os.environ.get("RUN_DOCTESTS"):
        pytest.skip("Doctests skipped by default. Set RUN_DOCTESTS=1 to run.")

    if any(fnmatch.fnmatch(example_id, p) for p in KNOWN_UNSUPPORTED):
        pytest.skip(f"Not yet implemented: {example_id}")

    try:
        ast = parse_to_ast(content)
        assert ast is not None
        assert ast.name == "document"
    except Exception as e:
        pytest.fail(f"Failed to parse {example_id}: {e}\nContent:\n{content}")
