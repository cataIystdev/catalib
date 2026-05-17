"""Безопасные импорты SDK exteraGram с заглушками для офлайн-тестов.

Единственная точка адаптации к SDK: если плагин исполняется в exteraGram —
используются настоящие классы и функции; вне приложения (юнит-тесты на
обычном Python) подключаются минимальные заглушки с тем же интерфейсом.
Это устраняет россыпь ``try/except`` по плагину и даёт офлайн-тестируемость
доменной логики. Код только стандартной библиотеки и SDK.
"""

from __future__ import annotations

import tempfile
from typing import Any

#: Истинно, если плагин исполняется внутри exteraGram (SDK доступен).
SDK_AVAILABLE: bool

try:  # pragma: no cover - ветка выполняется только на устройстве
    from base_plugin import (
        BasePlugin,
        HookResult,
        HookStrategy,
        MenuItemData,
        MenuItemType,
    )

    SDK_AVAILABLE = True
except Exception:  # pragma: no cover - ветка для обычного Python
    SDK_AVAILABLE = False

    class HookStrategy:
        """Заглушка стратегий хука, повторяющая значения SDK."""

        DEFAULT = "DEFAULT"
        CANCEL = "CANCEL"
        MODIFY = "MODIFY"
        MODIFY_FINAL = "MODIFY_FINAL"

    class HookResult:
        """Заглушка результата хука."""

        def __init__(self, strategy: str | None = None, params: Any = None) -> None:
            self.strategy = strategy or HookStrategy.DEFAULT
            self.params = params

    class MenuItemType:
        """Заглушка типов пунктов меню (значения как в SDK exteraGram)."""

        DRAWER_MENU = "DRAWER_MENU"
        MESSAGE_CONTEXT_MENU = "MESSAGE_CONTEXT_MENU"
        CHAT_ACTION_MENU = "CHAT_ACTION_MENU"
        PROFILE_ACTION_MENU = "PROFILE_ACTION_MENU"

    class MenuItemData:
        """Заглушка описания пункта меню."""

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    class BasePlugin:
        """Заглушка базового класса плагина для офлайн-тестов.

        Повторяет минимальный публичный интерфейс SDK, фиксируя вызовы
        регистрации, чтобы их можно было проверить в тестах.
        """

        def __init__(self) -> None:
            self._settings: dict[str, Any] = {}
            self.registered_hooks: list[Any] = []
            self.registered_menu_items: list[Any] = []
            self.logged: list[str] = []

        def add_on_send_message_hook(self, priority: int = 0) -> None:
            self.registered_hooks.append(("send_message", priority))

        def add_hook(self, name: str, priority: int = 0) -> None:
            self.registered_hooks.append((name, priority))

        def add_menu_item(self, data: Any) -> None:
            self.registered_menu_items.append(data)

        def get_setting(self, key: str, default: Any = None) -> Any:
            return self._settings.get(key, default)

        def set_setting(self, key: str, value: Any) -> None:
            self._settings[key] = value

        def log(self, message: str) -> None:
            self.logged.append(message)


def log(message: str) -> None:
    """Записать строку в лог приложения (или в no-op вне exteraGram)."""
    try:  # pragma: no cover - на устройстве
        from android_utils import log as _log

        _log(message)
    except Exception:
        pass


def run_on_ui_thread(callback: Any) -> None:
    """Выполнить callback в UI-потоке (на устройстве) или сразу (офлайн)."""
    try:  # pragma: no cover - на устройстве
        from android_utils import run_on_ui_thread as _ui

        _ui(callback)
        return
    except Exception:
        callback()


def get_plugins_dir() -> str:
    """Каталог плагинов на устройстве; во офлайн-режиме — временный каталог."""
    try:  # pragma: no cover - на устройстве
        from file_utils import get_plugins_dir as _dir

        return _dir()
    except Exception:
        return tempfile.gettempdir()


__all__ = [
    "SDK_AVAILABLE",
    "BasePlugin",
    "HookResult",
    "HookStrategy",
    "MenuItemData",
    "MenuItemType",
    "get_plugins_dir",
    "log",
    "run_on_ui_thread",
]
