from asciidoctrine.nodes import Listing, Literal, Text


def test_listing_raw_code():
    # Listing with single text element
    node = Listing(inlines=[Text("print('hello')\n")])
    assert node.code == "print('hello')\n"


def test_explicit_callouts_and_stripping():
    # Python/Ruby comments
    node = Listing(
        inlines=[
            Text("import sys  # <1>\nsys.exit(0) # <2> <3>\nprint('no callout')\n")
        ]
    )

    assert node.callouts == {1: [1], 2: [2, 3]}
    assert node.stripped_code == ("import sys\nsys.exit(0)\nprint('no callout')\n")


def test_c_style_callouts_and_stripping():
    node = Listing(inlines=[Text("const x = 1; // <1>\nconst y = 2; /* <2> */\n")])
    assert node.callouts == {1: [1], 2: [2]}
    assert node.stripped_code == ("const x = 1;\nconst y = 2;\n")


def test_xml_style_callouts_and_stripping():
    # XML style comments with explicit brackets and bare numbers
    node = Listing(inlines=[Text("<html> <!-- <1> -->\n<body> <!--2-->\n")])
    assert node.callouts == {1: [1], 2: [2]}
    assert node.stripped_code == ("<html>\n<body>\n")


def test_sequential_callouts():
    # Sequential callouts mixed with explicit numbers
    node = Listing(inlines=[Text("line 1 <.>\nline 2 <.>\nline 3 <5>\nline 4 <.>\n")])
    assert node.callouts == {1: [1], 2: [2], 3: [5], 4: [6]}
    assert node.stripped_code == ("line 1\nline 2\nline 3\nline 4\n")


def test_verbatim_integrity():
    # Make sure inline code containing '<' and '>' is not treated as callout if not trailing
    node = Listing(inlines=[Text("if x < 5:\n    pass\n")])
    assert node.callouts == {}
    assert node.stripped_code == "if x < 5:\n    pass\n"


def test_literal_properties():
    # Identical properties on Literal node
    node = Literal(inlines=[Text("literal output <.>\n")])
    assert node.code == "literal output <.>\n"
    assert node.callouts == {1: [1]}
    assert node.stripped_code == "literal output\n"


def test_parsed_listing_block_callouts():
    from asciidoctrine.lark_parser import parse_to_ast

    source = (
        "[source,ruby]\n"
        "----\n"
        "require 'json' # <1>\n"
        "puts JSON.generate({ok: true}) # <2>\n"
        "----\n"
    )
    doc = parse_to_ast(source)
    listing = doc.blocks[0]
    assert len(listing.inlines) == 4
    assert listing.inlines[0].value == "require 'json'"
    assert listing.inlines[1].value == 1
    assert listing.inlines[2].value == "\nputs JSON.generate({ok: true})"
    assert listing.inlines[3].value == 2
    assert listing.callouts == {1: [1], 2: [2]}
    assert listing.stripped_code == "require 'json'\nputs JSON.generate({ok: true})"
