"""Тест публичного API ``catalib.support``: новые имена добавлены, прежние
сохранены (обратная совместимость вендоринга в сторонних плагинах).
"""

from __future__ import annotations

import catalib.support as support

#: Имена, существовавшие до 0.2.0 — обязаны остаться (вендоринг не сломать).
_LEGACY = {
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
}

#: Имена, добавленные в 0.2.0.
_NEW = {
    "AppEvent",
    "AppEventSpec",
    "BaseHook",
    "HookFilter",
    "MethodHook",
    "MethodReplacement",
    "XposedSpec",
    "find_class",
    "hook_filters",
    "xposed",
}

#: Имена, добавленные в 0.3.0 (полный паритет с SDK).
_NEW_0_3 = {
    # Модули-области.
    "android",
    "bulletins",
    "classes",
    "client",
    "dialogs",
    "files",
    "formatting",
    "proxy",
    "reflection",
    # Поднятые на верхний уровень.
    "AlertDialogBuilder",
    "BulletinHelper",
    "RawEntity",
    "TLEntityType",
    "parse_text",
    # Class proxy.
    "Base",
    "ClassHelper",
    "J",
    "JavaHelper",
    "PyObj",
    "java_subclass",
    "jMVELmethod",
    "jMVELoverride",
    "jclassbuilder",
    "jconstructor",
    "jfield",
    "jgetmethod",
    "jmethod",
    "joverload",
    "joverride",
    "jpreconstructor",
    "jsetmethod",
}


def test_legacy_names_preserved() -> None:
    for name in _LEGACY:
        assert name in support.__all__, f"исчезло публичное имя {name}"
        assert hasattr(support, name), f"нет атрибута {name}"


def test_new_names_exported() -> None:
    for name in _NEW | _NEW_0_3:
        assert name in support.__all__, f"не экспортировано {name}"
        assert hasattr(support, name), f"нет атрибута {name}"


def test_proxy_and_helpers_usable_from_facade() -> None:
    # Class proxy доступен прямо из catalib.support (приоритет пользователя).
    assert callable(support.java_subclass)
    assert callable(support.jfield)
    obj = support.PyObj.create({"k": 1})
    assert obj.value == {"k": 1}
    # UI-хелперы и контроллеры — через подмодули.
    assert hasattr(support.client, "send_text")
    assert hasattr(support.files, "read_file")
    assert support.parse_text("x") == {"message": "x", "entities": []}


def test_all_matches_attributes() -> None:
    for name in support.__all__:
        assert hasattr(support, name), f"в __all__ есть {name}, но атрибута нет"


def test_hook_has_app_event() -> None:
    assert hasattr(support.hook, "app_event")
    assert hasattr(support.hook, "send_message")
    assert hasattr(support.hook, "request")
