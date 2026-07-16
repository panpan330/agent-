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
filters.py    Build Qdrant payload filters from supported metadata fields.
vector_store.py Build Qdrant points and write embedded chunks through the REST API.
ingestion.py  Orchestrate load -> split -> embed -> upsert for local ingestion.
retriever.py  Convert a user query into a vector and retrieve filtered top_k chunks above an optional score threshold.
```

Planned files for later lessons:

```text
generator.py     Build prompts and generate answers from retrieved chunks.
pipeline.py      Orchestrate ingestion and question-answering flows.
```

Stage 4 lesson 15 adds basic top_k retrieval with fake query embeddings and Qdrant
Query API parsing. Stage 4 lesson 16 adds basic payload filtering by supported
metadata fields such as permission group, business domain, document type, and
source. Stage 4 lesson 17 adds score_threshold support so low-scoring retrieved
chunks can be excluded before answer generation. It still does not perform answer
generation or real embedding model calls.
