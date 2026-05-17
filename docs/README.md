# Документация catalib

Точка входа в документацию проекта. Документация ведётся на русском языке
параллельно с разработкой и зеркалит структуру кода.

## Оглавление

- Архитектура
  - [Обзор системы](architecture/overview.md)
  - Решения (ADR)
    - [ADR-0001: Модульный монолит](architecture/decisions/ADR-0001-modulnyj-monolit.md)
    - [ADR-0002: Bundler + sys.meta_path](architecture/decisions/ADR-0002-bundler-meta-path.md)
    - [ADR-0003: Мини-фреймворк поверх SDK](architecture/decisions/ADR-0003-mini-frejmvork-poverh-sdk.md)
    - [ADR-0004: Деплой через dev server](architecture/decisions/ADR-0004-deploy-cherez-dev-server.md)
  - [Эмпирические данные](architecture/evidence/)
- Планы
  - [Implementation Plan](plans/implementation-plan.md)
  - [Task Plan](plans/task-plan.md)
- [Глоссарий](glossary.md)
- [Компоненты](components/README.md) — документация по слоям, в каждом
  документе раздел «Связи».
- Руководства
  - [Рабочий сценарий на устройстве](guides/device-workflow.md)

## Принцип

Документация — часть единицы работы, а не отдельная фаза. Любое изменение
публичного поведения сопровождается обновлением соответствующих документов и
раздела `CHANGELOG.md` в том же коммите.
