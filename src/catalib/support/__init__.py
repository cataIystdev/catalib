"""Публичный API мини-фреймворка, импортируемый плагином.

Этот подпакет целиком встраивается в собранный плагин и исполняется под
Chaquopy. Зависит только от стандартной библиотеки и SDK exteraGram.

Типовое использование в плагине::

    from catalib.support import CatalibPlugin, hook, settings

    class MyPlugin(CatalibPlugin):
        @hook.send_message
        def on_send_message_hook(self, account, params):
            ...

        def settings(self):
            return [settings.header("Мой плагин")]
"""

from __future__ import annotations

from catalib.support import settings
from catalib.support.hooks import HookSpec, hook
from catalib.support.plugin import CatalibPlugin, MenuSpec, menu_item
from catalib.support.sdk import (
    SDK_AVAILABLE,
    HookResult,
    HookStrategy,
    get_plugins_dir,
    log,
    run_on_ui_thread,
)
from catalib.support.settings import SettingItem

__all__ = [
    "SDK_AVAILABLE",
    "CatalibPlugin",
    "HookResult",
    "HookSpec",
    "HookStrategy",
    "MenuSpec",
    "SettingItem",
    "get_plugins_dir",
    "hook",
    "log",
    "menu_item",
    "run_on_ui_thread",
    "settings",
]
