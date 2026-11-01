"""Index all supported files in data/documents into the persistent ChromaDB store."""
from pathlib import Path

from app.ingestion.loader import load_files, split_documents
from app.retrieval.vector_store import add_chunks


def main():
    paths = [str(path) for path in Path("data/documents").iterdir() if path.is_file()]
    if not paths:
        print("No files found in data/documents")
        return
    documents = load_files(paths)
    chunks = split_documents(documents)
    count = add_chunks(chunks)
    print(f"Loaded {len(documents)} documents and indexed {count} chunks.")


if __name__ == "__main__":
    main()
