# app/crew/tasks.py
from crewai import Agent, Task


def create_review_orchestration_task(
    agent: Agent | None = None, context: list[Task] | None = None
) -> Task:
    description = """
Ты координируешь ревью кода для MR целиком.

Текущие входные данные:
- project_id: {project_id}
- mr_iid: {mr_iid}
- project_path: {project_path}
- diff_context: {diff_context}

Вход:
- diff_context: {"changes": [...], ...}; каждая change имеет поля new_path/old_path/diff.
- project_id: числовой/строковый ID проекта
- mr_iid: IID merge request
- project_path: путь проекта в GitLab (если есть)

Твоя задача:
- Выбери, какие файлы стоит анализировать (не бери каждый файл), обоснуй выбор.
- Распредели файлы по агентам/специализациям.
- Выдели самые рискованные зоны и вероятные сбои.
- Оставь вывод машинно-читаемым.

Вывод:
Верни ТОЛЬКО JSON:
{
  "selected_files": ["path1", "path2"],
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
Нормализуй diff_context MR в структурированный пакет для последующих агентов.

Текущие входные данные:
- project_id: {project_id}
- mr_iid: {mr_iid}
- project_path: {project_path}
- diff_context: {diff_context}

Включи:
- список изменений (changes), включи короткую статистику по каждому файлу
- идентификаторы MR (project_id, mr_iid) и, если есть, repo_url/project_path
- краткую цель изменений и область покрытия
- быстрые риск-заметки (security/perf/testing)
- количество добавлений/удалений
- если переданы project_id и mr_iid: дерни GitLab tool, чтобы получить контекст MR
  (метаданные, заметки) и включи это в вывод
- если указан repo_url: сделай поверхностный clone, прочитай изменения из MR/коммита,
  извлеки сигнатуры методов/функций без чтения полных тел, когда возможно.

Вывод:
Верни ТОЛЬКО JSON:
{
  "changes": [{"file_path": "...", "language": "...", "stats": {"added_lines": int, "removed_lines": int}}],
  "project_id": 123,
  "mr_iid": 5,
  "change_summary": "...",
  "risk_notes": ["item"],
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
- diff_context и предоставленный контекст (список changes). Сфокусируйся только на выбранных файлаx из orchestration.selected_files.

Вывод:
Верни ТОЛЬКО JSON-список находок:
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

    Агент должен вернуть JSON-список находок.
    В MVP строгую схему не навязываем.
    """
    description = """
Тебе дан список изменений (changes). Не нужно анализировать каждый файл.
Фокусируйся только на файлах, которые выбрал тимлид (orchestration.selected_files)
или которые контекст подчёркивает как рискованные.

Для каждого выбранного файла возьми его diff/old_code/new_code и:
1. Найди проблемы корректности, безопасности, производительности, стиля и поддержки.
2. На каждую проблему сформируй элемент:
   - severity: одно из ["info", "minor", "major", "critical"]
   - summary: краткое одно предложение
   - description: подробности
   - suggested_fix: как исправить (опционально код)

Вывод:
Верни ТОЛЬКО JSON-список находок (можно агрегировать по файлам в полях).
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
Проведи ревью с фокусом на безопасность для выбранных файлов (orchestration.selected_files).

Учитывай:
- auth/z, секреты, криптография, инъекции, SSRF, RCE, десериализация, песочница
- утечки данных, логирование чувствительных данных, риски цепочки поставок
- эксплуатируемость и меры защиты

Вывод:
Верни ТОЛЬКО JSON-список находок (severity, summary, description, suggested_fix).
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
Проведи ревью производительности и надежности выбранных файлов (orchestration.selected_files).

Учитывай:
- временная/пространственная сложность, горячие пути, IO, аллокации, кеш, векторизацию
- конкурентность, блокировки, async, гонки
- устойчивость: ретраи, таймауты, backpressure, утечки ресурсов

Вывод:
Верни ТОЛЬКО JSON-список находок (severity, summary, description, suggested_fix).
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
Проведи ревью тестирования и UX/API только для выбранных файлов (orchestration.selected_files).

Учитывай:
- отсутствующие или слабые тесты, флейки, границы, негативные сценарии
- изменения контрактов API/CLI, сообщения об ошибках, логирование, телеметрию
- пользовательские регрессии или пробелы в документации

Вывод:
Верни ТОЛЬКО JSON-список находок (severity, summary, description, suggested_fix)
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

Если в inputs есть `project_id` и `mr_iid`, МОЖНО отправить короткую MR-заметку
через GitLab comment tool с топ-находками. Держи ее лаконичной.
"""
    return Task(
        description=description,
        expected_output="JSON object with summary plus merged findings array.",
        name="report_composer",
        agent=agent,
        context=context or [],
    )
