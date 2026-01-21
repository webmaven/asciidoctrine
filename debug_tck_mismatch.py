from asciidoc_parser.lark_parser import parse_to_ast
from asciidoc_parser.resolver import ASGResolver
import json
import os

def remove_location(obj):
    if isinstance(obj, dict):
        return {k: remove_location(v) for k, v in obj.items() if k != "location"}
    elif isinstance(obj, list):
        return [remove_location(i) for i in obj]
    else:
        return obj

source = "single word\n"
ast = parse_to_ast(source)
resolver = ASGResolver(ast)
asg = resolver.resolve(ast)

# Match adapter logic for inline tests
actual_output = asg["blocks"][0]["inlines"]

expected_path = "vendor/asciidoc-tck/tests/inline/no-markup/single-word-output.json"
with open(expected_path, "r") as f:
    expected_output = json.load(f)

actual_clean = remove_location(actual_output)
expected_clean = remove_location(expected_output)

if actual_clean == expected_clean:
    print("MATCH (ignoring location)")
else:
    print("MISMATCH")
    import difflib
    diff = difflib.ndiff(
        json.dumps(expected_clean, indent=2).splitlines(),
        json.dumps(actual_clean, indent=2).splitlines()
    )
    print("\n".join(diff))
