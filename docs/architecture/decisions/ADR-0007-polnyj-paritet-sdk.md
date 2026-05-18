# ADR-0007: Полный паритет support со всем публичным SDK и декомпозиция на модули

- **Статус:** принято
- **Дата:** 2026-05-18

## Контекст

ADR-0006 (0.2.0) довёл до паритета настройки, меню, события приложения и
Xposed-хуки. Но `catalib.support` по-прежнему покрывал не весь публичный
SDK exteraGram. По официальной документации
(<https://plugins.exteragram.app/docs>) вне обёрток оставались целые
области: `android_utils` (`R`/listeners/`copy_to_clipboard`),
`client_utils` (очереди, запросы, отправка, контроллеры,
`NotificationCenterDelegate`), `file_utils`, `hook_utils` (поля через
рефлексию), `extera_utils.text_formatting`, `ui.alert.AlertDialogBuilder`,
`ui.bulletin.BulletinHelper`, а также — отмеченный пользователем как
приоритетный — управляемый class proxy `extera_utils.classes`
(`Base`/`java_subclass`/`joverride`/`jfield`/… `J`/`PyObj`). Не хватало и
полноты в уже покрытых областях: все поля `HookResult`, методы
офлайн-`BasePlugin` (`export_settings`/`hook_all_methods`/…),
`on_long_click`/`SimpleSettingFactory` в настройках, карта
`pre_request`/`post_request`/`on_update`/`on_updates` хуков.

Требование пользователя: реализовать **всё**, без заглушек-пустышек и
TODO для функционала; источник истины — официальная документация и
веб-поиск (MCP вторичен, бывает неполным). Жёсткое ограничение прежнее:
не сломать ничего (слой вендорится в сторонние плагины), всё аддитивно.

`sdk.py` при добавлении всего этого превысил бы разумный размер модуля
(правило 3.1).

## Решение

Довести `catalib.support` до полного паритета со всем публичным SDK и
**декомпозировать слой на модули по областям SDK**:

- `sdk` — ядро (`BasePlugin`, `HookResult` со всеми полями, `HookStrategy`,
  `MenuItemData`, `MenuItemType`, `AppEvent`, `MethodHook`/
  `MethodReplacement`/`BaseHook`, `HookFilter`, `hook_filters`,
  `find_class`, `log`, `run_on_ui_thread(delay=)`, `get_plugins_dir`,
  `SDK_AVAILABLE`); офлайн-`BasePlugin` доведён до полного интерфейса;
- `android` — `android_utils`; `client` — `client_utils`;
  `files` — `file_utils`; `reflection` — `hook_utils`;
  `formatting` — `extera_utils.text_formatting`;
  `dialogs` — `ui.alert.AlertDialogBuilder`;
  `bulletins` — `ui.bulletin.BulletinHelper`;
  `proxy` — `extera_utils.classes` (class proxy);
  `classes` — FQN-константы общих Java-классов;
- `settings` доведён до паритета (`on_long_click`, `link_alias` у
  Selector, `create_sub_fragment`/`link_alias` у Custom,
  `simple_setting_factory`);
- `hooks`/`plugin` — декларативная карта `pre_request`/`post_request`/
  `on_update`/`on_updates` с диспетчеризацией.

Принцип каждого модуля прежний (ADR-0003): на устройстве — настоящий SDK
через безопасный импорт; офлайн — **функциональная** заглушка с тем же
контрактом (не TODO: `files` реально работает с ФС; `client.run_on_queue`
офлайн исполняет callable; `proxy` инстанцирует классы-прокси и
соблюдает порядок конструкторов; рекордеры `dialogs`/`bulletins`
фиксируют вызовы). Граница офлайн-режима, где Java объективно недоступен
(реальный разбор сущностей `parse_text`, super-вызовы Java-родителя),
документирована как контракт, а не как недоделка.

Новые модули добавлены в вендоринг (`bundler.vendor`) — иначе собранные
плагины не загрузятся; инвариант закреплён интеграционным тестом сборки.
Публичный API (`support/__init__.py`) ре-экспортирует весь surface
аддитивно (модули-области + поднятые наверх частые имена + весь class
proxy); прежние имена и сигнатуры сохранены.

## Альтернативы

- **Оставить один большой `sdk.py`.** Отвергнуто: нарушает правило 3.1
  (один модуль — одна ответственность, ~300–400 строк), плохо
  навигируется и тестируется.
- **Только тонкие ре-экспорты без офлайн-поведения.** Отвергнуто:
  потеряли бы офлайн-тестируемость плагинов — ключевую ценность ADR-0003;
  и противоречит требованию «всё полностью работающее».
- **Богатый catalib-DSL поверх каждой области.** Отвергнуто как
  избыточное и рискованное: задача — полное и точное покрытие SDK;
  декларативный сахар оставлен там, где он уже оправдан (хуки, меню,
  Xposed, app-event, settings).
- **Доверять MCP как источнику сигнатур.** Отвергнуто по прямому
  указанию: первичны официальная документация и веб-поиск.

## Последствия

- Плагин может пользоваться **любым** документированным API exteraGram
  через `catalib.support`, с офлайн-тестируемостью; class proxy доступен
  прямо из фасада.
- Слой стал из 5 модулей — 14; навигация и тесты по областям; ADR
  фиксирует декомпозицию.
- Публичная поверхность только расширяется; вендоренные копии в старых
  плагинах (например backrooms) продолжают работать — подтверждено
  пересборкой backrooms и его тестами.

## Связи

- Зависит от: ADR-0003 (мини-фреймворк поверх SDK), ADR-0006 (паритет
  0.2.0), ADR-0001 (граница сред).
- Используется: `catalib.support.*` (14 модулей), `bundler.vendor`;
  `docs/plans/implementation-plan.md` (раздел 2, структура, 16),
  `docs/plans/task-plan.md` (T-200..T-217),
  `docs/components/support.md`.
- Связанные документы: [support](../../components/support.md),
  [ADR-0006](ADR-0006-paritet-support-sdk.md),
  [ADR-0003](ADR-0003-mini-frejmvork-poverh-sdk.md). Внешняя ссылка:
  официальная документация SDK <https://plugins.exteragram.app/docs>.
