"""Безопасное вычисление арифметики через разбор AST.

Допускаются только числовые литералы, скобки и операции ``+ - * / // % **``
с унарными ``+``/``-``. Имена, вызовы, атрибуты и прочее запрещены, поэтому
произвольный код выполнить нельзя. Степень ограничена, чтобы исключить
вычислительные злоупотребления.
"""

from __future__ import annotations

import ast
import operator

from ..core.errors import CommandError

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

#: Максимальный показатель степени.
_MAX_POW = 1000


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise CommandError("допустимы только числа")
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval(node.left)
        right = _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_POW:
            raise CommandError(f"показатель степени ограничен {_MAX_POW}")
        try:
            return _BIN_OPS[type(node.op)](left, right)
        except ZeroDivisionError as exc:
            raise CommandError("деление на ноль") from exc
    raise CommandError("выражение содержит недопустимые элементы")


def evaluate(expression: str) -> float:
    """Вычислить арифметическое выражение.

    :raises CommandError: при синтаксической ошибке или недопустимых узлах.
    """
    expression = (expression or "").strip()
    if not expression:
        raise CommandError("пустое выражение")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CommandError(f"синтаксическая ошибка: {exc.msg}") from exc
    return _eval(tree)
