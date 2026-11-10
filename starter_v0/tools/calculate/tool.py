from __future__ import annotations

import ast
import operator
from typing import Any

from tools._shared import err

_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MAX_EXPRESSION_CHARS = 200
MAX_EXPONENT = 100


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ValueError(f"exponent larger than {MAX_EXPONENT} is not allowed")
        return _BIN_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval(node.operand))
    raise ValueError("only numbers and + - * / % ** ( ) are allowed")


def calculate(expression: str = "") -> dict[str, Any]:
    """Evaluate a plain arithmetic expression. No names, calls or attributes are evaluated."""
    try:
        expr = (expression or "").strip()
        if not expr:
            return {"tool": "calculate", "error": "EmptyExpression", "message": "expression is empty"}
        if len(expr) > MAX_EXPRESSION_CHARS:
            return {"tool": "calculate", "error": "TooLong", "message": f"max {MAX_EXPRESSION_CHARS} characters"}
        value = _eval(ast.parse(expr, mode="eval"))
        return {"tool": "calculate", "expression": expr, "result": value}
    except ZeroDivisionError as exc:
        return err("calculate", exc)
    except Exception as exc:
        return err("calculate", exc)
