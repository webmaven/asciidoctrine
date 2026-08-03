import json
import os

from asciidoctrine.lark_parser import parse_to_ast


def run_examples():
    examples_dir = "examples"
    if not os.path.exists(examples_dir):
        print(f"Directory '{examples_dir}' not found.")
        return

    for filename in os.listdir(examples_dir):
        if filename.endswith(".adoc"):
            filepath = os.path.join(examples_dir, filename)
            print(f"--- Parsing {filename} ---")
            with open(filepath, "r") as f:
                source = f.read()

            try:
                ast = parse_to_ast(source)
                print(json.dumps(ast.to_dict(), indent=2))
            except Exception as e:
                print(f"Error parsing {filename}: {e}")
            print("\n")


if __name__ == "__main__":
    run_examples()
