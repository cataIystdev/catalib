"""Фильтрация logcat по идентификатору плагина (чистая логика).

Плагины обычно логируют как ``[plugin_id] ...`` через ``self.log`` /
``android_utils.log`` — в logcat это просто строки. Здесь только
строковая фильтрация (тестируется офлайн); чтение logcat — в
:func:`catalib.deploy.adb.logcat`. Поведение совпадает с инструментом
MCP ``adb_get_logs``: регистронезависимая подстрока, а если совпадений
нет — подсказка и «хвост» последних строк.
"""

from __future__ import annotations

#: Сколько последних строк показать, если по фильтру ничего не нашлось.
DEFAULT_TAIL = 20


def filter_log(text: str, needle: str, *, tail: int = DEFAULT_TAIL) -> str:
    """Оставить строки ``text``, содержащие ``needle`` (без учёта регистра).

    :param text: сырой вывод logcat.
    :param needle: подстрока для фильтра (обычно ``plugin_id``); пустая —
        вернуть ``text`` как есть (режим «без фильтра»).
    :param tail: сколько последних строк показать, если совпадений нет.
    """
    if not needle:
        return text
    lines = text.splitlines()
    low = needle.lower()
    matched = [line for line in lines if low in line.lower()]
    if matched:
        return "\n".join(matched)
    return (
        f'Строк с "{needle}" не найдено в последних {len(lines)} строках.\n\n'
        f"Последние {tail}:\n" + "\n".join(lines[-tail:])
    )
