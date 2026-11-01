from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


@lru_cache
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache
def get_vector_store() -> Chroma:
    Path(settings.chroma_directory).mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_directory,
    )


def add_chunks(chunks):
    if not chunks:
        return 0

    store = get_vector_store()
    ids = [chunk.metadata["chunk_id"] for chunk in chunks]

    store.add_documents(chunks, ids=ids)

    return len(chunks)


def search_chunks(query: str, k: int | None = None):
    return get_vector_store().similarity_search(
        query,
        k=k or settings.retrieval_k
    )


def list_indexed_documents():
    collection = get_vector_store()._collection

    result = collection.get(include=["metadatas"])

    unique = {}

    for metadata in result.get("metadatas", []) or []:
        source = metadata.get("source", "unknown")

        entry = unique.setdefault(
            source,
            {
                "source": source,
                "source_type": metadata.get("source_type", "unknown"),
                "chunks": 0
            }
        )

        entry["chunks"] += 1

    return sorted(
        unique.values(),
        key=lambda item: item["source"]
    )


def delete_indexed_document(source: str):
    collection = get_vector_store()._collection

    result = collection.get(
        where={"source": source},
        include=["metadatas"]
    )

    ids = result.get("ids", [])
    metadatas = result.get("metadatas", []) or []

    if not ids:
        return {
            "deleted_chunks": 0,
            "deleted_files": 0
        }

    # Remove only the selected document's embeddings.
    collection.delete(ids=ids)

    # Remove original files when their storage paths are available.
    upload_dir = Path("./data/uploads").resolve()
    deleted_files = 0

    for metadata in metadatas:
        storage_path = metadata.get("storage_path")

        if not storage_path:
            continue

        file_path = Path(storage_path).resolve()

        # Prevent deletion outside the uploads directory.
        if file_path.parent == upload_dir and file_path.is_file():
            file_path.unlink()
            deleted_files += 1

    return {
        "deleted_chunks": len(ids),
        "deleted_files": deleted_files
    }