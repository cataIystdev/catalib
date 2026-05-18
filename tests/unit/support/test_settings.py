"""Тесты декларативных настроек: полный паритет с ``ui.settings`` и
строгая обратная совместимость (см. ADR-0006).

Ключевой инвариант: прежние вызовы ``header``/``switch``/``text_input``/
``text`` формируют тот же ``params``, что и до 0.2.0 (вендоринг слоя в
сторонних плагинах не должен сломаться).
"""

from __future__ import annotations

import pytest

from catalib.support import settings

# --- Обратная совместимость: прежние сигнатуры → прежний params ---


def test_header_unchanged() -> None:
    assert settings.header("Заголовок") == settings.SettingItem(
        "header", {"text": "Заголовок"}
    )


def test_switch_legacy_call_unchanged() -> None:
    item = settings.switch("k", "Текст", default=True, subtext="пояснение")
    assert item.kind == "switch"
    assert item.params == {
        "key": "k",
        "text": "Текст",
        "default": True,
        "subtext": "пояснение",
    }


def test_switch_without_subtext_omits_it() -> None:
    item = settings.switch("k", "Текст")
    assert item.params == {"key": "k", "text": "Текст", "default": False}


def test_text_input_legacy_call_unchanged() -> None:
    item = settings.text_input("token", "Токен", subtext="секрет")
    assert item.kind == "input"
    assert item.params == {
        "key": "token",
        "text": "Токен",
        "default": "",
        "subtext": "секрет",
    }


def test_text_legacy_call_unchanged() -> None:
    item = settings.text("Инфо", subtext="строка")
    assert item.kind == "text"
    assert item.params == {"text": "Инфо", "subtext": "строка"}


# --- Новые компоненты ---


def test_divider_with_and_without_text() -> None:
    assert settings.divider().params == {}
    assert settings.divider("Раздел").params == {"text": "Раздел"}
    assert settings.divider().kind == "divider"


def test_selector_builds_params() -> None:
    item = settings.selector(
        "mode", "Режим", 1, ["A", "B", "C"], icon="exteraPlugins/1"
    )
    assert item.kind == "selector"
    assert item.params == {
        "key": "mode",
        "text": "Режим",
        "default": 1,
        "items": ["A", "B", "C"],
        "icon": "exteraPlugins/1",
    }


def test_selector_rejects_empty_or_nonstring_items() -> None:
    with pytest.raises(ValueError, match="непустым списком"):
        settings.selector("k", "T", 0, [])
    with pytest.raises(ValueError, match="только строки"):
        settings.selector("k", "T", 0, ["ok", 1])  # type: ignore[list-item]


def test_edit_text_optional_params() -> None:
    assert settings.edit_text("k", "подсказка").params == {
        "key": "k",
        "hint": "подсказка",
    }
    item = settings.edit_text(
        "k", "h", default="d", multiline=True, max_length=120, mask="\\d+"
    )
    assert item.kind == "edittext"
    assert item.params == {
        "key": "k",
        "hint": "h",
        "default": "d",
        "multiline": True,
        "max_length": 120,
        "mask": "\\d+",
    }


def test_custom_requires_a_source() -> None:
    with pytest.raises(ValueError, match="item, view или factory"):
        settings.custom()
    factory = lambda *a: None  # noqa: E731 - короткая фабрика для теста
    item = settings.custom(factory=factory, factory_args=(1, 2))
    assert item.kind == "custom"
    assert item.params == {"factory": factory, "factory_args": (1, 2)}


# --- Новые параметры существующих компонентов ---


def test_text_clickable_first_class_api() -> None:
    calls: list[str] = []

    def handler(_view: object) -> None:
        calls.append("clicked")

    item = settings.text("Запустить", on_click=handler, accent=True)
    assert item.kind == "text"
    assert item.params["on_click"] is handler
    assert item.params["accent"] is True
    item.params["on_click"](object())
    assert calls == ["clicked"]


def test_text_flags_omitted_when_false() -> None:
    item = settings.text("Просто текст")
    assert item.params == {"text": "Просто текст"}


def test_switch_new_keyword_params() -> None:
    cb = lambda *a: None  # noqa: E731 - заглушка обработчика
    item = settings.switch(
        "k", "T", icon="ic", on_change=cb, link_alias="alias"
    )
    assert item.params == {
        "key": "k",
        "text": "T",
        "default": False,
        "icon": "ic",
        "on_change": cb,
        "link_alias": "alias",
    }


def test_build_offline_returns_self() -> None:
    item = settings.text("X")
    assert item.build() is item


def test_all_kinds_have_sdk_class_mapping() -> None:
    expected = {
        "header",
        "divider",
        "switch",
        "selector",
        "input",
        "edittext",
        "text",
        "custom",
    }
    assert set(settings._SDK_CLASS_BY_KIND) == expected
