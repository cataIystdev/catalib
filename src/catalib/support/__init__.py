"""Публичный API мини-фреймворка, импортируемый плагином.

Этот подпакет целиком встраивается в собранный плагин и исполняется под
Chaquopy. Зависит только от стандартной библиотеки и SDK exteraGram.

Слой даёт **полный паритет** с публичным SDK exteraGram (ADR-0007),
сгруппированный по модулям-областям и доступный как из
``catalib.support``, так и по подмодулям:

- ``settings`` — декларативные ``ui.settings`` (все компоненты/параметры);
- ``hook`` / ``menu_item`` / ``xposed`` — декларативные хуки, меню,
  Xposed; ``CatalibPlugin`` — авто-регистрация;
- ``android`` — ``android_utils`` (``R``/listeners/``copy_to_clipboard``);
- ``client`` — ``client_utils`` (очереди/запросы/отправка/контроллеры);
- ``files`` — ``file_utils``; ``reflection`` — ``hook_utils``;
- ``formatting`` — ``extera_utils.text_formatting``;
- ``dialogs`` — ``AlertDialogBuilder``; ``bulletins`` — ``BulletinHelper``;
- ``proxy`` — class proxy (``extera_utils.classes``);
- ``classes`` — FQN-константы общих Java-классов.

На устройстве всё делегирует настоящему SDK; офлайн — функциональные
заглушки с тем же контрактом для юнит-тестов. Расширения строго
аддитивны: прежние имена и сигнатуры сохранены (ADR-0006, ADR-0007).
"""

from __future__ import annotations

from catalib.support import (
    android,
    bulletins,
    classes,
    client,
    dialogs,
    files,
    formatting,
    proxy,
    reflection,
    settings,
)
from catalib.support.bulletins import BulletinHelper
from catalib.support.dialogs import AlertDialogBuilder
from catalib.support.formatting import RawEntity, TLEntityType, parse_text
from catalib.support.hooks import AppEventSpec, HookSpec, hook
from catalib.support.plugin import CatalibPlugin, MenuSpec, menu_item
from catalib.support.proxy import (
    Base,
    ClassHelper,
    J,
    JavaHelper,
    PyObj,
    java_subclass,
    jclassbuilder,
    jconstructor,
    jfield,
    jgetmethod,
    jmethod,
    jMVELmethod,
    jMVELoverride,
    joverload,
    joverride,
    jpreconstructor,
    jsetmethod,
)
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
    # Ядро и декларативные примитивы (прежние имена сохранены).
    "SDK_AVAILABLE",
    # Часто используемые имена, поднятые на верхний уровень.
    "AlertDialogBuilder",
    "AppEvent",
    "AppEventSpec",
    # Class proxy (раздел отмечен пользователем как приоритетный).
    "Base",
    "BaseHook",
    "BulletinHelper",
    "CatalibPlugin",
    "ClassHelper",
    "HookFilter",
    "HookResult",
    "HookSpec",
    "HookStrategy",
    "J",
    "JavaHelper",
    "MenuSpec",
    "MethodHook",
    "MethodReplacement",
    "PyObj",
    "RawEntity",
    "SettingItem",
    "TLEntityType",
    "XposedSpec",
    # Модули-области (паритет 0.3.0).
    "android",
    "bulletins",
    "classes",
    "client",
    "dialogs",
    "files",
    "find_class",
    "formatting",
    "get_plugins_dir",
    "hook",
    "hook_filters",
    "jMVELmethod",
    "jMVELoverride",
    "java_subclass",
    "jclassbuilder",
    "jconstructor",
    "jfield",
    "jgetmethod",
    "jmethod",
    "joverload",
    "joverride",
    "jpreconstructor",
    "jsetmethod",
    "log",
    "menu_item",
    "parse_text",
    "proxy",
    "reflection",
    "run_on_ui_thread",
    "settings",
    "xposed",
]
