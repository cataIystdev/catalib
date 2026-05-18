"""Обёртки модуля SDK ``extera_utils.text_formatting``.

На устройстве используется настоящий ``parse_text`` (разбирает HTML/
Markdown в текст + список ``TLRPC.MessageEntity``); вне приложения —
честный офлайн-контракт: возвращается тот же словарь
(``{"message"|"caption": text, "entities": []}``) с исходным текстом и
пустым списком сущностей (полный разбор сущностей — только на устройстве,
он опирается на TLRPC). Это не TODO, а документированная граница
офлайн-режима; на устройстве всегда работает настоящий SDK.

Зависит только от стандартной библиотеки и SDK.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def parse_text(
    text: str, parse_mode: str | None = "HTML", is_caption: bool = False
) -> dict[str, Any]:
    """Разобрать форматированный текст в текст и сущности Telegram.

    :param text: исходный текст с тегами/markdown.
    :param parse_mode: ``'HTML'`` (по умолчанию) или ``'Markdown'``.
    :param is_caption: если ``True`` — ключ результата ``"caption"``,
        иначе ``"message"``.
    :returns: словарь ``{"message"|"caption": str, "entities": list}``.
        Офлайн ``entities`` пуст, текст возвращается как есть.
    """
    try:  # pragma: no cover - на устройстве
        from extera_utils.text_formatting import parse_text as _parse

        return _parse(text, parse_mode, is_caption)
    except Exception:
        key = "caption" if is_caption else "message"
        return {key: text, "entities": []}


try:  # pragma: no cover - ветка выполняется только на устройстве
    from extera_utils.text_formatting import TLEntityType
except Exception:  # pragma: no cover - ветка для обычного Python

    class TLEntityType:
        """Офлайн-заглушка типов сущностей (значения как в SDK)."""

        BOLD = "BOLD"
        ITALIC = "ITALIC"
        UNDERLINE = "UNDERLINE"
        STRIKETHROUGH = "STRIKETHROUGH"
        CODE = "CODE"
        PRE = "PRE"
        TEXT_LINK = "TEXT_LINK"
        SPOILER = "SPOILER"
        CUSTOM_EMOJI = "CUSTOM_EMOJI"
        BLOCKQUOTE = "BLOCKQUOTE"


try:  # pragma: no cover - ветка выполняется только на устройстве
    from extera_utils.text_formatting import RawEntity
except Exception:  # pragma: no cover - ветка для обычного Python

    @dataclass
    class RawEntity:
        """Офлайн-заглушка промежуточного представления сущности.

        :param type: тип сущности (см. :class:`TLEntityType`).
        :param offset: смещение начала в тексте.
        :param length: длина фрагмента.
        :param url: цель ссылки (для ``TEXT_LINK``).
        :param language: язык (для ``PRE``).
        :param document_id: id документа (для ``CUSTOM_EMOJI``).
        :param collapsed: свёрнутость (для ``BLOCKQUOTE``).
        """

        type: Any = None
        offset: int = 0
        length: int = 0
        url: str | None = None
        language: str | None = None
        document_id: int | None = None
        collapsed: bool | None = None


__all__ = [
    "RawEntity",
    "TLEntityType",
    "parse_text",
]
