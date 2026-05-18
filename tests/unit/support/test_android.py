"""Тесты обёрток ``android_utils`` (офлайн-контракт)."""

from __future__ import annotations

from catalib.support import android


def test_runnable_invokes_callable() -> None:
    seen: list[int] = []
    r = android.R(lambda: seen.append(1))
    r.run()
    r()
    assert seen == [1, 1]


def test_on_click_listener_passes_view() -> None:
    received: list[object] = []
    listener = android.OnClickListener(lambda v: received.append(v))
    listener.onClick("view-a")
    listener("view-b")
    assert received == ["view-a", "view-b"]


def test_on_long_click_listener_returns_bool() -> None:
    listener = android.OnLongClickListener(lambda v: 1)
    assert listener.onLongClick("v") is True
    falsy = android.OnLongClickListener(lambda v: 0)
    assert falsy("v") is False


def test_copy_to_clipboard_records_offline() -> None:
    android._clipboard_history.clear()
    android.copy_to_clipboard("https://t.me/exteraPlugins")
    assert android._clipboard_history == ["https://t.me/exteraPlugins"]


def test_log_and_run_on_ui_thread_reexported() -> None:
    android.log("сообщение")  # не должно бросать
    seen: list[int] = []
    android.run_on_ui_thread(lambda: seen.append(1), delay=100)
    assert seen == [1]


def test_all_exports_present() -> None:
    for name in android.__all__:
        assert hasattr(android, name)
