from pathlib import Path
from uuid import uuid4
import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.graph.workflow import run_rag
from app.ingestion.loader import load_files, load_urls, split_documents
from app.retrieval.vector_store import (
    add_chunks,
    list_indexed_documents,
    delete_indexed_document,
)

router = APIRouter()

UPLOAD_DIR = Path("./data/uploads")
FEEDBACK_FILE = Path("./data/feedback.jsonl")


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class FeedbackRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1)
    rating: str = Field(pattern="^(up|down)$")
    comment: str | None = Field(default=None, max_length=2000)


@router.post("/query")
def query_documents(request: QueryRequest):
    try:
        return run_rag(request.question)

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {exc}"
        ) from exc


@router.post("/ingest")
async def ingest_documents(
    files: list[UploadFile] = File(default=[]),
    urls: str | None = Form(default=None)
):
    documents = []
    errors = []

    if files:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        for upload in files:
            suffix = Path(upload.filename or "").suffix.lower()

            if suffix not in {".txt", ".md", ".html", ".htm", ".pdf"}:
                errors.append({
                    "file": upload.filename,
                    "error": "Unsupported file type"
                })
                continue

            destination = UPLOAD_DIR / f"{uuid4().hex}{suffix}"

            try:
                destination.write_bytes(await upload.read())

                loaded_documents = load_files([str(destination)])

                for document in loaded_documents:
                    document.metadata["source"] = (
                        upload.filename or destination.name
                    )

                    document.metadata["storage_path"] = str(
                        destination.resolve()
                    )

                documents.extend(loaded_documents)

            except Exception as exc:
                errors.append({
                    "file": upload.filename,
                    "error": str(exc)
                })

                destination.unlink(missing_ok=True)

    if urls:
        for url in [item.strip() for item in urls.splitlines() if item.strip()]:
            try:
                documents.extend(load_urls([url]))

            except Exception as exc:
                errors.append({
                    "url": url,
                    "error": str(exc)
                })

    if not documents:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No documents were ingested",
                "errors": errors
            }
        )

    try:
        chunks = split_documents(documents)
        count = add_chunks(chunks)

        return {
            "message": "Ingestion completed",
            "documents_received": len(documents),
            "chunks_indexed": count,
            "errors": errors
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {exc}"
        ) from exc


@router.get("/documents")
def get_documents():
    try:
        documents = list_indexed_documents()

        return {
            "total_documents": len(documents),
            "documents": documents
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not list documents: {exc}"
        ) from exc


@router.delete("/documents/{source}")
def remove_document(source: str):
    try:
        result = delete_indexed_document(source)

        if result["deleted_chunks"] == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{source}' was not found."
            )

        return {
            "message": f"Document '{source}' deleted successfully.",
            **result
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not delete document: {exc}"
        ) from exc


@router.post("/feedback", status_code=201)
def submit_feedback(request: FeedbackRequest):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

    record = request.model_dump()

    record["created_at"] = (
        __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat()
    )

    with FEEDBACK_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "message": "Feedback recorded",
        "rating": request.rating
    }