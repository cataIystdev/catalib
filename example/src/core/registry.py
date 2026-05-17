"""Реестр команд и диспетчеризация."""

from __future__ import annotations

from collections.abc import Iterable

from ..core.command import Command
from ..core.errors import UnknownCommandError


class CommandRegistry:
    """Хранит команды по имени и выполняет их.

    :param stats: необязательный сервис статистики; при наличии у него
        вызывается ``increment(name)`` на каждую успешную команду.
    """

    def __init__(self, stats=None) -> None:
        self._commands: dict[str, Command] = {}
        self._stats = stats

    def register(self, command: Command) -> None:
        """Зарегистрировать команду (имя должно быть уникальным и непустым)."""
        if not command.name:
            raise ValueError("у команды пустое имя")
        if command.name in self._commands:
            raise ValueError(f"команда {command.name!r} уже зарегистрирована")
        self._commands[command.name] = command

    def register_all(self, commands: Iterable[Command]) -> None:
        """Зарегистрировать набор команд."""
        for command in commands:
            self.register(command)

    def has(self, name: str) -> bool:
        """Известна ли команда с таким именем."""
        return name in self._commands

    def names(self) -> list[str]:
        """Отсортированный список имён команд."""
        return sorted(self._commands)

    def dispatch(self, name: str, args: str) -> str:
        """Выполнить команду по имени.

        :raises UnknownCommandError: если команда не зарегистрирована.
        """
        command = self._commands.get(name)
        if command is None:
            raise UnknownCommandError(f"неизвестная команда {name!r}")
        result = command.execute(args)
        if self._stats is not None:
            self._stats.increment(name)
        return result

    def help_text(self, prefix: str) -> str:
        """Сводная справка по всем командам."""
        lines = ["exteraToolbox — доступные команды:"]
        lines += [self._commands[name].help_line(prefix) for name in self.names()]
        return "\n".join(lines)
