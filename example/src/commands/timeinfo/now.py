"""Команда ``.now`` — текущая дата и время."""

from __future__ import annotations

from datetime import datetime

from ...core.command import Command


class NowCommand(Command):
    """Возвращает текущие дату и время в ISO 8601."""

    name = "now"
    summary = "текущие дата и время"

    def __init__(self, clock=datetime.now) -> None:
        self._clock = clock

    def execute(self, args: str) -> str:
        return self._clock().isoformat(timespec="seconds")
