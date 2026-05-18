"""Тесты обёрток ``client_utils`` (офлайн-контракт)."""

from __future__ import annotations

import pytest

from catalib.support import client


def test_queue_constants_values() -> None:
    assert client.PLUGINS_QUEUE == "pluginsQueue"
    assert client.STAGE_QUEUE == "stageQueue"
    assert client.GLOBAL_QUEUE == "globalQueue"
    assert client.CACHE_CLEAR_QUEUE == "cacheClearQueue"
    assert client.SEARCH_QUEUE == "searchQueue"
    assert client.PHONE_BOOK_QUEUE == "phoneBookQueue"
    assert client.THEME_QUEUE == "themeQueue"
    assert client.EXTERNAL_NETWORK_QUEUE == "externalNetworkQueue"


def test_run_on_queue_executes_immediately_offline() -> None:
    client._queue_runs.clear()
    seen: list[int] = []
    result = client.run_on_queue(lambda: seen.append(7) or "ok", delay_ms=300)
    assert seen == [7]
    assert result == "ok"
    assert client._queue_runs == [("pluginsQueue", 300)]


def test_get_queue_by_name_none_offline() -> None:
    assert client.get_queue_by_name(client.STAGE_QUEUE) is None


def test_send_request_returns_incrementing_id_offline() -> None:
    client._sent.clear()
    a = client.send_request({"@": "ping"})
    b = client.send_request({"@": "ping"})
    assert isinstance(a, int) and b == a + 1
    assert ("request", {"@": "ping"}) in client._sent


def test_send_helpers_record_offline() -> None:
    client._sent.clear()
    client.send_text(1, "hi")
    client.send_photo(1, "/p.jpg", caption="c", high_quality=True)
    client.send_document(1, "/d.pdf")
    client.send_video(1, "/v.mp4")
    client.send_audio(1, "/a.mp3")
    client.send_message({"peer": 1, "message": "m"})
    kinds = [row[0] for row in client._sent]
    assert kinds == ["text", "photo", "document", "video", "audio", "message"]


def test_edit_message_validates_parse_mode() -> None:
    client._sent.clear()
    client.edit_message("msg", text="t", parse_mode="HTML")
    assert client._sent[-1][0] == "edit"
    with pytest.raises(ValueError, match="parse_mode"):
        client.edit_message("msg", text="t", parse_mode="BBCode")


def test_controllers_return_none_offline() -> None:
    assert client.get_messages_controller() is None
    assert client.get_last_fragment() is None
    assert client.get_user_config() is None
    assert client.get_notification_center() is None


def test_notification_center_delegate_subclassable() -> None:
    received: list[tuple] = []

    class D(client.NotificationCenterDelegate):
        def didReceivedNotification(self, id, account, args):
            received.append((id, account, args))

    d = D()
    d.didReceivedNotification(5, 0, ["a"])
    assert received == [(5, 0, ["a"])]
    # Базовая офлайн-реализация — no-op, не бросает.
    assert client.NotificationCenterDelegate().didReceivedNotification(1, 0, None) is None


def test_all_exports_present() -> None:
    for name in client.__all__:
        assert hasattr(client, name)
