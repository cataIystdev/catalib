# Разбор exteraToolbox

В репозитории есть `example/` — намеренно глубокий плагин **exteraToolbox**
(44 модуля), показывающий сборку реального дерева пакетов. Это набор
чат-команд: калькулятор, заметки, генераторы, дата/время.

## Дерево

```
example/
├── catalib.toml
├── pyproject.toml          # офлайн-тесты
├── conftest.py
└── src/
    ├── __init__.py
    ├── plugin.py           # точка входа: хук + меню + настройки
    ├── config.py           # константы
    ├── core/               # command, parser, registry, errors
    ├── safe_eval/          # безопасный калькулятор на AST
    ├── domain/             # note, dice (модели)
    ├── storage/            # paths, json_store, notes_repository
    ├── services/           # notes_service, stats_service
    ├── util/               # formatting, textwrap_helpers
    ├── ui/                 # settings_schema
    └── commands/
        ├── calc.py, stats_cmd.py
        ├── text/           # b64, регистр, реверс
        ├── random/         # кубики, монета, пароль
        ├── timeinfo/       # now, in
        ├── ids/            # uuid, hash
        └── notes/          # note add/list/del/clear
```

Каждый каталог с модулями имеет `__init__.py`. Импорты — относительные
через несколько уровней (`from ..core.errors import CommandError`).

## Слои

- **core** — модель `Command`, разбор сообщения (`parser`), реестр и
  диспетчеризация (`registry`), исключения.
- **safe_eval** — вычисление арифметики через `ast` без `eval`
  (разрешены только числа и операции, степень ограничена).
- **domain** — чистые модели (`Note`, `DiceSpec`) без Android.
- **storage** — `JsonStore` (атомарная запись), `NotesRepository`;
  каталог данных через `catalib.support.get_plugins_dir()`.
- **services** — бизнес-логика (`NotesService`, `StatsService`) с
  человекочитаемыми ответами; час инъектируется для тестируемости.
- **commands** — по команде на модуль, сгруппированы по темам.
- **ui** — схема настроек.
- **plugin.py** — единственный `@hook.send_message`, который парсит
  префикс, диспетчеризует команду через реестр и заменяет сообщение
  результатом; плюс пункт меню и настройки.

## Точка входа (фрагмент)

```python
class ToolboxPlugin(CatalibPlugin):
    def on_load(self):
        base = data_dir()
        self._stats = StatsService(base)
        self._registry = CommandRegistry()
        self._registry.register_all(
            build_commands(CommandContext(
                notes=NotesService(NotesRepository(base)), stats=self._stats))
        )

    @hook.send_message
    def on_send_message_hook(self, account, params):
        message = getattr(params, "message", None)
        if not isinstance(message, str):
            return HookResult()
        parsed = parse(message, self._prefix())
        if parsed is None:
            return HookResult()
        name, args = parsed
        try:
            result = self._registry.dispatch(name, args)
        except UnknownCommandError:
            return HookResult()
        except CommandError as exc:
            result = f"[toolbox] ошибка: {exc}"
        params.message = clamp_result(result)
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    @menu_item("exteraToolbox: справка", menu_type="DRAWER_MENU", icon="msg_info")
    def show_help(self, context: dict):
        log(self._registry.help_text(self._prefix()))
```

## Команды (префикс по умолчанию `.`)

`.help` `.calc <выраж>` `.b64 enc|dec <данные>` `.upper/.lower/.title <текст>`
`.rev <текст>` `.roll NdM[+K]` `.coin` `.pw [длина]` `.now`
`.in <N> <s|m|h|d>` `.uuid` `.hash <алго> <текст>`
`.note add|list|del|clear` `.stats`

Сообщение с командой заменяется результатом (стратегия `MODIFY`).

## Сборка и тесты

```bash
catalib build --project example      # example/dist/toolbox.py + .plugin (44 модуля)
cd example && pytest                 # офлайн-тесты доменной логики
```

Доменная логика (калькулятор, кубики, заметки, реестр, парсер) полностью
покрыта офлайн-тестами без Android — за счёт чистых слоёв и инъекции
времени/каталога.

## Чему учит пример

- Глубокая модульность собирается в один файл без изменения кода.
- Относительные импорты через много уровней работают на устройстве.
- Чистые доменные слои + тонкий `plugin.py` = офлайн-тестируемость.
- Вендоренный `catalib.support` обслуживает `from catalib.support import ...`
  на устройстве, где `catalib` не установлен.
