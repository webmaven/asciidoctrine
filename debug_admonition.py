from asciidoc_parser.lark_parser import parse_to_ast
import json

source = """[TIP]
====
Code example:

----
def hello():
    print("world")
----
====
"""

ast = parse_to_ast(source)
print(json.dumps(ast, indent=2))
