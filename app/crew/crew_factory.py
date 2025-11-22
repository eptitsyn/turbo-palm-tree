# app/crew/crew_factory.py
from typing import Any

from crewai import Crew, Process

from app.crew.agents import (
    create_code_reviewer_agent,
    create_context_builder_agent,
    create_performance_reliability_agent,
    create_report_composer_agent,
    create_review_orchestrator_agent,
    create_security_reviewer_agent,
    create_static_analysis_agent,
    create_testing_ux_reviewer_agent,
)
from app.crew.tasks import (
    create_context_builder_task,
    create_file_diff_review_task,
    create_performance_review_task,
    create_report_composer_task,
    create_review_orchestration_task,
    create_security_review_task,
    create_static_analysis_task,
    create_testing_review_task,
)


def create_review_crew() -> Crew:
    orchestrator = create_review_orchestrator_agent()
    context_builder = create_context_builder_agent()
    static_collector = create_static_analysis_agent()
    general_reviewer = create_code_reviewer_agent()
    security_reviewer = create_security_reviewer_agent()
    perf_reviewer = create_performance_reliability_agent()
    testing_reviewer = create_testing_ux_reviewer_agent()
    composer = create_report_composer_agent()

    orchestration_task = create_review_orchestration_task(agent=orchestrator)
    context_task = create_context_builder_task(
        agent=context_builder,
        context=[orchestration_task],
    )
    static_task = create_static_analysis_task(
        agent=static_collector,
        context=[orchestration_task, context_task],
    )
    general_task = create_file_diff_review_task(
        agent=general_reviewer,
        context=[context_task, static_task],
    )
    security_task = create_security_review_task(
        agent=security_reviewer,
        context=[context_task, static_task],
    )
    performance_task = create_performance_review_task(
        agent=perf_reviewer,
        context=[context_task, static_task],
    )
    testing_task = create_testing_review_task(
        agent=testing_reviewer,
        context=[context_task, static_task],
    )
    report_task = create_report_composer_task(
        agent=composer,
        context=[
            orchestration_task,
            context_task,
            static_task,
            general_task,
            security_task,
            performance_task,
            testing_task,
        ],
    )

    return Crew(
        agents=[
            orchestrator,
            context_builder,
            static_collector,
            general_reviewer,
            security_reviewer,
            perf_reviewer,
            testing_reviewer,
            composer,
        ],
        tasks=[
            orchestration_task,
            context_task,
            static_task,
            general_task,
            security_task,
            performance_task,
            testing_task,
            report_task,
        ],
        process=Process.sequential,
        tracing=True,
        verbose=True,
    )


def run_file_diff_review(diff_context: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Execute the crew on a diff context and return structured findings.

    Always returns a list of dicts for mypy compatibility.
    """

    crew = create_review_crew()
    try:
        result = crew.kickoff(inputs={"diff_context": diff_context})
    except Exception as exc:  # noqa: BLE001
        return [
            {
                "severity": "major",
                "summary": "Agent execution failed",
                "description": (
                    "The code review agent could not run. Ensure a compatible "
                    "OpenAI-style LLM endpoint is available and credentials are set."
                ),
                "raw_output": str(exc),
            }
        ]

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
