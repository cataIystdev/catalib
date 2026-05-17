"""Команда ``.pw`` — генерация пароля криптостойким источником."""

from __future__ import annotations

import secrets
import string

from ...core.command import Command
from ...core.errors import CommandError

_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
_MIN_LEN = 4
_MAX_LEN = 128
_DEFAULT_LEN = 16


class PasswordCommand(Command):
    """Генерирует случайный пароль заданной длины (по умолчанию 16)."""

    name = "pw"
    summary = "сгенерировать пароль"
    usage = "[длина]"

    def execute(self, args: str) -> str:
        raw = args.strip()
        if not raw:
            length = _DEFAULT_LEN
        else:
            try:
                length = int(raw)
            except ValueError as exc:
                raise CommandError("длина должна быть числом") from exc
        if not (_MIN_LEN <= length <= _MAX_LEN):
            raise CommandError(f"длина должна быть {_MIN_LEN}..{_MAX_LEN}")
        return "".join(secrets.choice(_ALPHABET) for _ in range(length))
