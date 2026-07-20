import pytest

from asciidoctrine.lark_parser import AsciiDocSyntaxError, parse_to_ast
from asciidoctrine.nodes import Document
from asciidoctrine.serializer import serialize_to_asciidoc


@pytest.fixture
def test_env(tmp_path):
    sub_adoc = tmp_path / "sub.adoc"
    sub_adoc.write_text("Valid text.\n\n[#my-id\n\nAlso valid.", encoding="utf-8")

    sub_valid_adoc = tmp_path / "sub_valid.adoc"
    sub_valid_adoc.write_text("Valid text.", encoding="utf-8")
    return tmp_path, sub_adoc, sub_valid_adoc


# Scenario 1: Syntax error in the main document, though it does have some includes.
@pytest.mark.parametrize("strict", [True, False])
def test_error_in_main_with_includes(test_env, strict):
    tmp_path, sub_adoc, sub_valid_adoc = test_env
    main_adoc = tmp_path / "main.adoc"
    # The include is valid, but the main doc has a syntax error at line 5
    main_adoc.write_text(
        "Hello\n\ninclude::sub_valid.adoc[]\n\n[#my-id\n\nWorld", encoding="utf-8"
    )

    if strict:
        with pytest.raises(AsciiDocSyntaxError) as exc_info:
            parse_to_ast(
                main_adoc.read_text(encoding="utf-8"),
                base_dir=str(tmp_path),
                safe_mode=False,
                strict=strict,
            )
        assert exc_info.value.line in (4, 5)
        assert exc_info.value.filepath in (str(main_adoc), "<root>", None)
    else:
        # In permissive mode, the malformed attribute list degrades to a paragraph
        doc = parse_to_ast(
            main_adoc.read_text(encoding="utf-8"),
            base_dir=str(tmp_path),
            safe_mode=False,
            strict=strict,
        )
        assert isinstance(doc, Document)


# Scenario 2: Syntax error introduced in an included fragment.
@pytest.mark.parametrize("strict", [True, False])
def test_error_in_included_fragment(test_env, strict):
    tmp_path, sub_adoc, sub_valid_adoc = test_env
    main_adoc = tmp_path / "main.adoc"
    # The main doc is valid, but sub.adoc has a syntax error at line 3
    main_adoc.write_text("Hello\n\ninclude::sub.adoc[]\n\nWorld", encoding="utf-8")

    if strict:
        with pytest.raises(AsciiDocSyntaxError) as exc_info:
            parse_to_ast(
                main_adoc.read_text(encoding="utf-8"),
                base_dir=str(tmp_path),
                safe_mode=False,
                strict=strict,
            )
        assert exc_info.value.line == 3
        assert exc_info.value.filepath == str(sub_adoc)
    else:
        doc = parse_to_ast(
            main_adoc.read_text(encoding="utf-8"),
            base_dir=str(tmp_path),
            safe_mode=False,
            strict=strict,
        )
        assert isinstance(doc, Document)


# Scenario 3 & 5: Serialize AST without includes (round-tripped). Preprocessor is off.
@pytest.mark.parametrize("strict", [True, False])
def test_serialize_without_includes_preprocessor_off(test_env, strict):
    tmp_path, sub_adoc, sub_valid_adoc = test_env
    source = "Hello\n\ninclude::sub_valid.adoc[]\n\nWorld\n"

    doc = parse_to_ast(
        source,
        base_dir=str(tmp_path),
        safe_mode=False,
        strict=strict,
        preprocess_directives=False,
    )

    # Serializing should yield the original source exactly
    result = serialize_to_asciidoc(doc)
    assert result == source


# Scenario 4: Serialize AST with includes. It produces a warning.
@pytest.mark.parametrize("strict", [True, False])
def test_serialize_with_includes_preprocessor_on(test_env, strict):
    tmp_path, sub_adoc, sub_valid_adoc = test_env
    source = "Hello\n\ninclude::sub_valid.adoc[]\n\nWorld\n"

    doc = parse_to_ast(
        source,
        base_dir=str(tmp_path),
        safe_mode=False,
        strict=strict,
        preprocess_directives=True,
    )

    # Serializing should produce a UserWarning about preprocessed includes
    with pytest.warns(
        UserWarning, match="Original include directives cannot be reconstructed"
    ):
        result = serialize_to_asciidoc(doc)

    # The included content should be expanded
    assert "Valid text." in result
    assert "include::sub_valid.adoc[]" not in result


# Scenario 6: Preprocessor is off, so Lark substitutes placeholders for includes. There was a syntax error.
@pytest.mark.parametrize("strict", [True, False])
def test_error_in_main_preprocessor_off(test_env, strict):
    tmp_path, sub_adoc, sub_valid_adoc = test_env
    main_adoc = tmp_path / "main.adoc"
    # sub.adoc has a syntax error, but preprocessor is off so it's just a placeholder!
    # However, the main document has a syntax error at line 5
    main_adoc.write_text(
        "Hello\n\ninclude::sub.adoc[]\n\n[#my-id\n\nWorld", encoding="utf-8"
    )

    if strict:
        with pytest.raises(AsciiDocSyntaxError) as exc_info:
            parse_to_ast(
                main_adoc.read_text(encoding="utf-8"),
                base_dir=str(tmp_path),
                safe_mode=False,
                strict=strict,
                preprocess_directives=False,
            )
        # Even though sub.adoc has an error if expanded, we don't expand it.
        # The error caught is at line 5 of main.adoc
        assert exc_info.value.line in (4, 5)
        assert exc_info.value.filepath in (str(main_adoc), "<root>", None)
    else:
        doc = parse_to_ast(
            main_adoc.read_text(encoding="utf-8"),
            base_dir=str(tmp_path),
            safe_mode=False,
            strict=strict,
            preprocess_directives=False,
        )
        assert isinstance(doc, Document)
