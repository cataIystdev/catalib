"""Шаблоны файлов для ``catalib init``.

Подстановки выполняются через :meth:`str.format` с ключами ``plugin_id``,
``name``, ``author``, ``class_name`` (а в манифесте — ещё ``description``).
Поэтому в **коде** шаблонов не должно быть литеральных фигурных скобок
(никаких f-строк) — нужное форматирование строится конкатенацией; так
``str.format`` не ломается. Доменные модули (без плейсхолдеров) через
``format`` не пропускаются и могут использовать f-строки свободно.

Каждый :class:`Template` собирается ``catalib build`` без правок и несёт
офлайн-тест. Доступные шаблоны: см. :data:`TEMPLATES`.
"""

from __future__ import annotations

from dataclasses import dataclass

MANIFEST = """\
[plugin]
id = "{plugin_id}"
name = "{name}"
version = "1.0.0"
description = "{description}"
author = "{author}"
icon = "exteraPlugins/1"
min_version = ">=12.5.1"
sdk_version = ">=1.4.4"

[build]
src = "src"
entry = "plugin"
out = "dist"
"""

ROOT_INIT = '"""Пакет плагина {name}."""\n'

PYPROJECT = """\
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
"""

GITIGNORE = "dist/\n__pycache__/\n*.pyc\n.venv/\n"

README = """\
# {name}

Модульный плагин exteraGram (шаблон `{template}`). Сборка в один файл:

```
catalib build
```

Результат: `dist/{plugin_id}.py` — устанавливается в exteraGram как обычный
плагин. Разработка с автодеплоем на устройство:

```
catalib watch --deploy
```

Офлайн-тесты (без устройства и SDK):

```
pytest
```
"""

# --- шаблон hook (по умолчанию): хук исходящих сообщений ------------------
# Файлы байт-в-байт совпадают с прежним единственным шаблоном — обратная
# совместимость генерации и существующих тестов.

_HOOK_GREETING = '''\
"""Пример доменного модуля без зависимостей от Android (тестируется офлайн)."""

from __future__ import annotations


def build_greeting(name: str) -> str:
    """Вернуть приветствие для имени.

    :param name: имя; пустое имя заменяется на «мир».
    """
    cleaned = name.strip() or "мир"
    return f"Привет, {cleaned}!"
'''

_HOOK_PLUGIN = '''\
"""Точка входа плагина: подкласс CatalibPlugin с хуком исходящих сообщений."""

from __future__ import annotations

from catalib.support import CatalibPlugin, HookResult, HookStrategy, hook, settings

from .greeting import build_greeting


class {class_name}(CatalibPlugin):
    """Заменяет команду ``.hello <имя>`` на приветствие."""

    @hook.send_message
    def on_send_message_hook(self, account, params):
        message = getattr(params, "message", None)
        if not isinstance(message, str) or not message.startswith(".hello"):
            return HookResult()
        name = message[len(".hello") :].strip()
        params.message = build_greeting(name)
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    def settings(self):
        return [
            settings.header("{name}"),
            settings.text("Использование", subtext=".hello Алиса -> Привет, Алиса!"),
        ]
'''

_HOOK_TEST = '''\
"""Офлайн-тест доменной логики плагина (без Android/SDK)."""

from src.greeting import build_greeting


def test_build_greeting_uses_name() -> None:
    assert build_greeting("Алиса") == "Привет, Алиса!"


def test_build_greeting_defaults_when_empty() -> None:
    assert build_greeting("   ") == "Привет, мир!"
'''

# --- шаблон minimal: самый маленький рабочий каркас -----------------------

_MIN_CORE = '''\
"""Доменный модуль без зависимостей от Android (тестируется офлайн)."""

from __future__ import annotations


def status_line(name: str) -> str:
    """Строка для лога при загрузке плагина."""
    return f"{name}: плагин загружен"
'''

_MIN_PLUGIN = '''\
"""Минимальный плагин: только инициализация и заголовок настроек."""

from __future__ import annotations

from catalib.support import CatalibPlugin, settings

from .core import status_line


class {class_name}(CatalibPlugin):
    """Каркас без хуков — точка старта для своей логики."""

    def on_load(self):
        self.log(status_line("{name}"))

    def settings(self):
        return [settings.header("{name}")]
'''

_MIN_TEST = '''\
"""Офлайн-тест доменной логики (без Android/SDK)."""

from src.core import status_line


def test_status_line_mentions_name() -> None:
    assert status_line("Demo") == "Demo: плагин загружен"
'''

# --- шаблон menu: пункт контекстного меню сообщения -----------------------

_MENU_ACTIONS = '''\
"""Доменная логика пункта меню (чистая, тестируется офлайн)."""

from __future__ import annotations


def shout(text: str) -> str:
    """Привести текст к «крику»: верхний регистр без крайних пробелов."""
    return text.strip().upper()
'''

_MENU_PLUGIN = '''\
"""Плагин с пунктом контекстного меню сообщения."""

from __future__ import annotations

from catalib.support import CatalibPlugin, menu_item, settings

from .actions import shout


class {class_name}(CatalibPlugin):
    """Добавляет в меню сообщения пункт, логирующий «крик» из текста."""

    @menu_item("Крикнуть", "MESSAGE_CONTEXT_MENU")
    def on_shout(self, context):
        # context — dict от SDK; офлайн в тесте передаётся свой.
        text = ""
        if isinstance(context, dict):
            text = context.get("message", "") or ""
        self.log("shout -> " + shout(text))

    def settings(self):
        return [
            settings.header("{name}"),
            settings.text("Как пользоваться", subtext="Меню сообщения -> Крикнуть"),
        ]
'''

_MENU_TEST = '''\
"""Офлайн-тесты: доменная логика + пункт меню через catalib.testing."""

from catalib.testing import PluginHarness

from src.actions import shout
from src.plugin import {class_name}


def test_shout_uppercases_trimmed() -> None:
    assert shout("  привет  ") == "ПРИВЕТ"


def test_menu_item_registered_and_clickable() -> None:
    harness = PluginHarness.load({class_name})
    assert [item.text for item in harness.menu_items] == ["Крикнуть"]
    harness.click_menu("Крикнуть", message="ого")
    assert harness.logged == ["shout -> ОГО"]
'''

# --- шаблон settings: настройки управляют хуком ---------------------------

_SET_FORMAT = '''\
"""Доменная логика форматирования (чистая, тестируется офлайн)."""

from __future__ import annotations


def decorate(message: str, prefix: str) -> str:
    """Добавить префикс к сообщению (пустой префикс — без изменений)."""
    prefix = prefix.strip()
    if not prefix:
        return message
    return "[" + prefix + "] " + message
'''

_SET_PLUGIN = '''\
"""Плагин, чьё поведение управляется настройками."""

from __future__ import annotations

from catalib.support import CatalibPlugin, HookResult, HookStrategy, hook, settings

from .format import decorate

ENABLED_KEY = "enabled"
PREFIX_KEY = "prefix"


class {class_name}(CatalibPlugin):
    """Если включено — добавляет настраиваемый префикс к исходящим сообщениям."""

    @hook.send_message
    def on_send_message_hook(self, account, params):
        if not self.get_setting(ENABLED_KEY, False):
            return HookResult()
        message = getattr(params, "message", None)
        if not isinstance(message, str) or not message:
            return HookResult()
        params.message = decorate(message, self.get_setting(PREFIX_KEY, ""))
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    def settings(self):
        return [
            settings.header("{name}"),
            settings.switch(ENABLED_KEY, "Добавлять префикс", False),
            settings.text_input(PREFIX_KEY, "Префикс", "tag"),
        ]
'''

_SET_TEST = '''\
"""Офлайн-тесты: доменная логика + хук с настройками через catalib.testing."""

from catalib.testing import PluginHarness

from src.format import decorate
from src.plugin import ENABLED_KEY, PREFIX_KEY, {class_name}


def test_decorate_adds_prefix() -> None:
    assert decorate("hi", "tag") == "[tag] hi"
    assert decorate("hi", "  ") == "hi"


def test_hook_respects_enabled_setting() -> None:
    off = PluginHarness.load({class_name})
    assert off.send_message("hi").strategy == "DEFAULT"

    on = PluginHarness.load({class_name}, settings={{ENABLED_KEY: True, PREFIX_KEY: "x"}})
    result = on.send_message("hi")
    assert result.strategy == "MODIFY"
    assert on.last_params.message == "[x] hi"
'''


@dataclass(frozen=True, slots=True)
class Template:
    """Описание шаблона ``catalib init``.

    :param description: значение ``plugin.description`` в манифесте и
        краткое назначение шаблона (для справки CLI).
    :param files: переменная часть проекта — относительный путь -> контент
        (через ``str.format`` с ключами подстановки). Общие файлы
        (``pyproject.toml`` и пр.) добавляет генератор.
    """

    description: str
    files: dict[str, str]


#: Имя шаблона по умолчанию (обратная совместимость ``catalib init``).
DEFAULT_TEMPLATE = "hook"

#: Реестр доступных шаблонов. Ключ — значение ``--template``.
TEMPLATES: dict[str, Template] = {
    "hook": Template(
        "Плагин exteraGram, собранный catalib",
        {
            "src/greeting.py": _HOOK_GREETING,
            "src/plugin.py": _HOOK_PLUGIN,
            "tests/test_plugin.py": _HOOK_TEST,
        },
    ),
    "minimal": Template(
        "Минимальный плагин exteraGram (catalib)",
        {
            "src/core.py": _MIN_CORE,
            "src/plugin.py": _MIN_PLUGIN,
            "tests/test_plugin.py": _MIN_TEST,
        },
    ),
    "menu": Template(
        "Плагин exteraGram с пунктом меню (catalib)",
        {
            "src/actions.py": _MENU_ACTIONS,
            "src/plugin.py": _MENU_PLUGIN,
            "tests/test_plugin.py": _MENU_TEST,
        },
    ),
    "settings": Template(
        "Плагин exteraGram с настройками (catalib)",
        {
            "src/format.py": _SET_FORMAT,
            "src/plugin.py": _SET_PLUGIN,
            "tests/test_plugin.py": _SET_TEST,
        },
    ),
}
