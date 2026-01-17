#!/usr/bin/env python3
import sys
import json
from asciidoc_parser import parse_to_ast
from asciidoc_parser.asg_visitor import ASGVisitor

def main():
    try:
        # Read from stdin
        input_data = sys.stdin.read()
        if not input_data:
            return

        payload = json.loads(input_data)
        contents = payload.get("contents", "")
        parse_type = payload.get("type", "block")

        # Ensure trailing newline to satisfy parser requirements
        if contents and not contents.endswith("\n"):
            contents += "\n"

        # Invoke the parser
        ast = parse_to_ast(contents)

        # Transform AST to ASG
        visitor = ASGVisitor()
        asg = visitor.visit(ast)

        if parse_type == "inline":
            # For inline type, TCK expects a list of inlines.
            if asg.get("blocks") and asg["blocks"][0].get("name") == "paragraph":
                print(json.dumps(asg["blocks"][0]["inlines"]))
            else:
                print(json.dumps([]))
        else:
            # Block type
            print(json.dumps(asg))

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
