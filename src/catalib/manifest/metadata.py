"""Статическая (AST) валидация метаданных плагина exteraGram.

exteraGram читает дандеры (``__id__``, ``__name__`` и т. д.) из файла плагина
через ``ast`` и принимает значения, ТОЛЬКО если это строковые литералы
(``ast.Constant``). Динамические значения (``__id__ = get_id()``,
``__id__ = NAME + "x"``) приводят к тому, что метаданные не считываются и
плагин не загружается.

Этот модуль повторяет ту же логику и дополнительно проверяет совпадение
``__id__`` с именем выходного файла и формат версии. Используется и для
проверки собранного файла, и для валидации произвольного ``.py`` плагина.
"""

from __future__ import annotations

import ast

from catalib.manifest.model import VERSION_PATTERN

#: Дандеры-строки, обязательные для валидного плагина exteraGram.
REQUIRED_STRING_DUNDERS = ("__id__", "__name__", "__version__")

#: Дандер со списком зависимостей (список строковых литералов).
REQUIREMENTS_DUNDER = "__requirements__"


class MetadataError(ValueError):
    """Ошибка статической проверки метаданных с указанием места."""


def _dunder_targets(node: ast.Assign) -> list[str]:
    """Вернуть имена целей присваивания вида ``__name__`` (одиночные Name)."""
    names: list[str] = []
    for target in node.targets:
        if isinstance(target, ast.Name) and target.id.startswith("__") and target.id.endswith("__"):
            names.append(target.id)
    return names


def _is_string_constant(value: ast.expr) -> bool:
    """Истинно, если узел — строковый литерал ``ast.Constant``."""
    return isinstance(value, ast.Constant) and isinstance(value.value, str)


def _is_string_sequence(value: ast.expr) -> bool:
    """Истинно, если узел — список/кортеж строковых литералов."""
    if not isinstance(value, ast.List | ast.Tuple):
        return False
    return all(_is_string_constant(element) for element in value.elts)


def extract_metadata(source: str) -> dict[str, object]:
    """Извлечь статические метаданные из исходника так же, как exteraGram.

    Считываются только модульного уровня присваивания дандеров, где значение —
    строковый литерал (или список строк для ``__requirements__``).

    :param source: исходный текст плагина.
    :returns: словарь ``имя_без_подчёркиваний -> значение``.
    :raises MetadataError: при синтаксической ошибке исходника.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise MetadataError(f"синтаксическая ошибка в исходнике: {exc}") from exc

    metadata: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for name in _dunder_targets(node):
            if name == REQUIREMENTS_DUNDER and _is_string_sequence(node.value):
                metadata[name[2:-2]] = [
                    element.value
                    for element in node.value.elts  # type: ignore[attr-defined]
                ]
            elif _is_string_constant(node.value):
                metadata[name[2:-2]] = node.value.value
    return metadata


def validate_metadata(source: str, expected_id: str) -> None:
    """Проверить, что метаданные собранного файла корректны и литеральны.

    :param source: исходный текст собранного плагина.
    :param expected_id: ожидаемый ``__id__`` (равный имени файла без ``.py``).
    :raises MetadataError: с перечислением всех найденных проблем.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise MetadataError(f"синтаксическая ошибка в собранном файле: {exc}") from exc

    problems: list[str] = []
    seen: dict[str, ast.expr] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for name in _dunder_targets(node):
            seen.setdefault(name, node.value)
            value = node.value
            if name == REQUIREMENTS_DUNDER:
                if not _is_string_sequence(value):
                    problems.append(
                        f"строка {node.lineno}: {name} должен быть списком строковых литералов"
                    )
            elif not _is_string_constant(value):
                problems.append(
                    f"строка {node.lineno}: {name} должен быть строковым литералом "
                    "(динамические метаданные exteraGram не читает)"
                )

    for dunder in REQUIRED_STRING_DUNDERS:
        if dunder not in seen:
            problems.append(f"отсутствует обязательный дандер {dunder}")

    id_node = seen.get("__id__")
    if id_node is not None and _is_string_constant(id_node):
        actual_id = id_node.value  # type: ignore[attr-defined]
        if actual_id != expected_id:
            problems.append(
                f"__id__ ({actual_id!r}) не совпадает с именем файла ({expected_id!r}.py)"
            )

    version_node = seen.get("__version__")
    if version_node is not None and _is_string_constant(version_node):
        version_value = version_node.value  # type: ignore[attr-defined]
        if not VERSION_PATTERN.match(version_value):
            problems.append(
                f"__version__ ({version_value!r}) не соответствует формату N[.N[.N[.N]]]"
            )

    if problems:
        raise MetadataError("; ".join(problems))
