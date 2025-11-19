# app/crew/crew_factory.py
from typing import Any

from crewai import Crew

from app.crew.agents import create_code_reviewer_agent
from app.crew.tasks import create_file_diff_review_task


def create_review_crew() -> Crew:
    """
    Construct a simple crew with a single code reviewer agent
    and a single task for per-file diff review.
    """
    reviewer = create_code_reviewer_agent()
    review_task = create_file_diff_review_task()

    return Crew(
        agents=[reviewer],
        tasks=[review_task],
        verbose=False,
    )


def run_file_diff_review(diff_context: dict[str, Any]) -> list[dict[str, Any]]:
    """
    High-level helper used by Celery task.
    diff_context should include at least:
      - file_path
      - language
      - diff
      - old_code
      - new_code

    For MVP this just calls crew.kickoff and assumes the
    result is a JSON list of findings. Later you can make
    it more robust and add validation.
    """
    crew = create_review_crew()

    # crewAI works with inputs via tasks; simplest way is to
    # set the context on the crew or pass as input variable.
    # Here we assume the only task expects `diff_context` input.
    result = crew.kickoff(inputs={"diff_context": diff_context})

    # For the MVP, if result is string, pretend it's JSON-ish;
    # real implementation: parse JSON and validate.
    if isinstance(result, str):
        # TODO: replace with json.loads + schema validation
        return [
            {
                "severity": "info",
                "summary": "Dummy result from string output",
                "raw_output": result,
            }
        ]

    if isinstance(result, dict):
        # Provide a loose default convention: result["findings"]
        return result.get("findings", [])

    # Last fallback: wrap result in a single finding
    return [
        {
            "severity": "info",
            "summary": "Unexpected output type from crew",
            "raw_output": str(result),
        }
    ]
