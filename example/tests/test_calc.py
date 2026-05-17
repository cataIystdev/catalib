"""Тесты безопасного калькулятора и команды .calc."""

import pytest
from src.commands.calc import CalcCommand
from src.core.errors import CommandError
from src.safe_eval.arithmetic import evaluate


@pytest.mark.parametrize(
    ("expr", "expected"),
    [
        ("2+2", 4),
        ("2 + 3 * 4", 14),
        ("(2 + 3) * 4", 20),
        ("10 / 4", 2.5),
        ("10 // 4", 2),
        ("10 % 3", 1),
        ("2 ** 10", 1024),
        ("-5 + 3", -2),
    ],
)
def test_evaluate_arithmetic(expr: str, expected: float) -> None:
    assert evaluate(expr) == expected


@pytest.mark.parametrize("expr", ["__import__('os')", "a + 1", "len([1])", "1;2", ""])
def test_evaluate_rejects_unsafe(expr: str) -> None:
    with pytest.raises(CommandError):
        evaluate(expr)


def test_division_by_zero() -> None:
    with pytest.raises(CommandError, match="ноль"):
        evaluate("1/0")


def test_power_limit() -> None:
    with pytest.raises(CommandError, match="степени"):
        evaluate("2 ** 100000")


def test_calc_command_formats_result() -> None:
    assert CalcCommand().execute("2 + 2") == "2 + 2 = 4"
    assert CalcCommand().execute("10/4") == "10/4 = 2.5"
