"""Команда ``.roll`` — бросок кубиков ``NdM[+K]``."""

from __future__ import annotations

import random

from ...core.command import Command
from ...domain.dice import DiceSpec


class DiceCommand(Command):
    """Бросает кубики по спецификации и показывает раскладку."""

    name = "roll"
    summary = "бросок кубиков NdM[+K]"
    usage = "NdM[+K]"

    def execute(self, args: str) -> str:
        spec = DiceSpec.parse(args)
        rolls = [random.randint(1, spec.sides) for _ in range(spec.count)]
        total = sum(rolls) + spec.modifier
        detail = " + ".join(str(r) for r in rolls)
        if spec.modifier:
            sign = "+" if spec.modifier > 0 else "-"
            detail = f"{detail} {sign} {abs(spec.modifier)}"
        return f"{args.strip()}: [{detail}] = {total}"
