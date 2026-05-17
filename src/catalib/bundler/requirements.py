"""Слияние зависимостей плагина (``__requirements__``).

Итоговый список зависимостей складывается из манифеста и объявлений
``__requirements__`` в модулях дерева. Дубликаты удаляются с сохранением
порядка. exteraGram устанавливает только pure-Python wheels, поэтому
зависимости из явного списка бинарных пакетов отклоняются с понятной ошибкой.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from catalib.bundler.model import SourceModule
from catalib.manifest.metadata import extract_metadata

#: Пакеты с обязательными бинарными расширениями: в exteraGram не работают.
#: Имена нормализованы по PEP 503 (строчные, разделитель «-»).
BINARY_BLOCKLIST = frozenset(
    {
        "numpy",
        "pandas",
        "scipy",
        "cryptography",
        "opencv-python",
        "opencv-python-headless",
        "opencv-contrib-python",
    }
)

_NAME_BOUNDARY = re.compile(r"[<>=!~;\[\s]")


class RequirementsError(ValueError):
    """Ошибка слияния/валидации зависимостей плагина."""


def _normalize_name(requirement: str) -> str:
    """Выделить и нормализовать имя дистрибутива из строки требования PEP 508."""
    head = _NAME_BOUNDARY.split(requirement.strip(), 1)[0]
    return re.sub(r"[-_.]+", "-", head).lower()


def merge_requirements(
    manifest_requirements: Iterable[str],
    modules: Iterable[SourceModule],
) -> tuple[str, ...]:
    """Собрать итоговый список зависимостей плагина.

    :param manifest_requirements: зависимости из ``[plugin].requirements``.
    :param modules: модули дерева исходников (сканируются на ``__requirements__``).
    :returns: кортеж требований без дубликатов в порядке первого появления.
    :raises RequirementsError: если требование указывает на бинарный пакет из
        :data:`BINARY_BLOCKLIST` или пусто.
    """
    ordered: list[str] = []
    seen: set[str] = set()

    def add(requirement: str, origin: str) -> None:
        normalized = requirement.strip()
        if not normalized:
            raise RequirementsError(f"пустое требование в {origin}")
        dist = _normalize_name(normalized)
        if dist in BINARY_BLOCKLIST:
            raise RequirementsError(
                f"{normalized!r} ({origin}): бинарный пакет {dist!r} не "
                "поддерживается exteraGram (только pure-Python wheels)"
            )
        if normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)

    for requirement in manifest_requirements:
        add(requirement, "манифест")

    for module in modules:
        meta = extract_metadata(module.source)
        module_reqs = meta.get("requirements")
        if isinstance(module_reqs, list):
            for requirement in module_reqs:
                add(requirement, f"модуль {module.relpath}")

    return tuple(ordered)
