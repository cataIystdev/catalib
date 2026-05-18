"""Модель дерева исходников плагина для сборки.

Плагин на устройстве импортируется exteraGram как один модуль с именем
``<plugin_id>``. catalib трактует исходное дерево ``src/`` как пакет, корнем
которого является этот модуль: файл ``src/__init__.py`` становится телом
верхнего модуля, остальные файлы — его подмодулями ``<plugin_id>.<имя>``.
Имена внутри дерева хранятся относительными (без префикса ``<plugin_id>``),
префикс добавляется встроенным загрузчиком в рантайме.
"""

from __future__ import annotations

from dataclasses import dataclass


class DiscoveryError(ValueError):
    """Ошибка обхода дерева исходников плагина."""


@dataclass(frozen=True, slots=True)
class SourceModule:
    """Один модуль или пакет в дереве исходников плагина.

    :param relname: относительное точечное имя без префикса ``<plugin_id>``
        (например ``utils`` или ``pkg.sub``). Для корневого ``__init__.py``
        имя пустое.
    :param relpath: путь относительно корня ``src`` в posix-форме
        (например ``pkg/sub.py``); используется как origin для трейсбеков.
    :param source: полный исходный текст файла.
    :param is_package: истинно для ``__init__.py`` (пакет).
    """

    relname: str
    relpath: str
    source: str
    is_package: bool

    @property
    def is_root(self) -> bool:
        """Истинно для корневого ``src/__init__.py`` (тело верхнего модуля)."""
        return self.relname == ""


@dataclass(frozen=True, slots=True)
class SourceTree:
    """Полное дерево исходников плагина.

    :param modules: все модули и пакеты дерева, включая корневой (если есть).
    :param entry: относительное имя модуля точки входа (подкласс плагина).
    """

    modules: tuple[SourceModule, ...]
    entry: str

    @property
    def root(self) -> SourceModule | None:
        """Корневой модуль (``src/__init__.py``), либо ``None``, если его нет."""
        for module in self.modules:
            if module.is_root:
                return module
        return None

    @property
    def submodules(self) -> tuple[SourceModule, ...]:
        """Все модули, кроме корневого, в детерминированном порядке."""
        return tuple(m for m in self.modules if not m.is_root)


@dataclass(frozen=True, slots=True)
class BundleResult:
    """Результат сборки плагина.

    :param text: содержимое выходного файла ``<plugin_id>.py``.
    :param filename: имя выходного файла.
    :param requirements: итоговый список зависимостей.
    :param module_count: число встроенных модулей плагина (включая корневой).
    :param vendored_kept: вшитые модули ``catalib`` (после отбора).
    :param vendored_pruned: отсечённые модули ``catalib``.
    :param vendor_full: вендоринг выполнен полностью (без отбора).
    :param vendor_warnings: причины полного вендоринга/замечания.
    """

    text: str
    filename: str
    requirements: tuple[str, ...]
    module_count: int
    vendored_kept: tuple[str, ...] = ()
    vendored_pruned: tuple[str, ...] = ()
    vendor_full: bool = False
    vendor_warnings: tuple[str, ...] = ()
