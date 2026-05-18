# Changelog

Все значимые изменения в этом проекте будут документироваться в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Добавлено

- Модуль `catalib.support.android` — обёртки `android_utils`: `R`,
  `OnClickListener`, `OnLongClickListener`, `copy_to_clipboard`,
  ре-экспорт `log`/`run_on_ui_thread`. Офлайн-заглушки реально вызывают
  переданный callable. См. ADR-0007.
- Полный паритет встраиваемого слоя `catalib.support` со всем публичным
  SDK exteraGram (по официальной документации). Ядро `support.sdk`:
  `HookResult` со всеми полями SDK (`strategy`, `request`, `response`,
  `update`, `updates`, `params`); офлайн-`BasePlugin` доведён до полного
  интерфейса (`export_settings`, `import_settings`,
  `set_setting(reload_settings=)`, `remove_menu_item`,
  `add_hook(match_substring=)`, `hook_method` с
  `before_filters`/`after_filters`/`before`/`after`, `hook_all_methods`,
  `hook_all_constructors`, `add_menu_item` возвращает идентификатор);
  `run_on_ui_thread(delay=)`. Всё аддитивно — прежние сигнатуры и
  поведение сохранены. См. ADR-0007.

## [0.2.0] - 2026-05-18

### Добавлено

- Публичный API `catalib.support` дополнен новыми именами (`xposed`,
  `AppEvent`, `HookFilter`, `hook_filters`, `MethodHook`,
  `MethodReplacement`, `BaseHook`, `find_class`, `AppEventSpec`,
  `XposedSpec`) с сохранением всех прежних. Обратная совместимость
  поверхности закреплена тестом. См. ADR-0006.
- `catalib.support.settings`: полный паритет с `ui.settings` exteraGram —
  компоненты `divider`, `selector`, `edit_text` (EditText), `custom` и
  расширенные параметры существующих (`switch`/`text_input`/`text`):
  `on_click`, `on_change`, `icon`, `accent`, `red`, `link_alias`,
  `create_sub_fragment`, `multiline`, `max_length`, `mask`. Кликабельная
  строка теперь первоклассна — `settings.text(..., on_click=...)` вместо
  ручного перебора API клика. Расширения строго аддитивны: прежние вызовы
  `header`/`switch`/`text_input`/`text` формируют тот же `params`. См.
  ADR-0006.
- `catalib.support.xposed`: декларативные Xposed-хуки методов Java —
  декоратор `@xposed(class_fqn, method_name, *, phase, priority,
  is_constructor, arg_types, filters)`. `CatalibPlugin` сам разрешает класс
  через `find_class`, строит мост `MethodHook`/`MethodReplacement`,
  регистрирует хук в `on_plugin_load` и снимает его в `on_plugin_unload`;
  `HookFilter` пробрасывается через `hook_filters`. Ошибки рефлексии
  логируются и не роняют загрузку (pitfall #7). Добавлен переопределяемый
  `on_unload`. Прежнее поведение `on_plugin_unload` (его отсутствие)
  сохранено для плагинов без Xposed. Модуль вендорится в собранный плагин.
  См. ADR-0006.
- `catalib.support`: декларативная обработка событий жизненного цикла
  приложения — декоратор `@hook.app_event` (бар-форма — все события; с
  аргументами `AppEvent` — выбранные) и диспетчер `CatalibPlugin.on_app_event`.
  Прямое переопределение `on_app_event` в подклассе сохранено; пустой плагин
  по-прежнему без поведения. См. ADR-0006.
- `catalib.support.menu_item`: необязательные поля пункта меню `item_id`,
  `condition`, `priority` (keyword-only). Пробрасываются в `MenuItemData`
  только когда заданы — прежний вызов формирует тот же `MenuItemData`.
- `catalib.support.sdk`: безопасные импорты и офлайн-заглушки расширенного
  SDK exteraGram — `AppEvent`, `MethodHook`, `MethodReplacement`, `BaseHook`,
  `HookFilter`, `hook_filters`, `find_class`. Импортируются независимо от
  ядра: отсутствие имени на старой сборке SDK не сбрасывает `SDK_AVAILABLE`
  и не подменяет ядро заглушками. Делает Xposed-хуки и события приложения
  офлайн-тестируемыми. См. ADR-0006.
- Полное руководство пользователя в формате GitBook (`book/`,
  `.gitbook.yaml`): установка, быстрый старт, руководство, CLI, деплой,
  внутреннее устройство, примеры, решение проблем, публикация в PyPI и
  настройка GitBook. Опубликовано:
  <https://raito-kyokai.gitbook.io/catalib>.
- Подготовка к публикации в PyPI: расширенные классификаторы и URL
  проекта в `pyproject.toml`, группа зависимостей `publish`
  (`build`, `twine`); пакет проходит `python -m build` и `twine check`.
- `catalib build` дополнительно создаёт идентичную копию собранного файла
  с расширением `.plugin` (`<plugin_id>.plugin`) рядом с `.py`.
- Пример многофайлового плагина `exteraToolbox` в `example/`: глубокое
  дерево (44 модуля, вложенные пакеты, относительные импорты) с набором
  чат-команд; собирается `catalib build` в один файл и покрыт офлайн-тестами.
- Сборка модульного дерева исходников плагина в один самодостаточный
  `<plugin_id>.py`, пригодный для штатной установки в exteraGram
  (команда `catalib build`, флаг `--check`).
- Встроенный загрузчик на `sys.meta_path`: обычные относительные импорты и
  пакеты внутри плагина, трейсбеки указывают на исходные файлы; изоляция
  плагинов и безопасная повторная загрузка. Подтверждено на устройстве.
- Мини-фреймворк `catalib.support`: базовый класс `CatalibPlugin` с
  автоматической регистрацией объявленных хуков и пунктов меню,
  типизированные настройки, безопасные импорты SDK с заглушками для
  офлайн-тестов. Встраивается в собранный файл.
- Шаблон модульного плагина: команда `catalib init`.
- Слежение за исходниками с пересборкой и автодеплоем на устройство через
  dev server exteraGram: команда `catalib watch [--deploy]`.
- Валидация манифеста `catalib.toml` и статическая AST-проверка метаданных
  (литеральность дандеров, совпадение `__id__` с именем файла).

### Изменено

- `watchfiles` больше не обязательная зависимость: вынесен в опциональную
  группу `watch` (`pip install "catalib[watch]"`). Команды `build`, `init`,
  `version` работают без него — важно для установки на телефоне
  (Termux/Pydroid), где Rust-бэкенд `watchfiles` собрать сложно. Команда
  `watch` подключает пакет лениво; при отсутствии — понятная ошибка с
  подсказкой по установке. См. ADR-0005.
- Шаблон `catalib init` больше не задаёт по умолчанию жёсткое
  `sdk_version` (на старых сборках с меньшей версией SDK это блокировало
  установку плагина).

### Исправлено

- Встроенный загрузчик вычищает устаревшие вендоренные модули
  `catalib.*` из общего `sys.modules` при каждой загрузке. Без этого копия
  `catalib.support` из прошлого деплоя/другого плагина оставалась в кеше
  и затеняла свежую (плагин падал старым кодом, например прежним API
  меню). Распознаются и модули, собранные предыдущими версиями загрузчика
  (по синтетическому origin); настоящий host-`catalib` не затрагивается.
- Компилятор больше не эмитит нестандартный дандер `__min_version__`:
  exteraGram показывал на него отдельный экран несовместимости даже при
  совместимой версии приложения. Эмитится только канонический
  `__app_version__`.
- `catalib.support`: пункты меню строятся корректным API SDK
  `MenuItemData(menu_type=MenuItemType.*, text=..., on_click=...)`, где
  обработчик принимает `context: dict`. Раньше использовался
  несуществующий аргумент `item_type`, из-за чего `on_plugin_load` падал
  с `TypeError` при включении плагина с пунктом меню.
