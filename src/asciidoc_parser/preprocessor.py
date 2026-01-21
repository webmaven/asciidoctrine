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
        self.include_regex = re.compile(r"^include::([^\[]+)\[\]\s*$")

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
            match = self.include_regex.match(line.rstrip())
            if match:
                include_path = match.group(1).strip()

                target_file_path = os.path.abspath(
                    os.path.join(current_dir, include_path)
                )

                # Security check: verify target is within base directory if safe_mode is on
                if self.safe_mode and os.path.commonprefix([target_file_path, self.base_dir]) != self.base_dir:
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
