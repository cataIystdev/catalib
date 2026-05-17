"""Точка входа плагина exteraToolbox.

Единственный хук исходящих сообщений разбирает команды с префиксом и
выполняет их через реестр. Регистрация хука и пункта меню — автоматическая
(мини-фреймворк catalib). Метаданные берутся из ``catalib.toml``.
"""

from __future__ import annotations

from typing import Any

from catalib.support import (
    CatalibPlugin,
    HookResult,
    HookStrategy,
    hook,
    log,
    menu_item,
)

from .commands import CommandContext, build_commands
from .config import (
    DEFAULT_PREFIX,
    SETTING_COUNT_STATS,
    SETTING_PREFIX,
    SETTING_SHOW_ERRORS,
)
from .core.errors import CommandError, UnknownCommandError
from .core.parser import parse
from .core.registry import CommandRegistry
from .services.notes_service import NotesService
from .services.stats_service import StatsService
from .storage.notes_repository import NotesRepository
from .storage.paths import data_dir
from .ui.settings_schema import build_settings
from .util.formatting import clamp_result


class ToolboxPlugin(CatalibPlugin):
    """Набор чат-команд: калькулятор, заметки, генераторы, дата/время."""

    def on_load(self) -> None:
        base = data_dir()
        self._stats = StatsService(base)
        notes_service = NotesService(NotesRepository(base))
        self._registry = CommandRegistry()
        self._registry.register_all(
            build_commands(CommandContext(notes=notes_service, stats=self._stats))
        )
        log(f"[toolbox] загружен, команд: {len(self._registry.names())}")

    def settings(self) -> list[Any]:
        return build_settings()

    def _prefix(self) -> str:
        value = self.get_setting(SETTING_PREFIX, DEFAULT_PREFIX)
        return value if isinstance(value, str) and value else DEFAULT_PREFIX

    @hook.send_message
    def on_send_message_hook(self, account: int, params: Any) -> Any:
        message = getattr(params, "message", None)
        if not isinstance(message, str):
            return HookResult()
        parsed = parse(message, self._prefix())
        if parsed is None:
            return HookResult()
        name, args = parsed

        show_errors = bool(self.get_setting(SETTING_SHOW_ERRORS, True))
        try:
            if name == "help":
                result = self._registry.help_text(self._prefix())
            else:
                result = self._registry.dispatch(name, args)
                if bool(self.get_setting(SETTING_COUNT_STATS, True)):
                    self._stats.increment(name)
        except UnknownCommandError:
            return HookResult()
        except CommandError as exc:
            if not show_errors:
                return HookResult()
            result = f"[toolbox] ошибка: {exc}"

        params.message = clamp_result(result)
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    @menu_item("exteraToolbox: справка")
    def show_help(self) -> None:
        log(self._registry.help_text(self._prefix()))
