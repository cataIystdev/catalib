"""Исключения ядра команд."""

from __future__ import annotations


class CommandError(Exception):
    """Ожидаемая ошибка выполнения команды (показывается пользователю)."""


class UnknownCommandError(CommandError):
    """Запрошена несуществующая команда."""
