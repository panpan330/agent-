# Agent Evaluation Data

This directory stores small, curated evaluation datasets for the learning
ticket Agent.

Current files:

```text
agent_cases.json  Stage 6 initial Agent evaluation cases.
```

Each case is split into:

- `inputs`: what the user sends to the Agent;
- `expected`: the expected intent, route, fields, tool use, or safety behavior;
- `metadata`: task type, business domain, case type, difficulty, and tags.

Stage 6 lesson 3 designs this dataset. Later lessons will read these cases to
evaluate intent classification, ticket field extraction, Agent routing, RAG
behavior, tool use, confirmation boundaries, and bad cases.

Stage 6 lesson 4 reads `agent_cases.json` with
`app/agents/intent_evaluation.py` and can be run locally with:

```powershell
uv run python scripts/agent_intent_eval.py
```

Stage 6 lesson 5 reads the same dataset with
`app/agents/field_evaluation.py` and can be run locally with:

```powershell
uv run python scripts/agent_ticket_field_eval.py
```

Stage 6 lesson 6 reads the same dataset with
`app/agents/route_evaluation.py` and can be run locally with:

```powershell
uv run python scripts/agent_route_eval.py
```

Stage 6 lesson 7 reads the same dataset with
`app/agents/rag_agent_evaluation.py` and can be run locally with:

```powershell
uv run python scripts/agent_rag_eval.py
```
