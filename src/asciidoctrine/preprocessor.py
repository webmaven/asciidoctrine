"""
Preprocessor for AsciiDoc source, handling directives like include::.
"""

import os
import re
from typing import Optional, Set


class PreprocessorError(Exception):
    """Custom exception for preprocessor errors."""

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

    def process(self, source: str) -> str:
        """
        Main entry point for processing the source text.
        Args:
            source (str): The AsciiDoc source text.
        Returns:
            str: The source text with `include::` directives replaced by file content.
        """
        return self._process_source(source, self.base_dir, set())

    def _process_source(
        self, source: str, current_dir: str, included_files: Set[str]
    ) -> str:
        """
        Recursively processes source text, handling includes.
        """
        processed_lines = []
        for line in source.splitlines(True):
            # 1. C-Level No-Colon Short-Circuit
            if ":" not in line:
                processed_lines.append(line)
                continue

            match = self.include_regex.match(line.rstrip())
            if match:
                include_path = match.group(1).strip()
                attr_str = match.group(2).strip()

                target_file_path = os.path.abspath(
                    os.path.join(current_dir, include_path)
                )

                # Security check: verify target is within base directory if
                # safe_mode is on
                if (
                    self.safe_mode
                    and os.path.commonprefix([target_file_path, self.base_dir])
                    != self.base_dir
                ):
                    raise PreprocessorError(
                        f"Security error: include path '{include_path}' "
                        "attempts to access files outside the base directory."
                    )

                if not os.path.isfile(target_file_path):
                    raise PreprocessorError(
                        f"Include file not found: {target_file_path}"
                    )

                if target_file_path in included_files:
                    raise PreprocessorError(
                        f"Circular include detected: '{target_file_path}' "
                        "is already being included."
                    )

                with open(target_file_path, "r", encoding="utf-8") as f:
                    content_to_include = f.read()

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

                included_files.add(target_file_path)

                new_current_dir = os.path.dirname(target_file_path)

                processed_content = self._process_source(
                    content_to_include, new_current_dir, included_files
                )

                included_files.remove(target_file_path)

                processed_lines.append(processed_content)
            else:
                processed_lines.append(line)

        return "".join(processed_lines)
