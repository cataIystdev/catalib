# ADR-0004: Деплой на устройство через dev server exteraGram

- **Статус:** принято, эмпирически подтверждено (T-011)
- **Дата:** 2026-05-17

## Контекст

Документация и MCP описывают деплой как `adb push` файла в
`/data/user/0/com.exteragram.messenger/files/plugins/<plugin_id>.py`.
Эмпирически на устройстве NX789J (без root) установлено:

- Прямой `adb push` в приватный каталог приложения → `Permission denied`.
- `run-as` и `/data/local/tmp` недоступны, staging через них невозможен.
- exteraGram содержит встроенный dev server на TCP 42690 (включается режимом
  разработчика). Доставка идёт через него: приложение само пишет файл в свой
  приватный каталог.

Протокол dev server (реверс из `exteragram_utils`, проверен вживую):
сокет TCP, сообщения JSON вида `{"@": action, "#": request_id, ...args}`,
ответы содержат `"#"`. Действия: `ping`, `get_plugins`,
`write_plugin{plugin_id, content}`, `reload_plugin{plugin_id}`,
`start_debugger`/`stop_debugger`, и недокументированные, но рабочие
`set_plugin_enabled{plugin_id, enabled}`, `delete_plugin{plugin_id}`.

Сопутствующие наблюдения:

- Свежезаписанный плагин регистрируется выключенным (`enabled: false`);
  `on_plugin_load` вызывается только у включённого. Для прогона нужен либо
  `set_plugin_enabled true`, либо код на уровне модуля (исполняется при
  импорте движком независимо от состояния включения).
- Логи плагина (SDK `log`, Python stdout) в этой сборке не доходят до
  `adb logcat`. Надёжный канал результата при разработке — файл в общем
  хранилище приложения (`/storage/emulated/0/Android/data/.../files/`),
  забираемый `adb pull`.

## Решение

Модуль `deploy` использует `adb forward tcp:LOCAL tcp:42690` и далее
JSON-протокол dev server поверх локального сокета. Реализуется минимальный
клиент (без внешних зависимостей): `ping`, `get_plugins`, `write_plugin`,
`reload_plugin`, `set_plugin_enabled`, `delete_plugin`. `adb` вызывается
списком аргументов (без shell), `plugin_id` валидируется до использования.
`adb push` как канал доставки не используется.

## Альтернативы

- **`adb push` в каталог плагинов.** Отвергнуто: запрещено без root.
- **`run-as` + копирование.** Отвергнуто: `run-as` на устройстве отсутствует.
- **Зависимость от пакета `exteragram_utils`.** Отвергнуто как обязательная:
  протокол тривиален, лишняя внешняя зависимость не нужна; совместимость с
  его поведением сохраняется.

## Последствия

- Деплой требует включённого режима разработчика в exteraGram и запущенного
  приложения; это документируется в руководстве.
- `catalib watch --deploy` и ручной сценарий строятся на этом клиенте.
- Знание о `set_plugin_enabled`/`delete_plugin` упрощает автоматизацию
  (включение после первого деплоя, чистая переустановка).

## Связи

- Зависит от: ADR-0001, ADR-0002.
- Используется: модуль `deploy`, команды CLI `watch`/`build --deploy`;
  `docs/plans/implementation-plan.md` (разделы 2, 4, 11), `docs/plans/task-plan.md`
  (T-060, T-061).
- Связанные документы: `docs/architecture/evidence/T-011-probe-result.json`.
