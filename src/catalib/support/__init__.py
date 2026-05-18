"""Публичный API мини-фреймворка, импортируемый плагином.

Этот подпакет целиком встраивается в собранный плагин и исполняется под
Chaquopy. Зависит только от стандартной библиотеки и SDK exteraGram.

Типовое использование в плагине::

    from catalib.support import CatalibPlugin, hook, settings, xposed

    class MyPlugin(CatalibPlugin):
        @hook.send_message
        def on_send_message_hook(self, account, params):
            ...

        @hook.app_event(AppEvent.START)
        def on_start(self, event_type):
            ...

        @xposed("org.telegram.ui.ChatActivity", "onBackPressed", phase="before")
        def on_back(self, param):
            ...

        def settings(self):
            return [
                settings.header("Мой плагин"),
                settings.text("Запустить", on_click=self._run),
            ]

Слой не скрывает SDK: расширенные имена (``AppEvent``, ``HookFilter``,
``hook_filters``, ``MethodHook``, ``MethodReplacement``, ``BaseHook``,
``find_class``) ре-экспортируются с офлайн-заглушками. Все расширения 0.2.0
строго аддитивны: прежние имена и сигнатуры сохранены (см. ADR-0006).
"""

from __future__ import annotations

from catalib.support import settings
from catalib.support.hooks import AppEventSpec, HookSpec, hook
from catalib.support.plugin import CatalibPlugin, MenuSpec, menu_item
from catalib.support.sdk import (
    SDK_AVAILABLE,
    AppEvent,
    BaseHook,
    HookFilter,
    HookResult,
    HookStrategy,
    MethodHook,
    MethodReplacement,
    find_class,
    get_plugins_dir,
    hook_filters,
    log,
    run_on_ui_thread,
)
from catalib.support.settings import SettingItem
from catalib.support.xposed import XposedSpec, xposed

__all__ = [
    "SDK_AVAILABLE",
    "AppEvent",
    "AppEventSpec",
    "BaseHook",
    "CatalibPlugin",
    "HookFilter",
    "HookResult",
    "HookSpec",
    "HookStrategy",
    "MenuSpec",
    "MethodHook",
    "MethodReplacement",
    "SettingItem",
    "XposedSpec",
    "find_class",
    "get_plugins_dir",
    "hook",
    "hook_filters",
    "log",
    "menu_item",
    "run_on_ui_thread",
    "settings",
    "xposed",
]
