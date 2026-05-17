"""Разбор входящего сообщения в имя команды и аргументы."""

from __future__ import annotations


def parse(message: str, prefix: str) -> tuple[str, str] | None:
    """Разобрать сообщение в пару ``(имя_команды, аргументы)``.

    :param message: текст исходящего сообщения.
    :param prefix: текущий префикс команд (непустая строка).
    :returns: ``(name, args)`` если сообщение начинается с префикса и
        содержит имя команды; иначе ``None`` (сообщение не для плагина).
    """
    if not prefix or not message.startswith(prefix):
        return None
    body = message[len(prefix) :].strip()
    if not body:
        return None
    parts = body.split(maxsplit=1)
    name = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""
    if not name:
        return None
    return name, args
