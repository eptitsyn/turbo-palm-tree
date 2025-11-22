# app/crew/agents.py
from functools import lru_cache

from crewai import Agent, LLM

from app.config import settings


@lru_cache(maxsize=1)
def _default_llm() -> LLM:
    """Общая конфигурация LLM для всех агентов."""
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
        role="Координатор ревью",
        goal=(
            "Спланируй и распределяй ревью, убедись что каждый профильный агент "
            "покрывает свою область, а вывод остается в JSON‑схеме."
        ),
        backstory=(
            "Ты координируешь AI‑ревьюеров, устраняешь дубли и формируешь сжатый "
            "план ревью для команды."
        ),
        allow_delegation=False,
    )


def create_context_builder_agent() -> Agent:
    return _make_agent(
        role="Сборщик контекста",
        goal=(
            "Нормализуй diff_context в структурированный пакет с метаданными "
            "файла, рисками и кратким описанием изменений."
        ),
        backstory=(
            "Ты готовишь пригодный для работы контекст, чтобы другие агенты "
            "занимались анализом, а не сбором данных."
        ),
    )


def create_static_analysis_agent() -> Agent:
    return _make_agent(
        role="Сборщик статического анализа",
        goal=(
            "Запусти или сформируй вывод статанализа (ruff, mypy, bandit, eslint и др.) "
            "для указанного diff и верни нормализованные находки."
        ),
        backstory=(
            "Ты собираешь и нормализуешь вывод статических инструментов в единый "
            "JSON‑формат."
        ),
    )


def create_code_reviewer_agent() -> Agent:
    """
    Generalist LLM reviewer focusing on correctness, maintainability, and clarity.
    """
    return _make_agent(
        role="Старший ревьюер кода",
        goal=(
            "Проверь данный diff и найди потенциальные проблемы, "
            "верни ТОЛЬКО структурированный JSON со списком находок."
        ),
        backstory=(
            "Ты опытный инженер, отвечающий за качество, безопасность и поддержку "
            "кода в крупной кодовой базе."
        ),
    )


def create_security_reviewer_agent() -> Agent:
    return _make_agent(
        role="Специалист по безопасности",
        goal=(
            "Найди уязвимости, утечки секретов, пробелы в auth/z и рискованные "
            "шаблоны зависимостей или работы с данными в diff. Вывод — JSON находок."
        ),
        backstory=(
            "Ты думаешь как атакующий и как инженер безопасности, фокусируясь на "
            "моделях угроз, эксплуатируемости и мерах защиты."
        ),
    )


def create_performance_reliability_agent() -> Agent:
    return _make_agent(
        role="Ревьюер производительности и надежности",
        goal=(
            "Заметь регрессии по производительности, проблемы конкурентности, "
            "утечки ресурсов и пробелы в устойчивости в diff. Вывод — JSON находок."
        ),
        backstory=(
            "Ты оптимизируешь системы по пропускной способности, задержке и стабильности, "
            "держишь в уме сценарии сбоев."
        ),
    )


def create_testing_ux_reviewer_agent() -> Agent:
    return _make_agent(
        role="Ревьюер тестирования и UX",
        goal=(
            "Найди отсутствующие или слабые тесты, флейки и регрессии в UX/API. "
            "Вывод — JSON находок и предложенные тест-кейсы."
        ),
        backstory=(
            "Ты следишь, чтобы изменения были проверяемыми, хорошо покрытыми и учитывали "
            "опыт разработчика и конечного пользователя."
        ),
    )


def create_report_composer_agent() -> Agent:
    return _make_agent(
        role="Сборщик отчета",
        goal=(
            "Объедини и дедуплицируй находки всех агентов, соблюдай схему и "
            "сформируй итоговый структурированный отчет."
        ),
        backstory=(
            "Ты собираешь результаты в короткий отчет с единообразными уровнями, "
            "четкими резюме и применимыми исправлениями."
        ),
    )
