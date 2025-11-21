# app/crew/agents.py
from crewai import Agent, LLM

from app.config import settings


def create_code_reviewer_agent() -> Agent:
    """
    Minimal agent that uses your local LLM.
    You will need to configure crewAI to use an OpenAI-compatible client
    pointing to your local inference server in your global setup.
    """
    llm = LLM(
        model=settings.LLM_MODEL_NAME,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=0.0,
    )

    return Agent(
        role="Senior Code Reviewer",
        goal=(
            "Review the given code diff and identify potential issues, "
            "returning ONLY structured JSON with a list of findings."
        ),
        backstory=(
            "You are an experienced software engineer responsible for code quality, "
            "security, and maintainability in a large codebase."
        ),
        verbose=False,
        llm=llm,
    )
