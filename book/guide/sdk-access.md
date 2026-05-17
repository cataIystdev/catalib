# Доступ к SDK

`catalib.support.sdk` — единственная точка адаптации к SDK exteraGram.
Внутри exteraGram используются настоящие классы и функции; вне приложения
(офлайн-тесты) — совместимые заглушки. Это убирает россыпь `try/except` по
плагину и даёт офлайн-тестируемость.

## Что экспортирует `catalib.support`

```python
from catalib.support import (
    CatalibPlugin,        # базовый класс плагина
    HookResult, HookStrategy,
    SettingItem, settings,
    hook, menu_item,
    SDK_AVAILABLE,        # bool: исполняемся ли внутри exteraGram
    log,                  # запись в лог приложения
    run_on_ui_thread,     # выполнить callback в UI-потоке
    get_plugins_dir,      # путь к каталогу плагинов
)
```

Нижележащий модуль `catalib.support.sdk` дополнительно даёт `BasePlugin`,
`MenuItemData`, `MenuItemType`.

## Признак среды

```python
from catalib.support import SDK_AVAILABLE

if SDK_AVAILABLE:
    ...  # код, требующий настоящий SDK
```

`SDK_AVAILABLE` равен `True` только на устройстве. В тестах он `False`, и
заглушки имитируют интерфейс SDK (фиксируют регистрацию хуков/меню,
хранят настройки в памяти).

## Логирование

```python
from catalib.support import log

log("[my_plugin] что-то произошло")
```

На устройстве пишет в лог приложения; офлайн — безопасный no-op.
Учтите: в некоторых сборках логи плагина **не доходят до `adb logcat`** —
для диагностики надёжнее писать в файл в каталоге плагина (см.
[Подводные камни](../troubleshooting.md)).

## UI-поток

Хуки выполняются не в UI-потоке. Любое изменение View — через
`run_on_ui_thread`:

```python
from catalib.support import run_on_ui_thread

run_on_ui_thread(lambda: my_view.setText("готово"))
```

Офлайн callback выполняется немедленно (для тестов).

## Файловая система

```python
from catalib.support import get_plugins_dir
import os

base = os.path.join(get_plugins_dir(), "my_plugin_data")
os.makedirs(base, exist_ok=True)
```

Каталог плагинов доступен для записи (подтверждено на устройстве). Офлайн
`get_plugins_dir()` возвращает временный каталог. Не забывайте создавать
родительские каталоги перед записью файла.

## Доступ к «сырому» SDK

Слой тонкий и ничего не запрещает. Если нужен класс SDK, которого нет в
обёртках, импортируйте его напрямую с защитой:

```python
try:
    from client_utils import send_message
except Exception:
    send_message = None
```

Но если такой код должен тестироваться офлайн — лучше изолировать его за
небольшим адаптером и подменять в тестах, как это делает `catalib.support`.

## Граница встраиваемой среды

`catalib.support` и `catalib.runtime` вшиваются в собранный плагин и
исполняются под Chaquopy. Они зависят **только** от стандартной библиотеки
и SDK exteraGram. Не импортируйте в код плагина инструментальные пакеты
(`typer`, `watchfiles`, подпакеты `catalib.cli/bundler/...`) — на
устройстве их нет.
