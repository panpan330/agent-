# RAG Evaluation Data

This directory stores small, versioned evaluation datasets for local RAG
experiments.

Current files:

```text
retrieval_cases.json  Minimal retrieval evaluation cases for the sample knowledge base.
```

Each retrieval case describes:

- the user `query`;
- the expected source document;
- the expected section or chunk when stable enough;
- optional metadata filters such as `permission_group` and `business_domain`;
- whether the query is expected to return no results.

Stage 4 lesson 38 uses this dataset with `scripts/rag_retrieval_eval.py` to
calculate Hit Rate@K, Recall@K, Precision@K, MRR@K, and bad cases.
