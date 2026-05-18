# Хуки

Хуки перехватывают события exteraGram. catalib даёт декларативную разметку:
помеченный метод регистрируется автоматически в `on_plugin_load` — это
исключает типичную ошибку «хук определён, но не зарегистрирован».

```python
from catalib.support import hook
```

## Хук исходящих сообщений

```python
from catalib.support import CatalibPlugin, HookResult, HookStrategy, hook


class P(CatalibPlugin):
    @hook.send_message
    def on_send_message_hook(self, account, params):
        ...
```

Применяется и с приоритетом:

```python
    @hook.send_message(priority=5)
    def on_send_message_hook(self, account, params):
        ...
```

`@hook.send_message` приводит к автоматическому вызову
`self.add_on_send_message_hook(priority)` в `on_plugin_load`. Имя метода
может быть любым — важна пометка декоратором (но `on_send_message_hook` —
конвенциональное имя обработчика SDK).

### Сигнатура и контракт

`on_send_message_hook(self, account: int, params)` вызывается для каждого
исходящего сообщения. Вернуть нужно `HookResult`:

- `HookResult()` — ничего не делать, пропустить дальше (стратегия `DEFAULT`);
- `HookResult(strategy=HookStrategy.MODIFY, params=params)` — отправить
  изменённое сообщение;
- `HookResult(strategy=HookStrategy.CANCEL)` — отменить отправку.

### Безопасный шаблон

`params.message` может отсутствовать или быть не строкой — **всегда
проверяйте**:

```python
@hook.send_message
def on_send_message_hook(self, account, params):
    message = getattr(params, "message", None)
    if not isinstance(message, str):
        return HookResult()
    if not message.startswith(".cmd"):
        return HookResult()
    params.message = message.upper()
    return HookResult(strategy=HookStrategy.MODIFY, params=params)
```

## Хук сетевого запроса

```python
class P(CatalibPlugin):
    @hook.request("messages.sendMessage", priority=0)
    def on_request(self, *args):
        ...
```

`@hook.request("<имя запроса>")` приводит к `self.add_hook("<имя запроса>")`
в `on_plugin_load`. Имя запроса обязано быть непустой строкой (иначе
`ValueError` ещё на этапе импорта).

### Карта хук-методов запроса/апдейта

SDK по зарегистрированному имени вызывает фиксированные методы
`pre_request_hook`/`post_request_hook`/`on_update_hook`/
`on_updates_hook`. catalib даёт декларативные декораторы и сам
диспетчеризует вызов в помеченный метод (как `on_app_event`):

```python
class P(CatalibPlugin):
    @hook.pre_request("messages.sendMessage", priority=3)
    def before(self, request_name, account, request):
        return HookResult(strategy=HookStrategy.CANCEL)

    @hook.post_request("messages.sendMessage")
    def after(self, request_name, account, response, error):
        ...

    @hook.on_update("updateNewMessage")
    def upd(self, update_name, account, update):
        ...

    @hook.on_updates("Updates", match_substring=True)
    def upds(self, container_name, account, updates):
        ...
```

Каждый декоратор: `@hook.<kind>(name, *, priority=0,
match_substring=False)`. Обработчик может вернуть `HookResult` или
`None` (тогда — `DEFAULT`). `match_substring=True` матчит имя как
подстроку. Прямое переопределение `pre_request_hook` и т. п. в подклассе
по-прежнему перекрывает диспетчер.

## События приложения

```python
from catalib.support import AppEvent

class P(CatalibPlugin):
    @hook.app_event(AppEvent.START, AppEvent.RESUME)
    def on_fg(self, event_type):
        ...

    @hook.app_event           # без аргументов — все события
    def on_any(self, event_type):
        ...
```

`AppEvent`: `START`, `STOP`, `PAUSE`, `RESUME`. Диспетчер
`CatalibPlugin.on_app_event` вызывает подходящие методы; прямое
переопределение `on_app_event` по-прежнему работает.

## Xposed-хуки

Перехват метода/конструктора Java одним декоратором; авто-регистрация в
`on_plugin_load` и авто-`unhook` в `on_plugin_unload`:

```python
from catalib.support import xposed

class P(CatalibPlugin):
    @xposed("org.telegram.ui.ChatActivity", "onBackPressed", phase="before")
    def on_back(self, param):
        ...
```

`xposed(class_fqn, method_name="", *, phase="after", priority=10,
is_constructor=False, arg_types=None, filters=())`; `phase` ∈
`before`/`after`/`replace`. Фильтры — `HookFilter`/`hook_filters`.
Ошибки рефлексии логируются и не роняют загрузку. Если нужен **подкласс**
Java (а не перехват) — см. [Class proxy](class-proxy.md).

## HookResult и HookStrategy

Импортируются из `catalib.support`:

```python
from catalib.support import HookResult, HookStrategy
```

| `HookStrategy` | Значение | Смысл |
|----------------|----------|-------|
| `DEFAULT` | `"DEFAULT"` | не вмешиваться |
| `CANCEL` | `"CANCEL"` | отменить действие |
| `MODIFY` | `"MODIFY"` | применить изменённые `params` |
| `MODIFY_FINAL` | `"MODIFY_FINAL"` | изменить и не передавать дальше |

Вне exteraGram (офлайн-тесты) это совместимые заглушки — логику хука можно
тестировать на обычном Python.

## Важные ограничения

- **Хуки выполняются не в UI-потоке.** Для изменения UI используйте
  `run_on_ui_thread` (см. [Доступ к SDK](sdk-access.md)).
- **Никаких подпроцессов.** В Chaquopy `fork/exec` недоступны; вызов
  `subprocess`/`platform.platform()` роняет процесс. Используйте
  `os.uname()`/`sys.platform`, если нужна идентификация среды.
- **Тяжёлые/сетевые операции** не блокируйте в обработчике — выносите в
  очередь и возвращайте результат через UI-поток.

## Несколько хуков

В одном классе можно объявить сколько угодно помеченных методов — все
зарегистрируются автоматически:

```python
class P(CatalibPlugin):
    @hook.send_message
    def outgoing(self, account, params): ...

    @hook.request("messages.sendMessage")
    def on_send(self, *a): ...
```
