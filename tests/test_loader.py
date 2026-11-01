from langchain_core.documents import Document

from app.ingestion.loader import split_documents


def test_split_documents_preserves_source_and_adds_chunk_ids():
    document = Document(page_content=("FastAPI uses Python type hints. " * 100), metadata={"source": "sample.md", "source_type": "file"})
    chunks = split_documents([document])
    assert len(chunks) > 1
    assert all(chunk.metadata["source"] == "sample.md" for chunk in chunks)
    assert all(chunk.metadata.get("chunk_id") for chunk in chunks)
    assert all(len(chunk.page_content) <= 900 for chunk in chunks)
