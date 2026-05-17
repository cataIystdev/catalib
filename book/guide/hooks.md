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
