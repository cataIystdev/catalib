"""Форматирование результата перед отправкой в сообщение."""

from __future__ import annotations

from ..config import MAX_RESULT_LENGTH


def clamp_result(text: str) -> str:
    """Ограничить длину результата, чтобы не превышать лимит сообщения."""
    if len(text) <= MAX_RESULT_LENGTH:
        return text
    return text[: MAX_RESULT_LENGTH - 3] + "..."


def number_to_text(value: float) -> str:
    """Привести число к компактному виду (целые без дробной части)."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
