# Типизация и автодополнение

catalib типизирован (PEP 561) и поставляет type-стабы публичного SDK
exteraGram. Это даёт автодополнение и проверку типов в IDE и для
`catalib.support`, и для прямого доступа к SDK.

## `catalib.support` — из коробки

Пакет помечен `py.typed`, аннотации видны Pyright/Pylance/mypy сразу
после `pip install catalib`. Автодополняются `CatalibPlugin`, `hook.*`,
`menu_item`, `settings.*`, `client.*`, `files.*`, `HookResult`,
`HookStrategy` и т. д. — отдельных действий не нужно.

## Стабы SDK — `catalib stubs`

Сами модули SDK (`base_plugin`, `client_utils`, `file_utils`,
`android_utils`, `hook_utils`, `ui.settings`/`ui.alert`/`ui.bulletin`,
`extera_utils.text_formatting`/`extera_utils.classes`) на машине
разработчика не импортируются — IDE их не знает. Установите стабы в
проект:

```bash
cd my_plugin
catalib stubs            # копирует .pyi в ./typings/
```

Опции:

| Опция | По умолчанию | Назначение |
|-------|--------------|------------|
| `--dir`, `-d` | `typings` | каталог для стабов |
| `--force` | выкл. | перезаписать существующие стабы |

После этого автодополняется и прямой доступ к SDK:

```python
from base_plugin import HookResult, HookStrategy   # подсказки из стаба
from client_utils import get_messages_controller, PLUGINS_QUEUE
```

## Настройка IDE

- **VS Code (Pylance) / Pyright** — каталог `typings/` подхватывается
  **автоматически** (стандартный stub path). Ничего настраивать не нужно.
- **mypy** — добавьте в конфиг:

  ```toml
  [tool.mypy]
  mypy_path = "typings"
  ```

## Обновление

Стабы версионируются вместе с catalib. После `pip install -U catalib`
обновите их в проекте:

```bash
catalib stubs --force
```

## Что делать с `Any`

Объекты Java/Android из SDK по своей природе динамические — в стабах и
обёртках они типизированы как `Any` намеренно. Доменную логику плагина
держите в чистых модулях со строгими типами (см.
[структуру проекта](project-structure.md)) — она проверяется и
тестируется без устройства.
