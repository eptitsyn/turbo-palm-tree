# app/crew/crew_factory.py
from typing import Any

from crewai import Crew

from app.crew.agents import create_code_reviewer_agent
from app.crew.tasks import create_file_diff_review_task


def create_review_crew() -> Crew:
    reviewer = create_code_reviewer_agent()
    review_task = create_file_diff_review_task()

    return Crew(
        agents=[reviewer],
        tasks=[review_task],
        verbose=False,
    )


def run_file_diff_review(diff_context: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Execute the crew on a diff context and return structured findings.

    Always returns a list of dicts for mypy compatibility.
    """

    crew = create_review_crew()
    result = crew.kickoff(inputs={"diff_context": diff_context})

    # String → wrap into a one-item findings list
    if isinstance(result, str):
        return [
            {
                "severity": "info",
                "summary": "Crew returned a raw string",
                "raw_output": result,
            }
        ]

    # Dict → extract findings
    if isinstance(result, dict):
        findings = result.get("findings", None)

        if isinstance(findings, list):
            out: list[dict[str, Any]] = []
            for item in findings:
                if isinstance(item, dict):
                    out.append(item)
            return out

        # Unexpected "findings"
        return [
            {
                "severity": "info",
                "summary": "Unexpected 'findings' format in crew output",
                "raw_output": str(findings),
            }
        ]

    # Completely unexpected type
    return [
        {
            "severity": "info",
            "summary": "Crew returned unsupported output type",
            "raw_output": str(result),
        }
    ]
