from asciidoc_parser.lark_parser import parse_to_ast


def test_unconstrained_bold_functional():
    source = "**bold**anywhere\n"
    ast = parse_to_ast(source).to_dict()

    para = ast["blocks"][0]
    # Should have 2 inlines: span(bold) and text("anywhere")
    assert len(para["inlines"]) == 2
    assert para["inlines"][0]["variant"] == "strong"
    assert para["inlines"][0]["form"] == "unconstrained"
    assert para["inlines"][1]["value"] == "anywhere"


def test_indented_literal_block_functional():
    source = "  indented literal\n"
    ast = parse_to_ast(source).to_dict()

    # Should be a literal block, not a paragraph
    block = ast["blocks"][0]
    assert block["name"] == "literal"
    assert block["inlines"][0]["value"] == "indented literal"


def test_admonition_shorthand_functional():
    source = "NOTE: This is a note.\n"
    ast = parse_to_ast(source).to_dict()

    block = ast["blocks"][0]
    assert block["name"] == "admonition"
    assert block["variant"] == "note"
