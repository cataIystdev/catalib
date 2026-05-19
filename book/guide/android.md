# Разработка на устройстве (Termux/Pydroid)

catalib запускается не только с ПК, но и на самом телефоне, где работает
exteraGram — в [Termux](https://termux.dev/) или
[Pydroid 3](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3).
Можно писать плагин, собирать его и сразу деплоить в локальный
exteraGram, не подключая компьютер. Решения и их обоснование —
ADR-0011.

## Главное: на устройстве `adb` не нужен

`adb forward` нужен только чтобы пробросить порт **с** устройства **на**
ПК. Когда catalib уже на устройстве, dev server exteraGram слушает
`127.0.0.1:42690`, и catalib подключается к нему напрямую. Среда
определяется автоматически; принудительно — флагом `--adb/--no-adb`
(есть у `watch`, `logs`).

## Установка

### Termux (рекомендуется)

Полноценный Linux-userland: есть `pip`, `subprocess`, системные
бинарники (`logcat`).

```bash
pkg install python
pip install catalib
catalib doctor          # покажет: Среда: Termux (Android)
```

`watchfiles` ставить не нужно (Rust-бэкенд под Termux не собрать) —
`watch` сам использует stdlib-поллинг.

### Pydroid 3

Песочница приложения: `pip` без компиляторов (только чистый Python),
`subprocess` может быть урезан. `catalib` ставится через встроенный pip
(он чистый Python + `typer`). Команды сборки работают; команды,
которым нужен `subprocess` (`logs`, частично `doctor`), деградируют с
понятным сообщением, а не падают.

## Паритет команд

| Команда | На устройстве |
|---------|---------------|
| `build`, `init`, `stubs`, `version` | работают как на ПК (чистый Python) |
| `watch` | работает; без `watchfiles` — stdlib-поллинг (`--poll`) |
| `watch --deploy` | деплой напрямую в `127.0.0.1:42690`, без `adb` |
| `doctor` | печатает среду; на Android проверяет dev server напрямую, без `adb`/устройства |
| `logs` | системный `logcat` напрямую; см. ограничение ниже |

## Типичный цикл на телефоне

```bash
catalib init "My Plugin" --id myplugin
cd myplugin
catalib doctor                 # Среда: Termux (Android), dev server напрямую
catalib watch --deploy         # пересборка + деплой в локальный exteraGram
```

Открыт ли dev server: в exteraGram включите режим разработчика.
Включение нового плагина может потребовать одного захода в экран
плагинов (особенность ряда сборок — см.
[Рабочий процесс](../deployment/workflow.md)).

## Ограничение `logs` на устройстве

`catalib logs` на устройстве зовёт системный `logcat` напрямую. Но
**чужой** logcat (то, что пишет exteraGram) Android отдаёт только с
разрешением `READ_LOGS`. Обычное приложение Termux/Pydroid видит лишь
свои строки. Варианты получить чужие:

- **root** — `logcat` видит всё;
- **Shizuku** — запуск `logcat` через Shizuku-сервис;
- **adb-grant** — один раз с ПК:
  `pm grant com.termux android.permission.READ_LOGS` (имя пакета —
  вашего терминала).

Без привилегии `logs` честно сообщает об этом и подсказывает варианты,
а не делает вид, что работает. Альтернатива без прав — писать
диагностику плагина в файл (см. [Доступ к SDK](sdk-access.md)).

## Pydroid: что может не работать

Pydroid в части сборок запрещает `subprocess`. Тогда `logs` и проверка
dev server в `doctor` сообщат об ошибке (не упадут). Сборка/инициализация
(`build`/`init`/`stubs`) от `subprocess` не зависят и работают всегда.
Для полноценного цикла на телефоне предпочтителен Termux.

## Связи

- Зависит от: dev server exteraGram (ADR-0004), детект среды
  `catalib.platforms` (ADR-0011).
- Связанные страницы: [catalib watch](../cli/watch.md),
  [catalib doctor](../cli/doctor.md), [catalib logs](../cli/logs.md),
  [Рабочий процесс](../deployment/workflow.md).
