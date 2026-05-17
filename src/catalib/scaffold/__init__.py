"""Генерация шаблона модульного плагина (``catalib init``).

Создаёт минимальный, но рабочий проект: манифест, пакет ``src`` с точкой
входа и подмодулем (демонстрация относительного импорта), офлайн-тест.
Проект собирается ``catalib build`` без правок.
"""

from __future__ import annotations

from pathlib import Path

from catalib.manifest.model import PLUGIN_ID_PATTERN
from catalib.scaffold import templates


class ScaffoldError(ValueError):
    """Ошибка генерации шаблона проекта."""


def _class_name(plugin_id: str) -> str:
    """Преобразовать ``plugin_id`` в имя класса (``my_plugin`` -> ``MyPlugin``)."""
    return "".join(part.capitalize() for part in plugin_id.split("_")) + "Plugin"


def create_project(target_dir: Path, plugin_id: str, name: str, author: str = "") -> list[Path]:
    """Создать шаблон плагина в ``target_dir``.

    :param target_dir: каталог проекта (создаётся; должен быть пустым или
        отсутствовать).
    :param plugin_id: идентификатор плагина (валидируется как в манифесте).
    :param name: отображаемое имя плагина.
    :param author: автор (по умолчанию пусто).
    :returns: список созданных файлов.
    :raises ScaffoldError: при невалидном ``plugin_id`` или непустом каталоге.
    """
    if not PLUGIN_ID_PATTERN.match(plugin_id or ""):
        raise ScaffoldError(
            f"plugin_id {plugin_id!r} невалиден: 2–32 символа, [a-z] в начале, далее [a-z0-9_]"
        )
    if not name.strip():
        raise ScaffoldError("имя плагина не должно быть пустым")
    if target_dir.exists() and any(target_dir.iterdir()):
        raise ScaffoldError(f"каталог {target_dir} не пуст")

    subst = {
        "plugin_id": plugin_id,
        "name": name,
        "author": author,
        "class_name": _class_name(plugin_id),
    }
    files = {
        "catalib.toml": templates.MANIFEST.format(**subst),
        "pyproject.toml": templates.PYPROJECT,
        ".gitignore": templates.GITIGNORE,
        "README.md": templates.README.format(**subst),
        "conftest.py": "",
        "src/__init__.py": templates.ROOT_INIT.format(**subst),
        "src/greeting.py": templates.GREETING,
        "src/plugin.py": templates.PLUGIN.format(**subst),
        "tests/test_plugin.py": templates.TEST,
    }
    created: list[Path] = []
    for rel, content in files.items():
        path = target_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(path)
    return created
