"""Карта соответствия встроенных модулей исходным файлам.

Встроенный загрузчик компилирует каждый модуль отдельно с собственным
«origin» и регистрирует исходник в ``linecache`` под этим origin. Если origin
делать производным от исходного пути, трейсбеки на устройстве будут указывать
на реальные файлы разработчика (например
``File "<my_plugin>/pkg/sub.py", line 7``).
"""

from __future__ import annotations

from catalib.bundler.model import SourceTree


def runtime_fullname(plugin_id: str, relname: str) -> str:
    """Полное имя модуля в рантайме.

    Корневой модуль (``relname == ""``) — это сам модуль ``<plugin_id>``;
    подмодули доступны как ``<plugin_id>.<relname>``.
    """
    return plugin_id if relname == "" else f"{plugin_id}.{relname}"


def module_origin(plugin_id: str, relpath: str) -> str:
    """Origin модуля для ``compile`` и ``linecache`` (стабильный, читаемый)."""
    return f"<{plugin_id}>/{relpath}"


def build_source_map(plugin_id: str, tree: SourceTree) -> dict[str, str]:
    """Построить отображение «полное имя модуля -> origin».

    :param plugin_id: идентификатор плагина (он же имя корневого модуля).
    :param tree: дерево исходников.
    :returns: словарь ``fullname -> origin`` в детерминированном порядке.
    """
    return {
        runtime_fullname(plugin_id, module.relname): module_origin(plugin_id, module.relpath)
        for module in tree.modules
    }
