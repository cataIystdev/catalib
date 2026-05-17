# Рабочий сценарий на устройстве

Доставка плагина на устройство идёт через встроенный dev server exteraGram
(TCP 42690). Прямой `adb push` в приватный каталог плагинов без root
запрещён (см. [ADR-0004](../architecture/decisions/ADR-0004-deploy-cherez-dev-server.md)).

## Предусловия

1. Устройство подключено по ADB (`adb devices` показывает его).
2. exteraGram запущен.
3. В exteraGram включён движок плагинов и режим разработчика (dev server
   слушает порт 42690).

## Разработка с автодеплоем

```
catalib init "My Plugin" --id my_plugin
cd my_plugin
catalib watch --deploy            # пересборка и деплой при каждом изменении
```

`watch --deploy` собирает плагин, пробрасывает порт через `adb forward`,
по JSON-протоколу dev server выполняет `write_plugin`, `reload_plugin` и
при первом деплое `set_plugin_enabled(true)`.

Несколько устройств — флаг `--serial <серийный>`. Локальный порт проброса —
`--port`.

## Разовая сборка

```
catalib build                     # dist/<plugin_id>.py
```

Файл `dist/<plugin_id>.py` устанавливается конечным пользователем штатно
(импорт одного `.py` в exteraGram).

## Диагностика

- «не удалось подключиться к dev server» — приложение не запущено или не
  включён режим разработчика.
- Свежий плагин зарегистрирован, но `enabled: false` — деплой без `--deploy`
  не включает плагин; `watch --deploy` включает автоматически.
- Логи плагина могут не доходить до `adb logcat` в некоторых сборках;
  для диагностики пишите данные в каталог плагина и снимайте файлом.

## Связи

- Зависит от: компонент [deploy](../components/deploy.md).
- Используется: команда `catalib watch`.
- Связанные документы:
  [ADR-0004](../architecture/decisions/ADR-0004-deploy-cherez-dev-server.md),
  [обзор](../architecture/overview.md).
