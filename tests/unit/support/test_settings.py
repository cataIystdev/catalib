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


# --- Паритет 0.3.0: on_long_click, link_alias, SimpleSettingFactory ---


def test_on_long_click_on_all_components() -> None:
    cb = lambda *a: None  # noqa: E731 - заглушка обработчика
    assert settings.switch("k", "t", on_long_click=cb).params["on_long_click"] is cb
    assert (
        settings.selector("k", "t", 0, ["a"], on_long_click=cb).params["on_long_click"]
        is cb
    )
    assert (
        settings.text_input("k", "t", on_long_click=cb).params["on_long_click"] is cb
    )
    assert settings.text("t", on_long_click=cb).params["on_long_click"] is cb
    assert (
        settings.custom(view=object(), on_long_click=cb).params["on_long_click"] is cb
    )


def test_selector_link_alias_and_omitted_by_default() -> None:
    assert "link_alias" not in settings.selector("k", "t", 0, ["a"]).params
    item = settings.selector("k", "t", 0, ["a"], link_alias="al")
    assert item.params["link_alias"] == "al"


def test_custom_sub_fragment_and_link_alias() -> None:
    frag = lambda: []  # noqa: E731 - фабрика подэкрана
    item = settings.custom(
        view=object(), create_sub_fragment=frag, link_alias="x"
    )
    assert item.params["create_sub_fragment"] is frag
    assert item.params["link_alias"] == "x"


def test_legacy_calls_still_omit_new_params() -> None:
    # Обратная совместимость: прежние вызовы не добавляют новых ключей.
    assert settings.switch("k", "t").params == {
        "key": "k",
        "text": "t",
        "default": False,
    }
    assert "on_long_click" not in settings.text("info").params
    assert "link_alias" not in settings.selector("k", "t", 0, ["a"]).params


def test_simple_setting_factory_offline() -> None:
    cv = lambda *a: "view"  # noqa: E731 - офлайн create_view
    bv = lambda *a: None  # noqa: E731 - офлайн bind_view
    factory = settings.simple_setting_factory(
        cv, bv, is_clickable=True, on_click=lambda *a: None
    )
    assert factory.kwargs["create_view"] is cv
    assert factory.kwargs["bind_view"] is bv
    assert factory.kwargs["is_clickable"] is True
    assert "on_click" in factory.kwargs
    # Фабрика вызываема: factory(link_alias=..., *args).
    same = factory(1, 2, link_alias="al")
    assert same is factory
    assert factory.link_alias == "al"
    assert factory.call_args == (1, 2)
    # Пригодна как factory= в custom().
    item = settings.custom(factory=factory)
    assert item.params["factory"] is factory
