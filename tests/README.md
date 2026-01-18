# Test Suite

This directory contains the test suite for the AsciiDoc parser.

## Test Tiers

### Tier 1: Official TCK
Authoritative tests from the official AsciiDoc Technology Compatibility Kit (TCK).
Located in `tests/test_tck.py`. Uses `vendor/asciidoc-tck`.

### Tier 2: DocTest Parsing
Broad coverage using examples from the `asciidoctor-doctest` project.
Located in `tests/test_doctest_parsing.py`. Uses `vendor/asciidoctor-doctest`.
Many examples are currently skipped as they use features not yet implemented in this parser.

## Running Tests

Run all tests:
```bash
pytest
```

Run TCK only:
```bash
pytest tests/test_tck.py
```

Run DocTest only:
```bash
pytest tests/test_doctest_parsing.py
```
