# История изменений

Полная история ведётся в `CHANGELOG.md` в корне репозитория по формату
[Keep a Changelog](https://keepachangelog.com/ru/1.1.0/); проект следует
[Semantic Versioning](https://semver.org/lang/ru/).

Актуальная версия:
[CHANGELOG.md на GitHub](https://github.com/cataIystdev/catalib/blob/main/CHANGELOG.md).

## Заметные вехи

- Сборка модульного дерева в один самодостаточный `<plugin_id>.py`
  (CLI `build`), плюс идентичная копия `<plugin_id>.plugin`.
- Встроенный загрузчик на `sys.meta_path`: относительные импорты,
  пакеты, трейсбеки на исходники; очистка устаревших вендоренных
  `catalib.*` между деплоями.
- Мини-фреймворк `catalib.support`: авто-регистрация хуков и пунктов
  меню, типизированные настройки, безопасные импорты SDK.
- CLI `watch` с автодеплоем через dev server, `init` с шаблоном.
- Корректный API меню SDK (`MenuItemData(menu_type=..., on_click=...)`),
  отказ от нестандартного `__min_version__`.
- Пример `exteraToolbox` (44 модуля) и полная документация (эта книга).
- **0.2.0**: `watchfiles` опционален (`pip install "catalib[watch]"`,
  работает на телефоне); паритет support-слоя с SDK — полные настройки,
  кликабельная строка (`settings.text(on_click=)`), поля меню
  `item_id`/`condition`/`priority`, `@hook.app_event`, декларативные
  Xposed-хуки `@xposed` (ADR-0005, ADR-0006).
- **0.3.0**: полный паритет `catalib.support` со **всем** публичным SDK
  exteraGram — модули `android`/`client`/`files`/`reflection`/
  `formatting`/`dialogs`/`bulletins`/`proxy` (class proxy)/`classes`,
  карта хук-методов `pre_request`/`post_request`/`on_update`/
  `on_updates`, довод настроек и ядра до полноты; всё строго аддитивно
  (ADR-0007).
- **0.3.1**: помодульный tree-shaking вендоренного `catalib` — в сборку
  попадает только используемое (≈ −34% объёма `catalib`-части), опция
  `[build] vendor = auto|full`, консервативный fallback (ADR-0008).
- **0.3.2**: комфорт разработки — типизация PEP 561 + поставка SDK-стабов
  и `catalib stubs` (ADR-0009); `catalib doctor` (префлайт-диагностика);
  шаблоны `catalib init -t` и модуль `catalib.testing`; `catalib logs`;
  решение по `intents` подтверждено эмпирически (ADR-0010).
