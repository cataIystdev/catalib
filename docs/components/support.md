# Компонент: support

Назначение: мини-фреймворк, импортируемый плагином. Встраивается в собранный
файл (вендоринг), исполняется под Chaquopy. Слой не скрывает SDK — он убирает
шаблон и даёт офлайн-тестируемость. **Полный паритет со всем публичным SDK
exteraGram** зафиксирован в ADR-0007 (доведение паритета ADR-0006). Все
расширения 0.2.0 и 0.3.0 строго аддитивны.

Принцип каждого модуля: на устройстве — настоящий SDK через безопасный
импорт; офлайн — функциональная заглушка с тем же контрактом для тестов
(не TODO; на устройстве всегда работает настоящий SDK). Источник истины
по сигнатурам — официальная документация <https://plugins.exteragram.app/docs>
и веб-поиск; MCP — вторичная сверка.

## Состав

Слой декомпозирован на модули по областям SDK (ADR-0007):

- `sdk.py` — ядро: `BasePlugin` (офлайн-заглушка с полным интерфейсом:
  `get_setting`/`set_setting(reload_settings=)`/`export_settings`/
  `import_settings`, `add_menu_item`→id/`remove_menu_item`,
  `add_hook(match_substring=)`, `add_on_send_message_hook`,
  `hook_method(before_filters=,after_filters=,before=,after=)`,
  `hook_all_methods`, `hook_all_constructors`, `unhook_method`, `log`),
  `HookResult` (все поля: `strategy`/`request`/`response`/`update`/
  `updates`/`params`), `HookStrategy`, `MenuItemData`, `MenuItemType`,
  `AppEvent`, `MethodHook`/`MethodReplacement`/`BaseHook`, `HookFilter`,
  `hook_filters`, `find_class`, `log`, `run_on_ui_thread(delay=)`,
  `get_plugins_dir`, `SDK_AVAILABLE`. Расширенный SDK импортируется
  независимыми `try/except` (не влияет на `SDK_AVAILABLE`).
- `hooks.py` — декоратор `hook`: `send_message`, `request(name)`,
  `pre_request`/`post_request`/`on_update`/`on_updates(name, *, priority=,
  match_substring=)`, `app_event(*events)`; `HookSpec`, `AppEventSpec`,
  `REQUEST_HOOK_KINDS`.
- `settings.py` — полный паритет `ui.settings`: `header`, `divider`,
  `switch`, `selector`, `text_input` (Input), `edit_text` (EditText),
  `text` (кликабельный Text), `custom`; параметры `on_click`,
  `on_change`, `on_long_click`, `icon`, `accent`, `red`, `link_alias`,
  `create_sub_fragment`, `multiline`, `max_length`, `mask`; обёртка
  `simple_setting_factory` (`SimpleSettingFactory`). Прежние позиционные
  сигнатуры неизменны (новые параметры — keyword-only, в `params` только
  когда заданы).
- `xposed.py` — декларативные Xposed-хуки: `xposed(class_fqn,
  method_name, *, phase, priority, is_constructor, arg_types, filters)`,
  `XposedSpec`, `register_xposed`/`unregister_xposed`. Ошибки рефлексии
  логируются и не роняют загрузку (pitfall #7).
- `android.py` — `android_utils`: `R`, `OnClickListener`,
  `OnLongClickListener`, `copy_to_clipboard`, ре-экспорт `log`/
  `run_on_ui_thread`.
- `client.py` — `client_utils`: 8 констант очередей, `run_on_queue`,
  `get_queue_by_name`, `send_request`, `send_text`/`send_photo`/
  `send_document`/`send_video`/`send_audio`/`send_message`,
  `edit_message` (валидирует `parse_mode`), 17 геттеров контроллеров,
  `NotificationCenterDelegate`.
- `files.py` — `file_utils`: 7 getter'ов каталогов, `ensure_dir_exists`,
  `list_dir`, `write_file`, `read_file`, `delete_file` (офлайн —
  настоящая работа с ФС во временных каталогах).
- `reflection.py` — `hook_utils`: `find_class`, `get_private_field`/
  `set_private_field`, `get_static_private_field`/
  `set_static_private_field`.
- `formatting.py` — `extera_utils.text_formatting`: `parse_text(text,
  parse_mode='HTML', is_caption=False)`, `TLEntityType`, `RawEntity`.
- `dialogs.py` — `ui.alert.AlertDialogBuilder` (полный набор методов и
  констант `ALERT_TYPE_*`/`BUTTON_*`); офлайн — chainable-рекордер.
- `bulletins.py` — `ui.bulletin.BulletinHelper` (все `show_*`,
  `DURATION_*`); офлайн — рекордер.
- `proxy.py` — class proxy `extera_utils.classes`: `Base`,
  `java_subclass`, `joverride`, `joverload`, `jmethod`, `jMVELmethod`,
  `jMVELoverride`, `jclassbuilder`, `jfield`, `jgetmethod`, `jsetmethod`,
  `jconstructor`, `jpreconstructor`, `PyObj`, `J`/`JavaHelper`/
  `ClassHelper`. Офлайн — классы-прокси импортируются и инстанцируются,
  `jfield` — атрибут с default, соблюдён порядок
  `jpreconstructor`→`__init__`→`jconstructor`→`on_post_init`.
- `classes.py` — FQN-константы общих Java-классов (`CHAT_ACTIVITY`,
  `MESSAGE_OBJECT`, `TLRPC`, …) и словарь `COMMON_CLASSES`.
- `plugin.py` — `CatalibPlugin`: авто-регистрация помеченных хуков, меню,
  Xposed в `on_plugin_load`; диспетчеры `on_app_event` и
  `pre_request_hook`/`post_request_hook`/`on_update_hook`/
  `on_updates_hook`; авто-`unhook` и `on_unload` в `on_plugin_unload`;
  `create_settings`; маркер `__catalib_plugin__`; декоратор `menu_item`
  (`item_id`/`condition`/`priority`).
- `__init__.py` — публичный API (все модули-области + поднятые наверх
  частые имена + весь class proxy; прежние имена сохранены).

Граница среды: импортирует только стандартную библиотеку, SDK и
встраиваемый периметр `catalib` (проверяется тестом границы). Все модули
включены в вендоринг (`bundler.vendor`); пропуск модуля ломает загрузку
собранного плагина (закреплено интеграционным тестом сборки).

## Контракт публичного API

`from catalib.support import …` — прежние: `CatalibPlugin`, `hook`,
`menu_item`, `settings`, `xposed`, `SettingItem`, `HookSpec`,
`AppEventSpec`, `XposedSpec`, `MenuSpec`, `HookResult`, `HookStrategy`,
`SDK_AVAILABLE`, `AppEvent`, `HookFilter`, `hook_filters`, `MethodHook`,
`MethodReplacement`, `BaseHook`, `find_class`, `log`, `run_on_ui_thread`,
`get_plugins_dir`. Добавлено в 0.3.0: модули `android`, `client`,
`files`, `reflection`, `formatting`, `dialogs`, `bulletins`, `proxy`,
`classes`; поднятые наверх `AlertDialogBuilder`, `BulletinHelper`,
`parse_text`, `TLEntityType`, `RawEntity`; class proxy `Base`,
`java_subclass`, `joverride`, `joverload`, `jmethod`, `jMVELmethod`,
`jMVELoverride`, `jclassbuilder`, `jfield`, `jgetmethod`, `jsetmethod`,
`jconstructor`, `jpreconstructor`, `PyObj`, `J`, `JavaHelper`,
`ClassHelper`.

## Связи

- Зависит от: стандартная библиотека, SDK exteraGram.
- Используется: код плагина; вендорится `bundler.vendor` (все 14 модулей).
- Связанные документы:
  [ADR-0003](../architecture/decisions/ADR-0003-mini-frejmvork-poverh-sdk.md),
  [ADR-0006](../architecture/decisions/ADR-0006-paritet-support-sdk.md),
  [ADR-0007](../architecture/decisions/ADR-0007-polnyj-paritet-sdk.md),
  [bundler](bundler.md). Внешняя:
  <https://plugins.exteragram.app/docs>.
