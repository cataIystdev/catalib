"""Доменная модель броска кубиков формата ``NdM[+K]``."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..core.errors import CommandError

_DICE_RE = re.compile(r"^\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$", re.IGNORECASE)

#: Ограничения, чтобы исключить злоупотребление.
_MAX_COUNT = 100
_MAX_SIDES = 1000


@dataclass(frozen=True, slots=True)
class DiceSpec:
    """Разобранная спецификация броска.

    :param count: число кубиков (1..100).
    :param sides: число граней (2..1000).
    :param modifier: целочисленная поправка к сумме.
    """

    count: int
    sides: int
    modifier: int

    @staticmethod
    def parse(text: str) -> DiceSpec:
        """Разобрать строку вида ``2d6+1``.

        :raises CommandError: при неверном формате или выходе за пределы.
        """
        match = _DICE_RE.match(text or "")
        if not match:
            raise CommandError("формат: NdM[+K], например 2d6 или d20+1")
        count = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        modifier = int(match.group(3).replace(" ", "")) if match.group(3) else 0
        if not (1 <= count <= _MAX_COUNT):
            raise CommandError(f"число кубиков должно быть 1..{_MAX_COUNT}")
        if not (2 <= sides <= _MAX_SIDES):
            raise CommandError(f"число граней должно быть 2..{_MAX_SIDES}")
        return DiceSpec(count=count, sides=sides, modifier=modifier)
