# Компонент: support

Назначение: мини-фреймворк, импортируемый плагином. Встраивается в собранный
файл (вендоринг), исполняется под Chaquopy.

## Состав

- `sdk.py` — безопасные импорты SDK (`base_plugin`, `android_utils`, ...) с
  заглушками для офлайн-тестов; флаг `SDK_AVAILABLE`; `log`,
  `run_on_ui_thread`, `get_plugins_dir`.
- `hooks.py` — декоратор `hook` (`hook.send_message`, `hook.request(name)`),
  `HookSpec`.
- `settings.py` — декларативные элементы настроек (`header`, `switch`,
  `text_input`, `text`), ленивое построение `ui.settings` на устройстве.
- `plugin.py` — `CatalibPlugin`: автоматическая регистрация помеченных хуков
  и пунктов меню в `on_plugin_load`, `create_settings`, маркер
  `__catalib_plugin__` для загрузчика; декоратор `menu_item`.
- `__init__.py` — публичный API.

Граница среды: импортирует только стандартную библиотеку, SDK и встраиваемый
периметр `catalib` (проверяется тестом границы).

## Связи

- Зависит от: стандартная библиотека, SDK exteraGram.
- Используется: код плагина; вендорится `bundler.vendor`.
- Связанные документы:
  [ADR-0003](../architecture/decisions/ADR-0003-mini-frejmvork-poverh-sdk.md),
  [bundler](bundler.md).
