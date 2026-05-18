# Доступ к SDK

`catalib.support.sdk` — единственная точка адаптации к SDK exteraGram.
Внутри exteraGram используются настоящие классы и функции; вне приложения
(офлайн-тесты) — совместимые заглушки. Это убирает россыпь `try/except` по
плагину и даёт офлайн-тестируемость.

`catalib.support` даёт **полный паритет со всем публичным SDK
exteraGram** (ADR-0006, ADR-0007): на устройстве — настоящий SDK, офлайн —
функциональные заглушки с тем же контрактом для тестов. Источник истины
по сигнатурам — официальная документация
<https://plugins.exteragram.app/docs>.

## Что экспортирует `catalib.support`

```python
from catalib.support import (
    CatalibPlugin,        # базовый класс плагина
    HookResult, HookStrategy,
    SettingItem, settings,
    hook, menu_item, xposed,
    SDK_AVAILABLE,        # bool: исполняемся ли внутри exteraGram
    log,                  # запись в лог приложения
    run_on_ui_thread,     # выполнить callback в UI-потоке
    get_plugins_dir,      # путь к каталогу плагинов
    AppEvent,             # события жизненного цикла приложения
    HookFilter, hook_filters, MethodHook, MethodReplacement, BaseHook,
    find_class,           # поиск Java-класса
    # модули-области:
    android, client, files, reflection, formatting,
    dialogs, bulletins, proxy, classes,
    # часто используемое, поднятое наверх:
    AlertDialogBuilder, BulletinHelper, parse_text,
    # class proxy (см. отдельную страницу):
    Base, java_subclass, joverride, joverload, jmethod, jfield,
    jconstructor, jpreconstructor, jMVELmethod, jMVELoverride,
    jgetmethod, jsetmethod, jclassbuilder, PyObj, J,
)
```

## Полный паритет: модули-области

Каждый модуль доступен и как `from catalib.support import <модуль>`, и
как `from catalib.support.<модуль> import ...`.

### `android` — `android_utils`

```python
from catalib.support import android

android.copy_to_clipboard("https://t.me/exteraPlugins")
btn.setOnClickListener(android.OnClickListener(lambda v: ...))
btn.setOnLongClickListener(android.OnLongClickListener(lambda v: True))
some_view.post(android.R(lambda: ...))   # java.lang.Runnable
android.run_on_ui_thread(lambda: ..., delay=500)
```

### `client` — `client_utils`

```python
from catalib.support import client

client.run_on_queue(do_work, client.PLUGINS_QUEUE)   # вне UI-потока
client.send_text(peer_id, "привет", parse_mode="HTML")
client.send_photo(peer_id, "/path.jpg", caption="c", high_quality=True)
mc = client.get_messages_controller()                # 17 геттеров
client.send_request(req, lambda resp, err: ...)
```

Очереди: `STAGE_QUEUE`, `GLOBAL_QUEUE`, `CACHE_CLEAR_QUEUE`,
`SEARCH_QUEUE`, `PHONE_BOOK_QUEUE`, `THEME_QUEUE`,
`EXTERNAL_NETWORK_QUEUE`, `PLUGINS_QUEUE`. Подписка на уведомления —
подкласс `client.NotificationCenterDelegate`. `edit_message` бросает
`ValueError` при неподдерживаемом `parse_mode`.

### `files` — `file_utils`

```python
from catalib.support import files
import os

base = os.path.join(files.get_plugins_dir(), "my_data")
files.ensure_dir_exists(base)                 # создаёт и родителей
files.write_file(os.path.join(base, "x.json"), "{}")
data = files.read_file(os.path.join(base, "x.json"))   # None при ошибке
files.list_dir(base, recursive=True, extensions=[".json"])
files.delete_file(...)                         # bool
```

Каталоги: `get_plugins_dir`/`get_cache_dir`/`get_files_dir`/
`get_images_dir`/`get_videos_dir`/`get_audios_dir`/`get_documents_dir`.
`write_file` **не создаёт** родительские каталоги — вызовите
`ensure_dir_exists` заранее. Офлайн — настоящая работа с ФС во временных
каталогах.

### `reflection` — `hook_utils`

```python
from catalib.support import reflection

cls = reflection.find_class("org.telegram.messenger.BuildVars")
val = reflection.get_private_field(obj, "verified")
ok = reflection.set_static_private_field(cls, "DEBUG_VERSION", True)
```

Рефлексия хрупка — геттеры офлайн/при ошибке возвращают `None`, сеттеры
`False`; всегда проверяйте результат.

### `formatting` — `extera_utils.text_formatting`

```python
from catalib.support import parse_text

res = parse_text("<b>жирный</b>", parse_mode="HTML")
# {"message": "...", "entities": [...]}; is_caption=True → ключ "caption"
```

### `dialogs` — `AlertDialogBuilder`

```python
from catalib.support import AlertDialogBuilder

(AlertDialogBuilder(context)
    .set_title("Заголовок").set_message("Текст")
    .set_positive_button("OK", lambda b, w: b.dismiss())
    .create().show())
```

Константы `ALERT_TYPE_MESSAGE`/`ALERT_TYPE_LOADING`/`ALERT_TYPE_SPINNER`,
`BUTTON_POSITIVE`/`BUTTON_NEGATIVE`.

### `bulletins` — `BulletinHelper`

```python
from catalib.support import BulletinHelper

BulletinHelper.show_success("Готово")
BulletinHelper.show_with_button("Текст", icon, "Открыть", on_click)
```

Все `show_*` (info/error/success/simple/two_line/with_button/undo/
copied_to_clipboard/link_copied/file_saved_to_gallery/
file_saved_to_downloads) и `DURATION_*`.

### `classes` — FQN-константы

```python
from catalib.support import classes, find_class

activity = find_class(classes.CHAT_ACTIVITY)
```

### `proxy` — class proxy

Создание Java-подклассов из Python — см. отдельную страницу
[Class proxy](class-proxy.md).

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

Слой тонкий и ничего не запрещает. Почти весь публичный SDK уже покрыт
обёртками выше (с офлайн-тестируемостью) — используйте их. Если нужен
класс SDK, которого всё же нет в обёртках, импортируйте его напрямую с
защитой:

```python
try:
    from some_sdk_module import SomeClass
except Exception:
    SomeClass = None
```

Но если такой код должен тестироваться офлайн — изолируйте его за
небольшим адаптером и подменяйте в тестах, как это делает
`catalib.support`.

## Граница встраиваемой среды

`catalib.support` и `catalib.runtime` вшиваются в собранный плагин и
исполняются под Chaquopy. Они зависят **только** от стандартной библиотеки
и SDK exteraGram. Не импортируйте в код плагина инструментальные пакеты
(`typer`, `watchfiles`, подпакеты `catalib.cli/bundler/...`) — на
устройстве их нет.
