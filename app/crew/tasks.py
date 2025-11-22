# app/crew/tasks.py
from crewai import Agent, Task


def create_review_orchestration_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Ты координируешь ревью кода для одного diff_context.

Текущие входные данные:
- project_id: {project_id}
- mr_iid: {mr_iid}
- project_path: {project_path}
- diff_context: {diff_context}

Вход:
- diff_context: {file_path, language, diff, old_code, new_code}
- project_id: числовой/строковый ID проекта
- mr_iid: IID merge request
- project_path: путь проекта в GitLab (если есть)

Твоя задача:
- Дай короткий план, какие специализации смотрят на какие риски.
- Выдели самые рискованные зоны и вероятные сбои.
- Оставь вывод машинно‑читаемым.

Вывод:
Верни ТОЛЬКО JSON:
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
        context=context or [],
    )


def create_context_builder_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Нормализуй diff_context в структурированный пакет для последующих агентов.

Текущие входные данные:
- project_id: {project_id}
- mr_iid: {mr_iid}
- project_path: {project_path}
- diff_context: {diff_context}

Включи:
- метаданные файла (путь, язык)
- идентификаторы MR (project_id, mr_iid) и, если есть, repo_url/project_path
- краткую цель изменений и область покрытия
- быстрые риск‑заметки (security/perf/testing)
- количество добавлений/удалений
- если переданы project_id и mr_iid: дерни GitLab tool, чтобы получить контекст MR
  (метаданные, заметки) и включи это в вывод
- если указан repo_url: сделай поверхностный clone, прочитай изменения из MR/коммита,
  извлеки сигнатуры методов/функций без чтения полных тел, когда возможно.

Вывод:
Верни ТОЛЬКО JSON:
{
  "file_path": "...",
  "language": "...",
  "project_id": 123,
  "mr_iid": 5,
  "change_summary": "...",
  "risk_notes": ["item"],
  "stats": {"added_lines": int, "removed_lines": int},
  "diff": "...",
  "old_code": "...",
  "new_code": "...",
  "signatures": [{"name": "...", "args": ["..."]}],
  "mr_context": {"title": "...", "notes": ["..."]}
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
Работай как сборщик статанализа. Если инструменты недоступны, рассуждай по diff.

Вход:
- diff_context и предоставленный контекст.

Вывод:
Верни ТОЛЬКО JSON‑список находок:
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
    Ожидается `diff_context` во входе, содержит:
        - file_path
        - language
        - diff
        - old_code
        - new_code

    Агент должен вернуть JSON‑список находок.
    В MVP строгую схему не навязываем.
    """
    description = """
Тебе дано изменение кода (diff) одного файла.

Вход:
- file_path: путь к файлу
- language: язык программирования (например python, javascript)
- diff: unified diff фрагмент
- old_code: предыдущая версия
- new_code: новая версия

Твоя задача:
1. Найди проблемы корректности, безопасности, производительности, стиля и поддержки.
2. На каждую проблему сформируй элемент:
   - severity: одно из ["info", "minor", "major", "critical"]
   - summary: краткое одно предложение
   - description: подробности
   - suggested_fix: как исправить (опционально код)

Вывод:
Верни ТОЛЬКО JSON с верхнеуровневым списком находок, например:

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
Проведи ревью с фокусом на безопасность для diff_context.

Учитывай:
- auth/z, секреты, криптография, инъекции, SSRF, RCE, десериализация, песочница
- утечки данных, логирование чувствительных данных, риски цепочки поставок
- эксплуатируемость и меры защиты

Вывод:
Верни ТОЛЬКО JSON‑список находок (severity, summary, description, suggested_fix).
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
Проведи ревью производительности и надежности diff_context.

Учитывай:
- временная/пространственная сложность, горячие пути, IO, аллокации, кеш, векторизацию
- конкурентность, блокировки, async, гонки
- устойчивость: ретраи, таймауты, backpressure, утечки ресурсов

Вывод:
Верни ТОЛЬКО JSON‑список находок (severity, summary, description, suggested_fix).
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
Проведи ревью тестирования и UX/API для diff_context.

Учитывай:
- отсутствующие или слабые тесты, флейки, границы, негативные сценарии
- изменения контрактов API/CLI, сообщения об ошибках, логирование, телеметрию
- пользовательские регрессии или пробелы в документации

Вывод:
Верни ТОЛЬКО JSON‑список находок (severity, summary, description, suggested_fix)
и добавь массив `suggested_tests`, когда уместно.
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
Объедини и дедуплицируй находки всех задач ревью. Соблюдай схему.

Вход:
- выводы оркестрации, контекста, статанализа и всех ревьюеров.

Вывод:
Верни ТОЛЬКО JSON:
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

Если в inputs есть `project_id` и `mr_iid`, МОЖНО отправить короткую MR‑заметку
через GitLab comment tool с топ‑находками. Держи ее лаконичной.
"""
    return Task(
        description=description,
        expected_output="JSON object with summary plus merged findings array.",
        name="report_composer",
        agent=agent,
        context=context or [],
    )
