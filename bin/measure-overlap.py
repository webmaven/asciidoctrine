#!/usr/bin/env python3
"""Test coverage redundancy and overlap measurement tool.

This script parses the `.coverage` database using the official coverage API
to analyze test execution contexts, find over-tested lines of code, compute
Jaccard similarity between test suites, and detect fully redundant tests.
"""

import argparse
import os
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def main() -> None:
    # 0. Parse arguments
    parser = argparse.ArgumentParser(
        description="Test coverage redundancy and overlap measurement tool."
    )
    parser.add_argument(
        "--filter",
        type=str,
        help="Comma-separated list of substrings. Only include tests whose names contain any of these.",
    )
    parser.add_argument(
        "--exclude",
        type=str,
        help="Comma-separated list of substrings. Exclude tests whose names contain any of these.",
    )
    args = parser.parse_args()

    filter_subs = [s.strip() for s in args.filter.split(",")] if args.filter else []
    exclude_subs = [s.strip() for s in args.exclude.split(",")] if args.exclude else []

    # 1. Load coverage database
    try:
        import coverage
    except ImportError:
        print(
            "Error: 'coverage' package is not installed in the current environment.",
            file=sys.stderr,
        )
        sys.exit(1)

    db_path = ".coverage"
    if not os.path.exists(db_path):
        print(f"Error: Coverage database '{db_path}' not found.", file=sys.stderr)
        print(
            "Please run pytest with coverage first, e.g.: venv/bin/pytest --cov=src",
            file=sys.stderr,
        )
        sys.exit(1)

    cov = coverage.Coverage()
    cov.load()
    data = cov.get_data()

    # Get absolute path to src/asciidoctrine
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_prefix = os.path.join(root_dir, "src", "asciidoctrine")

    # 2. Extract mappings
    # Mapping of test_context -> set of (filepath, lineno)
    test_to_lines: Dict[str, Set[Tuple[str, int]]] = defaultdict(set)
    # Mapping of (filepath, lineno) -> list of test_contexts
    line_to_tests: Dict[Tuple[str, int], List[str]] = defaultdict(list)
    # List of all measured lines in src/
    total_measured_lines: Set[Tuple[str, int]] = set()

    for filepath in data.measured_files():
        # Only analyze package source files under src/asciidoctrine
        if not filepath.startswith(src_prefix):
            continue

        try:
            contexts_by_line = data.contexts_by_lineno(filepath)
        except Exception as e:
            print(
                f"Warning: Could not read contexts for {filepath}: {e}", file=sys.stderr
            )
            continue

        for lineno, contexts in contexts_by_line.items():
            # Clean contexts: filter out empty and metadata contexts
            clean_contexts = [
                ctx
                for ctx in contexts
                if ctx and ctx != "" and not ctx.startswith("pre-")
            ]
            if not clean_contexts:
                continue

            # Apply CLI filter and exclude rules
            filtered_contexts = []
            for ctx in clean_contexts:
                if filter_subs and not any(sub in ctx for sub in filter_subs):
                    continue
                if exclude_subs and any(sub in ctx for sub in exclude_subs):
                    continue
                filtered_contexts.append(ctx)

            if not filtered_contexts:
                continue

            loc = (filepath, lineno)
            total_measured_lines.add(loc)

            for ctx in filtered_contexts:
                test_to_lines[ctx].add(loc)
                line_to_tests[loc].append(ctx)

    if not total_measured_lines:
        print("No lines tracked with dynamic contexts under src/asciidoctrine/.")
        print(
            "Please verify pyproject.toml has dynamic_context enabled, and re-run your tests.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 3. Compute Redundancy Metrics
    total_covered = len(total_measured_lines)
    multi_tested_lines = [loc for loc, tests in line_to_tests.items() if len(tests) > 1]
    overlap_pct = (
        (len(multi_tested_lines) / total_covered) * 100 if total_covered else 0.0
    )

    print("=" * 80)
    print(" ASCIIDOCRINE TEST REDUNDANCY & OVERLAP AUDIT REPORT")
    print("=" * 80)
    print(f"Total Covered Lines (src/): {total_covered}")
    print(
        f"Lines Hit by Multiple Tests: {len(multi_tested_lines)} ({overlap_pct:.2f}%)"
    )
    print(f"Total Unique Test Contexts:  {len(test_to_lines)}")
    print("-" * 80)

    # 4. Top Over-Tested Lines
    print("\n[1] TOP 20 MOST OVER-TESTED LINES (HIGH HIT COUNT)")
    print("-" * 80)
    sorted_lines = sorted(
        line_to_tests.items(), key=lambda item: len(item[1]), reverse=True
    )

    # Cache file contents to display line snippets
    file_contents: Dict[str, List[str]] = {}

    for idx, (loc, tests) in enumerate(sorted_lines[:20], 1):
        filepath, lineno = loc
        rel_path = os.path.relpath(filepath, root_dir)

        # Read snippet
        snippet = ""
        if filepath not in file_contents:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    file_contents[filepath] = f.readlines()
            except Exception:
                file_contents[filepath] = []

        lines = file_contents[filepath]
        if 0 < lineno <= len(lines):
            snippet = lines[lineno - 1].strip()

        print(f"{idx:2d}. HITS: {len(tests):3d} | {rel_path}:{lineno}")
        print(f"    Code: {snippet}")

    # 5. Candidate Redundant Tests (Tests with 0 Unique Lines Covered)
    print("\n[2] TESTS WITH ZERO UNIQUE COVERAGE (CANDIDATES FOR CONSOLIDATION)")
    print("-" * 80)
    redundant_tests = []

    for test_ctx, lines_covered in sorted(test_to_lines.items()):
        unique_lines = []
        for loc in lines_covered:
            if len(line_to_tests[loc]) == 1:
                unique_lines.append(loc)

        if not unique_lines:
            redundant_tests.append((test_ctx, len(lines_covered)))

    if redundant_tests:
        print(
            f"Found {len(redundant_tests)} tests that do not cover any unique lines (100% of their coverage is covered by other tests):"
        )
        # Sort by line coverage size descending
        redundant_tests.sort(key=lambda x: x[1], reverse=True)
        for idx, (test_ctx, count) in enumerate(redundant_tests[:30], 1):
            print(f"  {idx:2d}. {test_ctx:<70} (Total Lines Executed: {count})")
        if len(redundant_tests) > 30:
            print(f"  ... and {len(redundant_tests) - 30} more.")
    else:
        print("  All tests cover at least one unique line!")

    # 6. High Jaccard Similarity Pairs (Highly Overlapping Tests)
    print("\n[3] HIGHLY OVERLAPPING TEST PAIRS (JACCARD SIMILARITY > 85%)")
    print("-" * 80)
    high_overlap_pairs = []
    test_list = list(test_to_lines.items())

    for i in range(len(test_list)):
        test_a, lines_a = test_list[i]
        for j in range(i + 1, len(test_list)):
            test_b, lines_b = test_list[j]
            intersection = len(lines_a & lines_b)
            union = len(lines_a | lines_b)
            if union == 0:
                continue
            jaccard = intersection / union
            if jaccard > 0.85:
                high_overlap_pairs.append((test_a, test_b, jaccard))

    if high_overlap_pairs:
        # Sort by Jaccard similarity descending
        high_overlap_pairs.sort(key=lambda x: x[2], reverse=True)
        for idx, (t1, t2, sim) in enumerate(high_overlap_pairs[:30], 1):
            print(f"  {idx:2d}. Similarity: {sim * 100:6.2f}%")
            print(f"      T1: {t1}")
            print(f"      T2: {t2}")
        if len(high_overlap_pairs) > 30:
            print(f"  ... and {len(high_overlap_pairs) - 30} more.")
    else:
        print("  No test pairs have overlap exceeding 85%!")
    print("=" * 80)


if __name__ == "__main__":
    main()
