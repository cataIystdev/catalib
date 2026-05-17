"""Доменная модель манифеста плагина и его инварианты.

Манифест описывает метаданные плагина exteraGram и параметры сборки. Модель
не зависит от способа загрузки (TOML, словарь и т. п.) — это чистые данные с
проверкой инвариантов. Загрузка из файла — в :mod:`catalib.manifest.loader`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

#: Идентификатор плагина обязан быть валидным именем Python-модуля, так как
#: exteraGram импортирует плагин как ``importlib.import_module(<plugin_id>)``.
#: 2–32 символа, начинается с латинской строчной буквы, далее [a-z0-9_].
PLUGIN_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,31}$")

#: Версия плагина: от одного до четырёх числовых сегментов через точку.
VERSION_PATTERN = re.compile(r"^\d+(\.\d+){0,3}$")

#: Ограничение версии приложения/SDK: необязательный оператор и версия.
CONSTRAINT_PATTERN = re.compile(r"^(>=|<=|==|>|<)?\d+(\.\d+){0,3}$")


class ManifestError(ValueError):
    """Ошибка валидации манифеста плагина с человекочитаемым сообщением."""


@dataclass(frozen=True, slots=True)
class BuildConfig:
    """Параметры сборки плагина.

    :param src: каталог с исходным деревом плагина относительно корня проекта.
    :param entry: имя модуля внутри ``src`` с подклассом точки входа плагина
        (без расширения, точечная нотация для вложенности).
    :param out: каталог, куда складывается собранный ``<plugin_id>.py``.
    """

    src: str = "src"
    entry: str = "plugin"
    out: str = "dist"

    def __post_init__(self) -> None:
        for name, value in (("src", self.src), ("entry", self.entry), ("out", self.out)):
            if not isinstance(value, str) or not value.strip():
                raise ManifestError(f"build.{name} должен быть непустой строкой")
        for name, value in (("src", self.src), ("out", self.out)):
            if value.startswith(("/", "\\")) or value.strip() != value:
                raise ManifestError(
                    f"build.{name} должен быть относительным путём без пробелов по краям"
                )


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Нормализованные метаданные плагина и параметры сборки.

    Все строковые метаданные попадают в выходной файл строковыми литералами
    (требование AST-парсера exteraGram), поэтому здесь они только проверяются
    на корректность, но не вычисляются.

    :param id: идентификатор плагина; равен имени выходного файла и имени
        импортируемого модуля.
    :param name: отображаемое имя плагина.
    :param version: версия плагина в формате ``N[.N[.N[.N]]]``.
    :param description: описание плагина.
    :param author: автор плагина.
    :param icon: идентификатор иконки exteraGram, например ``exteraPlugins/1``.
    :param min_version: ограничение версии приложения (``__app_version__``).
    :param sdk_version: ограничение версии SDK (``__sdk_version__``).
    :param requirements: список зависимостей в формате PEP 508.
    :param build: параметры сборки.
    """

    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    icon: str = ""
    min_version: str = ""
    sdk_version: str = ""
    requirements: tuple[str, ...] = ()
    build: BuildConfig = field(default_factory=BuildConfig)

    def __post_init__(self) -> None:
        if not PLUGIN_ID_PATTERN.match(self.id or ""):
            raise ManifestError(
                f"plugin.id {self.id!r} невалиден: ожидается 2–32 символа, "
                "начало с [a-z], далее [a-z0-9_]"
            )
        if not isinstance(self.name, str) or not self.name.strip():
            raise ManifestError("plugin.name должен быть непустой строкой")
        if not VERSION_PATTERN.match(self.version or ""):
            raise ManifestError(
                f"plugin.version {self.version!r} невалиден: ожидается формат N[.N[.N[.N]]]"
            )
        for attr in ("min_version", "sdk_version"):
            value = getattr(self, attr)
            if value and not CONSTRAINT_PATTERN.match(value):
                raise ManifestError(
                    f"plugin.{attr} {value!r} невалиден: ожидается [оператор]версия, "
                    "например '>=12.5.1'"
                )
        if not isinstance(self.requirements, tuple):
            raise ManifestError("plugin.requirements должен быть кортежем строк")
        for requirement in self.requirements:
            if not isinstance(requirement, str) or not requirement.strip():
                raise ManifestError("каждый элемент plugin.requirements — непустая строка")

    @property
    def output_filename(self) -> str:
        """Имя выходного файла плагина: ``<id>.py``."""
        return f"{self.id}.py"
