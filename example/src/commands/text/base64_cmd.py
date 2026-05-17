"""Команда ``.b64`` — кодирование/декодирование Base64."""

from __future__ import annotations

import base64
import binascii

from ...core.command import Command
from ...core.errors import CommandError


class Base64Command(Command):
    """``.b64 enc <текст>`` или ``.b64 dec <base64>``."""

    name = "b64"
    summary = "Base64: enc <текст> | dec <данные>"
    usage = "enc|dec <данные>"

    def execute(self, args: str) -> str:
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            raise CommandError("формат: enc <текст> или dec <base64>")
        mode, payload = parts[0].lower(), parts[1]
        if mode == "enc":
            return base64.b64encode(payload.encode("utf-8")).decode("ascii")
        if mode == "dec":
            try:
                return base64.b64decode(payload, validate=True).decode("utf-8")
            except (binascii.Error, ValueError, UnicodeDecodeError) as exc:
                raise CommandError("некорректные данные Base64") from exc
        raise CommandError("режим должен быть enc или dec")
