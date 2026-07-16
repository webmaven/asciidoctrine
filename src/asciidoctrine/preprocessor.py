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

    def __init__(self, base_dir: Optional[str] = None, safe_mode: bool = True) -> None:
        """
        Initializes the preprocessor.
        Args:
            base_dir (str, optional): The base directory for resolving include paths.
                                      Defaults to the current working directory.
            safe_mode (bool): If True, prevents including files outside base_dir.
        """
        self.base_dir = os.path.abspath(base_dir) if base_dir else os.getcwd()
        self.safe_mode = safe_mode
        self.include_regex = re.compile(r"^include::([^\[]+)\[(.*)\]\s*$")
        self.delimiter_regex = re.compile(
            r"^\s*(?:-{4,}|\.{4,}|\+{4,}|={4,}|\*{4,}|_{4,}|-{2}|\|===)\s*$"
        )
        self.is_preprocessed = False
        self.included_files_set: set[str] = set()

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

    def process(self, source: str) -> str:
        """
        Main entry point for processing the source text.
        Args:
            source (str): The AsciiDoc source text.
        Returns:
            str: The source text with `include::` directives replaced by file content.
        """
        self.is_preprocessed = False
        self.included_files_set.clear()
        return self._process_source(source, "<root>", [], [])

    def _process_source(
        self,
        source: str,
        current_file: str,
        include_stack: list[tuple[str, int, str]],
        delimiter_stack: list[str],
    ) -> str:
        """
        Recursively processes source text, handling includes.
        """
        current_dir = (
            os.path.dirname(current_file) if current_file != "<root>" else self.base_dir
        )
        processed_lines = []
        for line_num, line in enumerate(source.splitlines(True), start=1):
            match = None
            if ":" in line:
                match = self.include_regex.match(line.rstrip())

            if match:
                self.is_preprocessed = True
                include_path = match.group(1).strip()
                attr_str = match.group(2).strip()

                target_file_path = os.path.abspath(
                    os.path.join(current_dir, include_path)
                )

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
                            "attempts to access files outside the base directory."
                        )

                if not os.path.isfile(target_file_path):
                    raise PreprocessorError(
                        f"Include file not found: {target_file_path}"
                    )

                # Check if target_file_path is already in the include stack
                start_idx = next(
                    (
                        i
                        for i, item in enumerate(include_stack)
                        if item[0] == target_file_path
                    ),
                    None,
                )

                if start_idx is not None:
                    cycle_items = include_stack[start_idx:]
                    # All absolute file paths involved in the cycle (including current_file and target)
                    cycle_files = {item[0] for item in cycle_items} | {
                        target_file_path,
                        current_file,
                    }
                    real_cycle_files = {f for f in cycle_files if os.path.isfile(f)}

                    # Convert paths to base_dir-relative strings for the main error header
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
                                    abs_inc = os.path.abspath(
                                        os.path.join(file_dir, inc_path)
                                    )
                                    if abs_inc in real_cycle_files:
                                        caret_line = "^" + "~" * (len(line_text) - 1)
                                        diagnostic_lines.append(
                                            f'File "{rel_file}", line {idx}:\n'
                                            f"    {line_text}\n"
                                            f"    {caret_line}"
                                        )

                    detailed_diagnostics = "\n\n".join(diagnostic_lines)
                    error_msg = (
                        f"Circular include detected: {trace_str}\n\n"
                        f"{detailed_diagnostics}"
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
                            if (
                                remaining
                                and remaining[0].isspace()
                                and remaining.strip()
                            ):
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
                )

                if len(delimiter_stack) != initial_depth:
                    warnings.warn(
                        f"Include file '{include_path}' has unbalanced block delimiters. "
                        "Block delimiters should not be opened or closed across file boundaries.",
                        PreprocessorWarning,
                        stacklevel=2,
                    )

                processed_lines.append(processed_content)
            else:
                self._update_delimiter_stack(line, delimiter_stack)
                processed_lines.append(line)

        return "".join(processed_lines)
