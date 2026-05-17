"""Команды смены регистра: ``.upper``, ``.lower``, ``.title``."""

from __future__ import annotations

import abc

from ...core.command import Command
from ...core.errors import CommandError


class _CaseCommand(Command):
    """Базовая команда преобразования регистра."""

    @abc.abstractmethod
    def _transform(self, text: str) -> str:
        """Преобразовать текст (реализуется подклассом)."""

    def execute(self, args: str) -> str:
        text = args.strip()
        if not text:
            raise CommandError("нужен текст")
        return self._transform(text)


class UpperCommand(_CaseCommand):
    """Верхний регистр."""

    name = "upper"
    summary = "ВЕРХНИЙ регистр"
    usage = "<текст>"

    def _transform(self, text: str) -> str:
        return text.upper()


class LowerCommand(_CaseCommand):
    """Нижний регистр."""

    name = "lower"
    summary = "нижний регистр"
    usage = "<текст>"

    def _transform(self, text: str) -> str:
        return text.lower()


class TitleCommand(_CaseCommand):
    """Каждое Слово С Заглавной."""

    name = "title"
    summary = "Регистр Заголовка"
    usage = "<текст>"

    def _transform(self, text: str) -> str:
        return text.title()
