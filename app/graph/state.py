from typing import TypedDict, Any


class RAGState(TypedDict, total=False):
    question: str
    search_query: str
    query_type: str
    documents: list[Any]
    relevant_documents: list[Any]
    retry_count: int
    answer: str
    sources: list[dict]
    grading_notes: list[str]
