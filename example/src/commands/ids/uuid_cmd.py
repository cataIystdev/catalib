"""Команда ``.uuid`` — генерация UUID4."""

from __future__ import annotations

import uuid

from ...core.command import Command


class UuidCommand(Command):
    """Возвращает случайный UUID версии 4."""

    name = "uuid"
    summary = "случайный UUID4"

    def execute(self, args: str) -> str:
        return str(uuid.uuid4())
