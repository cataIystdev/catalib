# Тестирование плагина

Доменную логику (чистые модули) тестируют обычным `pytest` без всякой
обвязки — см. [структуру проекта](project-structure.md). Но проверить сам
**хук** или **пункт меню** мешает шаблон: нужно собрать фейковые
`params`/`context`, создать плагин и вызвать `on_plugin_load()` (иначе
обработчики не зарегистрированы). Модуль `catalib.testing` это убирает.

`catalib.testing` — часть catalib (dev-зависимость), **не вендорится** в
собранный плагин: он импортируется только тестами, никогда из
`src/plugin.py`. Работает офлайн, без устройства и SDK (на
[офлайн-заглушках](sdk-access.md)).

## Быстрый старт

```python
from catalib.testing import PluginHarness

from src.plugin import MyPlugin


def test_hello_command():
    h = PluginHarness.load(MyPlugin)
    result = h.send_message(".hello Алиса")
    assert result.strategy == "MODIFY"
    assert h.last_params.message == "Привет, Алиса!"
```

`PluginHarness.load` создаёт плагин, проставляет настройки и вызывает
`on_plugin_load()` — хуки и пункты меню регистрируются ровно как на
устройстве.

## API

### `make_params(message="", **fields)`

Объект `params` хука исходящих сообщений (атрибуты можно читать и
присваивать — хук обычно пишет `params.message`).

```python
from catalib.testing import make_params

p = make_params("текст", peer=123)
p.message = "другое"
```

### `make_context(**fields)`

`context`-словарь обработчика пункта меню (SDK передаёт `context: dict`).

### `PluginHarness`

| Член | Назначение |
|------|------------|
| `PluginHarness.load(cls, *, settings=None, **kw)` | создать плагин, применить настройки, вызвать `on_plugin_load()` |
| `.send_message(msg="", *, account=0, **fields)` | вызвать `@hook.send_message`-обработчик(и); вернуть `HookResult` |
| `.click_menu(text=None, *, context=None, **ctx)` | вызвать обработчик пункта меню (как клик) |
| `.last_params` | `params` последнего `send_message` (проверить мутацию) |
| `.menu_items` | зарегистрированные пункты меню (объекты `MenuItemData`) |
| `.registered_hooks` | зафиксированные регистрации хуков |
| `.logged` | строки, переданные `self.log(...)` плагином |

`load_plugin(...)` — краткий синоним `PluginHarness.load(...)`.

## Настройки в тесте

`settings=` (словарь) и/или именованные аргументы проставляются перед
`on_plugin_load()`, так что хук видит их через `self.get_setting(...)`:

```python
h = PluginHarness.load(MyPlugin, settings={"enabled": True}, prefix="tag")
assert h.send_message("hi").strategy == "MODIFY"
assert h.last_params.message == "[tag] hi"
```

## Пункт меню

```python
h = PluginHarness.load(MenuPlugin)
assert [i.text for i in h.menu_items] == ["Крикнуть"]
h.click_menu("Крикнуть", message="ого")     # ctx -> make_context(message="ого")
assert h.logged == ["shout -> ОГО"]
```

Обработчик логирует через `self.log(...)` — офлайн строки попадают в
`h.logged`, на устройстве идут в лог приложения.

## Откуда взять пример

`catalib init --template menu` и `--template settings` создают проекты, в
которых `tests/test_plugin.py` уже написан на `catalib.testing` — рабочая
отправная точка. См. [catalib init](../cli/init.md).
