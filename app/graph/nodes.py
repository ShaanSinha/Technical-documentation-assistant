from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.config import settings
from app.graph.state import RAGState
from app.retrieval.vector_store import search_chunks


def get_llm():
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")
    return ChatGroq(model=settings.groq_model, temperature=0, api_key=settings.groq_api_key)


def _text(response) -> str:
    return response.content if isinstance(response.content, str) else str(response.content)


def query_analysis(state: RAGState) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You improve search queries for technical documentation. Return only a concise search query. Preserve technical names and intent."),
        ("human", "Question: {question}\nRewrite this as an effective documentation search query."),
    ])
    rewritten = _text((prompt | get_llm()).invoke({"question": state["question"]})).strip()
    classification_prompt = ChatPromptTemplate.from_messages([
        ("system", "Classify the question into exactly one category: conceptual, how-to, troubleshooting, api-reference, other. Return only the category."),
        ("human", "{question}"),
    ])
    query_type = _text((classification_prompt | get_llm()).invoke({"question": state["question"]})).strip().lower()
    allowed = {"conceptual", "how-to", "troubleshooting", "api-reference", "other"}
    if query_type not in allowed:
        query_type = "other"
    return {"search_query": rewritten or state["question"], "query_type": query_type}


def retrieve(state: RAGState) -> dict:
    docs = search_chunks(state.get("search_query") or state["question"])
    return {"documents": docs}


def grade_documents(state: RAGState) -> dict:
    docs = state.get("documents", [])
    if not docs:
        return {"relevant_documents": [], "grading_notes": ["No documents retrieved."]}

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strict relevance grader for technical documentation. Decide whether the passage contains information useful for answering the question. Reply with only YES or NO."),
        ("human", "Question: {question}\n\nPassage:\n{passage}\n\nRelevant?"),
    ])
    chain = prompt | get_llm()
    relevant, notes = [], []
    for doc in docs:
        verdict = _text(chain.invoke({"question": state["question"], "passage": doc.page_content[:5000]})).strip().upper()
        if verdict.startswith("YES"):
            relevant.append(doc)
            notes.append("relevant")
        else:
            notes.append("irrelevant")
    return {"relevant_documents": relevant, "grading_notes": notes}


def rewrite_query(state: RAGState) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Rewrite a technical documentation search query to find different, more useful evidence. Return only the query. Do not answer the question."),
        ("human", "Original question: {question}\nPrevious search: {search_query}\nAttempt: {retry_count}\nCreate a better search query."),
    ])
    rewritten = _text((prompt | get_llm()).invoke({
        "question": state["question"],
        "search_query": state.get("search_query", state["question"]),
        "retry_count": state.get("retry_count", 0) + 1,
    })).strip()
    return {"search_query": rewritten or state["question"], "retry_count": state.get("retry_count", 0) + 1}


def generate_answer(state: RAGState) -> dict:
    docs = state.get("relevant_documents", [])
    if not docs:
        return {
            "answer": "I don't know based on the indexed documentation. The retrieved passages were insufficient or did not pass relevance grading.",
            "sources": [],
        }

    context_parts, sources = [], []
    seen = set()
    for index, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        chunk_id = doc.metadata.get("chunk_id", str(index))
        context_parts.append(f"[Source {index}: {source} | chunk {chunk_id}]\n{doc.page_content}")
        key = (source, chunk_id)
        if key not in seen:
            sources.append({"source": source, "chunk_id": chunk_id, "title": doc.metadata.get("title", "")})
            seen.add(key)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a technical documentation assistant. Answer only using the supplied context. If the context does not support a claim, say so. Be precise and explain steps when useful. Cite claims inline using [Source N]. Never invent APIs or facts."),
        ("human", "Question: {question}\nQuestion type: {query_type}\n\nContext:\n{context}\n\nWrite the answer with inline source citations."),
    ])
    answer = _text((prompt | get_llm()).invoke({
        "question": state["question"],
        "query_type": state.get("query_type", "other"),
        "context": "\n\n---\n\n".join(context_parts),
    })).strip()
    return {"answer": answer, "sources": sources}
