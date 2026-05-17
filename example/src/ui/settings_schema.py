"""Построение списка элементов настроек плагина."""

from __future__ import annotations

from catalib.support import SettingItem, settings

from ..config import (
    DEFAULT_PREFIX,
    SETTING_COUNT_STATS,
    SETTING_PREFIX,
    SETTING_SHOW_ERRORS,
)


def build_settings() -> list[SettingItem]:
    """Вернуть схему настроек exteraToolbox."""
    return [
        settings.header("exteraToolbox"),
        settings.text_input(
            SETTING_PREFIX,
            "Префикс команд",
            default=DEFAULT_PREFIX,
            subtext="Символ(ы) в начале сообщения, например . или !",
        ),
        settings.switch(
            SETTING_SHOW_ERRORS,
            "Показывать ошибки",
            default=True,
            subtext="Заменять сообщение текстом ошибки при неверном вводе",
        ),
        settings.switch(
            SETTING_COUNT_STATS,
            "Вести статистику",
            default=True,
            subtext="Считать число вызовов команд (.stats)",
        ),
        settings.text(
            "Подсказка",
            subtext="Отправьте <префикс>help со списком всех команд",
        ),
    ]
