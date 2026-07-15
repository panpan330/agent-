# RAG Internal Package

This package contains internal RAG building blocks for the AI service.

It is intentionally separate from `app/services` and `app/routers`:

- `app/rag` holds RAG domain components such as documents, chunks, loaders, splitters, embeddings, vector store adapters, retrievers, generators, and pipelines.
- `app/services` coordinates application use cases and external clients.
- `app/routers` exposes HTTP APIs.
- `app/schemas` holds API request and response models.

Current files:

```text
documents.py  Internal RAG document and chunk models.
```

Planned files for later lessons:

```text
loaders.py       Load Markdown/txt source documents.
splitters.py     Split documents into chunks.
embeddings.py    Convert chunk text and user queries into vectors.
vector_store.py  Hide Qdrant-specific read/write details behind a project adapter.
retriever.py     Retrieve top_k chunks with score and payload filtering.
generator.py     Build prompts and generate answers from retrieved chunks.
pipeline.py      Orchestrate ingestion and question-answering flows.
```

Stage 4 lesson 9 only creates the package boundary and internal data contracts.
It does not start Qdrant, create collections, write vectors, or expose a RAG API.
