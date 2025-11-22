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
