from asciidoc_parser.lark_parser import parse_to_ast

def test_nested_examples_multiple_levels():
    source = """
====
Level 1
=====
Level 2
======
Level 3
======
=====
====
"""
    ast = parse_to_ast(source)
    # Check nesting
    assert len(ast.blocks) == 1
    l1 = ast.blocks[0]
    assert len(l1.blocks) == 2 # "Level 1" (paragraph) and Level 2 block
    l2 = l1.blocks[1]
    assert len(l2.blocks) == 2 # "Level 2" and Level 3 block
    l3 = l2.blocks[1]
    assert len(l3.blocks) == 1 # "Level 3"
