# Публичный API

Импортируется внутри плагина: `from catalib.support import ...`. Этот
пакет вшивается в собранный файл.

## `CatalibPlugin`

Базовый класс плагина (наследник `base_plugin.BasePlugin`).

| Член | Описание |
|------|----------|
| `on_plugin_load()` | реализован catalib: регистрирует хуки/меню, затем зовёт `on_load()`. **Не переопределять.** |
| `on_load()` | переопределяемый хук инициализации (по умолчанию пуст). |
| `settings() -> list` | переопределяемый: вернуть список `SettingItem`. |
| `create_settings() -> list` | реализован catalib: строит элементы SDK из `settings()`. |
| `get_setting(key, default=None)` | значение настройки (метод SDK). |
| `set_setting(key, value)` | сохранить настройку (метод SDK). |
| `__catalib_plugin__ = True` | маркер для обнаружения класса загрузчиком. |

## Декораторы хуков — `hook`

| Форма | Эффект при загрузке |
|-------|---------------------|
| `@hook.send_message` / `(priority=N)` | `add_on_send_message_hook(N)` (откат без приоритета) |
| `@hook.request(name, priority=0)` | `add_hook(name)` |
| `@hook.pre_request(name, *, priority=0, match_substring=False)` | `add_hook(...)` + диспетчер `pre_request_hook` |
| `@hook.post_request(name, ...)` | `add_hook(...)` + диспетчер `post_request_hook` |
| `@hook.on_update(name, ...)` | `add_hook(...)` + диспетчер `on_update_hook` |
| `@hook.on_updates(name, ...)` | `add_hook(...)` + диспетчер `on_updates_hook` |
| `@hook.app_event(*events)` / `@hook.app_event` | диспетчер `on_app_event` (без аргументов — все события) |
| `@xposed(class_fqn, method_name="", *, phase="after", priority=10, is_constructor=False, arg_types=None, filters=())` | авто `hook_method`/`unhook_method` |

`hook.request`/`pre_request`/… требуют непустой `name` (иначе
`ValueError` при импорте). Обработчики: `send_message` —
`(self, account, params) -> HookResult`; `pre_request` —
`(self, request_name, account, request)`; `post_request` —
`(..., response, error)`; `on_update` — `(update_name, account,
update)`; `on_updates` — `(container_name, account, updates)`;
`app_event` — `(self, event_type)`; `xposed` — `(self, param)`.
`AppEvent` ∈ `{START, STOP, PAUSE, RESUME}`. Class proxy — см.
[Class proxy](../guide/class-proxy.md).

## Меню — `menu_item`

```python
menu_item(text, menu_type="DRAWER_MENU", icon="", subtext="",
          *, item_id="", condition=None, priority=0)
```

`menu_type` ∈ `{"DRAWER_MENU", "MESSAGE_CONTEXT_MENU",
"CHAT_ACTION_MENU", "PROFILE_ACTION_MENU"}`. Обработчик:
`(self, context: dict) -> None`. Неверный `menu_type` или пустой `text` —
`ValueError` при импорте. `item_id`/`condition`/`priority` —
keyword-only, в `MenuItemData` только когда заданы.

## Настройки — `settings`

| Функция | Сигнатура |
|---------|-----------|
| `settings.header` | `header(text)` |
| `settings.divider` | `divider(text="")` |
| `settings.switch` | `switch(key, text, default=False, subtext="", *, icon, on_change, on_long_click, link_alias)` |
| `settings.selector` | `selector(key, text, default, items, *, icon, on_change, on_long_click, link_alias)` |
| `settings.text_input` | `text_input(key, text, default="", subtext="", icon="", *, on_change, on_long_click, link_alias)` |
| `settings.edit_text` | `edit_text(key, hint, default="", *, multiline, max_length, mask, on_change)` |
| `settings.text` | `text(text, subtext="", icon="", *, accent, red, on_click, on_long_click, create_sub_fragment, link_alias)` |
| `settings.custom` | `custom(*, item, view, factory, factory_args, on_click, on_long_click, create_sub_fragment, link_alias)` |
| `settings.simple_setting_factory` | `(create_view, bind_view, *, is_clickable, is_shadow, create_item, on_click, on_long_click, attached_view, equals, content_equals)` |

Возвращают `SettingItem`; `SettingItem.build()` даёт объект `ui.settings`
на устройстве либо сам элемент офлайн. Новые keyword-параметры попадают в
SDK только когда заданы (обратная совместимость).

## Модули-области

`from catalib.support import <модуль>` или
`from catalib.support.<модуль> import ...`:

| Модуль | Покрывает |
|--------|-----------|
| `android` | `R`, `OnClickListener`, `OnLongClickListener`, `copy_to_clipboard`, `log`, `run_on_ui_thread` |
| `client` | очереди (`PLUGINS_QUEUE`…), `run_on_queue`, `send_*`, `edit_message`, 17 геттеров контроллеров, `NotificationCenterDelegate` |
| `files` | `get_*_dir` (7), `ensure_dir_exists`, `list_dir`, `write_file`, `read_file`, `delete_file` |
| `reflection` | `find_class`, `get/set_private_field`, `get/set_static_private_field` |
| `formatting` | `parse_text`, `TLEntityType`, `RawEntity` |
| `dialogs` | `AlertDialogBuilder` |
| `bulletins` | `BulletinHelper` |
| `proxy` | class proxy (см. [Class proxy](../guide/class-proxy.md)) |
| `classes` | FQN-константы (`CHAT_ACTIVITY`…), `COMMON_CLASSES` |

## Результаты хуков

| Имя | Описание |
|-----|----------|
| `HookResult(strategy=None, params=None, request=None, response=None, update=None, updates=None)` | результат хука со всеми полями SDK; `strategy` по умолчанию `DEFAULT` |
| `HookStrategy.DEFAULT` | не вмешиваться |
| `HookStrategy.CANCEL` | отменить |
| `HookStrategy.MODIFY` | применить изменённые `params` |
| `HookStrategy.MODIFY_FINAL` | изменить и не передавать дальше |

## Утилиты SDK

| Имя | Описание |
|-----|----------|
| `SDK_AVAILABLE: bool` | `True` только внутри exteraGram |
| `log(message: str)` | запись в лог приложения (офлайн — no-op) |
| `run_on_ui_thread(callback, delay=0)` | выполнить в UI-потоке (офлайн — сразу) |
| `get_plugins_dir() -> str` | каталог плагинов (офлайн — временный) |
| `find_class(name) -> Class \| None` | поиск Java-класса |
| `AppEvent` | `START`/`STOP`/`PAUSE`/`RESUME` |
| `HookFilter`, `hook_filters`, `MethodHook`, `MethodReplacement`, `BaseHook` | Xposed-примитивы |

Низкоуровнево доступны также `catalib.support.sdk.BasePlugin`,
`MenuItemData`, `MenuItemType` — для случаев, когда нужен прямой API SDK.
Офлайн-заглушка `BasePlugin` повторяет полный интерфейс
(`export_settings`/`import_settings`/`remove_menu_item`/
`hook_all_methods`/…), поэтому логику плагина можно тестировать без
устройства.

## Контракт совместимости

Публичный API `catalib.support` версионируется вместе с пакетом. Внутри
одного релиза catalib он стабилен. Вендоринг означает, что плагин несёт
свою копию `catalib.support` — пересоберите плагин новой версией catalib,
чтобы получить исправления.
