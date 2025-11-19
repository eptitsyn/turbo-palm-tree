# app/crew/tasks.py
from crewai import Task


def create_file_diff_review_task() -> Task:
    """
    Task expects `diff_context` in inputs, which contains:
        - file_path
        - language
        - diff
        - old_code
        - new_code

    The agent must respond with JSON list of findings.
    For MVP, we don't enforce strict schema here.
    """
    description = """
You are given a code change (diff) in a single file.

Input:
- file_path: path of the file
- language: programming language (e.g. python, javascript)
- diff: unified diff snippet
- old_code: previous version of the code
- new_code: new version of the code

Your job:
1. Identify problems in correctness, security, performance, style, and maintainability.
2. For each problem, produce an item with:
   - severity: one of ["info", "minor", "major", "critical"]
   - summary: short one-line description
   - description: detailed explanation
   - suggested_fix: how to fix it (optionally code snippet)

Output:
Return ONLY JSON with a top-level list of findings, for example:

[
  {
    "severity": "major",
    "summary": "Function does not handle None input",
    "description": "...",
    "suggested_fix": "..."
  }
]
"""

    return Task(
        description=description,
        expected_output="A JSON array of findings as described above.",
        # name is optional but nice for logging
        name="file_diff_review",
    )
