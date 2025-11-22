# app/crew/agents.py
from functools import lru_cache
from urllib.parse import urljoin, urlparse

from crewai import Agent, LLM
from crewai.tools.base_tool import BaseTool

from app.crew.tools.gitlab_tool import (
    fetch_merge_request_changes,
    fetch_merge_request_notes,
)
from app.crew.tools.repo_tool import (
    clone_repository,
    extract_python_signatures,
    list_repository_files,
)
from app.config import settings


@lru_cache(maxsize=1)
def _default_llm() -> LLM:
    """Общая конфигурация LLM для всех агентов."""
    return LLM(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        api_base=settings.LLM_API_BASE,
        timeout=settings.LLM_TIMEOUT,
        stream=settings.LLM_STREAM_CONNECTION,
        temperature=2.0,
    )


def _make_agent(role: str, goal: str, backstory: str, **kwargs) -> Agent:
    kwargs.setdefault("max_iter", settings.CREW_AGENT_MAX_ITER)
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True,
        llm=_default_llm(),
        **kwargs,
    )


class FetchMergeRequestChangesTool(BaseTool):
    name: str = "fetch_merge_request_changes"
    description: str = (
        "Получает изменения MR из GitLab. Аргументы: project_id, mr_iid."
    )

    def _run(
        self,
        project_id: int | str | None = None,
        mr_iid: int | str | None = None,
    ):
        if project_id is None or mr_iid is None:
            return {
                "status": "error",
                "error": "project_id and mr_iid are required",
            }
        return fetch_merge_request_changes(project_id=project_id, mr_iid=mr_iid)


class FetchMergeRequestNotesTool(BaseTool):
    name: str = "fetch_merge_request_notes"
    description: str = (
        "Получает список заметок MR из GitLab. Аргументы: project_id, mr_iid."
    )

    def _run(
        self,
        project_id: int | str | None = None,
        mr_iid: int | str | None = None,
    ):
        if project_id is None or mr_iid is None:
            return {
                "status": "error",
                "error": "project_id and mr_iid are required",
            }
        return fetch_merge_request_notes(project_id=project_id, mr_iid=mr_iid)


class CloneRepositoryTool(BaseTool):
    name: str = "clone_repository"
    description: str = (
        "Загружает репозиторий во временную папку и (опционально) переключается на ref/commit. "
        "Аргументы: repo_url (обязателен), ref, dest_dir, depth."
    )

    def _run(
        self,
        repo_url: str,
        ref: str | None = None,
        dest_dir: str | None = None,
        depth: int = 1,
    ):
        return clone_repository(
            repo_url=repo_url, ref=ref, dest_dir=dest_dir, depth=depth
        )


class ListRepositoryFilesTool(BaseTool):
    name: str = "list_repository_files"
    description: str = (
        "Возвращает список файлов репозитория (относительные пути). "
        "Аргументы: repo_path, max_files=5000, include_hidden=false."
    )

    def _run(
        self,
        repo_path: str,
        max_files: int = 5000,
        include_hidden: bool = False,
    ):
        return list_repository_files(
            repo_path=repo_path, max_files=max_files, include_hidden=include_hidden
        )


class ExtractPythonSignaturesTool(BaseTool):
    name: str = "extract_python_signatures"
    description: str = (
        "Извлекает сигнатуры функций/методов/классов из Python-файла. "
        "Аргументы: file_path."
    )

    def _run(self, file_path: str):
        return extract_python_signatures(file_path)


def create_review_orchestrator_agent() -> Agent:
    return _make_agent(
        role="Тимлид ревью MR",
        goal=(
            "Получить входной MR (project_id, mr_iid, project_path), быстро понять риск, "
            "раскидать задачи по агентам и следить, чтобы вывод был в корректной JSON-схеме."
        ),
        backstory=(
            "Ты тимлид команды AI-ревьюеров: умеешь быстро читать метаданные MR, "
            "ставить приоритеты и строго требуешь формального JSON-вывода без воды."
        ),
        allow_delegation=False,
    )


def create_context_builder_agent() -> Agent:
    tools: list[BaseTool] = [
        FetchMergeRequestChangesTool(),
        FetchMergeRequestNotesTool(),
    ]
    if settings.CREW_ENABLE_GIT_TOOLS:
        tools.extend(
            [
                CloneRepositoryTool(),
                ListRepositoryFilesTool(),
                ExtractPythonSignaturesTool(),
            ]
        )

    return _make_agent(
        role="Сборщик контекста MR",
        goal=(
            "Получить project_id/mr_iid/project_path (или repo_url), сходить в GitLab за MR, "
            "при необходимости клонировать репозиторий и вернуть нормализованный пакет "
            "diff_context с рисками и статистикой."
        ),
        backstory=(
            "Ты инженер платформы: умеешь опрашивать GitLab API, подтягивать заметки и diff, "
            "делать поверхностный git clone и собирать краткий контекст для остальных."
        ),
        tools=tools,
    )


def create_static_analysis_agent() -> Agent:
    return _make_agent(
        role="Сборщик статического анализа",
        goal=(
            "На базе diff_context и метаданных MR сформировать вывод статанализа "
            "(ruff, mypy, bandit, eslint и др.) или рассуждённые находки, вернуть "
            "нормализованный JSON."
        ),
        backstory=(
            "Ты интегратор инструментов: знаешь правила статанализа и выдаёшь единый "
            "JSON-формат для других агентов."
        ),
    )


def create_code_reviewer_agent() -> Agent:
    """
    Generalist LLM reviewer focusing on correctness, maintainability, and clarity.
    """
    return _make_agent(
        role="Старший ревьюер кода",
        goal=(
            "Проверить diff файла и связанные с MR метаданные, найти проблемы "
            "корректности/поддерживаемости, вернуть ТОЛЬКО JSON списка находок."
        ),
        backstory=(
            "Ты опытный инженер: быстро видишь дефекты, даёшь чёткие резюме и "
            "формализуешь вывод в JSON."
        ),
    )


def create_security_reviewer_agent() -> Agent:
    return _make_agent(
        role="Специалист по безопасности",
        goal=(
            "На основе diff и контекста MR найти уязвимости, утечки секретов, "
            "пробелы в auth/z и рискованные зависимости. Вывод — JSON находок."
        ),
        backstory=(
            "Ты миссек-инженер и блю-тимер: думаешь как атакующий, оцениваешь "
            "эксплуатируемость и предлагаешь mitigations в JSON."
        ),
    )


def create_performance_reliability_agent() -> Agent:
    return _make_agent(
        role="Ревьюер производительности и надёжности",
        goal=(
            "Замечать регрессии по производительности, проблемы конкурентности, "
            "утечки ресурсов и пробелы в устойчивости в diff/MR. Вывод — JSON находок."
        ),
        backstory=(
            "Ты SRE/перф-инженер: оптимизируешь throughput/latency, знаешь паттерны отказоустойчивости "
            "и описываешь риски компактно."
        ),
    )


def create_testing_ux_reviewer_agent() -> Agent:
    return _make_agent(
        role="Ревьюер тестирования и UX",
        goal=(
            "Найти отсутствующие или слабые тесты, флейки и регрессии в UX/API по diff и MR. "
            "Вывод — JSON находок + предложенные тест-кейсы."
        ),
        backstory=(
            "Ты QA/UX-специалист: заботишься о проверяемости, пользовательских контрактах "
            "и качестве сообщений об ошибках."
        ),
    )


def create_report_composer_agent() -> Agent:
    return _make_agent(
        role="Сборщик отчёта",
        goal=(
            "Объединить и дедуплицировать находки всех агентов, соблюсти схему и "
            "сформировать итоговый структурированный отчёт в JSON."
        ),
        backstory=(
            "Ты технический писатель/аналитик: умеешь ранжировать, кратко резюмировать "
            "и выдавать чистый JSON для публикации."
        ),
    )
