# Класс плагина

Точка входа плагина — подкласс `CatalibPlugin` из `catalib.support`.

```python
from catalib.support import CatalibPlugin


class MyPlugin(CatalibPlugin):
    def on_load(self) -> None:
        ...
```

`CatalibPlugin` — это `base_plugin.BasePlugin` exteraGram плюс тонкий слой:
автоматическая регистрация объявленных хуков и пунктов меню, типизированные
настройки. Прямой доступ к API SDK не ограничивается.

## Жизненный цикл

exteraGram создаёт экземпляр плагина и вызывает `on_plugin_load()`.
`CatalibPlugin.on_plugin_load()` делает следующее **за вас**:

1. регистрирует все методы, помеченные [`@hook.*`](hooks.md);
2. регистрирует все [пункты меню](menu-items.md);
3. регистрирует [Xposed-хуки](hooks.md#xposed-хуки) `@xposed`;
4. вызывает `self.on_load()` — ваш хук инициализации.

Поэтому **не переопределяйте `on_plugin_load`** — переопределяйте
`on_load`:

```python
class MyPlugin(CatalibPlugin):
    def on_load(self) -> None:
        # ваша инициализация: открыть хранилище, построить сервисы и т. п.
        self.store = MyStore(self.get_setting("path", "/default"))
```

`CatalibPlugin` также реализует диспетчеры, маршрутизирующие вызовы SDK
в помеченные методы: `on_app_event` (см. `@hook.app_event`),
`pre_request_hook`/`post_request_hook`/`on_update_hook`/
`on_updates_hook` (см. карту хук-методов). Их прямое переопределение в
подклассе по-прежнему работает (перекрывает диспетчер по MRO).

### Выгрузка

`on_plugin_unload()` реализован catalib: снимает зарегистрированные
Xposed-хуки и вызывает `self.on_unload()` — ваш хук очистки. Для кода
выгрузки переопределяйте **`on_unload`** (не `on_plugin_unload`):

```python
class MyPlugin(CatalibPlugin):
    def on_unload(self) -> None:
        self.store.close()
```

Без Xposed-хуков и без `on_unload` выгрузка — no-op (поведение как до
0.2.0, когда `on_plugin_unload` не определялся). Прямое переопределение
`on_plugin_unload` тоже поддерживается.

## Настройки

Метод `settings()` возвращает список элементов настроек; `CatalibPlugin`
сам реализует требуемый SDK `create_settings()`:

```python
from catalib.support import settings

class MyPlugin(CatalibPlugin):
    def settings(self):
        return [
            settings.header("Мой плагин"),
            settings.switch("enabled", "Включено", default=True),
        ]
```

Подробно — [Настройки](settings.md).

## Чтение и запись настроек

Используйте методы SDK `get_setting`/`set_setting`:

```python
prefix = self.get_setting("prefix", ".")
self.set_setting("counter", 1)
```

`get_setting(key, default)` возвращает `default`, если значения нет.

## Минимальный полный плагин

```python
from catalib.support import CatalibPlugin, HookResult, HookStrategy, hook


class EchoPlugin(CatalibPlugin):
    @hook.send_message
    def on_send_message_hook(self, account, params):
        msg = getattr(params, "message", None)
        if not isinstance(msg, str) or not msg.startswith(".echo "):
            return HookResult()
        params.message = msg[len(".echo "):]
        return HookResult(strategy=HookStrategy.MODIFY, params=params)
```

Этого достаточно: хук зарегистрируется автоматически, метаданные придут из
`catalib.toml`.

## Обнаружение класса

catalib находит класс плагина по принципу: класс **определён в модуле
точки входа** и является подклассом `CatalibPlugin`/`BasePlugin`.
`CatalibPlugin` помечен атрибутом `__catalib_plugin__ = True`, что
дополнительно помогает загрузчику. Не определяйте несколько классов
плагина в модуле точки входа — оставьте один; вспомогательные классы
выносите в другие модули.
