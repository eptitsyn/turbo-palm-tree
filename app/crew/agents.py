# app/crew/agents.py
from crewai import Agent

from app.config import settings


def create_code_reviewer_agent() -> Agent:
    """
    Minimal agent that uses your local LLM.
    You will need to configure crewAI to use an OpenAI-compatible client
    pointing to your local inference server in your global setup.
    """
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
        # In crewAI >= 0.28 you can pass model provider config via env or kwargs
        llm=settings.LLM_MODEL_NAME,  # adjust based on crewAI version
    )
