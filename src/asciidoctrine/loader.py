"""
File and resource loading abstractions for AsciiDoctrine.

This module decouples document parsing and preprocessing from physical disk I/O,
enabling hermetic in-memory execution, browser-based Pyodide sandboxing,
and customizable resource providers.
"""

from __future__ import annotations

import fnmatch
import os
import posixpath
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union


class FileProvider(ABC):
    """
    Abstract resource loader interface for resolving and reading document sources.

    `FileProvider` provides a standardized interface for file reading, path resolution,
    and document discovery across different storage media (local filesystem, in-memory
    virtual dictionaries, network streams, etc.).
    """

    @abstractmethod
    def read_text(self, path: Union[str, Path]) -> str:
        """
        Reads and returns the complete text content of a target document.

        `path`::
          Canonical or relative path identifier for the file to read.

        [NOTE]
        Must raise `FileNotFoundError` or `PermissionError` if the file cannot be accessed.
        """
        pass

    @abstractmethod
    def exists(self, path: Union[str, Path]) -> bool:
        """
        Checks whether the specified path exists in the provider.

        `path`::
          The file or directory path identifier to check.
        """
        pass

    @abstractmethod
    def is_file(self, path: Union[str, Path]) -> bool:
        """
        Checks whether the specified path points to a readable file.

        `path`::
          The path identifier to check.
        """
        pass

    @abstractmethod
    def resolve_path(
        self, path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None
    ) -> str:
        """
        Resolves a path relative to a base directory or workspace root.

        `path`::
          The relative or absolute path to resolve.
        `base_dir`::
          Optional reference directory for relative resolution. Defaults to the provider's root.
        """
        pass

    @abstractmethod
    def find_files(
        self, pattern: str = "*.adoc", base_dir: Optional[Union[str, Path]] = None
    ) -> List[str]:
        """
        Discovers all files matching a glob pattern within the target directory.

        `pattern`::
          Glob pattern to match against (e.g. `"*.adoc"`).
        `base_dir`::
          Optional sub-directory to start discovery from.
        """
        pass


class FsLoader(FileProvider):
    """
    Concrete filesystem provider backed by the host operating system.

    `FsLoader` reads files from the local disk and enforces path traversal security
    constraints when `safe_mode` is enabled.

    *Example:*
    [source,python]
    ----
    from asciidoctrine.loader import FsLoader

    loader = FsLoader(base_dir="/docs", safe_mode=True)
    content = loader.read_text("chapter1/intro.adoc")
    ----
    """

    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        safe_mode: Union[bool, int] = True,
    ) -> None:
        """
        Initializes the filesystem loader.

        `base_dir`::
          Root directory against which relative paths are resolved. Defaults to current working directory.
        `safe_mode`::
          If True (or integer >= 1), restricts file access to paths strictly contained inside `base_dir`.
        """
        self.base_dir = os.path.abspath(str(base_dir)) if base_dir else os.getcwd()
        self.safe_mode = bool(safe_mode)

    def _validate_safe_path(self, target_abs_path: str) -> None:
        """Enforces that target_abs_path resides within base_dir under safe_mode."""
        if not self.safe_mode:
            return
        try:
            common = os.path.commonpath([target_abs_path, self.base_dir])
            if common != self.base_dir:
                raise PermissionError(
                    f"Security error: path '{target_abs_path}' attempts to access files outside base directory '{self.base_dir}'."
                )
        except ValueError as exc:
            raise PermissionError(
                f"Security error: path '{target_abs_path}' is on a different drive or outside base directory '{self.base_dir}'."
            ) from exc

    def read_text(self, path: Union[str, Path]) -> str:
        resolved = self.resolve_path(path)
        with open(resolved, "r", encoding="utf-8") as f:
            return f.read()

    def exists(self, path: Union[str, Path]) -> bool:
        try:
            resolved = self.resolve_path(path)
            return os.path.exists(resolved)
        except PermissionError:
            return False

    def is_file(self, path: Union[str, Path]) -> bool:
        try:
            resolved = self.resolve_path(path)
            return os.path.isfile(resolved)
        except PermissionError:
            return False

    def resolve_path(
        self, path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None
    ) -> str:
        root = os.path.abspath(str(base_dir)) if base_dir else self.base_dir
        path_str = str(path)
        if os.path.isabs(path_str):
            resolved = os.path.abspath(path_str)
        else:
            resolved = os.path.abspath(os.path.join(root, path_str))
        self._validate_safe_path(resolved)
        return resolved

    def find_files(
        self, pattern: str = "*.adoc", base_dir: Optional[Union[str, Path]] = None
    ) -> List[str]:
        search_root = Path(self.resolve_path(base_dir or self.base_dir))
        if not search_root.is_dir():
            return []
        matches: List[str] = []
        for p in search_root.rglob(pattern):
            if p.is_file():
                matches.append(str(p.resolve()))
        return sorted(matches)


class MemoryLoader(FileProvider):
    """
    In-memory virtual filesystem loader backed by a dictionary.

    `MemoryLoader` stores file contents in a Python dictionary mapping POSIX-style relative
    paths to file content strings. It enables 100% hermetic unit testing, instant AST fixture
    assembly, and browser-native execution without touching the disk.

    *Example:*
    [source,python]
    ----
    from asciidoctrine.loader import MemoryLoader

    files = {
        "main.adoc": "= Title\\n\\ninclude::chapter1.adoc[]",
        "chapter1.adoc": "== Chapter 1\\n\\nContent text."
    }
    loader = MemoryLoader(files, base_dir="/workspace")
    content = loader.read_text("main.adoc")
    ----
    """

    def __init__(
        self,
        files: Optional[Dict[str, str]] = None,
        base_dir: str = "/workspace",
        safe_mode: Union[bool, int] = True,
    ) -> None:
        """
        Initializes the in-memory loader.

        `files`::
          Dictionary mapping relative path strings to source text strings.
        `base_dir`::
          Canonical root prefix for virtual file resolution (e.g. `"/workspace"`).
        `safe_mode`::
          If True, restricts virtual file resolution to within `base_dir`.
        """
        self.base_dir = self._normalize_posix_path(base_dir)
        self.safe_mode = bool(safe_mode)
        self._files: Dict[str, str] = {}
        if files:
            for k, v in files.items():
                norm_k = self.resolve_path(k)
                self._files[norm_k] = v

    @staticmethod
    def _normalize_posix_path(path: Union[str, Path]) -> str:
        p = str(path).replace("\\", "/")
        norm = posixpath.normpath(p)
        if not norm.startswith("/"):
            norm = "/" + norm
        return norm

    def put(self, path: Union[str, Path], content: str) -> None:
        """
        Adds or updates a virtual file in the in-memory filesystem.

        `path`::
          Relative or absolute path for the file.
        `content`::
          String content of the document.
        """
        resolved = self.resolve_path(path)
        self._files[resolved] = content

    def resolve_path(
        self, path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None
    ) -> str:
        p_str = str(path).replace("\\", "/")
        if p_str.startswith("/"):
            resolved = posixpath.normpath(p_str)
        else:
            root = self._normalize_posix_path(base_dir or self.base_dir)
            resolved = posixpath.normpath(posixpath.join(root, p_str))

        if self.safe_mode:
            prefix = (
                self.base_dir if self.base_dir.endswith("/") else self.base_dir + "/"
            )
            if not (resolved == self.base_dir or resolved.startswith(prefix)):
                raise PermissionError(
                    f"Security error: virtual path '{path}' attempts to access files outside base directory '{self.base_dir}'."
                )
        return resolved

    def read_text(self, path: Union[str, Path]) -> str:
        resolved = self.resolve_path(path)
        if resolved not in self._files:
            raise FileNotFoundError(
                f"Virtual file not found: '{path}' (resolved: '{resolved}')"
            )
        return self._files[resolved]

    def exists(self, path: Union[str, Path]) -> bool:
        try:
            resolved = self.resolve_path(path)
            if resolved in self._files:
                return True
            prefix = resolved + "/"
            return any(k.startswith(prefix) for k in self._files)
        except PermissionError:
            return False

    def is_file(self, path: Union[str, Path]) -> bool:
        try:
            resolved = self.resolve_path(path)
            return resolved in self._files
        except PermissionError:
            return False

    def find_files(
        self, pattern: str = "*.adoc", base_dir: Optional[Union[str, Path]] = None
    ) -> List[str]:
        root = self.resolve_path(base_dir or self.base_dir)
        prefix = root if root.endswith("/") else root + "/"
        matches: List[str] = []
        for file_path in self._files:
            if file_path == root or file_path.startswith(prefix):
                filename = posixpath.basename(file_path)
                if fnmatch.fnmatch(filename, pattern):
                    matches.append(file_path)
        return sorted(matches)
