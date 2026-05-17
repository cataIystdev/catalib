"""Базовая модель команды чата."""

from __future__ import annotations

import abc


class Command(abc.ABC):
    """Команда чата плагина.

    Подклассы задают ``name`` (имя без префикса), ``summary`` (краткое
    описание для справки) и реализуют :meth:`execute`.
    """

    #: Имя команды без префикса, в нижнем регистре.
    name: str = ""
    #: Краткое описание для встроенной справки.
    summary: str = ""
    #: Шаблон аргументов для справки (например ``"<выражение>"``).
    usage: str = ""

    @abc.abstractmethod
    def execute(self, args: str) -> str:
        """Выполнить команду.

        :param args: всё, что идёт после имени команды (без обрезки регистра).
        :returns: текст результата, который заменит исходное сообщение.
        :raises catalib... CommandError: при ожидаемой ошибке ввода.
        """

    def help_line(self, prefix: str) -> str:
        """Строка справки по команде с актуальным префиксом."""
        head = f"{prefix}{self.name}"
        if self.usage:
            head = f"{head} {self.usage}"
        return f"{head} — {self.summary}"
