"""Команда ``.in`` — момент времени через заданный интервал."""

from __future__ import annotations

from datetime import datetime, timedelta

from ...core.command import Command
from ...core.errors import CommandError

_UNITS = {
    "s": "seconds",
    "sec": "seconds",
    "m": "minutes",
    "min": "minutes",
    "h": "hours",
    "ч": "hours",
    "d": "days",
    "д": "days",
}
_MAX_AMOUNT = 1_000_000


class RelativeCommand(Command):
    """``.in 90 m`` — вернуть время через 90 минут (ISO 8601)."""

    name = "in"
    summary = "момент через интервал (s|m|h|d)"
    usage = "<число> <s|m|h|d>"

    def __init__(self, clock=datetime.now) -> None:
        self._clock = clock

    def execute(self, args: str) -> str:
        parts = args.split()
        if len(parts) != 2:
            raise CommandError("формат: <число> <s|m|h|d>")
        try:
            amount = int(parts[0])
        except ValueError as exc:
            raise CommandError("первое значение — число") from exc
        if not (1 <= amount <= _MAX_AMOUNT):
            raise CommandError(f"число должно быть 1..{_MAX_AMOUNT}")
        unit = _UNITS.get(parts[1].lower())
        if unit is None:
            raise CommandError("единица: s, m, h или d")
        moment = self._clock() + timedelta(**{unit: amount})
        return moment.isoformat(timespec="seconds")
