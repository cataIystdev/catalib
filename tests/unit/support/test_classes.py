"""Тесты FQN-констант общих Java-классов."""

from __future__ import annotations

from catalib.support import classes


def test_known_fqns() -> None:
    assert classes.CHAT_ACTIVITY == "org.telegram.ui.ChatActivity"
    assert classes.MESSAGE_OBJECT == "org.telegram.messenger.MessageObject"
    assert classes.ALERT_DIALOG == "org.telegram.ui.ActionBar.AlertDialog"
    assert classes.TLRPC == "org.telegram.tgnet.TLRPC"
    assert classes.SEND_MESSAGES_HELPER == "org.telegram.messenger.SendMessagesHelper"


def test_common_classes_mapping_consistent() -> None:
    assert classes.COMMON_CLASSES["ChatActivity"] == classes.CHAT_ACTIVITY
    assert classes.COMMON_CLASSES["TLRPC"] == classes.TLRPC
    assert len(classes.COMMON_CLASSES) == 12
    for fqn in classes.COMMON_CLASSES.values():
        assert fqn.startswith("org.telegram.")


def test_all_exports_present() -> None:
    for name in classes.__all__:
        assert hasattr(classes, name)
