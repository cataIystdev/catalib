"""Команда ``.rev`` — разворот строки."""

from __future__ import annotations

from ...core.command import Command
from ...core.errors import CommandError


class ReverseCommand(Command):
    """Переворачивает текст задом наперёд."""

    name = "rev"
    summary = "перевернуть текст"
    usage = "<текст>"

    def execute(self, args: str) -> str:
        text = args.strip()
        if not text:
            raise CommandError("нужен текст")
        return text[::-1]
