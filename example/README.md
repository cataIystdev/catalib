# exteraToolbox — пример многофайлового плагина для catalib

Намеренно глубокий модульный плагин: показывает, что catalib собирает дерево
из множества файлов, папок и подпапок в один `<plugin_id>.py`.

## Структура

```
src/
├── plugin.py                 точка входа (ToolboxPlugin)
├── config.py
├── core/                     command, parser, registry, errors
├── safe_eval/                безопасный калькулятор (AST)
├── domain/                   note, dice
├── storage/                  paths, json_store, notes_repository
├── services/                 notes_service, stats_service
├── util/                     formatting, textwrap_helpers
├── ui/                       settings_schema
└── commands/                 calc, stats_cmd
    ├── text/                 b64, регистр, реверс
    ├── random/               кубики, монета, пароль
    ├── timeinfo/             now, in
    ├── ids/                  uuid, hash
    └── notes/                note add/list/del/clear
```

Команды используют относительные импорты через несколько уровней пакетов и
вендоренный `catalib.support` — это и есть проверка сборки.

## Команды (префикс по умолчанию `.`, меняется в настройках)

`.help` `.calc <выраж>` `.b64 enc|dec <данные>` `.upper/.lower/.title <текст>`
`.rev <текст>` `.roll NdM[+K]` `.coin` `.pw [длина]` `.now` `.in <N> <s|m|h|d>`
`.uuid` `.hash <алго> <текст>` `.note add|list|del|clear` `.stats`

## Сборка

```
catalib build --project example          # -> example/dist/toolbox.py
```

## Офлайн-тесты доменной логики

```
cd example && pytest
```
