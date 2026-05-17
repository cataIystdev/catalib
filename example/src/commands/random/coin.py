"""Команда ``.coin`` — бросок монеты."""

from __future__ import annotations

import random

from ...core.command import Command


class CoinCommand(Command):
    """Возвращает «орёл» или «решка»."""

    name = "coin"
    summary = "бросить монету"

    def execute(self, args: str) -> str:
        return random.choice(["орёл", "решка"])
