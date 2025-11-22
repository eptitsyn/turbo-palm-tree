# app/crew/tools/ast_analysis_tool.py
import ast
from typing import Any


def ast_analysis_tool(code: str) -> dict[str, Any]:
    """
    Parses the AST of the code and returns structural metadata and simple smells.
    """
    result = {"functions": [], "classes": []}
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                result["functions"].append({
                    "name": node.name,
                    "args": len(node.args.args),
                    "docstring": ast.get_docstring(node)
                })
            elif isinstance(node, ast.ClassDef):
                result["classes"].append({
                    "name": node.name,
                    "docstring": ast.get_docstring(node)
                })
    except Exception as e:
        result["error"] = str(e)

    return result


def extract_method_signatures(code: str) -> list[dict[str, Any]]:
    """
    Returns lightweight function/method signature info without full bodies.
    Useful when agents should avoid reading entire file content.
    """
    signatures: list[dict[str, Any]] = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_names = [arg.arg for arg in node.args.args]
                defaults = len(node.args.defaults)
                signatures.append(
                    {
                        "name": node.name,
                        "args": arg_names,
                        "defaults": defaults,
                        "decorators": [getattr(d, "id", None) or getattr(d, "attr", None) for d in node.decorator_list],
                        "docstring": bool(ast.get_docstring(node)),
                    }
                )
    except Exception as exc:  # noqa: BLE001
        signatures.append({"error": str(exc)})

    return signatures
