# tools/calculate.py

import re
import math

def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.
    Supports common math functions and converts sin(x) to radians.
    """
    # convert sin(…) to sin(radians(…)) for degree inputs
    expression = re.sub(r'sin\((.*?)\)', r'sin(radians(\1))', expression)

    safe_env = {
        # math functions
        **{name: getattr(math, name) for name in (
            "acos","asin","atan","cos","sin","tan",
            "radians","degrees","pi","e","sqrt"
        )},
        # built-ins
        "abs": abs, "max": max, "min": min,
        "pow": pow, "round": round,
        "sum": sum, "len": len
    }

    try:
        result = eval(expression, {"__builtins__": {}}, safe_env)
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
