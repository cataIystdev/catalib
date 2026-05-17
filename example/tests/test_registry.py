"""Тесты реестра команд."""

import pytest
from src.core.command import Command
from src.core.errors import UnknownCommandError
from src.core.registry import CommandRegistry


class _Echo(Command):
    name = "echo"
    summary = "вернуть аргумент"
    usage = "<текст>"

    def execute(self, args: str) -> str:
        return args


class _Stats:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def increment(self, name: str) -> None:
        self.calls.append(name)


def test_register_and_dispatch() -> None:
    reg = CommandRegistry()
    reg.register(_Echo())
    assert reg.has("echo")
    assert reg.dispatch("echo", "привет") == "привет"


def test_duplicate_registration_rejected() -> None:
    reg = CommandRegistry()
    reg.register(_Echo())
    with pytest.raises(ValueError, match="уже зарегистрирована"):
        reg.register(_Echo())


def test_unknown_command_raises() -> None:
    with pytest.raises(UnknownCommandError):
        CommandRegistry().dispatch("nope", "")


def test_stats_incremented_on_success() -> None:
    stats = _Stats()
    reg = CommandRegistry(stats=stats)
    reg.register(_Echo())
    reg.dispatch("echo", "x")
    assert stats.calls == ["echo"]


def test_help_text_lists_commands_with_prefix() -> None:
    reg = CommandRegistry()
    reg.register(_Echo())
    text = reg.help_text("!")
    assert "!echo <текст> — вернуть аргумент" in text
