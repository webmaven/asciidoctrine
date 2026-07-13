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

## 📚 Submodule References

The project relies on four key submodules inside the `vendor/` directory:

1. **`vendor/asciidoc-tck/` (Technology Compatibility Kit)**:
   - **Purpose**: Authoritative conformance test suite for AsciiDoc specification compliance.
   - **Usage**: Automatically run via `./run-tck.sh` to ensure our parsed ASG matches the reference semantic model.
   - **Contributions**: We contribute expansions of the test suite to this submodule. Note that tests can only be contributed for parts of the specification that are already accepted.

2. **`vendor/asciidoc-lang/` (AsciiDoc Language Specification)**:
   - **Purpose**: Contains the source documents and schemas for the official AsciiDoc language standard.
   - **Usage**: Serves as our reference source for validating nodes and structural mappings (e.g., ASG schemas).
   - **Contributions**: This is where we contribute direct expansions or clarifications to the language specification itself.

3. **`vendor/asciidoctor-doctest/`**:
   - **Purpose**: Real-world AsciiDoc test corpus.
   - **Usage**: Used in `tests/test_doctest_parsing.py` to assert that complex formatting and structure examples compile without error.

4. **`vendor/asciidoc-parsing-lab/`**:
   - **Purpose**: Pre-draft grammar prototyping playground for the official AsciiDoc Language Specification.
   - **Usage**: Serving as the direct prototype laboratory where new spec grammars and features are drafted, compiled, and tested (using Peggy/JavaScript) before they are fully finalized and added to the official specification. Always use this as a design reference for emerging or debated language syntax.

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

### 3. Unified LF Normalization & Simplified Newline Lexing
- **Problem**: Lark's Earley parser suffered from extra backtrack overhead evaluating mixed line endings within complex regex block-delimited lookaheads (such as `LISTING_CONTENT: /(.+?)(?=\n-{4,})/s`). Additionally, when running inside browser/Pyodide sandboxed environments without native filesystem streams, copy-pasting across different OS clipboards introduced mixed CRLF/LF line endings, leading to silent format drift and noisy Git diffs on round-trips.
- **Solution**:
  1. Standardized all source line endings to standard Unix LF (`\n`) pre-parsing.
  2. Detected the original document's line ending preference using a fast, positional lookahead check on the very first encountered newline, storing it as `line_ending` on the root `Document` AST node along with `had_trailing_newline`.
  3. Simplified the `_NEWLINE` terminal in `grammar.lark` from the complex regex `_NEWLINE: /(\r\n|\n|\r)/` to a simple, faster literal match `_NEWLINE: "\n"`.
  4. Custom-translated all serialized newlines back to the document's original `line_ending` sequence inside the serializer's `write` method, ensuring $100\%$ exact, character-for-character round-trip accuracy on modern files.

### 4. Balancing Structural, List, and Inline Formatting Priorities in Earley Parser
- **Problem**: 
  1. Assigning a high priority (e.g. `.10`) to general inline formatting rules (`bold`, `italic`, `marked`, `superscript`, `subscript`) caused the parser to choose incorrect parse trees by greedy matching of formatting characters. This "stole" asterisks from list markers (turning lists into bold formatting nodes), stole underscores/asterisks from within attribute names and links, and broke literal monospace block formatting rules.
  2. Conversely, assigning too low a priority to structural block rules like `table` caused lines starting with table delimiters `|===` to be incorrectly swallowed as normal `paragraph` content when attributes (`[cols="1,2"]`) preceded them.
  3. Attempting to fix lists by assigning a high priority (e.g., `.10`) to the top-level list containers (`ulist`, `olist`, etc.) caused the Earley parser to split continuous lists of multiple items into separate, single-item lists. Because Earley maximizes the *sum* of priorities in the tree, splitting a list of 3 items into 3 separate container blocks yielded a higher total priority (`3 * 10 = 30`) than keeping them in a single container block (`1 * 10 = 10`).
- **What Didn't Work**:
  - Setting high priorities on all inline style rules broke other syntactic structures entirely.
  - Setting priorities on list container rules caused incorrect list block splits.
- **Solution**:
  1. **Moderate Inline Priorities**: Shifted standard inline formatting rules (`bold`, `italic`, `marked`, `superscript`, `subscript`) to moderate priorities (e.g., `bold.2`, `unconstrained_bold.3`) so they can successfully compete with default text matching, but are out-prioritized by structural elements.
  2. **High Table Priority**: Assigned high priority (`table.10`) to the table delimiter rule so that tables are prioritized over generic paragraph interpretation.
  3. **Item-Level List Priorities**: Assigned moderate-high priority (`.5`) to individual list item rules (`ulist_item.5`, `olist_item.5`, etc.) rather than the container rules (`ulist`, `olist`). Since the count of list items is identical regardless of how the list blocks are split, assigning priority to items avoids the Earley split multiplication problem while still ensuring that list markers are fully protected from being stolen by inline styles.
  4. **High Literal/Structure Priorities**: Kept high priority on attribute entry blocks (`attribute_entry.10`), inline links (`inline_link.10`), and literal monospace spans (`monospace.10`, `unconstrained_monospace.10`) to protect their contents from nested style interpretation.

### 5. Lexer Terminal Token Priority Conflicts inside Table Cells
- **Problem**: When a table contained multiple rows with complex inline elements (like URLs/URIs, formatting, etc.), the table block failed to parse, falling back to a series of plain `paragraph` blocks.
- **Cause**: High-priority inline terminals (like `URI` with priority `.3` or `inline_link` with priority `.10`) competed with the `TABLE_CELL` terminal (default priority 1). Lark's lexer matched these individual high-priority inline tokens *inside* the cell instead of tokenizing the entire cell content as a single `TABLE_CELL` terminal. Because the cell string was split into other tokens, the structural `table` rule failed to match.
- **What Didn't Work**: Setting a high priority on the structural `table` rule itself (e.g. `table.50`) only helps if the input is successfully tokenized. It did not prevent the lexer from mis-tokenizing cell text.
- **Solution**:
  1. Assigned an explicit priority of `.20` to the `TABLE_CELL` terminal rule in `grammar.lark`. This is higher than `.10` (for `inline_link`) and `.3` (for `URI`), ensuring the entire cell content is cleanly swallowed as a single `TABLE_CELL` token.
  2. Assigned a priority of `.30` to `TABLE_DELIM` to ensure it wins over `TABLE_CELL` when starting/ending a table.

## 🤖 Subagent & Model Routing Strategy

*   **Standing Instruction**: For all coding and coding-adjacent tasks, use your judgement to decide when a lower-power model would be appropriate and run that in a subagent.
