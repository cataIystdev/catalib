# Компонент: deploy

Назначение: доставка собранного плагина на устройство. Канал — встроенный
dev server exteraGram (TCP 42690); прямой `adb push` без root запрещён
(ADR-0004).

## Состав

- `adb.py` — `list_devices`, `forward_dev_server`/`remove_forward`,
  команды списком аргументов без shell; `AdbError`.
- `devserver.py` — `DevServerClient` (JSON-протокол, сопоставление по `#`,
  устойчивая склейка буфера): `ping`, `get_plugins`, `write_plugin`,
  `reload_plugin`, `set_plugin_enabled`, `delete_plugin`; `DevServerError`.
- `reload.py` — `deploy_plugin`: проброс порта, запись, перезагрузка,
  включение при первом деплое; `DeployReport`.

## Связи

- Зависит от: стандартная библиотека (`subprocess`, `socket`, `json`),
  внешний бинарь `adb`.
- Используется: `cli.watch` (флаг `--deploy`).
- Связанные документы:
  [ADR-0004](../architecture/decisions/ADR-0004-deploy-cherez-dev-server.md),
  [guides/device-workflow](../guides/device-workflow.md).
