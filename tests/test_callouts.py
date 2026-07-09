import pytest
from asciidoctrine.nodes import Listing, Literal, Text


def test_listing_raw_code():
    # Listing with single text element
    node = Listing(inlines=[Text("print('hello')\n")])
    assert node.code == "print('hello')\n"


def test_explicit_callouts_and_stripping():
    # Python/Ruby comments
    node = Listing(inlines=[Text(
        "import sys  # <1>\n"
        "sys.exit(0) # <2> <3>\n"
        "print('no callout')\n"
    )])
    
    assert node.callouts == {
        1: [1],
        2: [2, 3]
    }
    assert node.stripped_code == (
        "import sys\n"
        "sys.exit(0)\n"
        "print('no callout')\n"
    )


def test_c_style_callouts_and_stripping():
    node = Listing(inlines=[Text(
        "const x = 1; // <1>\n"
        "const y = 2; /* <2> */\n"
    )])
    assert node.callouts == {
        1: [1],
        2: [2]
    }
    assert node.stripped_code == (
        "const x = 1;\n"
        "const y = 2;\n"
    )


def test_xml_style_callouts_and_stripping():
    # XML style comments with explicit brackets and bare numbers
    node = Listing(inlines=[Text(
        "<html> <!-- <1> -->\n"
        "<body> <!--2-->\n"
    )])
    assert node.callouts == {
        1: [1],
        2: [2]
    }
    assert node.stripped_code == (
        "<html>\n"
        "<body>\n"
    )


def test_sequential_callouts():
    # Sequential callouts mixed with explicit numbers
    node = Listing(inlines=[Text(
        "line 1 <.>\n"
        "line 2 <.>\n"
        "line 3 <5>\n"
        "line 4 <.>\n"
    )])
    assert node.callouts == {
        1: [1],
        2: [2],
        3: [5],
        4: [6]
    }
    assert node.stripped_code == (
        "line 1\n"
        "line 2\n"
        "line 3\n"
        "line 4\n"
    )


def test_verbatim_integrity():
    # Make sure inline code containing '<' and '>' is not treated as callout if not trailing
    node = Listing(inlines=[Text(
        "if x < 5:\n"
        "    pass\n"
    )])
    assert node.callouts == {}
    assert node.stripped_code == "if x < 5:\n    pass\n"


def test_literal_properties():
    # Identical properties on Literal node
    node = Literal(inlines=[Text(
        "literal output <.>\n"
    )])
    assert node.code == "literal output <.>\n"
    assert node.callouts == {1: [1]}
    assert node.stripped_code == "literal output\n"
