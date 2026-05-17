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
| `@hook.send_message` | `add_on_send_message_hook()` |
| `@hook.send_message(priority=N)` | `add_on_send_message_hook(N)` (с откатом без приоритета) |
| `@hook.request(name, priority=0)` | `add_hook(name)` |

`hook.request(name)` требует непустой `name` (иначе `ValueError` при
импорте). Обработчик `send_message`: `(self, account, params) -> HookResult`.

## Меню — `menu_item`

```python
menu_item(text, menu_type="DRAWER_MENU", icon="", subtext="")
```

`menu_type` ∈ `{"DRAWER_MENU", "MESSAGE_CONTEXT_MENU",
"CHAT_ACTION_MENU", "PROFILE_ACTION_MENU"}`. Обработчик:
`(self, context: dict) -> None`. Неверный `menu_type` или пустой `text` —
`ValueError` при импорте.

## Настройки — `settings`

| Функция | Сигнатура |
|---------|-----------|
| `settings.header` | `header(text)` |
| `settings.switch` | `switch(key, text, default=False, subtext="")` |
| `settings.text_input` | `text_input(key, text, default="", subtext="", icon="")` |
| `settings.text` | `text(text, subtext="", icon="")` |

Возвращают `SettingItem`; `SettingItem.build()` даёт объект `ui.settings`
на устройстве либо сам элемент офлайн.

## Результаты хуков

| Имя | Описание |
|-----|----------|
| `HookResult(strategy=None, params=None)` | результат хука; `strategy` по умолчанию `DEFAULT` |
| `HookStrategy.DEFAULT` | не вмешиваться |
| `HookStrategy.CANCEL` | отменить |
| `HookStrategy.MODIFY` | применить изменённые `params` |
| `HookStrategy.MODIFY_FINAL` | изменить и не передавать дальше |

## Утилиты SDK

| Имя | Описание |
|-----|----------|
| `SDK_AVAILABLE: bool` | `True` только внутри exteraGram |
| `log(message: str)` | запись в лог приложения (офлайн — no-op) |
| `run_on_ui_thread(callback)` | выполнить в UI-потоке (офлайн — сразу) |
| `get_plugins_dir() -> str` | каталог плагинов (офлайн — временный) |

Низкоуровнево доступны также `catalib.support.sdk.BasePlugin`,
`MenuItemData`, `MenuItemType` — для случаев, когда нужен прямой API SDK.

## Контракт совместимости

Публичный API `catalib.support` версионируется вместе с пакетом. Внутри
одного релиза catalib он стабилен. Вендоринг означает, что плагин несёт
свою копию `catalib.support` — пересоберите плагин новой версией catalib,
чтобы получить исправления.
