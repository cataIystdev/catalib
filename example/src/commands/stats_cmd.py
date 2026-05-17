"""Команда ``.stats`` — сводка использования команд."""

from __future__ import annotations

from ..core.command import Command
from ..services.stats_service import StatsService


class StatsCommand(Command):
    """Показывает счётчики вызовов команд."""

    name = "stats"
    summary = "статистика использования команд"

    def __init__(self, stats: StatsService) -> None:
        self._stats = stats

    def execute(self, args: str) -> str:
        return self._stats.summary()
