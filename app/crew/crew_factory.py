# app/crew/crew_factory.py
import os
import tempfile
from pathlib import Path
from typing import Any

from crewai import Crew, Process
from app.crew.tools.gitlab_tool import (
    post_merge_request_comment,
    update_merge_request_comment,
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

# Disable telemetry/remote tracing in constrained environments and place crew storage
# in a writable temp directory to avoid read-only DB errors.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault(
    "CREWAI_STORAGE_DIR", str(Path(tempfile.gettempdir()) / "crewai_storage")
)
USE_STUB_LLM = os.getenv("CREW_USE_STUB_LLM", "false").lower() == "true"
FALLBACK_TO_STUB_ON_ERROR = (
    os.getenv("CREW_FALLBACK_TO_STUB_ON_ERROR", "true").lower() == "true"
)
POST_GITLAB_NOTE = os.getenv("CREW_POST_GITLAB_NOTE", "true").lower() == "true"
POST_GITLAB_PROGRESS_NOTE = (
    os.getenv("CREW_POST_GITLAB_PROGRESS_NOTE", "true").lower() == "true"
)


def _stub_findings(diff_context: dict[str, Any]) -> list[dict[str, Any]]:
    """Оффлайн‑резерв, если LLM недоступен."""
    file_path = diff_context.get("file_path", "<unknown>")
    diff = diff_context.get("diff", "")
    language = diff_context.get("language", "unknown")
    added_lines = sum(1 for line in diff.splitlines() if line.startswith("+"))
    removed_lines = sum(1 for line in diff.splitlines() if line.startswith("-"))
    return [
        {
            "severity": "info",
            "summary": "Черновое ревью (LLM оффлайн)",
            "description": (
                "LLM недоступна; сгенерирован оффлайн‑резервный отчет. "
                f"Файл: {file_path}, язык: {language}, "
                f"added_lines={added_lines}, removed_lines={removed_lines}."
            ),
            "suggested_fix": "Запусти с доступной LLM, чтобы получить реальные находки.",
            "source": "stub",
        }
    ]


def _post_gitlab_note(
    project_id: Any, mr_iid: Any, findings: list[dict[str, Any]]
) -> dict[str, Any] | None:
    if not POST_GITLAB_NOTE:
        return None
    if not project_id or not mr_iid:
        return None

    top = findings[:5]
    lines = [f"Итоги ревью ({len(findings)} всего):"]
    for item in top:
        sev = item.get("severity", "info")
        summary = item.get("summary", "").strip() or "<no summary>"
        lines.append(f"- [{sev}] {summary}")
    if len(findings) > len(top):
        lines.append(f"...и ещё {len(findings) - len(top)}.")

    body = "\n".join(lines)
    return post_merge_request_comment(
        project_id=project_id, mr_iid=mr_iid, body=body
    )


def _post_progress_note(project_id: Any, mr_iid: Any) -> dict[str, Any] | None:
    if not POST_GITLAB_PROGRESS_NOTE or not project_id or not mr_iid:
        return None

    body = "🤖 Ревью запущено… агенты анализируют изменения."
    return post_merge_request_comment(project_id=project_id, mr_iid=mr_iid, body=body)


def _update_progress_note(
    project_id: Any,
    mr_iid: Any,
    note_id: Any,
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not POST_GITLAB_PROGRESS_NOTE or not project_id or not mr_iid or not note_id:
        return None

    top = findings[:5]
    lines = ["🤖 Ревью завершено. Находки:"]
    for item in top:
        sev = item.get("severity", "info")
        summary = item.get("summary", "").strip() or "<no summary>"
        lines.append(f"- [{sev}] {summary}")
    if len(findings) > len(top):
        lines.append(f"...и ещё {len(findings) - len(top)}.")

    body = "\n".join(lines)
    return update_merge_request_comment(
        project_id=project_id,
        mr_iid=mr_iid,
        note_id=note_id,
        body=body,
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
        tracing=False,
        verbose=True,
    )


def run_file_diff_review(diff_context: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Execute the crew on a diff context and return structured findings.

    Always returns a list of dicts for mypy compatibility.
    """

    project_id = diff_context.get("project_id")
    mr_iid = diff_context.get("mr_iid")

    progress_note = _post_progress_note(project_id, mr_iid)
    progress_note_id = None
    if isinstance(progress_note, dict):
        note = progress_note.get("note")
        if isinstance(note, dict):
            progress_note_id = note.get("id") or note.get("note_id")

    crew = create_review_crew()
    try:
        result = crew.kickoff(inputs={"diff_context": diff_context})
    except Exception as exc:  # noqa: BLE001
        if USE_STUB_LLM or FALLBACK_TO_STUB_ON_ERROR:
            findings = _stub_findings(diff_context)
            _update_progress_note(project_id, mr_iid, progress_note_id, findings)
            return findings
        return [
            {
                "severity": "major",
                "summary": "Запуск агента завершился с ошибкой",
                "description": (
                    "Агент ревью не смог выполниться. Убедись, что доступна совместимая "
                    "LLM (OpenAI‑style) и заданы корректные креды."
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
        note_result = _post_gitlab_note(project_id, mr_iid, findings_list)
        if note_result and note_result.get("status") != "ok":
            findings_list.append(
                {
                    "severity": "info",
                    "summary": "Ошибка отправки заметки в GitLab",
                    "raw_output": str(note_result),
                }
            )
        _update_progress_note(project_id, mr_iid, progress_note_id, findings_list)
        return findings_list

    # Dict → extract findings
    if isinstance(result, dict):
        findings = result.get("findings", None)

        if isinstance(findings, list):
            out: list[dict[str, Any]] = []
            for item in findings:
                if isinstance(item, dict):
                    out.append(item)
            note_result = _post_gitlab_note(project_id, mr_iid, out)
            if note_result and note_result.get("status") != "ok":
                out.append(
                {
                    "severity": "info",
                    "summary": "Ошибка отправки заметки в GitLab",
                    "raw_output": str(note_result),
                }
            )
            _update_progress_note(project_id, mr_iid, progress_note_id, out)
            return out

        # Unexpected "findings"
        findings_list = [
            {
                "severity": "info",
                "summary": "Неожиданный формат 'findings' в выводе crew",
                "raw_output": str(findings),
            }
        ]
        note_result = _post_gitlab_note(project_id, mr_iid, findings_list)
        if note_result and note_result.get("status") != "ok":
            findings_list.append(
                {
                    "severity": "info",
                    "summary": "Ошибка отправки заметки в GitLab",
                    "raw_output": str(note_result),
                }
            )
        _update_progress_note(project_id, mr_iid, progress_note_id, findings_list)
        return findings_list

    # Completely unexpected type
    findings_list = [
        {
            "severity": "info",
            "summary": "Crew вернул неподдерживаемый тип вывода",
            "raw_output": str(result),
        }
    ]
    note_result = _post_gitlab_note(project_id, mr_iid, findings_list)
    if note_result and note_result.get("status") != "ok":
        findings_list.append(
            {
                "severity": "info",
                "summary": "GitLab note post failed",
                "raw_output": str(note_result),
            }
        )
    _update_progress_note(project_id, mr_iid, progress_note_id, findings_list)
    return findings_list
