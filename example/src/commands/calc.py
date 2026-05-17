"""Команда калькулятора ``.calc``."""

from __future__ import annotations

from ..core.command import Command
from ..safe_eval.arithmetic import evaluate
from ..util.formatting import number_to_text


class CalcCommand(Command):
    """Безопасно вычисляет арифметическое выражение."""

    name = "calc"
    summary = "вычислить арифметическое выражение"
    usage = "<выражение>"

    def execute(self, args: str) -> str:
        result = evaluate(args)
        return f"{args.strip()} = {number_to_text(result)}"
