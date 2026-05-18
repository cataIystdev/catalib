"""Тесты обёртки ``AlertDialogBuilder`` (офлайн-рекордер)."""

from __future__ import annotations

from catalib.support.dialogs import AlertDialogBuilder


def test_constants_present() -> None:
    assert AlertDialogBuilder.ALERT_TYPE_MESSAGE == 0
    assert AlertDialogBuilder.ALERT_TYPE_LOADING == 1
    assert AlertDialogBuilder.ALERT_TYPE_SPINNER == 2
    assert AlertDialogBuilder.BUTTON_POSITIVE == -1
    assert AlertDialogBuilder.BUTTON_NEGATIVE == -2


def test_chainable_builder_records_calls() -> None:
    b = AlertDialogBuilder("ctx")
    result = (
        b.set_title("T")
        .set_message("M")
        .set_positive_button("OK")
        .make_button_red(AlertDialogBuilder.BUTTON_POSITIVE)
        .create()
        .show()
    )
    assert result is b
    names = [c[0] for c in b.calls]
    assert names == [
        "set_title",
        "set_message",
        "set_positive_button",
        "make_button_red",
        "create",
        "show",
    ]
    assert b._shown is True


def test_lifecycle_offline_returns_none() -> None:
    b = AlertDialogBuilder("ctx", progress_style=AlertDialogBuilder.ALERT_TYPE_SPINNER)
    assert b.progress_style == 2
    assert b.get_dialog() is None
    assert b.get_button(AlertDialogBuilder.BUTTON_NEGATIVE) is None
    b.dismiss()
    assert b._dismissed is True
    assert ("dismiss",) in b.calls


def test_items_and_listeners_recorded() -> None:
    b = AlertDialogBuilder("ctx")
    b.set_items(["a", "b"], listener=lambda d, i: None)
    b.set_on_dismiss_listener(lambda d: None)
    b.set_blurred_background(True)
    kinds = [c[0] for c in b.calls]
    assert kinds == [
        "set_items",
        "set_on_dismiss_listener",
        "set_blurred_background",
    ]
