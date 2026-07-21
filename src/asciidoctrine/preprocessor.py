"""
Preprocessor for AsciiDoc source, handling directives like include::.
"""

import os
import re
import warnings
from typing import Optional


class PreprocessorError(Exception):
    """Custom exception for preprocessor errors."""

    pass


class CircularIncludeError(PreprocessorError):
    """Custom exception for circular inclusion loops in the preprocessor."""

    pass


class PreprocessorWarning(UserWarning):
    """Warning category for fragile preprocessor constructs."""

    pass


class Preprocessor:
    """
    Processes AsciiDoc source to handle `include::` directives.
    """

    def __init__(
        self,
        base_dir: Optional[str] = None,
        safe_mode: bool = True,
        preprocess_directives: bool = True,
        attributes: Optional[dict[str, str]] = None,
        strict: bool = True,
    ) -> None:
        """
        Initializes the preprocessor.

        base_dir::
          The base directory for resolving include paths.
          Defaults to the current working directory.
        safe_mode::
          If True, prevents including files outside base_dir.
        preprocess_directives::
          If True, processes AsciiDoc preprocessing directives like include::.
        """
        self.base_dir = os.path.abspath(base_dir) if base_dir else os.getcwd()
        self.safe_mode = safe_mode
        self.preprocess_directives = preprocess_directives
        self.attributes = attributes or {}
        self.strict = strict
        self.include_regex = re.compile(r"^include::([^\[]+)\[(.*)\]\s*$")
        self.delimiter_regex = re.compile(
            r"^\s*(?:-{4,}|\.{4,}|\+{4,}|/{4,}|={4,}|\*{4,}|_{4,}|-{2}|\|===)\s*$"
        )
        self.is_preprocessed = False
        self.included_files_set: set[str] = set()
        self.line_map: dict[int, tuple[str, int]] = {}

    def _parse_attributes(self, attr_str: str) -> dict[str, str]:
        """
        Parses attribute string character by character to handle quotes and delimiters.
        """
        if not attr_str.strip():
            return {}

        chunks: list[str] = []
        current: list[str] = []
        in_double_quote = False
        in_single_quote = False
        i = 0
        while i < len(attr_str):
            char = attr_str[i]
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif (
                (char == "," or char == ";")
                and not in_double_quote
                and not in_single_quote
            ):
                chunks.append("".join(current).strip())
                current = []
                i += 1
                continue
            current.append(char)
            i += 1
        if current:
            chunks.append("".join(current).strip())

        attrs = {}
        last_key = None
        for chunk in chunks:
            if not chunk:
                continue
            if "=" in chunk:
                key, val = chunk.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                attrs[key] = val
                last_key = key
            else:
                val = chunk.strip().strip('"').strip("'")
                if last_key in ("lines", "tag", "tags"):
                    attrs[last_key] = f"{attrs[last_key]};{val}"
                else:
                    attrs[chunk] = ""
        return attrs

    def _update_delimiter_stack(self, line: str, delimiter_stack: list[str]) -> None:
        line_strip = line.strip()
        if self.delimiter_regex.match(line_strip):
            if delimiter_stack and delimiter_stack[-1] == line_strip:
                delimiter_stack.pop()
            else:
                delimiter_stack.append(line_strip)

    def _evaluate_condition(self, condition_str: str) -> bool:
        """
        Evaluates a conditional expression string.
        Supports:
          - OR logic (comma-separated): attr-a,attr-b
          - AND logic (plus-separated): attr-a+attr-b
          - Negation: !attr
        """
        condition_str = condition_str.strip()
        if not condition_str:
            return False

        # Commas (OR) have lower precedence than pluses (AND) in logical evaluation
        if "," in condition_str:
            parts = condition_str.split(",")
            return any(self._evaluate_condition(p) for p in parts)

        # Then plus for AND logic
        if "+" in condition_str:
            parts = condition_str.split("+")
            return all(self._evaluate_condition(p) for p in parts)

        # Single attribute, check negation
        if condition_str.startswith("!"):
            attr_name = condition_str[1:].strip()
            return attr_name not in self.attributes

        return condition_str in self.attributes

    def _handle_include_directive(
        self,
        match: re.Match[str],
        current_file: str,
        current_dir: str,
        line_num: int,
        line: str,
        include_stack: list[tuple[str, int, str]],
        delimiter_stack: list[str],
        in_verbatim: str | None,
        expected_closer: str | None,
    ) -> str:
        """
        Handles actual file resolution, filtering, nesting, and cycle validation
        for an include:: directive match.
        """
        self.is_preprocessed = True
        include_path = match.group(1).strip()
        attr_str = match.group(2).strip()

        target_file_path = os.path.abspath(os.path.join(current_dir, include_path))

        # Security check: verify target is within base directory if
        # safe_mode is on
        if self.safe_mode:
            try:
                common = os.path.commonpath([target_file_path, self.base_dir])
                is_outside = common != self.base_dir
            except ValueError:
                is_outside = True

            if is_outside:
                raise PreprocessorError(
                    f"Security error: include path '{include_path}' "
                    f"attempts to access files outside the base directory."
                )

        if not os.path.isfile(target_file_path):
            if not self.strict:
                parent_file = (
                    os.path.relpath(current_file, self.base_dir)
                    if current_file != "<root>"
                    else "<root>"
                )
                warnings.warn(
                    f"Include file not found: {target_file_path}", PreprocessorWarning
                )
                return f"Unresolved directive in {parent_file} - include::{include_path}[]"
            raise PreprocessorError(f"Include file not found: {target_file_path}")

        # Check if target_file_path is already in the include stack
        start_idx = next(
            (i for i, item in enumerate(include_stack) if item[0] == target_file_path),
            None,
        )

        if start_idx is not None:
            cycle_items = include_stack[start_idx:]
            cycle_files = {item[0] for item in cycle_items} | {
                target_file_path,
                current_file,
            }
            real_cycle_files = {f for f in cycle_files if os.path.isfile(f)}

            cycle_paths = [
                os.path.relpath(item[0], self.base_dir)
                if item[0] != "<root>"
                else "<root>"
                for item in cycle_items
            ]
            current_rel = (
                os.path.relpath(current_file, self.base_dir)
                if current_file != "<root>"
                else "<root>"
            )
            target_rel = os.path.relpath(target_file_path, self.base_dir)
            trace_str = " -> ".join(cycle_paths + [current_rel, target_rel])

            # Statically scan all cycle files to list all mutual includes between them
            diagnostic_lines = []
            for file_path in sorted(real_cycle_files):
                rel_file = os.path.relpath(file_path, self.base_dir)
                file_dir = os.path.dirname(file_path)

                try:
                    with open(file_path, "r", encoding="utf-8") as f_obj:
                        file_lines = f_obj.readlines()
                except Exception:
                    continue

                for idx, line_raw in enumerate(file_lines, start=1):
                    line_text = line_raw.rstrip()
                    if ":" in line_raw:
                        m = self.include_regex.match(line_text)
                        if m:
                            inc_path = m.group(1).strip()
                            abs_inc = os.path.abspath(os.path.join(file_dir, inc_path))
                            if abs_inc in real_cycle_files:
                                caret_line = "^" + "~" * (len(line_text) - 1)
                                diagnostic_lines.append(
                                    f'File "{rel_file}", line {idx}:\n'
                                    f"    {line_text}\n"
                                    f"    {caret_line}"
                                )

            detailed_diagnostics = "\n\n".join(diagnostic_lines)
            error_msg = (
                f"Circular include detected: {trace_str}\n\n{detailed_diagnostics}"
            )
            raise CircularIncludeError(error_msg)

        with open(target_file_path, "r", encoding="utf-8") as f:
            content_to_include = f.read()

        self.included_files_set.add(target_file_path)

        # Parse and resolve include attributes
        attrs = self._parse_attributes(attr_str)
        content_lines = content_to_include.splitlines(True)

        # A. Tag / Tags filtering
        target_tags = set()
        if "tag" in attrs:
            target_tags.add(attrs["tag"])
        if "tags" in attrs:
            for t in re.split(r"[,;]", attrs["tags"]):
                if t.strip():
                    target_tags.add(t.strip())

        lines_to_keep = []
        if target_tags:
            active_tags = set()
            for fline in content_lines:
                tag_start_match = re.match(r"^\s*//\s*tag::([^\[]+)\[\]", fline)
                tag_end_match = re.match(r"^\s*//\s*end::([^\[]+)\[\]", fline)
                if tag_start_match:
                    tname = tag_start_match.group(1).strip()
                    active_tags.add(tname)
                    continue
                elif tag_end_match:
                    tname = tag_end_match.group(1).strip()
                    active_tags.discard(tname)
                    continue

                if active_tags.intersection(target_tags):
                    lines_to_keep.append(fline)
        else:
            for fline in content_lines:
                if re.match(r"^\s*//\s*(?:tag|end)::[^\[]+\[\]", fline):
                    continue
                lines_to_keep.append(fline)

        # B. Lines slicing
        if "lines" in attrs:
            ranges = []
            range_strs = re.split(r"[,;]", attrs["lines"])
            for r_str in range_strs:
                r_str = r_str.strip()
                if not r_str:
                    continue
                if ".." in r_str:
                    start_s, end_s = r_str.split("..", 1)
                    start = int(start_s.strip()) if start_s.strip() else 1
                    end = int(end_s.strip()) if end_s.strip() else None
                    ranges.append((start, end))
                else:
                    try:
                        num = int(r_str)
                        ranges.append((num, num))
                    except ValueError:
                        pass

            filtered_lines = []
            for idx, fline in enumerate(lines_to_keep, 1):
                keep = False
                for start, end in ranges:
                    if end is None:
                        if idx >= start:
                            keep = True
                            break
                    else:
                        if start <= idx <= end:
                            keep = True
                            break
                if keep:
                    filtered_lines.append(fline)
            lines_to_keep = filtered_lines

        # C. Level offset shifting
        if "leveloffset" in attrs:
            offset_str = attrs["leveloffset"].strip()
            offset = int(offset_str)

            shifted_lines = []
            for fline in lines_to_keep:
                if fline.startswith("="):
                    num_equals = len(fline) - len(fline.lstrip("="))
                    remaining = fline[num_equals:]
                    if remaining and remaining[0].isspace() and remaining.strip():
                        new_num_equals = max(0, num_equals + offset)
                        if new_num_equals > 0:
                            fline = "=" * new_num_equals + remaining
                        else:
                            fline = remaining.lstrip()
                shifted_lines.append(fline)
            lines_to_keep = shifted_lines

        content_to_include = "".join(lines_to_keep)

        initial_depth = len(delimiter_stack)

        processed_content = self._process_source(
            content_to_include,
            target_file_path,
            include_stack + [(current_file, line_num, line.rstrip())],
            delimiter_stack,
            in_verbatim=in_verbatim,
            expected_closer=expected_closer,
        )

        if len(delimiter_stack) != initial_depth:
            warnings.warn(
                f"Include file '{include_path}' has unbalanced block delimiters. "
                f"Block delimiters should not be opened or closed across file boundaries.",
                PreprocessorWarning,
                stacklevel=2,
            )

        return processed_content

    def process(self, source: str) -> str:
        """
        Main entry point for processing the source text.

        source::
          The AsciiDoc source text.

        Returns::
          The source text with `include::` directives replaced by file content.
        """
        self.is_preprocessed = False
        self.included_files_set.clear()
        self.line_map = {}
        self._global_line_counter = 1
        return self._process_source(source, "<root>", [], [], None, None)

    def _record_line(self, file_path: str, line_num: int) -> None:
        if not hasattr(self, "line_map"):
            self.line_map = {}
        if not hasattr(self, "_global_line_counter"):
            self._global_line_counter = 1
        self.line_map[self._global_line_counter] = (file_path, line_num)
        self._global_line_counter += 1

    def _process_source(
        self,
        source: str,
        current_file: str,
        include_stack: list[tuple[str, int, str]],
        delimiter_stack: list[str],
        in_verbatim: str | None = None,
        expected_closer: str | None = None,
    ) -> str:
        """
        Recursively processes source text, handling includes and translating verbatim blocks.
        """

        current_dir = (
            os.path.dirname(current_file) if current_file != "<root>" else self.base_dir
        )
        processed_lines = []
        metadata_pending = False
        conditional_stack: list[bool] = []

        def is_metadata(l_strip: str) -> bool:
            if l_strip.startswith("//") and not re.match(r"^/{4,}$", l_strip):
                return True
            if l_strip.startswith("[") and l_strip.endswith("]"):
                return True
            if (
                l_strip.startswith(".")
                and not re.match(r"^\.[\s\./\\]", l_strip)
                and not re.match(r"^\.{4,}$", l_strip)
            ):
                return True
            return False

        for line_num, line in enumerate(source.splitlines(True), start=1):
            line_strip = line.strip()

            # Handle conditional directives first (only if not inside verbatim)
            if in_verbatim is None:
                # 1. endif::[] or endif::some_attr[]
                endif_match = re.match(r"^endif::([^\[]*)\[(.*)\]\s*$", line_strip)
                if endif_match:
                    if conditional_stack:
                        conditional_stack.pop()
                    continue

                # 2. ifdef::attr[] or ifdef::attr[shorthand]
                ifdef_match = re.match(r"^ifdef::([^\[]*)\[(.*)\]\s*$", line_strip)
                if ifdef_match:
                    cond_str = ifdef_match.group(1).strip()
                    body_str = ifdef_match.group(2)
                    if body_str == "":
                        # Block style
                        eval_res = self._evaluate_condition(cond_str)
                        conditional_stack.append(eval_res)
                    else:
                        # Shorthand style (only if outer stack is fully active)
                        if all(conditional_stack):
                            eval_res = self._evaluate_condition(cond_str)
                            if eval_res:
                                newline = "\n" if line.endswith("\n") else ""
                                self._record_line(current_file, line_num)
                                processed_lines.append(body_str + newline)
                    continue

                # 3. ifndef::attr[] or ifndef::attr[shorthand]
                ifndef_match = re.match(r"^ifndef::([^\[]*)\[(.*)\]\s*$", line_strip)
                if ifndef_match:
                    cond_str = ifndef_match.group(1).strip()
                    body_str = ifndef_match.group(2)
                    if body_str == "":
                        # Block style
                        eval_res = not self._evaluate_condition(cond_str)
                        conditional_stack.append(eval_res)
                    else:
                        # Shorthand style (only if outer stack is fully active)
                        if all(conditional_stack):
                            eval_res = not self._evaluate_condition(cond_str)
                            if eval_res:
                                newline = "\n" if line.endswith("\n") else ""
                                self._record_line(current_file, line_num)
                                processed_lines.append(body_str + newline)
                    continue

            # If the current block is not active, skip processing the line
            if not all(conditional_stack):
                continue

            # We are in an active block, track dynamic attribute changes (if not inside verbatim)
            if in_verbatim is None:
                # Track attribute definitions
                attr_def_match = re.match(r"^:([a-zA-Z0-9_-]+):\s*(.*)$", line_strip)
                if attr_def_match:
                    self.attributes[attr_def_match.group(1)] = attr_def_match.group(
                        2
                    ).strip()

                # Track attribute removals
                attr_rem_match1 = re.match(r"^:!([a-zA-Z0-9_-]+):$", line_strip)
                attr_rem_match2 = re.match(r"^:([a-zA-Z0-9_-]+)!:$", line_strip)
                if attr_rem_match1:
                    self.attributes.pop(attr_rem_match1.group(1), None)
                elif attr_rem_match2:
                    self.attributes.pop(attr_rem_match2.group(1), None)

            if line_strip == "":
                metadata_pending = False
            elif in_verbatim is None and is_metadata(line_strip):
                metadata_pending = True
                self._record_line(current_file, line_num)
                processed_lines.append(line)
                continue

            # Check if this line is a verbatim delimiter
            is_listing_delim = bool(re.match(r"^-{4,}$", line_strip))
            is_literal_delim = bool(re.match(r"^\.{4,}$", line_strip))
            is_passthrough_delim = bool(re.match(r"^\+{4,}$", line_strip))
            is_comment_delim = bool(re.match(r"^/{4,}$", line_strip))

            if in_verbatim is not None:
                # We are inside a verbatim block
                if line_strip == expected_closer:
                    # Check same-length nesting violation
                    if metadata_pending:
                        warnings.warn(
                            f"Same-length nesting of verbatim block '{in_verbatim}' with delimiter '{line_strip}' "
                            f"detected at line {line_num}. This violates the AsciiDoc specification and will terminate "
                            f"the outer block prematurely.",
                            PreprocessorWarning,
                            stacklevel=2,
                        )
                    # Convert to synthetic outer end tag
                    line = f"--ASCIIDOCTRINE_OUTER_{in_verbatim.upper()}_END_{len(line_strip)}--\n"
                    in_verbatim = None
                    expected_closer = None
                    metadata_pending = False
                    if delimiter_stack and delimiter_stack[-1] == line_strip:
                        delimiter_stack.pop()
                    self._record_line(current_file, line_num)
                    processed_lines.append(line)
                    continue
                else:
                    # Inside verbatim block and not the closer
                    # We still process includes if present
                    match = None
                    if self.preprocess_directives and ":" in line:
                        match = self.include_regex.match(line.rstrip())

                    if match:
                        processed_content = self._handle_include_directive(
                            match,
                            current_file,
                            current_dir,
                            line_num,
                            line,
                            include_stack,
                            delimiter_stack,
                            in_verbatim,
                            expected_closer,
                        )
                        processed_lines.append(processed_content)

                    else:
                        if is_metadata(line_strip):
                            metadata_pending = True
                        else:
                            metadata_pending = False
                        self._record_line(current_file, line_num)
                        processed_lines.append(line)
                    continue

            # We are not in a verbatim block
            if is_listing_delim:
                line = f"--ASCIIDOCTRINE_OUTER_LISTING_START_{len(line_strip)}--\n"
                in_verbatim = "listing"
                expected_closer = line_strip
                delimiter_stack.append(line_strip)
                metadata_pending = False
                self._record_line(current_file, line_num)
                processed_lines.append(line)
                continue
            elif is_literal_delim:
                line = f"--ASCIIDOCTRINE_OUTER_LITERAL_START_{len(line_strip)}--\n"
                in_verbatim = "literal"
                expected_closer = line_strip
                delimiter_stack.append(line_strip)
                metadata_pending = False
                self._record_line(current_file, line_num)
                processed_lines.append(line)
                continue
            elif is_passthrough_delim:
                line = f"--ASCIIDOCTRINE_OUTER_PASSTHROUGH_START_{len(line_strip)}--\n"
                in_verbatim = "passthrough"
                expected_closer = line_strip
                delimiter_stack.append(line_strip)
                metadata_pending = False
                self._record_line(current_file, line_num)
                processed_lines.append(line)
                continue
            elif is_comment_delim:
                line = f"--ASCIIDOCTRINE_OUTER_COMMENT_START_{len(line_strip)}--\n"
                in_verbatim = "comment"
                expected_closer = line_strip
                delimiter_stack.append(line_strip)
                metadata_pending = False
                self._record_line(current_file, line_num)
                processed_lines.append(line)
                continue
            elif self.delimiter_regex.match(line_strip):
                # Other delimiters (e.g. ====, ****)
                self._update_delimiter_stack(line_strip, delimiter_stack)
                metadata_pending = False
                self._record_line(current_file, line_num)
                processed_lines.append(line)
            else:
                # Normal line
                match = None
                if self.preprocess_directives and ":" in line:
                    match = self.include_regex.match(line.rstrip())

                if match:
                    processed_content = self._handle_include_directive(
                        match,
                        current_file,
                        current_dir,
                        line_num,
                        line,
                        include_stack,
                        delimiter_stack,
                        in_verbatim,
                        expected_closer,
                    )
                    processed_lines.append(processed_content)
                else:
                    self._record_line(current_file, line_num)
                    processed_lines.append(line)

        if current_file == "<root>":
            self.root_in_verbatim = in_verbatim
            self.root_delimiter_stack = list(delimiter_stack)

        return "".join(processed_lines)
