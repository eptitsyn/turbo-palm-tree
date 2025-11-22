# app/crew/tools/vector_search_tool.py
from typing import List


def vector_search_tool(query: str) -> List[str]:
    """
    Retrieve similar code examples or explanations from Qdrant vector DB.
    Stub for now — later connect to Qdrant client.
    """
    # TODO: Integrate with Qdrant or LangChain retriever
    return [f"[Stub] Related item for query: '{query}'"]
