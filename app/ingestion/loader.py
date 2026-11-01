from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import settings

SUPPORTED_EXTENSIONS = {".txt", ".md", ".html", ".htm", ".pdf"}


def _document_from_file(path: Path) -> Document:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        raw = path.read_text(encoding="utf-8", errors="replace")
        if suffix in {".html", ".htm"}:
            text = BeautifulSoup(raw, "html.parser").get_text("\n", strip=True)
        else:
            text = raw

    if not text.strip():
        raise ValueError(f"No readable text found in {path.name}")
    return Document(page_content=text, metadata={"source": path.name, "source_type": "file"})


def _document_from_url(url: str) -> Document:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    response = requests.get(url, timeout=20, headers={"User-Agent": "TechnicalDocsAssistant/1.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()
    title = soup.title.get_text(strip=True) if soup.title else parsed.netloc
    text = soup.get_text("\n", strip=True)
    if not text:
        raise ValueError(f"No readable text found at {url}")
    return Document(page_content=text, metadata={"source": url, "title": title, "source_type": "url"})


def load_files(paths: Iterable[str]) -> list[Document]:
    return [_document_from_file(Path(path)) for path in paths]


def load_urls(urls: Iterable[str]) -> list[Document]:
    return [_document_from_url(url) for url in urls]


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "unknown")
        start = chunk.metadata.get("start_index", index)
        digest = hashlib.sha256(f"{source}:{start}:{chunk.page_content}".encode()).hexdigest()[:16]
        chunk.metadata["chunk_id"] = digest
    return chunks
