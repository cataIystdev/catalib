"""Команда ``.hash`` — хеш текста (md5/sha1/sha256)."""

from __future__ import annotations

import hashlib

from ...core.command import Command
from ...core.errors import CommandError

_ALGOS = {"md5", "sha1", "sha256", "sha512"}


class HashCommand(Command):
    """``.hash sha256 <текст>`` — шестнадцатеричный дайджест."""

    name = "hash"
    summary = "хеш текста (md5|sha1|sha256|sha512)"
    usage = "<алгоритм> <текст>"

    def execute(self, args: str) -> str:
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            raise CommandError("формат: <алгоритм> <текст>")
        algo, text = parts[0].lower(), parts[1]
        if algo not in _ALGOS:
            raise CommandError(f"алгоритмы: {', '.join(sorted(_ALGOS))}")
        digest = hashlib.new(algo, text.encode("utf-8")).hexdigest()
        return f"{algo}: {digest}"
