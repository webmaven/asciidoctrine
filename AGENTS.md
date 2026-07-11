# Agent Development & Testing Guide

This document provides a technical overview of the local development environment, project structure, and testing protocols for the `asciidoctrine` project. It is designed to help agents quickly onboard and contribute to the parser.

## 🏗 Project Architecture

`asciidoctrine` is a multi-pass AsciiDoc parser built on the **Lark** engine (Earley algorithm).

*   **Grammar**: `src/asciidoctrine/grammar.lark` (EBNF)
*   **AST Nodes**: `src/asciidoctrine/nodes.py` (Converged with ASG schema)
*   **Transformer**: `src/asciidoctrine/lark_parser.py` (CST to AST)
*   **Semantic Resolver**: `src/asciidoctrine/resolver.py` (Resolves attributes)
*   **Backend**: `src/asciidoctrine/docutils_backend.py` (Docutils/Sphinx integration)

## 🛠 Local Setup

### Python Environment
The project uses a standard Python 3.10+ virtual environment.

```bash
# Activation not strictly required if using absolute paths
# pip install -e ".[test,docs]"
```

*   **Python Path**: `venv/bin/python3`
*   **Pip Path**: `venv/bin/pip`
*   **Pytest Path**: `venv/bin/pytest`

### Pyodide Setup (for Functional Tests)
To run functional tests, you need a local Pyodide environment and built wheels in the `dist/` directory.

```bash
# 1. Create and populate dist/ directory
mkdir -p dist
curl -L https://github.com/pyodide/pyodide/releases/download/0.27.2/pyodide-0.27.2.tar.bz2 | tar -xjf - -C dist --strip-components=1

# 2. Build project wheel
venv/bin/python3 -m build --wheel

# 3. Download dependencies for Pyodide
venv/bin/python3 -m pip download lark -d dist/
```

### TCK Dependencies
The Technology Compatibility Kit (TCK) requires Node.js (>= 20) and npm.

```bash
cd vendor/asciidoc-tck
npm ci
```
*Note: `run-tck.sh` handles `npm ci` automatically if `node_modules` is missing.*

## 🧪 Testing Protocols

The project uses a multi-tiered testing strategy.

### 1. Standard Pytest Suite
Runs unit, integration, and doctest-based examples.

```bash
# Run all stable tests
venv/bin/pytest -k "not functional"

# Functional tests (Pyodide) currently require a 'pyodide/' dist directory
# and are known to fail in standard environments.
```

### 2. Official TCK Suite
Authoritative tests for AsciiDoc specification compliance.

```bash
./run-tck.sh
```
*   **Adapter**: `bin/tck-adapter.py` (Bridge between TCK runner and parser)
*   **TCK Location**: `vendor/asciidoc-tck/`

### 3. TCK Coverage Report
To see a summary of passed/failed TCK categories:

```bash
./run-tck-coverage.sh
```

## 📋 New Feature Checklist

When adding support for a new AsciiDoc element:

1.  **Grammar**: Add the rule to `src/asciidoctrine/grammar.lark`.
2.  **Node**: Define a new `Node` subclass in `src/asciidoctrine/nodes.py` that matches the [ASG schema](https://gitlab.eclipse.org/eclipse/asciidoc-lang/asciidoc-lang/-/blob/main/asg/schema.json).
3.  **Transformer**: Implement a corresponding method in `BlockTransformer` or `InlineTransformer`.
4.  **Resolver**: If the element contains text that supports attribute substitution, ensure it's handled in `src/asciidoctrine/resolver.py`.
5.  **Backend**: Add a `visit_<name>` method to `DocutilsRenderer` in `src/asciidoctrine/docutils_backend.py`.
6.  **Tests**:
    *   Add a unit test in `tests/test_blocks_parsing.py` or `tests/test_inlines_parsing.py`.
    *   Add a functional test or TCK-style test in `tests/tck_harness/`.

## 📁 Key File Paths

| Path | Description |
| :--- | :--- |
| `src/asciidoctrine/` | Core package source code |
| `src/asciidoctrine/grammar.lark` | Authority for the parser's syntax rules |
| `src/asciidoctrine/nodes.py` | AST definitions (Follows ASG schema naming) |
| `src/asciidoctrine/transformers/` | CST-to-AST transformation logic |
| `tests/` | Pytest directory |
| `tests/tck_harness/` | Local TCK test additions |
| `vendor/asciidoc-tck/` | Official TCK (Submodule) |
| `vendor/asciidoctor-doctest/` | External example corpus (Submodule) |
| `bin/tck-adapter.py` | CLI entry point for the TCK runner |

## 💡 Troubleshooting & Patterns

*   **Earley Ambiguity**: If the grammar becomes ambiguous, Lark will raise a `VisitError` or `AmbiguityError`. Use `?rule` in the grammar to compress simple wrappers.
*   **Location Tracking**: The parser uses inclusive locations (`end_column - 1`). Use `_set_location_from_children()` in the transformer to ensure accuracy.
*   **Attribute Resolution**: Rich attributes (nodes) are resolved to strings in `attributes.py`.
*   **Git Submodules**: If submodules are missing or empty, run `git submodule update --init --recursive`.

## 📝 Architectural & Parser Learnings

The following key learnings and design decisions have been consolidated to prevent redundant research and preserve architectural context:

### 1. AST vs. ASG Attribute Separation
- **AST (Abstract Syntax Tree)**: Created by `parse_to_ast()`. Retains all syntactic block nodes, including `:name: value` (`attribute_entry` nodes), for syntax-level testing and coordinate/formatting tools.
- **ASG (Abstract Semantic Graph)**: Resolved by `ASGResolver.resolve()`. Standalone `attribute_entry` and `comment` block nodes are **consumed and filtered out** from structural parent lists (`blocks`, `items`, etc.), while their values are resolved and mapped directly to the root `"attributes"` dictionary on the resolved document.

### 2. Mixed Shorthand, Named, and Positional Attribute Parsing
- In `lark_parser.py`, `attribute_list` handles attributes split by comma (respecting quotes).
- **Caution**: Do NOT check `attr_str.startswith("#") or attr_str.startswith(".")` as an early-return check. Doing so causes mixed attributes (such as `[#my-id,source,python]`) to fail, as the entire line gets mistakenly swallowed as a single shorthand ID.
- **Correct Pattern**: Split the entire string by comma first. Then, process each part sequentially, allowing individual parts to match shorthands (`#id` or `.role`), named attributes (`key=value`), options (`%option`), or positional attributes. Finally, map the first positional attribute to `style`, and the second positional to `language` if `style == "source"`.

### 3. Body-Level Attribute Propagation
- During parsing, `attribute_entry` nodes in the document body are transformed and populate the parser's local dictionary `self.attributes`.
- These attributes must be propagated to the root `Document.attributes` dictionary so the resolver can find and substitute them. This propagation is handled in the top-level `document` transformer method by updating `doc.attributes` with any unassigned keys from `self.attributes`.

### 4. Listing Node Metadata Properties
- To cleanly support tools like `asciidoctest` that inspect source code blocks, the `Listing` node in `nodes.py` exposes explicit Python properties:
  - `id`: Read/write accessor mapped to `self.attributes["id"]`.
  - `language`: Read/write accessor mapped to `self.attributes["language"]`.
  - `style`: Read/write accessor mapped to `self.attributes["style"]`.
  - `listing_title`: A helper property returning the string value of the block title node (`self.title`) or falling back to `self.attributes.get("title")`.

### 5. AST to ASG Node Structure Mapping
To produce a TCK-compliant Resolved Abstract Semantic Graph (ASG), the internal AST structure in `nodes.py` aligns directly with the official ASG schema. Each node implements a polymorphic `to_dict()` method producing compliant output:
- `Document`: `{"name": "document", "type": "block", "blocks": [], "attributes": {}, "header": {}}`
- `Paragraph`: `{"name": "paragraph", "type": "block", "inlines": []}`
- `Text`: `{"name": "text", "type": "string", "value": "text content"}`
- `Span`: `{"name": "span", "type": "inline", "variant": "strong|emphasis|code", "form": "constrained", "inlines": []}`
- `Section`: `{"name": "section", "type": "block", "level": 1, "title": [], "blocks": []}`
- `List`: `{"name": "list", "type": "block", "variant": "unordered|ordered", "marker": "*|.", "items": []}`
- `ListItem`: `{"name": "listItem", "type": "block", "principal": [], "blocks": []}`
- `Listing`: `{"name": "listing", "type": "block", "form": "delimited", "delimiter": "----", "inlines": []}`
- `Ref`: `{"name": "ref", "type": "inline", "variant": "link", "target": "url", "inlines": []}`

## 📝 Recording Grammar Learnings

* **Standing Instruction**: When you solve a grammar problem, don't leave the grammar file itself as the only record of whatever solution you devised, record an explanation as prose as well. Include what you tried that *didn't* work, and why.

### 1. Block Macro vs. Description List (DList) Earley Ambiguity
- **Problem**: Input lines like `toc::[]` (block macros with empty targets and attributes) were being parsed as description list (`dlist`) items instead of block macros.
- **Cause**: In the Earley parsing algorithm, Lark evaluates all matching branches. `toc::[]` matches `block_macro` (where name is `toc`, target is empty, attributes are empty). However, it *also* matched `dlist -> dlist_item -> dlist_term ("toc" + "::") + dlist_description ("[]" parsed as a paragraph)`. Because Lark chooses the parse tree with the highest sum of node-level priorities, the deeper nested `dlist` tree (~27 sum of priorities) scored higher than the shallow `block_macro` tree (20 priority).
- **What Didn't Work**: Adding internal priorities on sub-tokens (like `DLIST_MARKER_2` or `WORD`) did not work because the ambiguity exists at the structural rule-matching level, not the token-lexing level.
- **Solution**: Raised the `block_macro` rule priority in `grammar.lark` to `block_macro.50` so that its single-node tree score always outweighs any nested description list tree structure score.

### 2. Consecutive Block Attributes vs. Paragraph Earley Ambiguity (Issue #72)
- **Problem**: When block attribute lines were consecutive (such as `[.role-one]` followed by `[source,python]`), if they were preceded by a blank line (anywhere other than the very beginning of the document with no leading blank lines), the first attribute line was parsed as a standalone `paragraph` block containing the stringified representation of the attributes. Only the second attribute line merged with the actual target block.
- **Cause**: Because `paragraph` is defined as `(text_content _NEWLINE)+`, any attribute line like `[.role-one]\n` can syntactically match `paragraph` as well as `attribute_list` (which is part of the optional `(block_metadata)*` preceding blocks in `attributed_block`). Under some conditions (specifically after a blank line), Lark's Earley parser preferred splitting the blocks into a `paragraph` and an `attributed_block` rather than parsing them as a single `attributed_block` with two `block_metadata` children.
- **What Didn't Work**:
  - Assigning a high priority (e.g. `.10`) to the `attribute_list` rule or a priority `.5` to `block_metadata` solved the consecutive attribute issue but broke nested blocks inside sidebars, examples, and admonitions. This is because high-priority `attribute_list` rules shadowed specific block-starter terminals like `ADMONITION_START` (matching `[NOTE]`, `[IMPORTANT]`, etc.), causing the nested blocks to fail parsing entirely.
- **Solution**:
  1. Assigned a very low priority of `.1` on `attribute_list` and `anchor` rules in `grammar.lark`. This priority is sufficient to break the tie with `paragraph` (giving the merged `attributed_block` parse tree the necessary edge to always win when there are consecutive attribute lines) without forcing a fallback when parsed within constrained nesting contexts.
  2. Raised the priority of the `ADMONITION_START` terminal rule to `.5` to ensure specific admonition headers like `[NOTE]` always win over general `attribute_list.1` and are correctly parsed as block admonitions inside sidebars/examples.

## 🤖 Subagent & Model Routing Strategy

*   **Standing Instruction**: For all coding and coding-adjacent tasks, use your judgement to decide when a lower-power model would be appropriate and run that in a subagent.

