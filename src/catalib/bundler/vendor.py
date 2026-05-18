"""Вендоринг встраиваемого рантайма ``catalib.support`` в плагин.

На устройстве пакет ``catalib`` не установлен, поэтому модули
``catalib.support`` (и минимальный ``catalib``) встраиваются в собранный
плагин под их настоящими именами. Встроенный загрузчик отдаёт их так же,
как модули плагина.
"""

from __future__ import annotations

from importlib import resources

from catalib.bundler.model import SourceModule

#: Встраиваемые модули: имя -> (ресурсный путь, признак пакета).
_VENDOR_MODULES: tuple[tuple[str, str, bool], ...] = (
    ("catalib", "catalib/__init__.py", True),
    ("catalib.support", "catalib/support/__init__.py", True),
    ("catalib.support.sdk", "catalib/support/sdk.py", False),
    ("catalib.support.hooks", "catalib/support/hooks.py", False),
    ("catalib.support.settings", "catalib/support/settings.py", False),
    ("catalib.support.xposed", "catalib/support/xposed.py", False),
    ("catalib.support.android", "catalib/support/android.py", False),
    ("catalib.support.client", "catalib/support/client.py", False),
    ("catalib.support.files", "catalib/support/files.py", False),
    ("catalib.support.reflection", "catalib/support/reflection.py", False),
    ("catalib.support.formatting", "catalib/support/formatting.py", False),
    ("catalib.support.dialogs", "catalib/support/dialogs.py", False),
    ("catalib.support.bulletins", "catalib/support/bulletins.py", False),
    ("catalib.support.proxy", "catalib/support/proxy.py", False),
    ("catalib.support.classes", "catalib/support/classes.py", False),
    ("catalib.support.plugin", "catalib/support/plugin.py", False),
)


def _read(resource_path: str) -> str:
    """Прочитать исходник модуля из установленного пакета catalib."""
    package, _, filename = resource_path.rpartition("/")
    package_name = package.replace("/", ".")
    return resources.files(package_name).joinpath(filename).read_text(encoding="utf-8")


def vendored_modules() -> tuple[SourceModule, ...]:
    """Вернуть ВСЕ встраиваемые модули ``catalib`` как :class:`SourceModule`.

    ``relname`` равен полному имени модуля (без префикса плагина);
    ``relpath`` используется как читаемый origin для трейсбеков. Это полный
    набор; отбор фактически используемого делает
    :mod:`catalib.bundler.treeshake`.
    """
    return tuple(
        SourceModule(
            relname=fullname,
            relpath=resource_path,
            source=_read(resource_path),
            is_package=is_package,
        )
        for fullname, resource_path, is_package in _VENDOR_MODULES
    )


def all_vendor_modules() -> dict[str, SourceModule]:
    """Карта «полное имя модуля -> :class:`SourceModule`» по всему вендору."""
    return {module.relname: module for module in vendored_modules()}


#: Имя пакета-фасада мини-фреймворка.
SUPPORT_PACKAGE = "catalib.support"
#: Имя корневого вендоренного пакета.
ROOT_PACKAGE = "catalib"
