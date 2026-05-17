# Компонент: bundler

Назначение: превращение дерева исходников плагина в один самодостаточный
`<plugin_id>.py`.

## Состав

- `model.py` — `SourceModule`, `SourceTree`, `BundleResult`, `DiscoveryError`.
- `discovery.py` — обход `src`, относительные имена, защита от path traversal,
  требование `__init__.py` для каталогов с модулями.
- `requirements.py` — слияние `__requirements__` манифеста и модулей,
  блок-лист бинарных пакетов (`RequirementsError`).
- `sourcemap.py` — origin модулей для `linecache`/трейсбеков.
- `vendor.py` — встраиваемые модули `catalib.support` (на устройстве `catalib`
  не установлен).
- `compiler.py` — сборка выходного файла: литералы метаданных, встроенный
  загрузчик, таблица исходников, активация; синтаксическая и AST-проверка
  результата (`CompilerError`).

## Связи

- Зависит от: `manifest` (модель, валидация), `runtime` (исходник загрузчика).
- Используется: `cli._pipeline`.
- Связанные документы: [runtime](runtime.md), [manifest](manifest.md),
  [ADR-0002](../architecture/decisions/ADR-0002-bundler-meta-path.md),
  [ADR-0003](../architecture/decisions/ADR-0003-mini-frejmvork-poverh-sdk.md).
