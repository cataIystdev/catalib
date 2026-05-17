"""Помощники усечения текста."""

from __future__ import annotations


def shorten(text: str, width: int) -> str:
    """Усечь текст до ``width`` символов с многоточием.

    :param text: исходный текст (переводы строк заменяются пробелом).
    :param width: максимальная длина результата (минимум 4).
    """
    flattened = " ".join(text.split())
    if width < 4:
        width = 4
    if len(flattened) <= width:
        return flattened
    return flattened[: width - 3] + "..."
