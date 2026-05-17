"""Тесты точки входа: хук исходящих сообщений и автонастройка."""

from __future__ import annotations

import pytest
from src import plugin as plugin_module
from src.config import SETTING_PREFIX, SETTING_SHOW_ERRORS
from src.plugin import ToolboxPlugin


class Params:
    """Подделка params SDK с атрибутом message."""

    def __init__(self, message) -> None:
        self.message = message


@pytest.fixture
def plugin(tmp_path, monkeypatch) -> ToolboxPlugin:
    monkeypatch.setattr(plugin_module, "data_dir", lambda: str(tmp_path))
    instance = ToolboxPlugin()
    instance.on_plugin_load()
    return instance


def test_hook_auto_registered(plugin: ToolboxPlugin) -> None:
    assert ("send_message", 0) in plugin.registered_hooks
    assert len(plugin.registered_menu_items) == 1


def test_calc_rewrites_message(plugin: ToolboxPlugin) -> None:
    params = Params(".calc 2 + 2 * 10")
    result = plugin.on_send_message_hook(0, params)
    assert result.strategy == "MODIFY"
    assert params.message == "2 + 2 * 10 = 22"


def test_non_command_passthrough(plugin: ToolboxPlugin) -> None:
    params = Params("обычное сообщение")
    result = plugin.on_send_message_hook(0, params)
    assert result.strategy == "DEFAULT"
    assert params.message == "обычное сообщение"


def test_unknown_command_passthrough(plugin: ToolboxPlugin) -> None:
    params = Params(".нет_такой 1")
    result = plugin.on_send_message_hook(0, params)
    assert result.strategy == "DEFAULT"
    assert params.message == ".нет_такой 1"


def test_non_string_message_ignored(plugin: ToolboxPlugin) -> None:
    params = Params(None)
    assert plugin.on_send_message_hook(0, params).strategy == "DEFAULT"


def test_command_error_shown_when_enabled(plugin: ToolboxPlugin) -> None:
    params = Params(".calc 1/0")
    plugin.on_send_message_hook(0, params)
    assert "ошибка" in params.message and "ноль" in params.message


def test_command_error_hidden_when_disabled(plugin: ToolboxPlugin) -> None:
    plugin.set_setting(SETTING_SHOW_ERRORS, False)
    params = Params(".calc 1/0")
    result = plugin.on_send_message_hook(0, params)
    assert result.strategy == "DEFAULT"
    assert params.message == ".calc 1/0"


def test_help_lists_commands(plugin: ToolboxPlugin) -> None:
    params = Params(".help")
    plugin.on_send_message_hook(0, params)
    assert "exteraToolbox — доступные команды:" in params.message
    assert ".calc" in params.message and ".note" in params.message


def test_custom_prefix(plugin: ToolboxPlugin) -> None:
    plugin.set_setting(SETTING_PREFIX, "!")
    params = Params("!rev abc")
    plugin.on_send_message_hook(0, params)
    assert params.message == "cba"


def test_stats_counted(plugin: ToolboxPlugin) -> None:
    plugin.on_send_message_hook(0, Params(".uuid"))
    assert "uuid: 1" in plugin._stats.summary()
