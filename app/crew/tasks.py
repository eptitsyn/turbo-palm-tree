# app/crew/tasks.py
from crewai import Agent, Task


def create_review_orchestration_task(agent: Agent | None = None) -> Task:
    description = """
You coordinate a code review for a single diff_context.

Input:
- diff_context: {file_path, language, diff, old_code, new_code}

Your job:
- Produce a brief plan describing which specialties should focus on which risks.
- Highlight the riskiest areas and expected failure modes.
- Keep the output machine-readable.

Output:
Return ONLY JSON:
{
  "workplan": ["item 1", "item 2"],
  "risk_profile": "short text",
  "focus_areas": ["security", "testing", "performance"]
}
"""
    return Task(
        description=description,
        expected_output=(
            "JSON object with workplan, risk_profile, and focus_areas for the diff."
        ),
        name="review_orchestration",
        agent=agent,
    )


def create_context_builder_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Normalize the provided diff_context into a structured bundle for downstream agents.

Include:
- file metadata (path, language)
- summary of change intent and surface area
- quick risk notes (security/perf/testing)
- counts of additions/removals

Output:
Return ONLY JSON:
{
  "file_path": "...",
  "language": "...",
  "change_summary": "...",
  "risk_notes": ["item"],
  "stats": {"added_lines": int, "removed_lines": int},
  "diff": "...",
  "old_code": "...",
  "new_code": "..."
}
"""
    return Task(
        description=description,
        expected_output="JSON context bundle with metadata, risk notes, and change stats.",
        name="context_builder",
        agent=agent,
        context=context or [],
    )


def create_static_analysis_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Act as a static analysis collector. If tools are unavailable, reason from the diff.

Input:
- diff_context plus any context provided.

Output:
Return ONLY JSON list of findings:
[
  {
    "tool": "ruff|mypy|bandit|eslint|reasoned",
    "severity": "info|minor|major|critical",
    "summary": "...",
    "description": "...",
    "suggested_fix": "...",
    "rule_id": "optional"
  }
]
"""
    return Task(
        description=description,
        expected_output="JSON array of normalized static analysis findings.",
        name="static_analysis",
        agent=agent,
        context=context or [],
    )


def create_file_diff_review_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
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
        agent=agent,
        context=context or [],
    )


def create_security_review_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Perform a security-focused review of the diff_context.

Consider:
- auth/z, secrets, cryptography, injection, SSRF, RCE, deserialization, sandboxing
- data exposure, logging of sensitive data, and supply-chain risks
- exploitability and mitigations

Output:
Return ONLY JSON list of findings (severity, summary, description, suggested_fix).
"""
    return Task(
        description=description,
        expected_output="JSON array of security findings with mitigations.",
        name="security_review",
        agent=agent,
        context=context or [],
    )


def create_performance_review_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Perform a performance and reliability review of the diff_context.

Consider:
- time/space complexity, hot paths, IO, allocations, caching, vectorization
- concurrency, locking, async usage, race conditions
- resilience: retries, timeouts, backpressure, resource leaks

Output:
Return ONLY JSON list of findings (severity, summary, description, suggested_fix).
"""
    return Task(
        description=description,
        expected_output="JSON array of performance/reliability findings.",
        name="performance_reliability_review",
        agent=agent,
        context=context or [],
    )


def create_testing_review_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Perform a testing and UX/API review of the diff_context.

Consider:
- missing or weak tests, flaky patterns, boundary cases, negative paths
- API/CLI contract changes, error messages, logging, telemetry
- user-facing regressions or documentation gaps

Output:
Return ONLY JSON list of findings (severity, summary, description, suggested_fix),
and include a `suggested_tests` array when relevant.
"""
    return Task(
        description=description,
        expected_output=(
            "JSON array of testing/UX findings; each item may include suggested_tests."
        ),
        name="testing_ux_review",
        agent=agent,
        context=context or [],
    )


def create_report_composer_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Merge and deduplicate findings from all review tasks. Ensure schema consistency.

Input:
- outputs from orchestration, context building, static analysis, and all reviewers.

Output:
Return ONLY JSON:
{
  "summary": "short MR-level summary",
  "findings": [
    {
      "severity": "info|minor|major|critical",
      "summary": "...",
      "description": "...",
      "suggested_fix": "...",
      "source": "static|general|security|performance|testing"
    }
  ]
}

If `project_id` and `mr_iid` are available in the inputs, you MAY post a short
MR note using the GitLab comment tool to surface the top findings. Keep it concise.
"""
    return Task(
        description=description,
        expected_output="JSON object with summary plus merged findings array.",
        name="report_composer",
        agent=agent,
        context=context or [],
    )
