"""Тесты обёрток ``file_utils``: офлайн — настоящая работа с ФС."""

from __future__ import annotations

import os

from catalib.support import files


def test_dir_getters_return_paths() -> None:
    for getter in (
        files.get_plugins_dir,
        files.get_cache_dir,
        files.get_files_dir,
        files.get_images_dir,
        files.get_videos_dir,
        files.get_audios_dir,
        files.get_documents_dir,
    ):
        path = getter()
        assert isinstance(path, str) and path


def test_get_plugins_dir_keeps_tempdir_contract() -> None:
    import tempfile

    assert files.get_plugins_dir() == tempfile.gettempdir()


def test_write_read_delete_roundtrip(tmp_path) -> None:
    target = os.path.join(tmp_path, "data.txt")
    files.write_file(target, "привет")
    assert files.read_file(target) == "привет"
    assert files.delete_file(target) is True
    # Повторное удаление и чтение несуществующего — безопасны.
    assert files.delete_file(target) is False
    assert files.read_file(target) is None


def test_write_file_does_not_create_parent_dirs(tmp_path) -> None:
    nested = os.path.join(tmp_path, "missing", "data.txt")
    try:
        files.write_file(nested, "x")
        created = True
    except OSError:
        created = False
    assert created is False  # как в SDK: родителей не создаёт


def test_ensure_dir_exists_creates_parents(tmp_path) -> None:
    deep = os.path.join(tmp_path, "a", "b", "c")
    files.ensure_dir_exists(deep)
    assert os.path.isdir(deep)
    files.ensure_dir_exists(deep)  # идемпотентно


def test_list_dir_filters(tmp_path) -> None:
    files.ensure_dir_exists(os.path.join(tmp_path, "sub"))
    files.write_file(os.path.join(tmp_path, "a.json"), "{}")
    files.write_file(os.path.join(tmp_path, "b.txt"), "t")
    files.write_file(os.path.join(tmp_path, "sub", "c.json"), "{}")

    names = sorted(
        os.path.basename(p) for p in files.list_dir(str(tmp_path))
    )
    assert names == ["a.json", "b.txt"]

    only_json = sorted(
        os.path.basename(p)
        for p in files.list_dir(str(tmp_path), extensions=[".json"])
    )
    assert only_json == ["a.json"]

    dirs = files.list_dir(
        str(tmp_path), include_files=False, include_dirs=True
    )
    assert [os.path.basename(p) for p in dirs] == ["sub"]

    recursive = sorted(
        os.path.basename(p)
        for p in files.list_dir(
            str(tmp_path), recursive=True, extensions=[".json"]
        )
    )
    assert recursive == ["a.json", "c.json"]


def test_list_dir_missing_path_returns_empty() -> None:
    assert files.list_dir("/no/such/path/here") == []


def test_all_exports_present() -> None:
    for name in files.__all__:
        assert hasattr(files, name)
