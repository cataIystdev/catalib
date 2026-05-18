# Changelog

Все значимые изменения в этом проекте будут документироваться в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Добавлено

- Типизация (PEP 561): маркер `catalib/py.typed` и классификатор
  `Typing :: Typed` — аннотации `catalib.support` теперь видны
  Pyright/Pylance/mypy без действий.
- Поставка type-стабов публичного SDK exteraGram (`.pyi` для
  `base_plugin`/`client_utils`/`file_utils`/`android_utils`/`hook_utils`/
  `ui.settings`/`ui.alert`/`ui.bulletin`/`extera_utils.text_formatting`/
  `extera_utils.classes`) и команда `catalib stubs [--dir] [--force]`,
  устанавливающая их в `typings/` проекта (автодополнение прямого
  доступа к SDK). См. ADR-0009.
- Команда `catalib doctor [--project] [--serial] [--port]` —
  префлайт-диагностика окружения: Python ≥ 3.11, наличие `adb`,
  подключённое устройство, доступность dev server (через временный
  `adb forward`, снимается сразу) и валидность `catalib.toml`. Код
  возврата `1` только при критических проблемах (старый Python, битый
  манифест); отсутствие устройства/dev server — предупреждение, сборке
  не мешает.
- `python -m catalib` — добавлен `__main__`, делегирует в ту же точку
  входа, что и консольная команда (раньше падал с
  «No module named catalib.__main__», хотя был задокументирован).
- Шаблоны `catalib init --template, -t`: `hook` (по умолчанию, как
  раньше — байт-в-байт), `minimal` (голый каркас), `menu` (пункт
  контекстного меню), `settings` (поведение от настроек). Каждый
  собирается без правок и несёт офлайн-тест.
- Модуль `catalib.testing` — помощники офлайн-тестов плагинов
  (`make_params`, `make_context`, `PluginHarness`/`load_plugin`):
  вызвать хук/пункт меню как в SDK без устройства. Pytest-нейтрален, не
  вендорится в собранный плагин. Тесты шаблонов `menu`/`settings` уже на
  нём (руководство — раздел «Тестирование плагина» в book).
- Команда `catalib logs [--project] [--serial] [--lines] [--clear]
  [--all] [--filter]` — logcat устройства, отфильтрованный по
  `plugin_id` из манифеста (плагины логируют как `[plugin_id] ...`).
  Команда и логика совпадают с инструментом MCP `adb_get_logs`. Чистая
  фильтрация — `catalib.devicelogs.filter_log` (офлайн-тестируемо),
  чтение — `catalib.deploy.adb.logcat`. См. ADR-0010.

### Решено

- Модуль SDK `intents` решено **не оборачивать**: его нет статически в
  APK (даётся приложением в рантайме), он вне выверенного справочника
  SDK, поверхность не зафиксирована. Обёртка по догадке противоречит
  ADR-0006/0007 и не тестируема офлайн. Прямой импорт на устройстве
  по-прежнему доступен (book — «Доступ к SDK», escape-hatch с
  оговоркой). См. ADR-0010.

## [0.3.1] - 2026-05-18

### Добавлено

- Помодульный отбор вендоренного `catalib` (tree-shaking): в собранный
  плагин вшиваются только модули `catalib.*`, которые плагин реально
  импортирует, плюс их транзитивные зависимости; для `catalib.support`
  генерируется урезанный `__init__`, не тянущий отсечённые подмодули.
  На реальных плагинах (`example`, backrooms) собранный файл стал
  существенно легче (≈ −34% объёма `catalib`-части). Анализ статический
  (AST), консервативный: при неоднозначных импортах (весь пакет как
  объект, `import *`, несопоставимое имя, `catalib` вне `catalib.support`)
  выполняется полный вендоринг с предупреждением. См. ADR-0008.
- Опция манифеста `[build] vendor` (`"auto"` по умолчанию | `"full"`):
  страховка для плагинов с динамическими импортами SDK.
- `catalib build` печатает сводку вендоринга: отобрано/отсечено модулей
  либо «полный» с причинами.

### Изменено

- По умолчанию `catalib build`/`watch` вшивают только используемые
  модули `catalib` (раньше — весь `catalib.support`). Поведение
  совместимо: при любой неоднозначности — полный вендоринг. Чтобы
  принудительно вернуть прежнее поведение: `[build] vendor = "full"`.

## [0.3.0] - 2026-05-18

### Добавлено

- Проверка обновлений: `catalib.check_for_updates()` безопасно
  сверяется с PyPI и, если есть более новая версия, CLI печатает одну
  строку-уведомление в stderr. Не чаще раза в сутки (кеш
  `~/.cache/catalib/update-check.json`), любая ошибка/таймаут — молча,
  отключение `CATALIB_NO_UPDATE_CHECK=1`. Не выполняется при импорте
  пакета (вендоренный `catalib` в плагине не делает сетевых запросов).
- Публичный API `catalib.support` ре-экспортирует весь новый паритетный
  surface (модули `android`/`client`/`files`/`reflection`/`formatting`/
  `dialogs`/`bulletins`/`proxy`/`classes` плюс поднятые наверх
  `AlertDialogBuilder`/`BulletinHelper`/`parse_text` и весь class proxy),
  сохраняя все прежние имена. Новые модули добавлены в вендоринг — иначе
  собранные плагины не загрузились бы (закреплено интеграционным тестом
  сборки). См. ADR-0007.
- Декларативная карта хук-методов запроса/апдейта: декораторы
  `@hook.pre_request`/`@hook.post_request`/`@hook.on_update`/
  `@hook.on_updates(name, *, priority=, match_substring=)` и диспетчеры
  `CatalibPlugin.pre_request_hook`/`post_request_hook`/`on_update_hook`/
  `on_updates_hook` (авто-`add_hook`, маршрутизация по имени/подстроке,
  возврат `HookResult`). `@hook.request` сохранён как прежде; прямое
  переопределение хук-методов в подклассе по-прежнему перекрывает
  диспетчер. См. ADR-0007.
- `catalib.support.settings` доведён до полного паритета: параметр
  `on_long_click` у `switch`/`selector`/`text_input`/`text`/`custom`,
  `link_alias` у `selector`, `create_sub_fragment`/`link_alias` у
  `custom`; добавлена обёртка `simple_setting_factory(...)`
  (`ui.settings.SimpleSettingFactory`). Строго аддитивно — прежние
  вызовы формируют тот же `params`. См. ADR-0007.
- Модуль `catalib.support.classes` — FQN-константы общих Java-классов
  Telegram/Android (`CHAT_ACTIVITY`, `MESSAGE_OBJECT`, `TLRPC`, …) и
  словарь `COMMON_CLASSES`. Чистые данные, доступны всегда.
  См. ADR-0007.
- Модуль `catalib.support.proxy` — управляемый class proxy
  (`extera_utils.classes`): `Base`, `java_subclass`, `joverride`,
  `joverload`, `jmethod`, `jMVELmethod`, `jMVELoverride`, `jclassbuilder`,
  `jfield`, `jgetmethod`, `jsetmethod`, `jconstructor`, `jpreconstructor`,
  `PyObj`, `J`/`JavaHelper`/`ClassHelper`. На устройстве полностью
  ре-экспортируется настоящий DSL; офлайн — функциональные заглушки
  (декларации классов-проксей импортируются и инстанцируются, `jfield`
  как атрибут с default, порядок pre/init/ctor/post соблюдён,
  `J`/`PyObj` проксируют объект). См. ADR-0007.
- Модуль `catalib.support.bulletins` — обёртка `ui.bulletin.BulletinHelper`
  со всеми `show_*` (`show_info`/`show_error`/`show_success`/`show_simple`/
  `show_two_line`/`show_with_button`/`show_undo`/`show_copied_to_clipboard`/
  `show_link_copied`/`show_file_saved_to_gallery`/
  `show_file_saved_to_downloads`) и `DURATION_*`. Офлайн — рекордер.
  См. ADR-0007.
- Модуль `catalib.support.dialogs` — обёртка `ui.alert.AlertDialogBuilder`
  с полным набором методов (заголовок/сообщение/пункты/кнопки/слушатели/
  внешний вид/прогресс/жизненный цикл) и константами (`ALERT_TYPE_*`,
  `BUTTON_*`). Офлайн — chainable-рекордер. См. ADR-0007.
- Модуль `catalib.support.formatting` — обёртки
  `extera_utils.text_formatting`: `parse_text(text, parse_mode='HTML',
  is_caption=False)`, `TLEntityType`, `RawEntity`. Офлайн — честный
  контракт словаря с исходным текстом и пустыми сущностями.
  См. ADR-0007.
- Модуль `catalib.support.client` — обёртки `client_utils`: 8 констант
  очередей, `run_on_queue` (офлайн — синхронный вызов),
  `get_queue_by_name`, `send_request`, `send_text`/`send_photo`/
  `send_document`/`send_video`/`send_audio`/`send_message`,
  `edit_message` (валидирует `parse_mode`), 17 геттеров контроллеров,
  `NotificationCenterDelegate`. См. ADR-0007.
- Модуль `catalib.support.reflection` — обёртки `hook_utils`:
  `find_class` (ре-экспорт), `get_private_field`, `set_private_field`,
  `get_static_private_field`, `set_static_private_field`. Офлайн —
  безопасный контракт (геттеры → `None`, сеттеры → `False`).
  См. ADR-0007.
- Модуль `catalib.support.files` — обёртки `file_utils`: 7 getter'ов
  каталогов (`get_plugins_dir`/`get_cache_dir`/…/`get_documents_dir`),
  `ensure_dir_exists`, `list_dir`, `write_file`, `read_file`,
  `delete_file`. Офлайн — настоящая работа с файловой системой во
  временных каталогах (полные реализации, контракты SDK сохранены).
  См. ADR-0007.
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

### Изменено

- Комментарий-шапка собранного файла теперь содержит ссылку на
  репозиторий: «Файл сгенерирован catalib
  (https://github.com/cataIystdev/catalib) из модульного дерева
  исходников».

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
