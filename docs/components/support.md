# Компонент: support

Назначение: мини-фреймворк, импортируемый плагином. Встраивается в собранный
файл (вендоринг), исполняется под Chaquopy. Слой не скрывает SDK — он убирает
шаблон и даёт офлайн-тестируемость; паритет с публичным SDK exteraGram
зафиксирован в ADR-0006. Все расширения 0.2.0 строго аддитивны.

## Состав

- `sdk.py` — безопасные импорты SDK (`base_plugin`, `android_utils`, ...) с
  заглушками для офлайн-тестов; флаг `SDK_AVAILABLE`; `log`,
  `run_on_ui_thread`, `get_plugins_dir`. Расширенный SDK (независимые
  `try/except`, не влияют на `SDK_AVAILABLE`): `AppEvent`, `MethodHook`,
  `MethodReplacement`, `BaseHook`, `HookFilter`, `hook_filters`,
  `find_class`. Стаб `BasePlugin` имеет `hook_method`/`unhook_method` для
  офлайн-тестов Xposed.
- `hooks.py` — декоратор `hook`: `hook.send_message`, `hook.request(name)`,
  `hook.app_event(*events)` (без аргументов — все события); `HookSpec`,
  `AppEventSpec`.
- `settings.py` — полный паритет с `ui.settings`: `header`, `divider`,
  `switch`, `selector`, `text_input` (Input), `edit_text` (EditText),
  `text` (кликабельный Text), `custom`. Параметры SDK: `on_click`,
  `on_change`, `icon`, `accent`, `red`, `link_alias`, `create_sub_fragment`,
  `multiline`, `max_length`, `mask`. Прежние позиционные сигнатуры
  `header`/`switch`/`text_input`/`text` неизменны (новые параметры —
  keyword-only, в `params` попадают только когда заданы). Ленивое
  построение `ui.settings` на устройстве, офлайн — сам `SettingItem`.
- `xposed.py` — декларативные Xposed-хуки: декоратор `xposed(class_fqn,
  method_name, *, phase, priority, is_constructor, arg_types, filters)`;
  `XposedSpec`; помощники `register_xposed`/`unregister_xposed` и мост
  `MethodHook`/`MethodReplacement`. Ошибки рефлексии логируются и не роняют
  загрузку (pitfall #7).
- `plugin.py` — `CatalibPlugin`: автоматическая регистрация помеченных
  хуков, пунктов меню и Xposed-хуков в `on_plugin_load`; диспетчер
  `on_app_event`; авто-`unhook` и `on_unload` в `on_plugin_unload`;
  `create_settings`; маркер `__catalib_plugin__` для загрузчика; декоратор
  `menu_item` с полями `item_id`/`condition`/`priority`.
- `__init__.py` — публичный API (новые имена добавлены, прежние сохранены).

Граница среды: импортирует только стандартную библиотеку, SDK и встраиваемый
периметр `catalib` (проверяется тестом границы). Новый модуль `xposed.py`
включён в вендоринг (`bundler.vendor`).

## Контракт публичного API

`from catalib.support import` — `CatalibPlugin`, `hook`, `menu_item`,
`settings`, `xposed`, `SettingItem`, `HookSpec`, `AppEventSpec`,
`XposedSpec`, `MenuSpec`, `HookResult`, `HookStrategy`, `SDK_AVAILABLE`,
`AppEvent`, `HookFilter`, `hook_filters`, `MethodHook`, `MethodReplacement`,
`BaseHook`, `find_class`, `log`, `run_on_ui_thread`, `get_plugins_dir`.

## Связи

- Зависит от: стандартная библиотека, SDK exteraGram.
- Используется: код плагина; вендорится `bundler.vendor` (включая
  `xposed.py`).
- Связанные документы:
  [ADR-0003](../architecture/decisions/ADR-0003-mini-frejmvork-poverh-sdk.md),
  [ADR-0006](../architecture/decisions/ADR-0006-paritet-support-sdk.md),
  [bundler](bundler.md).
