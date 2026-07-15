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
loaders.py    Load Markdown/txt files into RagDocument objects.
splitters.py  Split RagDocument objects into RagChunk objects.
metadata.py   Normalize and validate RAG metadata before Qdrant payload writes.
embeddings.py Convert chunks into deterministic placeholder vectors.
vector_store.py Build Qdrant points and write embedded chunks through the REST API.
ingestion.py  Orchestrate load -> split -> embed -> upsert for local ingestion.
```

Planned files for later lessons:

```text
retriever.py     Retrieve top_k chunks with score and payload filtering.
generator.py     Build prompts and generate answers from retrieved chunks.
pipeline.py      Orchestrate ingestion and question-answering flows.
```

Stage 4 lesson 14 adds metadata normalization, required field validation, and a
Qdrant payload whitelist. It still does not perform retrieval, payload filtering,
answer generation, or real embedding model calls.
