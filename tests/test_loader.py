from pathlib import Path

import pytest

from asciidoctrine.loader import FsLoader, MemoryLoader

pytestmark = pytest.mark.unit


def test_memory_loader_basic_crud():
    files = {
        "main.adoc": "= Main Document\n\ninclude::chapter1.adoc[]",
        "chapter1.adoc": "== Chapter 1\n\nContent here.",
        "subdir/nested.adoc": "== Nested\n\nDeep content.",
    }
    loader = MemoryLoader(files, base_dir="/my/workspace", safe_mode=True)

    assert loader.exists("main.adoc")
    assert loader.is_file("main.adoc")
    assert (
        loader.read_text("main.adoc") == "= Main Document\n\ninclude::chapter1.adoc[]"
    )

    assert loader.exists("subdir/nested.adoc")
    assert loader.is_file("subdir/nested.adoc")
    assert loader.read_text("subdir/nested.adoc") == "== Nested\n\nDeep content."

    # Virtual directory existence check
    assert loader.exists("subdir")

    # Non-existent file
    assert not loader.exists("nonexistent.adoc")
    assert not loader.is_file("nonexistent.adoc")
    with pytest.raises(FileNotFoundError):
        loader.read_text("nonexistent.adoc")


def test_memory_loader_put_and_find_files():
    loader = MemoryLoader(base_dir="/workspace")
    loader.put("doc1.adoc", "Text 1")
    loader.put("sub/doc2.adoc", "Text 2")
    loader.put("sub/image.png", "binary data")

    assert loader.exists("doc1.adoc")
    assert loader.read_text("doc1.adoc") == "Text 1"

    adoc_files = loader.find_files("*.adoc")
    assert len(adoc_files) == 2
    assert "/workspace/doc1.adoc" in adoc_files
    assert "/workspace/sub/doc2.adoc" in adoc_files
    assert "/workspace/sub/image.png" not in adoc_files

    sub_adoc_files = loader.find_files("*.adoc", base_dir="sub")
    assert len(sub_adoc_files) == 1
    assert "/workspace/sub/doc2.adoc" in sub_adoc_files


def test_memory_loader_safe_mode_confinement():
    loader = MemoryLoader(base_dir="/workspace", safe_mode=True)
    loader.put("allowed.adoc", "Allowed")

    # Traversal out of base_dir should raise PermissionError
    with pytest.raises(PermissionError):
        loader.read_text("../outside.adoc")

    with pytest.raises(PermissionError):
        loader.resolve_path("/etc/passwd")


def test_fs_loader_real_disk(tmp_path: Path):
    doc1 = tmp_path / "doc1.adoc"
    doc1.write_text("Hello Disk", encoding="utf-8")

    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    doc2 = sub_dir / "doc2.adoc"
    doc2.write_text("Nested Disk", encoding="utf-8")

    loader = FsLoader(base_dir=str(tmp_path), safe_mode=True)

    assert loader.exists("doc1.adoc")
    assert loader.is_file("doc1.adoc")
    assert loader.read_text("doc1.adoc") == "Hello Disk"

    assert loader.exists("sub/doc2.adoc")
    assert loader.read_text("sub/doc2.adoc") == "Nested Disk"

    files = loader.find_files("*.adoc")
    assert len(files) == 2
    assert str(doc1.resolve()) in files
    assert str(doc2.resolve()) in files

    # Security check: outside base_dir
    with pytest.raises(PermissionError):
        loader.read_text("../outside.adoc")
