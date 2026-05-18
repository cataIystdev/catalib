"""Поставляемые catalib type-стабы (``.pyi``) публичного SDK exteraGram.

Сами SDK-модули (``base_plugin``, ``client_utils`` и т. д.) на машине
разработчика не импортируются, поэтому IDE без стабов не подсказывает их
API. ``catalib stubs`` копирует эти ``.pyi`` в каталог ``typings/``
проекта — Pyright/Pylance подхватывают его автоматически.
"""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

__all__ = ["install_stubs", "stub_files"]


def _stub_root() -> Path:
    """Каталог с .pyi внутри установленного пакета catalib."""
    return Path(str(resources.files(__name__)))


def stub_files() -> list[Path]:
    """Список всех поставляемых ``.pyi`` (рекурсивно)."""
    return sorted(_stub_root().rglob("*.pyi"))


def install_stubs(dest: Path, *, force: bool = False) -> list[Path]:
    """Скопировать стабы в каталог ``dest`` с сохранением структуры.

    :param dest: целевой каталог (обычно ``<project>/typings``).
    :param force: перезаписывать существующие файлы.
    :returns: список записанных путей.
    :raises FileExistsError: если файл существует и ``force`` ложно.
    """
    root = _stub_root()
    written: list[Path] = []
    for src in sorted(root.rglob("*.pyi")):
        rel = src.relative_to(root)
        target = dest / rel
        if target.exists() and not force:
            raise FileExistsError(f"уже существует: {target} (используйте --force)")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        written.append(target)
    return written
