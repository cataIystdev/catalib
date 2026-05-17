"""Сборка набора команд плагина.

Команды разнесены по подпакетам по темам. ``build_commands`` собирает их
все, передавая нужным командам сервисы через :class:`CommandContext`.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.command import Command
from ..services.notes_service import NotesService
from ..services.stats_service import StatsService
from .calc import CalcCommand
from .ids.hash_cmd import HashCommand
from .ids.uuid_cmd import UuidCommand
from .notes.commands import NoteCommand
from .random.coin import CoinCommand
from .random.dice import DiceCommand
from .random.password import PasswordCommand
from .stats_cmd import StatsCommand
from .text.base64_cmd import Base64Command
from .text.case import LowerCommand, TitleCommand, UpperCommand
from .text.reverse import ReverseCommand
from .timeinfo.now import NowCommand
from .timeinfo.relative import RelativeCommand


@dataclass(frozen=True, slots=True)
class CommandContext:
    """Зависимости команд, которым нужны сервисы."""

    notes: NotesService
    stats: StatsService


def build_commands(context: CommandContext) -> list[Command]:
    """Собрать полный список команд плагина."""
    return [
        CalcCommand(),
        Base64Command(),
        UpperCommand(),
        LowerCommand(),
        TitleCommand(),
        ReverseCommand(),
        DiceCommand(),
        CoinCommand(),
        PasswordCommand(),
        NowCommand(),
        RelativeCommand(),
        UuidCommand(),
        HashCommand(),
        NoteCommand(context.notes),
        StatsCommand(context.stats),
    ]
