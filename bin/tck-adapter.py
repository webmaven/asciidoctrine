#!/usr/bin/env python3
import sys
import json
from asciidoc_parser import parse_to_ast

def main():
    try:
        # Read from stdin (TASK-2.1 / Issue #37)
        input_data = sys.stdin.read()
        if not input_data:
            return

        payload = json.loads(input_data)
        contents = payload.get("contents", "")

        # Ensure trailing newline to satisfy parser requirements
        if contents and not contents.endswith("\n"):
            contents += "\n"

        # Invoke the parser (TASK-2.2 / Issue #38)
        # The returned AST is stored in the 'ast' variable.
        ast = parse_to_ast(contents)

        # For now, we return a hardcoded ASG-like dictionary as per TASK-2.4 / Issue #40.
        # Once TASK-3 (ASGVisitor) is implemented, this will be replaced with
        # the result of the ASGVisitor.
        asg = {
            "type": "document",
            "children": []
        }

        # Implement stdout Writing (TASK-2.4 / Issue #40)
        print(json.dumps(asg))
        sys.exit(0)

    except Exception as e:
        # Implement Basic Error Handling (TASK-2.3 / Issue #39)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
