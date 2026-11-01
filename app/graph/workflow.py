from langgraph.graph import StateGraph, START, END

from app.config import settings
from app.graph.state import RAGState
from app.graph.nodes import query_analysis, retrieve, grade_documents, rewrite_query, generate_answer


def route_after_grading(state: RAGState) -> str:
    if state.get("relevant_documents"):
        return "generate"
    if state.get("retry_count", 0) < settings.max_retries:
        return "rewrite"
    return "generate"


def build_graph():
    graph = StateGraph(RAGState)
    graph.add_node("query_analysis", query_analysis)
    graph.add_node("retrieve", retrieve)
    graph.add_node("grade_documents", grade_documents)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("generate", generate_answer)

    graph.add_edge(START, "query_analysis")
    graph.add_edge("query_analysis", "retrieve")
    graph.add_edge("retrieve", "grade_documents")
    graph.add_conditional_edges("grade_documents", route_after_grading, {
        "generate": "generate",
        "rewrite": "rewrite_query",
    })
    graph.add_edge("rewrite_query", "retrieve")
    graph.add_edge("generate", END)
    return graph.compile()


rag_graph = build_graph()


def run_rag(question: str) -> dict:
    result = rag_graph.invoke({"question": question, "retry_count": 0})
    return {
        "question": question,
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "query_type": result.get("query_type", "other"),
        "retries": result.get("retry_count", 0),
    }
