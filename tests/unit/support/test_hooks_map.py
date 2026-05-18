"""Тесты декларативной карты хук-методов запроса/апдейта (0.3.0)."""

from __future__ import annotations

import pytest

from catalib.support import CatalibPlugin, hook
from catalib.support.sdk import HookResult, HookStrategy


class Net(CatalibPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.seen: list[tuple] = []

    @hook.pre_request("messages.sendMessage", priority=3)
    def before_send(self, request_name, account, request):
        self.seen.append(("pre", request_name, account, request))
        return HookResult(HookStrategy.CANCEL)

    @hook.post_request("messages.sendMessage")
    def after_send(self, request_name, account, response, error):
        self.seen.append(("post", request_name, response, error))

    @hook.on_update("updateNewMessage")
    def on_new(self, update_name, account, update):
        self.seen.append(("upd", update_name))

    @hook.on_updates("Updates", match_substring=True)
    def on_many(self, container_name, account, updates):
        self.seen.append(("upds", container_name))


def test_request_hooks_registered_via_add_hook() -> None:
    p = Net()
    p.on_plugin_load()
    assert ("messages.sendMessage", 3) in p.registered_hooks
    assert ("messages.sendMessage", 0) in p.registered_hooks
    assert ("updateNewMessage", 0) in p.registered_hooks
    # match_substring фиксируется заглушкой add_hook отдельной записью.
    assert ("Updates", "substring") in p.registered_hooks


def test_pre_request_dispatch_returns_handler_result() -> None:
    p = Net()
    res = p.pre_request_hook("messages.sendMessage", 1, {"m": "hi"})
    assert res.strategy == HookStrategy.CANCEL
    assert p.seen[0] == ("pre", "messages.sendMessage", 1, {"m": "hi"})


def test_non_matching_name_returns_default_hookresult() -> None:
    p = Net()
    res = p.pre_request_hook("other.request", 1, None)
    assert isinstance(res, HookResult)
    assert res.strategy == HookStrategy.DEFAULT
    assert p.seen == []


def test_post_request_dispatch_default_when_handler_returns_none() -> None:
    p = Net()
    res = p.post_request_hook("messages.sendMessage", 1, "resp", None)
    assert res.strategy == HookStrategy.DEFAULT  # handler вернул None
    assert ("post", "messages.sendMessage", "resp", None) in p.seen


def test_on_updates_substring_match() -> None:
    p = Net()
    p.on_updates_hook("UpdatesCombined", 1, [])
    assert ("upds", "UpdatesCombined") in p.seen


def test_empty_plugin_request_hooks_are_safe() -> None:
    class Empty(CatalibPlugin):
        pass

    p = Empty()
    p.on_plugin_load()
    assert p.pre_request_hook("x", 0, None).strategy == HookStrategy.DEFAULT
    assert p.on_update_hook("x", 0, None).strategy == HookStrategy.DEFAULT


def test_direct_override_still_wins() -> None:
    class Raw(CatalibPlugin):
        def pre_request_hook(self, request_name, account, request):
            return "custom"

    assert Raw().pre_request_hook("a", 0, None) == "custom"


def test_decorator_requires_name() -> None:
    with pytest.raises(ValueError, match="непустой строкой"):
        hook.pre_request("")
    with pytest.raises(ValueError, match="непустой строкой"):
        hook.on_updates("")


def test_legacy_request_and_send_message_untouched() -> None:
    class Old(CatalibPlugin):
        @hook.send_message
        def on_send_message_hook(self, account, params):
            return None

        @hook.request("messages.getHistory")
        def on_request(self, *a):
            return None

    p = Old()
    p.on_plugin_load()
    assert ("send_message", 0) in p.registered_hooks
    assert ("messages.getHistory", 0) in p.registered_hooks
