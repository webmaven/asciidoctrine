#!/usr/bin/env python3
"""
AsciiDoctrine Linter & Auto-Fixer Demo

This example demonstrates how to leverage AsciiDoctrine's parsed Abstract Syntax Tree (AST),
NodeTransformer, and Native Serializer to build an automated formatting and linting tool.
"""

from asciidoctrine import parse_to_ast, serialize_to_asciidoc
from asciidoctrine.nodes import Node, Paragraph, Section, Span


class FormattingLinter:
    """
    A simple linter and formatter that traverses the AST,
    flags issues, and fixes them in-place.
    """

    def __init__(self):
        self.warnings = []

    def lint_and_fix(self, node: Node) -> Node:
        """
        Recursively walks and fixes AST nodes.
        """
        # 1. Inspect and fix the current node
        self._check_node(node)

        # 2. Recursively process child nodes
        if hasattr(node, "blocks") and node.blocks is not None:
            fixed_blocks = []
            for block in node.blocks:
                # Example rule: Strip completely empty paragraphs
                if isinstance(block, Paragraph) and not block.inlines:
                    self.warnings.append(
                        f"Line {getattr(block, 'start_line', '?')}: Removed empty Paragraph block"
                    )
                    continue  # Skip / remove this block
                fixed_blocks.append(self.lint_and_fix(block))
            node.blocks = fixed_blocks

        if hasattr(node, "inlines") and node.inlines is not None:
            fixed_inlines = []
            for inline in node.inlines:
                fixed_inlines.append(self.lint_and_fix(inline))
            node.inlines = fixed_inlines

        if isinstance(node, Section) and hasattr(node, "title") and node.title is not None:
            node.title = self.lint_and_fix(node.title)

        return node

    def _check_node(self, node: Node):
        # Rule 1: Warn on and clean up obsolete unconstrained monospace double backticks
        if isinstance(node, Span) and node.variant == "monospace" and node.form == "unconstrained":
            self.warnings.append(
                f"Line {getattr(node, 'start_line', '?')}: Found unconstrained monospace double-backticks. "
                "Standardizing to constrained single-backticks."
            )
            node.form = "constrained"

        # Rule 2: Enforce capitalized style keys (e.g. style="source")
        if hasattr(node, "attributes") and node.attributes:
            if "style" in node.attributes and node.attributes["style"] == "source":
                # Ensure a language is set if style is source
                if "language" not in node.attributes:
                    self.warnings.append(
                        f"Line {getattr(node, 'start_line', '?')}: Verbatim source block lacks a declared language."
                    )


def main():
    # A sample "dirty" document with several style issues:
    # 1. Unconstrained double backticks ``code`` instead of modern single backticks `code`
    # 2. An empty paragraph block
    # 3. A source block without a language attribute declared
    sample_asciidoc = """= Sample Document
Michael R. Bernstein

== Introduction

Here is some ``unconstrained monospace`` code that we want to standardize.

And here is an empty paragraph block below (represented by empty lines or whitespace):


[source]
----
print("Hello World")
----
"""

    print("=== Original Document ===")
    print(sample_asciidoc)
    print("==========================\n")

    # 1. Parse the original document to AST
    ast = parse_to_ast(sample_asciidoc)

    # 2. Run our formatting linter & fixer
    linter = FormattingLinter()
    fixed_ast = linter.lint_and_fix(ast)

    print("=== Lint Warnings ===")
    if linter.warnings:
        for warning in linter.warnings:
            print(f"[WARNING] {warning}")
    else:
        print("No style issues found!")
    print("=====================\n")

    # 3. Serialize the fixed AST back to standardized AsciiDoc source
    fixed_asciidoc = serialize_to_asciidoc(fixed_ast)

    print("=== Auto-Fixed Document ===")
    print(fixed_asciidoc)
    print("===========================")


if __name__ == "__main__":
    main()
