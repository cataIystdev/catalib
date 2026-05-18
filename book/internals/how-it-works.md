# Как работает сборка

Этот раздел — для тех, кто хочет понять механизм или дорабатывать catalib.

## Конвейер сборки

`catalib build` выполняет (модуль `catalib.cli._pipeline`):

1. **manifest** — `load_manifest`: читает `catalib.toml` (`tomllib`),
   строит `PluginManifest`/`BuildConfig`, строго проверяет ключи/типы.
2. **discovery** — `discover_sources`: обходит `src`, строит `SourceTree`
   (относительные имена, признак пакета, защита от path traversal,
   требование `__init__.py`).
3. **requirements** — `merge_requirements`: сливает `__requirements__`
   манифеста и модулей, отклоняет бинарные пакеты.
4. **sourcemap** — `build_source_map`: вычисляет origin каждого модуля
   для `linecache`/трейсбеков.
5. **vendor** — `vendored_modules`/`all_vendor_modules`: исходники
   `catalib.support` (+минимальный `catalib`) из установленного пакета.
6. **treeshake** — `plan_vendor` (модуль `bundler/treeshake.py`):
   помодульный отбор используемых плагином модулей `catalib` и их
   транзитивных зависимостей; для `catalib.support` — генерация
   урезанного `__init__`. Режим из `[build] vendor` (`auto`/`full`);
   при неоднозначных импортах — полный вендоринг с предупреждением.
   См. ADR-0008.
7. **compiler** — `compile_plugin`: собирает выходной текст из модулей
   плагина и отобранного `catalib`, проверяет синтаксис и AST-валидность
   метаданных.
8. запись `<plugin_id>.py` и `<plugin_id>.plugin`.

## Структура выходного файла

```python
# 1. Метаданные — строковыми литералами
__id__ = "my_plugin"
__name__ = "My Plugin"
__version__ = "1.0.0"
__app_version__ = ">=12.5.1"
__requirements__ = ["tinydb"]

# 2. Встроенный загрузчик (исходник catalib.runtime.bootstrap)
class _CatalibLoader: ...
class _CatalibFinder: ...
def catalib_install(module_name, module_globals, sources, entry_fullname): ...

# 3. Таблица исходников: fullname -> (исходник, пакет?, origin)
_CATALIB_SOURCES = {
    "my_plugin":        ("<src/__init__.py>", True,  "<my_plugin>/__init__.py"),
    "my_plugin.plugin": ("<src/plugin.py>",   False, "<my_plugin>/plugin.py"),
    "catalib":          ("...",               True,  "<catalib-vendor>/catalib/__init__.py"),
    "catalib.support":  ("...",               True,  "<catalib-vendor>/..."),
    "catalib.support.plugin": ("...",         False, "<catalib-vendor>/..."),
    ...
}
_CATALIB_ENTRY = "my_plugin.plugin"

# 4. Активация
catalib_install("my_plugin", globals(), _CATALIB_SOURCES, _CATALIB_ENTRY)
```

## Встроенный загрузчик

`catalib_install` (исполняется когда exteraGram импортирует
`<plugin_id>`):

1. Снимает прежние finder'ы этого плагина из `sys.meta_path` и удаляет
   его подмодули `<plugin_id>.*` из `sys.modules` (безопасный reload).
2. Вычищает устаревшие **вендоренные** `catalib.*` из `sys.modules`
   (по пометке `__catalib_vendored__` или синтетическому origin `"<...>"`).
   Настоящий host-`catalib` (в тестах) не трогается.
3. Вставляет `_CatalibFinder` в `sys.meta_path[0]`.
4. Восстанавливает идентичность модуля: литерал `__name__ = "<display>"`
   из метаданных перетёр имя модуля — оно возвращается к `<plugin_id>`,
   модуль делается пакетом (`__path__`, `__package__`, согласование
   `__spec__`).
5. Если есть `src/__init__.py` — исполняет его как тело верхнего модуля.
6. Импортирует точку входа; её относительные импорты резолвятся через
   finder.
7. Находит класс плагина (определённый в модуле точки входа, подкласс
   `BasePlugin`/`CatalibPlugin`) и поднимает его в пространство имён
   верхнего модуля, чтобы exteraGram его нашёл.

`_CatalibLoader.exec_module` регистрирует исходник в `linecache` под
origin и компилирует с этим origin — поэтому трейсбеки указывают на
исходные файлы (`File "<my_plugin>/core/parser.py", line 12`).

## Изоляция и устойчивость к reload

- Модули плагина живут под уникальным пакетом `<plugin_id>` (он уникален
  в exteraGram).
- Вендоренные `catalib.*` имеют общее имя между плагинами/деплоями. Без
  очистки копия из прошлого деплоя оставалась бы в общем `sys.modules` и
  затеняла свежую (наблюдалось как падение старым API). Поэтому шаг 2
  обязателен и распознаёт даже модули, собранные прежними версиями
  загрузчика.

## Почему именно `sys.meta_path`

Подтверждено на устройстве: Chaquopy сам использует кастомные finder'ы
(`AssetFinder`), пользовательский finder в `sys.meta_path` работает,
пакеты и относительные импорты резолвятся, трейсбеки через `linecache`
указывают на исходники. Подход не зависит от того, лежит ли каталог
плагинов в `sys.path` (работает в памяти). Эмпирические данные —
`docs/architecture/evidence/T-011-probe-result.json` в репозитории.

## Граница встраиваемой среды

`catalib.runtime` и `catalib.support` зависят только от стандартной
библиотеки и SDK. Это проверяется отдельным тестом (`runtime`/`support`
не импортируют `typer`/`watchfiles`/инструментальные подпакеты). Нарушение
границы валит тест.
