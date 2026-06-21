# tools/calculate.py

import ast
import math
import operator

_SAFE_OPS = {
    ast.Add:      operator.add,
    ast.Sub:      operator.sub,
    ast.Mult:     operator.mul,
    ast.Div:      operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod:      operator.mod,
    ast.Pow:      operator.pow,
    ast.USub:     operator.neg,
    ast.UAdd:     operator.pos,
}

_SAFE_FUNCS = {
    "acos":    math.acos,
    "asin":    math.asin,
    "atan":    math.atan,
    "cos":     math.cos,
    "sin":     math.sin,
    "tan":     math.tan,
    "radians": math.radians,
    "degrees": math.degrees,
    "sqrt":    math.sqrt,
    "log":     math.log,
    "log10":   math.log10,
    "exp":     math.exp,
    "floor":   math.floor,
    "ceil":    math.ceil,
    "abs":     abs,
    "max":     max,
    "min":     min,
    "pow":     math.pow,
    "round":   round,
    "sum":     sum,
    "len":     len,
}

_SAFE_CONSTS = {
    "pi": math.pi,
    "e":  math.e,
}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"Unsupported literal: {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in _SAFE_CONSTS:
            return _SAFE_CONSTS[node.id]
        raise ValueError(f"Unknown name: {node.id!r}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _SAFE_OPS[op_type](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _SAFE_OPS[op_type](_eval_node(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed")
        fname = node.func.id
        if fname not in _SAFE_FUNCS:
            raise ValueError(f"Unknown function: {fname!r}")
        if node.keywords:
            raise ValueError("Keyword arguments are not supported")
        args = [_eval_node(a) for a in node.args]
        return _SAFE_FUNCS[fname](*args)
    if isinstance(node, (ast.List, ast.Tuple)):
        elts = [_eval_node(e) for e in node.elts]
        return elts if isinstance(node, ast.List) else tuple(elts)
    raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    Supports arithmetic operators and common math functions (sin, cos, sqrt, etc.).
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as e:
        return f"Error: invalid expression syntax — {e}"
    try:
        result = _eval_node(tree)
        return f"Result: {result}"
    except Exception as e:
        return f"Error in calculation: {e}"


schema = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Evaluate a mathematical expression safely.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate"
                }
            },
            "required": ["expression"],
            "additionalProperties": False
        }
    }
}
