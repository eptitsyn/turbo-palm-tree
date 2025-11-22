# app/crew/tools/static_analysis_tool.py
import subprocess
import tempfile


def static_analysis_tool(code: str) -> list[dict[str, str]]:
    """
    Runs ruff, mypy, and bandit on the given code string.
    Returns structured issues.
    """
    findings = []
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        temp_path = f.name

    # Run Ruff
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", temp_path, "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        import json

        findings += json.loads(result.stdout)
    except Exception as e:  # noqa: BLE001
        findings.append({"tool": "ruff", "error": str(e)})

    # TODO: Add bandit, mypy support here
    return findings
