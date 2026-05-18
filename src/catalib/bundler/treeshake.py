"""Помодульный отбор вендоренных модулей ``catalib`` (tree-shaking).

В собранный плагин вшивается не весь ``catalib.support``, а только модули,
которые плагин реально импортирует, плюс их транзитивные зависимости
внутри ``catalib``. Для пакета ``catalib.support`` генерируется урезанный
``__init__``, чтобы импорт фасада не тянул отсечённые подмодули.

Анализ статический (AST) и консервативный: при любой неоднозначности
(импорт всего пакета как объекта, ``import *``, несопоставимое имя,
импорт ``catalib`` вне ``catalib.support``) выполняется полный вендоринг
с предупреждением — лучше больше байт, чем сломанный плагин.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from catalib.bundler.model import SourceModule, SourceTree
from catalib.bundler.vendor import (
    ROOT_PACKAGE,
    SUPPORT_PACKAGE,
    all_vendor_modules,
)

_SUPPORT_PREFIX = SUPPORT_PACKAGE + "."


@dataclass(frozen=True, slots=True)
class VendorPlan:
    """План вендоринга.

    :param modules: модули ``catalib`` для встраивания (для ``catalib.support``
        исходник может быть урезанным ``__init__``).
    :param full: выполнен полный вендоринг (отбор не применялся).
    :param kept: имена включённых модулей.
    :param pruned: имена отсечённых модулей.
    :param warnings: причины полного вендоринга/замечания для CLI.
    """

    modules: tuple[SourceModule, ...]
    full: bool
    kept: tuple[str, ...]
    pruned: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass
class _Usage:
    symbols: set[str]
    submodules: set[str]
    namespace: bool
    uses_catalib: bool
    foreign_catalib: bool
    star: bool


def _imports(source: str) -> list[ast.Import | ast.ImportFrom]:
    """Все узлы import/from-import (в т. ч. внутри функций) или ошибка разбора."""
    tree = ast.parse(source)
    return [n for n in ast.walk(tree) if isinstance(n, ast.Import | ast.ImportFrom)]


def _sub_of(dotted: str) -> str | None:
    """``catalib.support.client.x`` -> ``client``; иначе ``None``."""
    if dotted == SUPPORT_PACKAGE or not dotted.startswith(_SUPPORT_PREFIX):
        return None
    return dotted[len(_SUPPORT_PREFIX) :].split(".", 1)[0]


def _analyze_plugin(tree: SourceTree) -> _Usage:
    """Собрать, что плагин импортирует из ``catalib``."""
    u = _Usage(set(), set(), False, False, False, False)
    for module in tree.modules:
        for node in _imports(module.source):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name in (ROOT_PACKAGE, SUPPORT_PACKAGE):
                        u.uses_catalib = True
                        u.namespace = True
                    elif name.startswith(_SUPPORT_PREFIX):
                        u.uses_catalib = True
                        u.submodules.add(_sub_of(name))
                    elif name == ROOT_PACKAGE or name.startswith(ROOT_PACKAGE + "."):
                        u.uses_catalib = True
                        u.foreign_catalib = True
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mod = node.module
                names = [a.name for a in node.names]
                if mod == ROOT_PACKAGE:
                    u.uses_catalib = True
                    if "support" in names:
                        u.namespace = True
                    else:
                        u.foreign_catalib = True
                elif mod == SUPPORT_PACKAGE:
                    u.uses_catalib = True
                    if "*" in names:
                        u.star = True
                    else:
                        u.symbols.update(names)
                elif mod.startswith(_SUPPORT_PREFIX):
                    u.uses_catalib = True
                    u.submodules.add(_sub_of(mod))
                elif mod == ROOT_PACKAGE or mod.startswith(ROOT_PACKAGE + "."):
                    u.uses_catalib = True
                    u.foreign_catalib = True
    return u


def _export_map(support_init_src: str) -> tuple[dict[str, str], set[str]]:
    """Из настоящего ``catalib/support/__init__.py`` построить карты.

    :returns: ``(symbol -> подмодуль, множество ре-экспортируемых подмодулей)``.
    """
    symbol_to_sub: dict[str, str] = {}
    reexported_subs: set[str] = set()
    for node in _imports(support_init_src):
        if not isinstance(node, ast.ImportFrom) or node.level != 0 or not node.module:
            continue
        if node.module == SUPPORT_PACKAGE:
            for alias in node.names:
                reexported_subs.add(alias.asname or alias.name)
        elif node.module.startswith(_SUPPORT_PREFIX):
            sub = _sub_of(node.module)
            for alias in node.names:
                symbol_to_sub[alias.asname or alias.name] = sub
    return symbol_to_sub, reexported_subs


def _build_graph(mods: dict[str, SourceModule]) -> dict[str, set[str]]:
    """Граф зависимостей внутри ``catalib`` (имя -> множество зависимостей)."""
    graph: dict[str, set[str]] = {name: set() for name in mods}
    for name, module in mods.items():
        deps = graph[name]
        for node in _imports(module.source):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                m = node.module
                if m == SUPPORT_PACKAGE:
                    for a in node.names:
                        cand = f"{SUPPORT_PACKAGE}.{a.name}"
                        targets.append(cand if cand in mods else SUPPORT_PACKAGE)
                else:
                    targets = [m]
            for t in targets:
                if t in mods:
                    deps.add(t)
                if t == SUPPORT_PACKAGE or t.startswith(_SUPPORT_PREFIX):
                    deps.add(SUPPORT_PACKAGE)
                    deps.add(ROOT_PACKAGE)
        deps.discard(name)
    # Узел пакета catalib.support в auto-режиме НЕ наследует зависимости
    # настоящего (полного) __init__: он импортирует все подмодули, что
    # сделало бы замыкание полным. В сборку идёт урезанный __init__,
    # импортирующий только нужные подмодули (они добавляются как seeds и
    # через фикспоинт). Поэтому пакет зависит только от корня.
    if SUPPORT_PACKAGE in graph:
        graph[SUPPORT_PACKAGE] = {ROOT_PACKAGE}
    return graph


def _closure(seeds: set[str], graph: dict[str, set[str]]) -> set[str]:
    """Транзитивное замыкание по графу зависимостей."""
    seen: set[str] = set()
    stack = [s for s in seeds if s in graph]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(d for d in graph[cur] if d not in seen)
    return seen


def _render_support_init(
    submodule_bindings: set[str],
    symbols: set[str],
    symbol_to_sub: dict[str, str],
) -> str:
    """Сгенерировать урезанный ``catalib/support/__init__.py``."""
    lines = [
        '"""Урезанный фасад catalib.support (сгенерирован catalib).',
        "",
        "Импортирует только то, что использует плагин, чтобы фасад не",
        'тянул отсечённые подмодули."""',
        "",
        "from __future__ import annotations",
        "",
    ]
    for sub in sorted(submodule_bindings):
        lines.append(f"from {SUPPORT_PACKAGE} import {sub}")
    by_sub: dict[str, list[str]] = {}
    for name in symbols:
        by_sub.setdefault(symbol_to_sub[name], []).append(name)
    for sub in sorted(by_sub):
        names = ", ".join(sorted(by_sub[sub]))
        lines.append(f"from {SUPPORT_PACKAGE}.{sub} import {names}")
    exported = sorted(submodule_bindings | symbols)
    lines.append("")
    lines.append("__all__ = [" + ", ".join(repr(x) for x in exported) + "]")
    return "\n".join(lines) + "\n"


def _full_plan(mods: dict[str, SourceModule], warnings: tuple[str, ...]) -> VendorPlan:
    return VendorPlan(
        modules=tuple(mods.values()),
        full=True,
        kept=tuple(sorted(mods)),
        pruned=(),
        warnings=warnings,
    )


def plan_vendor(tree: SourceTree, mode: str = "auto") -> VendorPlan:
    """Построить план вендоринга ``catalib`` для дерева исходников плагина.

    :param tree: дерево исходников плагина.
    :param mode: ``"auto"`` — отбор используемого; ``"full"`` — всё.
    """
    mods = all_vendor_modules()
    if mode == "full":
        return _full_plan(mods, ())

    try:
        usage = _analyze_plugin(tree)
    except SyntaxError as exc:
        return _full_plan(mods, (f"не удалось разобрать исходники плагина: {exc}",))

    if not usage.uses_catalib:
        return VendorPlan((), False, (), tuple(sorted(mods)), ())

    reasons: list[str] = []
    if usage.namespace:
        reasons.append(
            "плагин связывает весь пакет catalib.support как объект — статический отбор невозможен"
        )
    if usage.foreign_catalib:
        reasons.append("плагин импортирует catalib вне catalib.support")
    if usage.star:
        reasons.append("в плагине `from catalib.support import *`")

    symbol_to_sub, reexported = _export_map(mods[SUPPORT_PACKAGE].source)

    seed_subs: set[str] = set(usage.submodules)
    init_bindings: set[str] = set()
    init_symbols: set[str] = set()
    for name in usage.symbols:
        if name in reexported:
            seed_subs.add(name)
            init_bindings.add(name)
        elif name in symbol_to_sub:
            seed_subs.add(symbol_to_sub[name])
            init_symbols.add(name)
        else:
            reasons.append(f"имя {name!r} из catalib.support не сопоставлено подмодулю")

    if reasons:
        return _full_plan(mods, tuple(reasons))

    graph = _build_graph(mods)

    # Фикспоинт: подмодули из закрытия могут сами делать
    # `from catalib.support import X` — это требует наличия X в урезанном
    # __init__ и его подмодуля в наборе.
    while True:
        seeds = {ROOT_PACKAGE, SUPPORT_PACKAGE} | {f"{SUPPORT_PACKAGE}.{s}" for s in seed_subs}
        reach = _closure(seeds, graph) & set(mods)
        extra_reasons: list[str] = []
        before = (len(seed_subs), len(init_bindings), len(init_symbols))
        for fn in reach:
            if fn in (ROOT_PACKAGE, SUPPORT_PACKAGE):
                continue
            for node in _imports(mods[fn].source):
                if (
                    not isinstance(node, ast.ImportFrom)
                    or node.level != 0
                    or node.module != SUPPORT_PACKAGE
                ):
                    continue
                for alias in node.names:
                    nm = alias.name
                    if nm == "*":
                        extra_reasons.append(f"`import *` из catalib.support в {fn}")
                    elif nm in reexported:
                        seed_subs.add(nm)
                        init_bindings.add(nm)
                    elif nm in symbol_to_sub:
                        seed_subs.add(symbol_to_sub[nm])
                        init_symbols.add(nm)
                    else:
                        extra_reasons.append(f"имя {nm!r} (из {fn}) не сопоставлено подмодулю")
        if extra_reasons:
            return _full_plan(mods, tuple(extra_reasons))
        if (len(seed_subs), len(init_bindings), len(init_symbols)) == before:
            break

    trimmed = _render_support_init(init_bindings, init_symbols, symbol_to_sub)
    selected: list[SourceModule] = []
    for fn in sorted(reach):
        m = mods[fn]
        if fn == SUPPORT_PACKAGE:
            m = SourceModule(
                relname=m.relname,
                relpath=m.relpath,
                source=trimmed,
                is_package=True,
            )
        selected.append(m)

    return VendorPlan(
        modules=tuple(selected),
        full=False,
        kept=tuple(sorted(reach)),
        pruned=tuple(sorted(set(mods) - reach)),
        warnings=(),
    )
