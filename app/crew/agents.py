# app/crew/agents.py
from functools import lru_cache

from crewai import Agent, LLM

from app.config import settings
from app.crew.tools.gitlab_tool import post_merge_request_comment


@lru_cache(maxsize=1)
def _default_llm() -> LLM:
    """Shared LLM configuration for all agents."""
    return LLM(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=2.0,
    )


def _make_agent(role: str, goal: str, backstory: str, **kwargs) -> Agent:
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
        llm=_default_llm(),
        **kwargs,
    )


def create_review_orchestrator_agent() -> Agent:
    return _make_agent(
        role="Review Orchestrator",
        goal=(
            "Plan and route the code review, ensuring each specialist agent covers "
            "its area and that outputs stay within the JSON schema."
        ),
        backstory=(
            "You coordinate AI reviewers, deduplicate overlapping work, and provide "
            "a concise review plan for the crew to follow."
        ),
        allow_delegation=False,
    )


def create_context_builder_agent() -> Agent:
    return _make_agent(
        role="Context Builder",
        goal=(
            "Normalize the provided diff_context into a structured bundle "
            "including file metadata, risks, and change summary."
        ),
        backstory=(
            "You prepare actionable review context so other agents can focus on "
            "analysis rather than data gathering."
        ),
    )


def create_static_analysis_agent() -> Agent:
    return _make_agent(
        role="Static Analysis Collector",
        goal=(
            "Run or reason about static analysis (ruff, mypy, bandit, eslint, etc.) "
            "for the provided diff and return normalized findings."
        ),
        backstory=(
            "You specialize in aggregating and normalizing outputs from static "
            "analysis tools into a unified JSON format."
        ),
    )


def create_code_reviewer_agent() -> Agent:
    """
    Generalist LLM reviewer focusing on correctness, maintainability, and clarity.
    """
    return _make_agent(
        role="Senior Code Reviewer",
        goal=(
            "Review the given code diff and identify potential issues, "
            "returning ONLY structured JSON with a list of findings."
        ),
        backstory=(
            "You are an experienced software engineer responsible for code quality, "
            "security, and maintainability in a large codebase."
        ),
    )


def create_security_reviewer_agent() -> Agent:
    return _make_agent(
        role="Security Specialist",
        goal=(
            "Detect security vulnerabilities, secret leaks, auth/z gaps, and risky "
            "dependency or data-handling patterns in the diff. Output JSON findings."
        ),
        backstory=(
            "You think like both an attacker and a security engineer, focusing on "
            "threat models, exploitability, and mitigations."
        ),
    )


def create_performance_reliability_agent() -> Agent:
    return _make_agent(
        role="Performance & Reliability Reviewer",
        goal=(
            "Spot performance regressions, concurrency issues, resource leaks, and "
            "resilience gaps in the diff. Output JSON findings."
        ),
        backstory=(
            "You optimize systems for throughput, latency, and stability while "
            "keeping failure modes in mind."
        ),
    )


def create_testing_ux_reviewer_agent() -> Agent:
    return _make_agent(
        role="Testing & UX Reviewer",
        goal=(
            "Identify missing or weak tests, flaky patterns, and user-facing/API "
            "regressions. Output JSON findings plus suggested test cases."
        ),
        backstory=(
            "You ensure changes are verifiable, well-covered, and considerate of the "
            "developer or end-user experience."
        ),
    )


def create_report_composer_agent() -> Agent:
    return _make_agent(
        role="Report Composer",
        goal=(
            "Merge and deduplicate findings from all agents, enforce schema, and "
            "produce the final structured review output."
        ),
        backstory=(
            "You synthesize results into a concise report with consistent severities, "
            "clear summaries, and actionable fixes."
        ),
        tools=[post_merge_request_comment],
    )
