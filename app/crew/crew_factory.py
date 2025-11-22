# app/crew/crew_factory.py
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from crewai import Crew, Process

try:
    import json_repair
except Exception:  # pragma: no cover - optional dependency
    json_repair = None

from app.crew.gitlab_notes import (
    post_findings_note,
    post_progress_note,
    update_progress_note,
)
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

# Telemetry/remote tracing: default off, opt-in via CREW_ENABLE_CLOUD_TRACING=true.
ENABLE_CLOUD_TRACING = os.getenv("CREW_ENABLE_CLOUD_TRACING", "false").lower() == "true"
if ENABLE_CLOUD_TRACING:
    os.environ["OTEL_SDK_DISABLED"] = "false"
    os.environ.setdefault("CREWAI_TRACING_ENABLED", "true")
else:
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")

# Place crew storage in a writable temp directory to avoid read-only DB errors.
os.environ.setdefault(
    "CREWAI_STORAGE_DIR", str(Path(tempfile.gettempdir()) / "crewai_storage")
)
USE_STUB_LLM = os.getenv("CREW_USE_STUB_LLM", "false").lower() == "true"
FALLBACK_TO_STUB_ON_ERROR = (
    os.getenv("CREW_FALLBACK_TO_STUB_ON_ERROR", "true").lower() == "true"
)
CREW_CACHE_ENABLED = os.getenv("CREW_CACHE_ENABLED", "true").lower() == "true"

# Cache a single Crew instance to avoid rebuilding agents/tasks on every call.
_CREW_CACHE: Crew | None = None


def _stub_findings(diff_context: dict[str, Any]) -> list[dict[str, Any]]:
    """Оффлайн-резерв, если LLM недоступен."""
    changes = diff_context.get("changes") or []
    file_path = "<unknown>"
    if changes and isinstance(changes, list):
        first = changes[0] or {}
        file_path = first.get("new_path") or first.get("old_path") or "<unknown>"
        diff = first.get("diff", "")
        added_lines = sum(1 for line in diff.splitlines() if line.startswith("+"))
        removed_lines = sum(1 for line in diff.splitlines() if line.startswith("-"))
    else:
        diff = diff_context.get("diff", "")
        added_lines = sum(1 for line in diff.splitlines() if line.startswith("+"))
        removed_lines = sum(1 for line in diff.splitlines() if line.startswith("-"))
    language = diff_context.get("language", "unknown")
    return [
        {
            "severity": "info",
            "summary": "Черновое ревью (LLM оффлайн)",
            "description": (
                "LLM недоступна; сгенерирован оффлайн-резервный отчет. "
                f"Файл: {file_path}, язык: {language}, "
                f"added_lines={added_lines}, removed_lines={removed_lines}."
            ),
            "suggested_fix": "Запусти с доступной LLM, чтобы получить реальные находки.",
            "source": "stub",
        }
    ]


def _build_review_crew() -> Crew:
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
        process=Process.hierarchical,
        manager_agent=orchestrator,
        tracing=ENABLE_CLOUD_TRACING,
        verbose=True,
    )


def create_review_crew() -> Crew:
    """
    Create (or reuse) the crew responsible for running code review.

    When CREW_CACHE_ENABLED=true (default), the Crew is cached to avoid
    reconstructing agents and tasks for every run. Set to false if you
    need a fresh Crew per invocation (e.g., hot-reload scenarios).
    """
    global _CREW_CACHE

    if CREW_CACHE_ENABLED and _CREW_CACHE is not None:
        return _CREW_CACHE

    crew = _build_review_crew()
    if CREW_CACHE_ENABLED:
        _CREW_CACHE = crew
    return crew


def _parse_json_like(raw: Any) -> Any | None:
    """Try to parse arbitrary output into JSON-compatible python objects."""
    if isinstance(raw, (dict, list)):
        return raw
    text = str(raw)
    for parser in (json.loads,):
        try:
            return parser(text)
        except Exception:
            continue
    if json_repair is not None:
        try:
            return json_repair.loads(text)
        except Exception:
            return None
    return None


def run_file_diff_review(diff_context: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Execute the crew on a diff context and return structured findings.

    Always returns a list of dicts for mypy compatibility.
    """

    project_id = diff_context.get("project_id")
    mr_iid = diff_context.get("mr_iid")

    progress_note_id = diff_context.get("progress_note_id")
    if progress_note_id is None:
        progress_note = post_progress_note(project_id, mr_iid)
        if isinstance(progress_note, dict):
            note = progress_note.get("note")
            if isinstance(note, dict):
                progress_note_id = note.get("id") or note.get("note_id")

    crew = create_review_crew()
    kickoff_inputs = {
        "diff_context": diff_context,
        "project_id": project_id,
        "mr_iid": mr_iid,
        "project_path": diff_context.get("project_path"),
    }
    try:
        result = crew.kickoff(inputs=kickoff_inputs)
    except Exception as exc:  # noqa: BLE001
        if USE_STUB_LLM or FALLBACK_TO_STUB_ON_ERROR:
            findings = _stub_findings(diff_context)
            update_progress_note(project_id, mr_iid, progress_note_id, findings)
            return findings
        return [
            {
                "severity": "major",
                "summary": "Запуск агента завершился с ошибкой",
                "description": (
                    "Агент ревью не смог выполниться. Убедись, что доступна совместимая "
                    "LLM (OpenAI-style) и заданы корректные креды."
                ),
                "raw_output": str(exc),
            }
        ]

    # String → wrap into a one-item findings list
    if isinstance(result, str):
        findings_list = [
            {
                "severity": "info",
                "summary": "Crew вернул сырой текст",
                "raw_output": result,
            }
        ]
        note_result = post_findings_note(
            project_id, mr_iid, findings_list, note_id=progress_note_id
        )
        if note_result and note_result.get("status") != "ok":
            findings_list.append(
                {
                    "severity": "info",
                    "summary": "Ошибка отправки заметки в GitLab",
                    "raw_output": str(note_result),
                }
            )
        update_progress_note(project_id, mr_iid, progress_note_id, findings_list)
        return findings_list

    # Dict → extract findings
    if isinstance(result, dict):
        findings = result.get("findings", None)

        if isinstance(findings, list):
            out: list[dict[str, Any]] = []
            for item in findings:
                if isinstance(item, dict):
                    out.append(item)
            note_result = post_findings_note(project_id, mr_iid, out, note_id=progress_note_id)
            if note_result and note_result.get("status") != "ok":
                out.append(
                    {
                        "severity": "info",
                        "summary": "Ошибка отправки заметки в GitLab",
                        "raw_output": str(note_result),
                    }
                )
            update_progress_note(project_id, mr_iid, progress_note_id, out)
            return out

        # Unexpected "findings"
        findings_list = [
            {
                "severity": "info",
                "summary": "Неожиданный формат 'findings' в выводе crew",
                "raw_output": str(findings),
            }
        ]
        note_result = post_findings_note(
            project_id, mr_iid, findings_list, note_id=progress_note_id
        )
        if note_result and note_result.get("status") != "ok":
            findings_list.append(
                {
                    "severity": "info",
                    "summary": "Ошибка отправки заметки в GitLab",
                    "raw_output": str(note_result),
                    }
                )
        update_progress_note(project_id, mr_iid, progress_note_id, findings_list)
        return findings_list

    # List → treat as findings list (already aggregated)
    if isinstance(result, list):
        out: list[dict[str, Any]] = []
        for item in result:
            if isinstance(item, dict):
                out.append(item)
        if not out:
            out = [
                {
                    "severity": "info",
                    "summary": "Crew вернул список без элементов-словарей",
                    "raw_output": str(result),
                }
            ]
        note_result = post_findings_note(project_id, mr_iid, out, note_id=progress_note_id)
        if note_result and note_result.get("status") != "ok":
            out.append(
                {
                    "severity": "info",
                    "summary": "Ошибка отправки заметки в GitLab",
                    "raw_output": str(note_result),
                }
            )
        update_progress_note(project_id, mr_iid, progress_note_id, out)
        return out

    # Try to parse JSON-like string output from crew objects
    parsed = _parse_json_like(result)

    if isinstance(parsed, dict):
        parsed_findings = parsed.get("findings")
        if isinstance(parsed_findings, list):
            out: list[dict[str, Any]] = []
            for item in parsed_findings:
                if isinstance(item, dict):
                    out.append(item)
            if not out:
                out = [
                    {
                        "severity": "info",
                        "summary": "JSON вывод не содержит валидных элементов findings",
                        "raw_output": str(parsed),
                    }
                ]
            note_result = post_findings_note(project_id, mr_iid, out, note_id=progress_note_id)
            if note_result and note_result.get("status") != "ok":
                out.append(
                    {
                        "severity": "info",
                        "summary": "Ошибка отправки заметки в GitLab",
                        "raw_output": str(note_result),
                    }
                )
            update_progress_note(project_id, mr_iid, progress_note_id, out)
            return out
        # Dict without findings → report gracefully
        findings_list = [
            {
                "severity": "info",
                "summary": "JSON вывод без поля findings",
                "raw_output": str(parsed),
            }
        ]
        note_result = post_findings_note(
            project_id, mr_iid, findings_list, note_id=progress_note_id
        )
        if note_result and note_result.get("status") != "ok":
            findings_list.append(
                {
                    "severity": "info",
                    "summary": "Ошибка отправки заметки в GitLab",
                    "raw_output": str(note_result),
                }
            )
        update_progress_note(project_id, mr_iid, progress_note_id, findings_list)
        return findings_list

    if isinstance(parsed, list):
        out: list[dict[str, Any]] = []
        for item in parsed:
            if isinstance(item, dict):
                out.append(item)
        if not out:
            out = [
                {
                    "severity": "info",
                    "summary": "JSON список без элементов-словарей",
                    "raw_output": str(parsed),
                }
            ]
        note_result = post_findings_note(project_id, mr_iid, out, note_id=progress_note_id)
        if note_result and note_result.get("status") != "ok":
            out.append(
                {
                    "severity": "info",
                    "summary": "Ошибка отправки заметки в GitLab",
                    "raw_output": str(note_result),
                }
            )
        update_progress_note(project_id, mr_iid, progress_note_id, out)
        return out

    # Completely unexpected type
    findings_list = [
        {
            "severity": "info",
            "summary": "Crew вернул неподдерживаемый тип вывода",
            "raw_output": str(result),
        }
    ]
    note_result = post_findings_note(
        project_id, mr_iid, findings_list, note_id=progress_note_id
    )
    if note_result and note_result.get("status") != "ok":
        findings_list.append(
            {
                "severity": "info",
                "summary": "GitLab note post failed",
                "raw_output": str(note_result),
            }
        )
    update_progress_note(project_id, mr_iid, progress_note_id, findings_list)
    return findings_list
