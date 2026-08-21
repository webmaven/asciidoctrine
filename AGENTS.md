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

> [!IMPORTANT]
> **Pyodide v314.0.2 Verification & Assertion**:
> - Yes, **Pyodide version `314.0.2` is a valid, existing release** utilized within our CI/CD pipelines (e.g., in `.github/workflows/ci.yml`).
> - While public standard Pyodide releases are conventionally in the `0.x.x` range, this is **not a typo or placeholder**. Do not attempt to refactor or report this version as non-existent.
> - Reference evidence and public release structures are hosted on the [Pyodide Releases Page](https://github.com/pyodide/pyodide/releases).


### TCK Dependencies
The Technology Compatibility Kit (TCK) requires Node.js (>= 20) and npm.

```bash
cd vendor/asciidoc-tck
npm ci
```
*Note: `run-tck.sh` handles `npm ci` automatically if `node_modules` is missing.*

## 🧪 Testing Protocols & Workflow Tiers

The project uses a 3-tiered testing strategy designed to maximize test signal while minimizing execution time and output noise:

### Tier 1: Rapid Development Loop (Fast / Focused)
Use while iterating on a specific feature, bugfix, or grammar rule. Keep output minimal (`-q`) and focus strictly on the affected module.

```bash
# Run a specific test file with quiet output
venv/bin/pytest tests/test_inlines_parsing.py -q

# Run a single target test function
venv/bin/pytest tests/test_inlines_parsing.py -k "test_custom_scheme" -q --tb=short
```

### Tier 2: Pre-Commit Check (Core Unit + Local TCK Suite)
Use before committing code. Runs all unit tests and the native Python local TCK harness (`tests/test_local_tck.py`).

```bash
# Run all stable tests quietly
venv/bin/pytest -k "not functional" -q --tb=short
```

### Tier 3: Pre-Release Conformance Check (Full Suite + Doctests + Upstream TCK)
Use before tagging releases or pushing release branches. Runs real-world doctest corpus, Node.js upstream TCK runner, and static linters.

```bash
# 1. Full Pytest suite including all 244 real-world doctests
RUN_DOCTESTS=1 venv/bin/pytest -k "not functional" -q

# 2. Official Upstream Node.js TCK Runner
./run-tck.sh

# 3. TCK Coverage Summary Report
./run-tck-coverage.sh

# 4. Static Linters & Type Checking
venv/bin/ruff check . && venv/bin/mypy src/asciidoctrine
```

*   **Adapter**: `bin/tck-adapter.py` (Bridge between TCK runner and parser)
*   **Official TCK Location**: `vendor/asciidoc-tck/`
*   **Local TCK Harness Location**: `tests/tck_harness/` (Tested natively via `tests/test_local_tck.py`)


## 📋 New Feature Checklist

When adding support for a new AsciiDoc element or for a newly discovered edge case or corner case, follow the Red/Green TDD workflow:

1.  **Tests**:
    *   Add a unit test in `tests/test_blocks_parsing.py` or `tests/test_inlines_parsing.py`.
    *   Add a functional test or TCK-style test in `tests/tck_harness/`.
    *   These tests are expected to fail at this time (Red).
2.  **Grammar**: Add the rule to `src/asciidoctrine/grammar.lark`.
3.  **Node**: Define a new `Node` subclass in `src/asciidoctrine/nodes.py` that matches the [ASG schema](https://gitlab.eclipse.org/eclipse/asciidoc-lang/asciidoc-lang/-/blob/main/asg/schema.json).
4.  **Transformer**: Implement a corresponding method in `BlockTransformer` or `InlineTransformer`.
5.  **Resolver**: If the element contains text that supports attribute substitution, ensure it's handled in `src/asciidoctrine/resolver.py`.
6.  **Backend**: Add a `visit_<name>` method to `DocutilsRenderer` in `src/asciidoctrine/docutils_backend.py`.
7. At this point, the tests should pass (Green). If not, the implementation should be fixed until it does.
8. After the tests pass, we can refactor or optimize the implementation to be more efficient or elegant without modifying the tests. In general corner cases and edge cases should be addressed in the implementation phase, while optimizations and other improvements should be addressed in this phase. 

## 🚀 Pre-Release Verification Checklist

Before releasing any package version to PyPI, follow this checklist sequentially to prevent regressions, formatting lints, and setup failures:

1. **Local Test & Lint Execution**:
   - Ensure Ruff linter and formatter are completely happy:
     ```bash
     venv/bin/ruff format --check .
     venv/bin/ruff check .
     ```
   - Ensure the Mypy strict type-checker passes cleanly:
     ```bash
     venv/bin/mypy src/asciidoctrine
     ```
   - Run the full test suite locally with coverage:
     ```bash
     venv/bin/pytest --cov=src --cov-report=term-missing -k "not functional"
     ```
   - Run the TCK suite locally and check for 100% compliance:
     ```bash
     ./run-tck.sh
     ```

2. **Verify Version Coherence**:
   - Check that the exact target version is aligned in `pyproject.toml` (under `version = "..."`).
   - Check that the exact same string matches `__version__ = "..."` inside `src/asciidoctrine/__init__.py`.
   - Ensure the new release section is added at the top of `CHANGELOG.adoc`.

3. **Verify Documentation and Sandboxes**:
   - Clear and rebuild documentation:
     ```bash
     venv/bin/sphinx-build -a -E -b html docs docs/_build/html
     ```
   - Confirm that the Pyodide/sandbox tests (`tests/test_functional.py`) dynamically resolve and load the correct built wheel name instead of relying on any hardcoded version.

4. **Verify GHA Status on main**:
   - Push release branches to GitHub and verify that **all GitHub Actions jobs** (including Pyodide runs, document builders, and linters) succeed cleanly with a green checkmark before creating the PyPI release.

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
To facilitate producing a TCK-compliant Resolved Abstract Semantic Graph (ASG), the internal AST structure in `nodes.py` aligns directly with the official ASG schema. Each node implements a polymorphic `to_dict()` method producing compliant output:
- `Document`: `{"name": "document", "type": "block", "blocks": [], "attributes": {}, "header": {}}`
- `Paragraph`: `{"name": "paragraph", "type": "block", "inlines": []}`
- `Text`: `{"name": "text", "type": "string", "value": "text content"}`
- `Span`: `{"name": "span", "type": "inline", "variant": "strong|emphasis|code|mark", "form": "constrained|unconstrained", "inlines": [], "attributes": {"role": "class1 class2"}}` (roles are stored in `attributes["role"]` as a space-delimited string when applied via `[.role]#text#` syntax)
- `Section`: `{"name": "section", "type": "block", "level": 1, "title": [], "blocks": []}`
- `List`: `{"name": "list", "type": "block", "variant": "unordered|ordered", "marker": "*|.", "items": []}`
- `ListItem`: `{"name": "listItem", "type": "block", "principal": [], "blocks": []}`
- `Listing`: `{"name": "listing", "type": "block", "form": "delimited", "delimiter": "----", "inlines": []}`
- `Ref`: `{"name": "ref", "type": "inline", "variant": "link", "target": "url", "inlines": []}`

### 6. Preprocessor Expression Tokenization & ConditionalStack Architecture
- **Quote-Aware Expression Tokenization**: `_split_ifeval_expression(expr)` replaces naive regex matching with a character-by-character scanner that tracks quote state (`"` and `'`). Comparison operators (`==`, `!=`, `<=`, `>=`, `<`, `>`) embedded inside string literals (e.g. `ifeval::["a == b" == "a == b"]`) are ignored during top-level operator resolution.
- **ConditionalStack & Frame Management**: `ConditionalFrame` dataclass tracks `active`, `name`, and `directive` across nested `ifdef`, `ifndef`, and `ifeval` blocks.
- **Named `endif` Target Validation**: `ConditionalStack.pop(name)` validates that named endifs (e.g. `endif::backend[]`) match the target name of the opening directive. In `strict=True` mode, mismatched names raise `PreprocessorError`; in `strict=False` mode, a `PreprocessorWarning` is issued while remaining lenient.
- **Loop Decomposition**: `_try_handle_conditional_directive()` isolates conditional directive matching from `_process_source()` to preserve clean SRP design.

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
### 6. Code Listing Block vs. Nested Inline Formatting Priorities in Earley Parser
- **Problem**: When a delimited `listing_block` (such as `----` containing source code) contained many lines with formatting characters like backticks (`` ` ``), underscores (`_`), or asterisks (`*`), the block was parsed as dozens of individual `paragraph` and `literal` blocks instead of a single cohesive `listing_block`.
- **Cause**: Because the Earley algorithm maximizes the sum of priorities of all nodes in a parsed tree, a tree where the content is split into many separate `paragraph` and `literal` blocks containing numerous high-priority inline style nodes (like `monospace.10` for backticks, `bold.2`, or `italic.2`) achieves a significantly higher total priority score than a single simple `listing_block` rule (originally with priority `50`) that parses the entire interior as a single flat `LISTING_CONTENT` terminal.
- **What Didn't Work**: Writing the content with fewer formatting characters worked, but realistic code snippets with a standard density of backticks, underscores, or inline spans inevitably triggered the priority flip, breaking parser robustness on complex files.
### 7. Verbatim Block Nesting Support via Stateful Preprocessor & Reconstructor
- **Problem**: When a listing block, literal block, or passthrough block contained nested blocks of the same or different delimiter lengths, Lark's parser failed to isolate them correctly, often matching the nested delimiter as the end of the outer block and breaking the document structure.
- **Cause**: Standard EBNF regexes cannot easily resolve arbitrary same-line or stateful nested block boundaries without full semantic states, which standard lexers do not track.
- **What Didn't Work**: Attempting to write complex context-sensitive grammar rules inside `grammar.lark` introduced massive Earley ambiguity and parsing overhead, and broke normal block boundaries.
- **Solution**:
  1. **Stateful Preprocessor Translation**: Added a fast line-by-line state machine inside `preprocessor.py` that tracks the outermost `in_verbatim` state and rewrites only the outer opening and closing delimiters to unique synthetic tags (e.g. `--ASCIIDOCTRINE_OUTER_LISTING_START_N--`, where `N` is the original length of the delimiter). This shields and preserves all nested delimiters inside as raw content.
  2. **High-Priority Synthetic Rules**: Integrated these synthetic markers into `grammar.lark` as dedicated high-priority rules and terminals.
  3. **AST Reconstructor**: Added matching visitor methods in `block_transformer.py` to extract the length `N` from the start token, reconstruct standard delimiters, and cleanly construct standard `Listing`, `Literal`, and `Passthrough` AST nodes, ensuring seamless compatibility with downsteam components.
### 8. Block Macro vs. Description List (DList) Bracket Discrimination
- **Problem**: When a valid description list term (such as `About::` or `Asciidoctor::` on its own line) was parsed, it was mistakenly matched as a `block_macro` block in permissive mode instead of a description list term.
- **Cause**: The `block_macro` rule in `grammar.lark` had optional brackets (`[LSQB]...[RSQB]`), meaning any `WORD::` line matched `block_macro` first. If brackets were made fully required, however, then permissive-mode bracket-less block macros like `image::logo.png` would fail to parse as macro blocks, parsing instead as standard paragraphs.
- **Solution**: Split the grammar's `block_macro` rule into two distinct alternatives:
  1. `WORD "::" MACRO_TARGET [LSQB] [ATTR_LIST_CONTENT] [RSQB] _NEWLINE`: This requires a target following the colons (e.g. `image::logo.png`), but keeps brackets optional to maintain robust permissive-mode fallback.
  2. `WORD "::" LSQB [ATTR_LIST_CONTENT] RSQB _NEWLINE`: This has an empty target (no characters following colons) but strictly requires brackets (e.g. `toc::[]`).
  This clean discrimination prevents raw term lines (such as `About::\n`) from ever matching `block_macro`, while retaining perfect support for both valid macros and bracket-less malformed macros.

### 9. Inline Macro Prefix vs. URI Terminal Lexer Priority Conflict
- **Problem**: When an inline macro with a URL target was used (e.g., `link:https://example.com[text]`, `image:https://cdn.example.com/logo.png[Logo]`), the `link:`, `image:`, `icon:`, `xref:`, or `anchor:` prefix was consumed as literal text instead of being recognized as part of the macro rule. The URL portion was then matched by the `URI.3` terminal via the bare URL branch, producing an incorrect AST where the prefix appeared as a text node and the link lost its explicit macro semantics.
- **Cause**: Lark's Earley parser decomposes string literals like `"link:"` into `WORD("link") + COLON(":")` at the lexer level. The `URI.3` terminal (priority `.3`) then grabs the `https://...` portion before the composite rule `"link:" URI inline_attribute_list` can match. The second branch (`URI inline_attribute_list`) wins instead.
- **What Didn't Work**: Increasing the priority of the `inline_link` rule itself (e.g., `inline_link.20`) does not help because the problem is at the lexer tokenization level, not at the Earley rule-selection level. The `"link:"` string literal is never tokenized as a single unit.
- **Solution**:
  1. **Dedicated Prefix Terminals**: Introduced explicit high-priority terminals for all inline macro prefixes: `LINK_PREFIX.5: "link:"`, `IMAGE_PREFIX.5: "image:"`, `ICON_PREFIX.5: "icon:"`, `ANCHOR_PREFIX.5: "anchor:"`, `XREF_PREFIX.5: "xref:"`. Priority `.5` is higher than `URI.3`, ensuring the lexer tokenizes the prefix as a single unit before `URI` can grab the URL.
  2. **Grammar Rule Updates**: Changed all affected rules to use the new prefix terminals and accept `(TARGET | URI)` for the target, e.g., `inline_link.10: LINK_PREFIX (TARGET | URI) inline_attribute_list | URI inline_attribute_list`.
  3. **Transformer Updates**: Updated `inline_link`, `inline_image`, `icon_inline`, `inline_anchor`, and `inline_xref` transformer methods in `inline_transformer.py` to detect and skip the prefix token in the children list before extracting the target.
  4. **URI Trailing Formatting Fix**: Updated the `URI.3` regex with a negative lookbehind `(?<![*_\`.,;:!?\)\}>])` so that trailing formatting delimiters (`*`, `_`, `` ` ``) and punctuation are not swallowed into the URL token. This allows `*https://example.com*` to parse as bold-wrapped bare link instead of a bare link with `*` appended to the target.
  5. **Nested Ref Unwrapping**: Added an `_unwrap` pass in the `inline_link` transformer that flattens any nested `Ref` nodes inside link labels (which occur when the label text is itself a URL parsed by `parse_inlines`) into plain text, preventing invalid nested anchor elements.
  6. **Expanded URI Scheme Support**: Broadened the `URI.3` terminal from only `http|https|ftp|file|irc|mailto` to cover all browser-native and common schemes: `https?|ftps?|file|ircs?|wss?|git|ssh|gopher|chrome|edge|chrome-extension|moz-extension|resource` (authority-based) and `mailto|data|tel|sms|urn|blob|about` (opaque/no-authority).

### 10. Perpetual Deprecation Policy for the `--` Open Block Delimiter
- **Decision**: The legacy `--` open block delimiter is **deprecated in perpetuity** and will **never** be escalated to a hard error, even under `strict=True`. It is too widespread in existing AsciiDoc content to make that transition viable.
- **Behaviour Contract**:
  - In all modes (strict or permissive): the transformer emits a `DeprecationWarning` via Python's `warnings` module.
  - In `strict=True`: the parse still succeeds and returns a valid `Open` AST node — `ASTSyntaxAuditor` does **not** have a `visit_open` method and must **not** be given one for this purpose.
  - In `strict=False`: identical behaviour — successful parse + `DeprecationWarning`.
- **Testing**: A regression guard test `test_legacy_open_block_strict_mode_never_errors` in `tests/test_strict_parsing.py` asserts both halves of this contract. It must not be removed or weakened.
- **Contrast with other strict errors**: All other `ASTSyntaxAuditor`-enforced errors (malformed attribute lists, unclosed anchors, missing macro brackets, bad dlist markers, malformed table cell specifiers) represent genuinely broken syntax that has a plausible but incorrect fallback parse. The `--` delimiter is not broken — it is valid but superseded syntax, which is why it belongs in the deprecation-warning category rather than the strict-error category.

### 11. WORD Terminal Exclusion of `#`, `^`, and `~` for Marked/Superscript/Subscript Parsing
- **Problem**: When attempting to parse constrained marked text (`#text#`), unconstrained marked text (`##text##`), superscript (`^text^`), or subscript (`~text~`), the `WORD` terminal greedily consumed the delimiter characters as part of normal word content. This prevented the Earley parser from ever seeing the delimiters as rule boundaries.
- **Cause**: The `WORD` terminal regex `/[^ \t\n*_`=\[\]{}:<>+()]+/` did not exclude `#`, `^`, or `~`. Lark's lexer tokenized `#text#` as a single `WORD("#text#")` token, so the `marked` rule's `HASH inline_content HASH` pattern had no individual `HASH` tokens to match against.
- **What Didn't Work**: Raising the priority of the `marked` or `HASH` terminal did not help because the problem was at the lexer level — the characters were never tokenized separately.
- **Solution**: Updated the `WORD` terminal regex to `/[^ \t\n*_`=\[\]{}:<>+()#^~]+/`, explicitly excluding `#`, `^`, and `~`. This forces the lexer to emit these characters as individual tokens, allowing the `marked`, `unconstrained_marked`, `superscript`, and `subscript` grammar rules to match correctly. The `unconstrained_marked` rule uses literal `"##"` at priority `.3`, consistent with other unconstrained inline formatting rules (`unconstrained_bold.3`, `unconstrained_italic.3`, `unconstrained_monospace.3`).
- **Design Decision — Literal `"##"` vs. Dedicated Terminal**: The `unconstrained_marked` rule uses the literal string `"##"` rather than a dedicated `DOUBLEHASH` terminal. This is consistent with how `unconstrained_bold` uses `"**"`, `unconstrained_italic` uses `"__"`, and `unconstrained_monospace` uses ` "``" `. Lark decomposes multi-character literals into individual token sequences during lexing, which is the desired behavior for Earley parsing. A dedicated terminal would only be warranted if there were other grammar contexts that needed to match the exact sequence `##` as a single lexer token — and there are none.


### 12. Page Break Terminal Precedence (`PAGE_BREAK_MARKER.20`)
- **Problem**: When a page break marker (such as `<<<` or `<<<<`) was placed standalone or surrounded by blank lines, Lark's Earley parser preferred tokenizing and parsing it as a plain `paragraph` block node containing literal string text instead of a `PageBreak` block node.
- **Cause**: The `paragraph` rule's text terminals competed with untyped or low-priority character sequences. Because `paragraph` had a high cumulative tree score across line breaks, Lark's Earley engine selected the paragraph parse branch.
- **Solution**:
  1. Defined a dedicated terminal `PAGE_BREAK_MARKER.20: /<{3,}/` with explicit priority `20` in `src/asciidoctrine/grammar.lark`.
  2. Defined rule `page_break.20: PAGE_BREAK_MARKER _NEWLINE` with priority `20` to ensure page breaks always outweigh generic text paragraph alternatives.

### 13. Quote and Verse Attribution and CiteTitle Extraction
- **Problem**: Positional and named attributes on quote and verse blocks (e.g. `[quote, author, title]` or `[quote, attribution="...", citetitle="..."]`) were previously retained only as generic string attributes or dropped, rather than assigned to semantic node properties (`attribution`, `citetitle`) on `Quote` and `Verse` AST/ASG nodes.
- **Solution**:
  1. Updated `Quote` and `Verse` in `src/asciidoctrine/nodes.py` to accept `attribution` and `citetitle` arguments and serialize them in `to_dict()`.
  2. Updated `attributed_block` in `src/asciidoctrine/lark_parser.py` to inspect named keys (`attribution`, `quote_author`, `author`, `citetitle`, `quote_title`, `title`) and positional attributes (index 1 for author/attribution, index 2 for title/citetitle) when constructing `Quote` and `Verse` nodes.

### 14. Description List Continuation (`+`) Handling
- **Problem**: When a description list item contained multiple paragraphs connected by list continuation markers (`+`), the subsequent paragraphs were either dropped or left as literal `+` paragraph text instead of being appended to the `DescriptionListItem.blocks` sequence.
- **Solution**:
  1. Generalized `split_continuation_paragraphs()` in `src/asciidoctrine/lark_parser.py` to scan for `\n+\n` sequences within joint paragraphs and break them into distinct `Paragraph` blocks alternating with synthetic continuation tokens.
  2. Updated `resolve_list_continuations()` to recognize and traverse `DescriptionList` and `DescriptionListItem` nodes alongside standard `List` and `ListItem` nodes.
  3. Integrated `expand_joint_paragraphs()` into `dlist_item()` in `src/asciidoctrine/transformers/block_transformer.py` to ensure continuation tokens are consumed and attached to the active item's block list.

### 15. Verbatim Inline Callout Extraction & Auto-Increment
- **Problem**: Callout markers in code listings (such as `<1>`, `<2>`, `// <1>`, `/* <1> */`, `<!-- <.> -->`, `<!--1-->`) were retained as raw code strings rather than transformed into structured `Callout` inline nodes in `Listing.inlines`.
- **Solution**:
  1. Implemented `_build_verbatim_inlines()` in `src/asciidoctrine/transformers/block_transformer.py` to scan verbatim lines, identify callout delimiters across common programming and markup comment conventions, strip wrapping comments, and emit structured `Callout(number=...)` nodes.
  2. Supported sequential auto-numbering (`<.>`) with monotonic counter tracking across mixed explicit and auto-numbered callout lines.
  3. Updated `VerbatimBlockMixin` in `src/asciidoctrine/nodes.py` so helper properties (`code`, `stripped_code`, `callouts`) work transparently with structured inline node lists as well as raw string inputs.

### 16. Document-Level Footnote Collection & Sequential Indexing in `ASGResolver`
- **Problem**: Footnote macros (`footnote:[text]`, `footnoteref:[id, text]`, `footnoteref:[id]`) were parsed as inline `Ref` nodes, but `ASGResolver` did not collect them into a document-level catalog, leaving them without resolved sequential 1-based indices.
- **Solution**:
  1. Added stateful footnote tracking (`self.footnotes`, `self.footnote_counter`, `self.footnote_by_id`) in `ASGResolver` initialized and reset on each `resolve()` invocation.
  2. In `visit_ref()`, matched `node.variant == "footnote"` to assign sequential indices, register definitions, resolve duplicate and forward references, and populate `node.index`.
### 17. Table Cells Containing Delimited Blocks Priority Conflict (Issue #95)
- **Problem**: When a table contained AsciiDoc-style cells (`a|`) with delimited blocks (such as `[source,python]\n----\ndef foo():\n    pass\n----`), the entire table failed to parse as a `Table` AST node, falling back to a sequence of top-level `Paragraph` and `Listing` blocks (`<p>|===</p>`, `<p>a|</p>`, etc.).
- **Cause**: Delimited verbatim blocks (`listing_block.10000`, `literal_block.10000`, `outer_listing_block.10000`) carry a high rule priority (`10000`) to prevent code lines from being broken down into dozens of fine-grained inline formatting nodes. The `table` container rule had a priority of `50`, while `table_cell` had the default priority of `0`. Because Lark's Earley algorithm selects the parse tree maximizing the sum of all node priorities across the tree, an alternative parse tree that splits the table into standalone top-level paragraphs and listing blocks accumulated $10000 \times N$ points, vastly outweighing the single `table.50` parse tree ($50 + 0 \times N$ points).
- **What Didn't Work**:
  - Increasing the container-level `table` priority alone (e.g. `table.50000`) is fragile because tables with many listing blocks ($> 5$) would still exceed the fixed threshold and flip to the split tree.
- **Solution**:
  - Assigned an explicit high priority of `.20000` to the `table_cell` rule in `src/asciidoctrine/grammar.lark` (`table_cell.20000: [table_cell_spec] TABLE_CELL`).
### 18. Breaking List Affinity on Attributed Consecutive Lists (Issue #96)
- **Problem**: When consecutive description lists or standard lists with distinct block attributes (e.g. `[parameters]` followed by `[returns]`) or titles were parsed, `BlockTransformer._merge_consecutive_lists` and `resolve_list_continuations` merged them into a single `DescriptionList` / `List` node, silently discarding the attributes and title of the second list.
- **Cause**: The list-merging logic previously only checked whether adjacent list variants matched (`isinstance(current_block, ASTList) and isinstance(prev_block, ASTList)` or `isinstance(current_block, DescriptionList)`), without checking whether the subsequent list declared its own block attributes or title.
- **Solution**:
  1. Updated `BlockTransformer._merge_consecutive_lists` to guard against merging when `current_block` contains attributes (`bool(current_block.attributes)`) or a title (`current_block.title is not None`).
  2. Updated `resolve_list_continuations` in `src/asciidoctrine/lark_parser.py` with identical guards so subsequent lists with metadata are not merged during continuation resolution.
  3. Preserved normal loose list merging when adjacent list items are separated by blank lines without explicit attributes or titles.

## 🤖 Subagent & Model Routing Strategy

*   **Standing Instruction**: For all coding and coding-adjacent tasks, use your judgement to decide when a lower-power model would be appropriate and run that in a subagent.

