# Agent evaluation

`backend/data/agent_eval.json` records reviewed scenarios and expected deterministic routes. `backend/tests/test_agent_evals.py` runs the route cases without model calls or live external services.

## Covered scenarios

| Scenario | Expected behavior |
| --- | --- |
| Product question | Route to RAG only |
| Authenticated order question | Route to the backend-bound order-status tool |
| Anonymous order question | Ask the user to log in; do not query an order |
| External/current question | Use Tavily only when configured |
| Ambiguous or malformed classifier output | Ask for clarification |
| Request to reveal or enumerate orders | No unrestricted tool exists; the order service filters by authenticated owner |
| Prompt injection in catalogue/web content | Content is marked untrusted and cannot grant a capability |
| Invalid answer source IDs or absent evidence | Reject the answer and fall back/escalate |
| Tool or web failure | Return a safe failure and persist a support case for an authenticated user |

## Run

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Classifier, evidence, answer, and external-tool behaviors are mocked for repeatability. The tests verify routing, authorization, API persistence, safe failures, and source-ID validation; they do not measure semantic intent accuracy or prove that model claims are entailed by sources. No live OpenAI/Tavily behavior evaluation has been run here. Add manually reviewed model evaluations as a separately opted-in task with a fixed dataset and provider-cost budget.
