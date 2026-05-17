"""Тесты разбора команды из сообщения."""

from src.core.parser import parse


def test_parses_name_and_args() -> None:
    assert parse(".calc 2 + 2", ".") == ("calc", "2 + 2")


def test_lowercases_name_keeps_args_case() -> None:
    assert parse(".B64 Enc Привет", ".") == ("b64", "Enc Привет")


def test_no_args() -> None:
    assert parse(".coin", ".") == ("coin", "")


def test_not_a_command_without_prefix() -> None:
    assert parse("calc 2+2", ".") is None


def test_custom_multichar_prefix() -> None:
    assert parse("!!roll 2d6", "!!") == ("roll", "2d6")


def test_prefix_only_is_none() -> None:
    assert parse(".", ".") is None
    assert parse(".   ", ".") is None
