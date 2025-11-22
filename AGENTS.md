# AGENTS.md — Code Review Agent Roster

This project uses crewAI to run local-LLM agents against code diffs. Below is the current, wired-up agent plus the recommended team for a comprehensive review pipeline.

## Current (implemented)
- **Senior Code Reviewer** (`app/crew/agents.py`): Uses the configured OpenAI-compatible LLM (`LLM_MODEL_NAME`, `LLM_API_BASE`, `LLM_API_KEY`) to read a single-file diff and return ONLY JSON with findings (`severity`, `summary`, `description`, `suggested_fix`). The agent is bound to the `file_diff_review` task in `app/crew/tasks.py` and executed by `create_review_crew()` in `app/crew/crew_factory.py`.

## Recommended full crew
| Agent | Purpose | Inputs | Output | Status |
| --- | --- | --- | --- | --- |
| **Review Orchestrator** | Routes work, fans out tasks, deduplicates overlapping findings, enforces JSON schema, and merges reports. | MR metadata, file list, task configs | Consolidated findings payload + routing decisions | Planned |
| **Context Builder** | Collects file contents, diffs, blame history, and commit messages; prioritizes risky files. | Repo path, MR/commit refs, diffs | Structured context bundle per file (paths, diffs, language hints) | Planned |
| **Static Analysis Collector** | Runs linters/security tools (ruff, bandit, mypy, eslint, etc.) and normalizes outputs. | Paths/diffs, tool configs | Normalized static findings with severity + rule IDs | Planned |
| **Senior Code Reviewer (LLM)** | Generalist LLM reviewer for correctness, maintainability, and clarity. | Single-file diff context (as used today) | JSON findings list (severity, summary, description, suggested_fix) | Implemented |
| **Security Specialist (LLM)** | Focuses on vulns, auth/z, secrets, data handling, and supply-chain risks. | Diff + security checklist, deps manifest (when available) | Security-focused findings with exploit scenarios + mitigations | Planned |
| **Performance & Reliability Reviewer (LLM)** | Flags perf regressions, concurrency issues, resource leaks, and resiliency gaps. | Diff + runtime hints (language, framework) | Perf/reliability findings with benchmarks or guardrails | Planned |
| **Testing & UX Reviewer (LLM)** | Spots missing tests, flaky patterns, and user-facing regressions (APIs, CLI, UI). | Diff + existing tests + API/schema refs | Test/UX findings with suggested test cases | Planned |
| **Report Composer** | Ranks and deduplicates all findings, emits MR summary + inline-friendly payloads. | All findings from LLM + static agents | Sorted findings list + MR summary + inline comment candidates | Planned |

## Expected flow
1) Intake (Context Builder) gathers diffs and metadata.  
2) Static Analysis Collector runs tools; Orchestrator fans out LLM tasks per file/risk.  
3) LLM agents (Reviewer/Security/Performance/Testing) process assigned diffs.  
4) Report Composer merges/dedupes, enforces schema, and emits the final structured response.

## Implementation notes
- All agents should emit machine-readable JSON; keep `severity` within `["info","minor","major","critical"]`.  
- Reuse the LLM client setup in `app/crew/agents.py`; adjust `settings.LLM_*` or `.env` to swap models/endpoints.  
- Add new agents by mirroring the current agent factory pattern and registering them in a crew (see `create_review_crew()`).
