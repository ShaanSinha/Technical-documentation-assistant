# TechDocs

A documentation assistant that lets you upload technical documents and
ask questions about their content. It uses retrieval-augmented
generation (RAG) to find relevant passages and generate answers grounded
in the indexed documents.

## Features

-   Upload PDF, TXT, Markdown and HTML documents.
-   Split documents into chunks and create embeddings.
-   Store and search document embeddings with ChromaDB.
-   Ask questions through a React web interface.
-   Retrieve relevant passages and generate answers with a Groq-hosted
    language model.
-   Run a LangGraph workflow for retrieval and answer generation.
-   View indexed documents and their chunk counts.
-   Submit helpful or unhelpful feedback on answers.
-   Keep recent conversations in the browser.

## Tech stack

  Area              Technologies
  ----------------- ------------------------------------
  Frontend          React, Vite, JavaScript, CSS
  Backend API       Python, FastAPI
  Workflow          LangGraph
  Language model    Groq API
  Embeddings        Hugging Face Sentence Transformers
  Vector database   ChromaDB

## Project structure

``` text
technical-docs-assistant/
├── app/
│   ├── graph/             # LangGraph workflow
│   ├── ingestion/         # Document loading and splitting
│   ├── retrieval/         # Vector database and retrieval
│   ├── routes/            # FastAPI endpoints
│   └── main.py            # FastAPI application
├── data/
│   ├── uploads/            # Uploaded documents
│   └── feedback.jsonl      # Saved feedback
├── chroma_db/              # ChromaDB persistent storage
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── style.css
│   ├── index.html
│   └── package.json
├── ingest_corpus.py
├── requirements.txt
└── .env
```

## Requirements

-   Python 3.13 (or a compatible Python version supported by the
    installed dependencies)
-   Node.js and npm
-   A Groq API key


## How it works

1.  **Ingestion:** A user uploads a document or provides a URL.
2.  **Loading and splitting:** The backend extracts document content and
    splits it into smaller chunks.
3.  **Embedding and storage:** Text chunks are converted into embeddings
    and stored in ChromaDB.
4.  **Retrieval:** When a question is submitted, relevant chunks are
    retrieved from the vector database.
5.  **Answer generation:** The LangGraph workflow uses the retrieved
    context and the configured Groq model to prepare an answer.
6.  **Feedback:** Users can rate answers; feedback is stored by the
    backend.

The assistant can return an uncertainty response when the indexed
documentation does not provide enough relevant information.

