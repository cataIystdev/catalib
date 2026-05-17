# Рецепты

Готовые шаблоны частых задач. Все используют только публичный API
`catalib.support` и стандартную библиотеку.

## Команда, переписывающая сообщение

```python
from catalib.support import CatalibPlugin, HookResult, HookStrategy, hook


class P(CatalibPlugin):
    @hook.send_message
    def on_send_message_hook(self, account, params):
        msg = getattr(params, "message", None)
        if not isinstance(msg, str) or not msg.startswith(".up "):
            return HookResult()
        params.message = msg[len(".up "):].upper()
        return HookResult(strategy=HookStrategy.MODIFY, params=params)
```

## Отмена отправки по условию

```python
@hook.send_message
def on_send_message_hook(self, account, params):
    msg = getattr(params, "message", None)
    if isinstance(msg, str) and msg.strip() == ".cancel":
        return HookResult(strategy=HookStrategy.CANCEL)
    return HookResult()
```

## Персистентное хранилище (JSON)

```python
import json, os
from catalib.support import CatalibPlugin, get_plugins_dir


class P(CatalibPlugin):
    def on_load(self):
        self._dir = os.path.join(get_plugins_dir(), "myplugin_data")
        os.makedirs(self._dir, exist_ok=True)
        self._path = os.path.join(self._dir, "state.json")

    def _load(self):
        if not os.path.isfile(self._path):
            return {}
        try:
            with open(self._path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def _save(self, data):
        tmp = self._path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, self._path)
```

Совет: вынесите это в модуль `storage/` и тестируйте офлайн с `tmp_path`.

## Настройка, влияющая на поведение

```python
from catalib.support import CatalibPlugin, HookResult, HookStrategy, hook, settings


class P(CatalibPlugin):
    def settings(self):
        return [
            settings.header("Эхо"),
            settings.text_input("prefix", "Префикс", default="."),
        ]

    @hook.send_message
    def on_send_message_hook(self, account, params):
        msg = getattr(params, "message", None)
        prefix = self.get_setting("prefix", ".")
        if not isinstance(msg, str) or not msg.startswith(prefix + "echo "):
            return HookResult()
        params.message = msg[len(prefix) + 5:]
        return HookResult(strategy=HookStrategy.MODIFY, params=params)
```

## Пункт меню с доступом к контексту

```python
from catalib.support import CatalibPlugin, log, menu_item


class P(CatalibPlugin):
    @menu_item("ID чата", menu_type="CHAT_ACTION_MENU")
    def chat_id(self, context: dict):
        log(f"chatId={context.get('chatId')} account={context.get('account')}")
```

## Тяжёлая операция без блокировки UI

Хуки выполняются не в UI-потоке. Не делайте сетевых/тяжёлых вызовов
синхронно в обработчике, который должен быстро вернуть `HookResult`.
Вычислите быстро, верните результат; для отложенного обновления UI
используйте `run_on_ui_thread`:

```python
from catalib.support import run_on_ui_thread

def _later(view):
    run_on_ui_thread(lambda: view.setText("готово"))
```

Не используйте `subprocess`/`os.fork`/`platform.platform()` — в Chaquopy
это роняет процесс. Для идентификации среды — `os.uname()`/`sys.platform`.

## Разбор команды с аргументами

Простой парсер «префикс + имя + аргументы»:

```python
def parse(message: str, prefix: str):
    if not message.startswith(prefix):
        return None
    body = message[len(prefix):].strip()
    if not body:
        return None
    parts = body.split(maxsplit=1)
    return parts[0].lower(), (parts[1].strip() if len(parts) > 1 else "")
```

Полная реализация с реестром команд — в [exteraToolbox](toolbox.md).
