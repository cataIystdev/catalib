"""Тесты домена кубиков и команды .roll."""

import pytest
from src.commands.random import dice as dice_module
from src.commands.random.dice import DiceCommand
from src.core.errors import CommandError
from src.domain.dice import DiceSpec


def test_parse_full_spec() -> None:
    spec = DiceSpec.parse("2d6+3")
    assert (spec.count, spec.sides, spec.modifier) == (2, 6, 3)


def test_parse_defaults_count_to_one() -> None:
    spec = DiceSpec.parse("d20")
    assert (spec.count, spec.sides, spec.modifier) == (1, 20, 0)


@pytest.mark.parametrize("bad", ["", "abc", "0d6", "2d1", "101d6", "2d1001"])
def test_parse_rejects_invalid(bad: str) -> None:
    with pytest.raises(CommandError):
        DiceSpec.parse(bad)


def test_dice_command_is_deterministic_with_patched_rng(monkeypatch) -> None:
    monkeypatch.setattr(dice_module.random, "randint", lambda a, b: b)
    assert DiceCommand().execute("3d6+1") == "3d6+1: [6 + 6 + 6 + 1] = 19"
