"""Тесты обёртки ``BulletinHelper`` (офлайн-рекордер)."""

from __future__ import annotations

from catalib.support.bulletins import BulletinHelper


def test_duration_constants() -> None:
    assert BulletinHelper.DURATION_SHORT == 1500
    assert BulletinHelper.DURATION_LONG == 2750
    assert BulletinHelper.DURATION_PROLONG == 5000


def test_standard_bulletins_recorded() -> None:
    BulletinHelper.shown.clear()
    BulletinHelper.show_info("i")
    BulletinHelper.show_error("e")
    BulletinHelper.show_success("s")
    assert [row[0] for row in BulletinHelper.shown] == ["info", "error", "success"]
    assert BulletinHelper.shown[0][1] == "i"


def test_rich_bulletins_recorded() -> None:
    BulletinHelper.shown.clear()
    BulletinHelper.show_simple("t", 10)
    BulletinHelper.show_two_line("title", "sub", 11)
    BulletinHelper.show_with_button("t", 12, "OK", lambda: None)
    BulletinHelper.show_undo("u", lambda: None)
    BulletinHelper.show_copied_to_clipboard()
    BulletinHelper.show_link_copied(is_private_link_info=True)
    BulletinHelper.show_file_saved_to_gallery(is_video=True, amount=3)
    BulletinHelper.show_file_saved_to_downloads("IMAGE", amount=2)
    kinds = [row[0] for row in BulletinHelper.shown]
    assert kinds == [
        "simple",
        "two_line",
        "with_button",
        "undo",
        "copied_to_clipboard",
        "link_copied",
        "file_saved_to_gallery",
        "file_saved_to_downloads",
    ]


def test_with_button_default_duration() -> None:
    BulletinHelper.shown.clear()
    BulletinHelper.show_with_button("t", 1, "B", lambda: None)
    row = BulletinHelper.shown[0]
    assert row[-1] == BulletinHelper.DURATION_PROLONG
