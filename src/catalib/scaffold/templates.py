"""Шаблоны файлов для ``catalib init``.

Подстановки выполняются через :meth:`str.format` с ключами ``plugin_id``,
``name``, ``author``. Сгенерированный проект собирается ``catalib build`` и
демонстрирует модульность (точка входа + относительный импорт подмодуля).
"""

from __future__ import annotations

MANIFEST = """\
[plugin]
id = "{plugin_id}"
name = "{name}"
version = "1.0.0"
description = "Плагин exteraGram, собранный catalib"
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

GREETING = '''\
"""Пример доменного модуля без зависимостей от Android (тестируется офлайн)."""

from __future__ import annotations


def build_greeting(name: str) -> str:
    """Вернуть приветствие для имени.

    :param name: имя; пустое имя заменяется на «мир».
    """
    cleaned = name.strip() or "мир"
    return f"Привет, {cleaned}!"
'''

PLUGIN = '''\
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

TEST = '''\
"""Офлайн-тест доменной логики плагина (без Android/SDK)."""

from src.greeting import build_greeting


def test_build_greeting_uses_name() -> None:
    assert build_greeting("Алиса") == "Привет, Алиса!"


def test_build_greeting_defaults_when_empty() -> None:
    assert build_greeting("   ") == "Привет, мир!"
'''

PYPROJECT = """\
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
"""

GITIGNORE = "dist/\n__pycache__/\n*.pyc\n.venv/\n"

README = """\
# {name}

Модульный плагин exteraGram. Сборка в один файл:

```
catalib build
```

Результат: `dist/{plugin_id}.py` — устанавливается в exteraGram как обычный
плагин. Разработка с автодеплоем на устройство:

```
catalib watch --deploy
```
"""
