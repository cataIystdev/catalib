"""Тесты обёрток ``text_formatting`` (офлайн-контракт)."""

from __future__ import annotations

from catalib.support import formatting


def test_parse_text_message_key_offline() -> None:
    result = formatting.parse_text("<b>hi</b>")
    assert result == {"message": "<b>hi</b>", "entities": []}


def test_parse_text_caption_key_offline() -> None:
    result = formatting.parse_text("*x*", parse_mode="Markdown", is_caption=True)
    assert set(result) == {"caption", "entities"}
    assert result["caption"] == "*x*"
    assert result["entities"] == []


def test_tl_entity_type_constants() -> None:
    assert formatting.TLEntityType.BOLD == "BOLD"
    assert formatting.TLEntityType.TEXT_LINK == "TEXT_LINK"
    assert formatting.TLEntityType.CUSTOM_EMOJI == "CUSTOM_EMOJI"
    assert formatting.TLEntityType.BLOCKQUOTE == "BLOCKQUOTE"


def test_raw_entity_offline_fields() -> None:
    e = formatting.RawEntity(
        type=formatting.TLEntityType.TEXT_LINK, offset=2, length=5, url="https://x"
    )
    assert e.offset == 2 and e.length == 5
    assert e.url == "https://x"
    assert e.language is None and e.document_id is None and e.collapsed is None


def test_all_exports_present() -> None:
    for name in formatting.__all__:
        assert hasattr(formatting, name)
