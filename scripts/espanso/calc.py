#!/usr/bin/env python3
import sys
import math
import ast


def evaluate(expr):
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed.update({"abs": abs, "round": round, "int": int, "float": float})
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Attribute, ast.Subscript)):
            raise ValueError("Unsupported expression")
    result = eval(expr, {"__builtins__": {}}, allowed)
    if isinstance(result, float) and result == int(result):
        return str(int(result))
    return str(result)


if __name__ == "__main__":
    expr = " ".join(sys.argv[1:]).strip()
    if not expr:
        print("")
        sys.exit(0)
    try:
        print(evaluate(expr))
    except Exception as e:
        print(f"? {e}")
