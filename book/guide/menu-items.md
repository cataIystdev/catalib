# Пункты меню

Метод можно объявить обработчиком пункта меню декоратором `menu_item`.
catalib зарегистрирует его автоматически в `on_plugin_load`, построив
корректный `MenuItemData` SDK.

```python
from catalib.support import CatalibPlugin, menu_item


class P(CatalibPlugin):
    @menu_item("Моё действие", menu_type="DRAWER_MENU", icon="msg_info")
    def my_action(self, context: dict) -> None:
        ...
```

## Сигнатура декоратора

```python
menu_item(text, menu_type="DRAWER_MENU", icon="", subtext="",
          *, item_id="", condition=None, priority=0)
```

| Параметр | Назначение |
|----------|------------|
| `text` | подпись пункта меню (непустая строка) |
| `menu_type` | тип меню, одно из значений ниже |
| `icon` | необязательное имя drawable-иконки (например `msg_info`) |
| `subtext` | необязательная подпись под текстом |
| `item_id` | необязательный стабильный идентификатор пункта |
| `condition` | необязательный предикат показа пункта |
| `priority` | необязательный приоритет (0 — не передаётся в SDK) |

Новые поля (`item_id`/`condition`/`priority`) — keyword-only и
пробрасываются в `MenuItemData` только когда заданы: прежний вызов
формирует тот же `MenuItemData`, что и раньше.

Неверный `menu_type` или пустой `text` приводят к `ValueError` ещё на
этапе импорта плагина — ошибка обнаруживается сразу.

## Типы меню

| `menu_type` | Где появляется |
|-------------|----------------|
| `DRAWER_MENU` | боковое меню (гамбургер) |
| `MESSAGE_CONTEXT_MENU` | долгое нажатие на сообщение |
| `CHAT_ACTION_MENU` | меню действий в чате |
| `PROFILE_ACTION_MENU` | меню действий в профиле/канале |

## Обработчик принимает `context`

**Метод-обработчик обязан принимать аргумент `context: dict`** — это
требование SDK. Через него доступны:

```
account, context, fragment, dialog_id,
user, userId, userFull,
chat, chatId, chatFull,
encryptedChat, message, groupedMessages, botInfo
```

Пример:

```python
@menu_item("Сохранить чат", menu_type="CHAT_ACTION_MENU")
def save_chat(self, context: dict) -> None:
    chat_id = context.get("chatId")
    account = context.get("account")
    ...
```

## Как это собирается

`menu_item` сохраняет на методе спецификацию `MenuSpec`. В
`on_plugin_load` catalib вызывает:

```python
self.add_menu_item(MenuItemData(
    menu_type=MenuItemType.DRAWER_MENU,
    text="Моё действие",
    on_click=self.my_action,
    icon="msg_info",
))
```

То есть используется реальный API SDK: `MenuItemData(menu_type=...,
text=..., on_click=...)`, а не угаданные аргументы. Это исправление
конкретной ошибки `TypeError: MenuItemData.__init__() got an unexpected
keyword argument 'item_type'` (см. [Подводные камни](../troubleshooting.md)).

## Несколько пунктов

Объявляйте сколько нужно — все зарегистрируются:

```python
class P(CatalibPlugin):
    @menu_item("Справка", menu_type="DRAWER_MENU", icon="msg_info")
    def help(self, context): ...

    @menu_item("Скопировать ID", menu_type="MESSAGE_CONTEXT_MENU")
    def copy_id(self, context): ...
```
