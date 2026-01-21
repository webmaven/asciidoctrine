#!/usr/bin/env python3
"""
TCK Adapter for AsciiDoc Parser.
Converts AsciiDoc source to TCK-compliant ASG JSON.
"""

import json
import sys

from asciidoc_parser import parse_to_ast
from asciidoc_parser.resolver import ASGResolver


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
        resolver = ASGResolver(ast)
        asg = resolver.resolve(ast)

        def clean_asg_for_tck(obj):
            if isinstance(obj, dict):
                # TCK doesn't expect 'form' in spans
                res = {
                    k: clean_asg_for_tck(v)
                    for k, v in obj.items()
                    if k != "form"
                }
                # TCK prefers omitting empty child collections in some contexts
                for key in ["blocks", "inlines", "items"]:
                    if key in res and not res[key]:
                        del res[key]
                return res
            elif isinstance(obj, list):
                return [clean_asg_for_tck(i) for i in obj]
            return obj

        if parse_type == "inline":
            # For inline type, TCK expects a list of inlines.
            if asg.get("blocks") and asg["blocks"][0].get("name") == "paragraph":
                output = clean_asg_for_tck(asg["blocks"][0]["inlines"])
            else:
                output = []
        else:
            # Block type
            output = clean_asg_for_tck(asg)

        result_json = json.dumps(output)
        
        # DEBUG LOGGING
        with open("tck_debug.log", "a", encoding="utf-8") as f:
            f.write(f"--- TEST TYPE: {parse_type} ---\n")
            f.write(f"INPUT:\n{contents}\n")
            f.write(f"OUTPUT:\n{result_json}\n\n")

        print(result_json)
        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
