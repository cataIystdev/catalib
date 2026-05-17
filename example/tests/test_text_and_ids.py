"""Тесты текстовых команд и генераторов идентификаторов/хешей."""

import re
import uuid

import pytest
from src.commands.ids.hash_cmd import HashCommand
from src.commands.ids.uuid_cmd import UuidCommand
from src.commands.text.base64_cmd import Base64Command
from src.commands.text.case import LowerCommand, TitleCommand, UpperCommand
from src.commands.text.reverse import ReverseCommand
from src.core.errors import CommandError


def test_base64_roundtrip() -> None:
    enc = Base64Command().execute("enc Привет")
    assert Base64Command().execute(f"dec {enc}") == "Привет"


@pytest.mark.parametrize("bad", ["", "enc", "dec не_base64!", "xxx data"])
def test_base64_errors(bad: str) -> None:
    with pytest.raises(CommandError):
        Base64Command().execute(bad)


def test_case_commands() -> None:
    assert UpperCommand().execute("abc Привет") == "ABC ПРИВЕТ"
    assert LowerCommand().execute("ABC ПРИВЕТ") == "abc привет"
    assert TitleCommand().execute("привет мир") == "Привет Мир"


def test_reverse() -> None:
    assert ReverseCommand().execute("abcГ") == "Гcba"


def test_reverse_requires_text() -> None:
    with pytest.raises(CommandError):
        ReverseCommand().execute("   ")


def test_uuid_is_valid_v4() -> None:
    value = UuidCommand().execute("")
    parsed = uuid.UUID(value)
    assert parsed.version == 4


def test_hash_sha256_known_value() -> None:
    out = HashCommand().execute("sha256 abc")
    assert out == ("sha256: ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


def test_hash_rejects_unknown_algo() -> None:
    with pytest.raises(CommandError, match="алгоритмы"):
        HashCommand().execute("crc32 abc")


def test_uuid_unique() -> None:
    assert UuidCommand().execute("") != UuidCommand().execute("")
    assert re.fullmatch(r"[0-9a-f-]{36}", UuidCommand().execute(""))
