"""Типизированные декларативные настройки плагина.

Описание настроек не зависит от наличия SDK: на устройстве элементы
конвертируются в классы ``ui.settings`` exteraGram, в офлайн-тестах остаются
самодостаточными объектами с теми же полями.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

#: Поддерживаемые типы элементов настроек и соответствующие классы ui.settings.
_SDK_CLASS_BY_KIND = {
    "header": "Header",
    "switch": "Switch",
    "input": "Input",
    "text": "Text",
}


@dataclass(frozen=True, slots=True)
class SettingItem:
    """Один элемент настроек плагина.

    :param kind: тип элемента (``header`` | ``switch`` | ``input`` | ``text``).
    :param params: именованные параметры, передаваемые классу ``ui.settings``.
    """

    kind: str
    params: dict[str, Any] = field(default_factory=dict)

    def build(self) -> Any:
        """Построить объект ``ui.settings`` (на устройстве) либо вернуть себя.

        В офлайн-окружении SDK недоступен — возвращается сам элемент, что
        удобно для модульных тестов.
        """
        try:  # pragma: no cover - выполняется только на устройстве
            from ui import settings as sdk_settings

            sdk_class = getattr(sdk_settings, _SDK_CLASS_BY_KIND[self.kind])
            return sdk_class(**self.params)
        except Exception:
            return self


def header(text: str) -> SettingItem:
    """Заголовок секции настроек."""
    return SettingItem("header", {"text": text})


def switch(key: str, text: str, default: bool = False, subtext: str = "") -> SettingItem:
    """Переключатель булевой настройки."""
    params: dict[str, Any] = {"key": key, "text": text, "default": default}
    if subtext:
        params["subtext"] = subtext
    return SettingItem("switch", params)


def text_input(
    key: str, text: str, default: str = "", subtext: str = "", icon: str = ""
) -> SettingItem:
    """Текстовое поле ввода."""
    params: dict[str, Any] = {"key": key, "text": text, "default": default}
    if subtext:
        params["subtext"] = subtext
    if icon:
        params["icon"] = icon
    return SettingItem("input", params)


def text(text: str, subtext: str = "", icon: str = "") -> SettingItem:
    """Информационная строка."""
    params: dict[str, Any] = {"text": text}
    if subtext:
        params["subtext"] = subtext
    if icon:
        params["icon"] = icon
    return SettingItem("text", params)
