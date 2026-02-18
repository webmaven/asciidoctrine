import os
from typing import Any, ClassVar, Dict

from docutils import nodes
from sphinx.parsers import Parser as SphinxParser

from .docutils_backend import DocutilsRenderer
from .lark_parser import parse_to_ast


class AsciiDocParser(SphinxParser):
    """
    Sphinx parser for AsciiDoc files.
    """

    supported: ClassVar[tuple[str, ...]] = ("asciidoc", "adoc")

    def parse(self, inputstring: str, document: nodes.document) -> None:
        """
        Parse the input string and update the docutils document.
        """
        # document is the docutils document provided by Sphinx.
        # It already has settings, etc.

        # Determine base_dir for includes relative to the source file
        base_dir = None
        source_path = getattr(document, "attributes", {}).get("source", None)
        if source_path:
            base_dir = os.path.dirname(os.path.abspath(source_path))

        try:
            # We parse to our custom AST first
            # Disable safe_mode for Sphinx builds to allow including files from
            # project root
            ast = parse_to_ast(inputstring, base_dir=base_dir, safe_mode=False)

            # Then we use our new DocutilsRenderer to populate the Sphinx/Docutils tree
            renderer = DocutilsRenderer(document)
            renderer.visit(ast)

        except Exception as e:
            # Report error in the rendered document
            error = nodes.error("", nodes.paragraph("", f"AsciiDoc Parse Error: {e}"))
            document += error


def setup(app: Any) -> Dict[str, Any]:
    """
    Sphinx extension setup function.
    """
    app.add_source_suffix(".adoc", "asciidoc")
    app.add_source_suffix(".asciidoc", "asciidoc")
    app.add_source_parser(AsciiDocParser)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
