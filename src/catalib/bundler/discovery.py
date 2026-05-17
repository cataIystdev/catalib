"""Обход дерева исходников плагина и построение :class:`SourceTree`.

Каталог ``src`` трактуется как пакет с корнем-модулем ``<plugin_id>``.
Каждый каталог, содержащий модули, обязан иметь ``__init__.py`` — это
гарантирует предсказуемые относительные импорты и совпадение поведения с
встроенным загрузчиком.
"""

from __future__ import annotations

from pathlib import Path

from catalib.bundler.model import DiscoveryError, SourceModule, SourceTree

#: Имена каталогов, которые не обходятся.
_SKIP_DIRS = {"__pycache__"}


def _relname_for(rel: Path) -> tuple[str, bool]:
    """Вернуть относительное точечное имя и признак пакета для пути.

    :param rel: путь файла относительно корня ``src`` (posix-семантика).
    :returns: пара ``(relname, is_package)``; для ``src/__init__.py`` —
        ``("", True)``.
    """
    parts = list(rel.parts)
    if rel.name == "__init__.py":
        package_parts = parts[:-1]
        return ".".join(package_parts), True
    module_parts = [*parts[:-1], rel.stem]
    return ".".join(module_parts), False


def discover_sources(src_dir: Path, entry: str) -> SourceTree:
    """Построить дерево исходников плагина из каталога ``src``.

    :param src_dir: каталог с исходным деревом плагина.
    :param entry: относительное точечное имя модуля точки входа.
    :raises DiscoveryError: если каталог отсутствует, есть выход за пределы
        ``src`` (path traversal), каталог с модулями без ``__init__.py`` или
        модуль точки входа не найден.
    """
    if not src_dir.is_dir():
        raise DiscoveryError(f"каталог исходников не найден: {src_dir}")

    src_root = src_dir.resolve()
    modules: list[SourceModule] = []
    dirs_with_modules: set[Path] = set()
    package_dirs: set[Path] = set()

    for path in sorted(src_root.rglob("*.py")):
        resolved = path.resolve()
        if not resolved.is_relative_to(src_root):
            raise DiscoveryError(f"файл вне каталога src (path traversal): {path}")
        rel = resolved.relative_to(src_root)
        if any(part in _SKIP_DIRS or part.startswith(".") for part in rel.parts):
            continue

        relname, is_package = _relname_for(rel)
        try:
            source = resolved.read_text(encoding="utf-8")
        except OSError as exc:
            raise DiscoveryError(f"не удалось прочитать {rel}: {exc}") from exc

        modules.append(
            SourceModule(
                relname=relname,
                relpath=rel.as_posix(),
                source=source,
                is_package=is_package,
            )
        )
        if is_package:
            package_dirs.add(resolved.parent)
        if rel.parent != Path("."):
            dirs_with_modules.add((src_root / rel.parent).resolve())

    if not modules:
        raise DiscoveryError(f"в {src_dir} нет ни одного .py модуля")

    missing_init = sorted(
        str(d.relative_to(src_root)) for d in dirs_with_modules if d not in package_dirs
    )
    if missing_init:
        raise DiscoveryError("каталоги с модулями без __init__.py: " + ", ".join(missing_init))

    modules.sort(key=lambda m: (not m.is_root, m.relname))
    tree = SourceTree(modules=tuple(modules), entry=entry)

    known = {m.relname for m in modules}
    if entry not in known:
        available = ", ".join(sorted(n for n in known if n)) or "(только корневой)"
        raise DiscoveryError(f"модуль точки входа {entry!r} не найден; доступны: {available}")
    return tree
