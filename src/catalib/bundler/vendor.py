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
    ("catalib.support.plugin", "catalib/support/plugin.py", False),
)


def _read(resource_path: str) -> str:
    """Прочитать исходник модуля из установленного пакета catalib."""
    package, _, filename = resource_path.rpartition("/")
    package_name = package.replace("/", ".")
    return resources.files(package_name).joinpath(filename).read_text(encoding="utf-8")


def vendored_modules() -> tuple[SourceModule, ...]:
    """Вернуть встраиваемые модули ``catalib.support`` как :class:`SourceModule`.

    ``relname`` здесь равен полному имени модуля (без префикса плагина);
    ``relpath`` используется как читаемый origin для трейсбеков.
    """
    modules = []
    for fullname, resource_path, is_package in _VENDOR_MODULES:
        modules.append(
            SourceModule(
                relname=fullname,
                relpath=resource_path,
                source=_read(resource_path),
                is_package=is_package,
            )
        )
    return tuple(modules)
