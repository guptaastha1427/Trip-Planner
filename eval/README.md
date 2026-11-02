# RAG and agent evaluation harness

Offline-first evaluation for the Travel Planner capstone. Production code under `services/` is called as-is; metrics and datasets live here.

## Layout

| Path | Purpose |
|------|---------|
| `datasets/*.jsonl` | Golden cases per component |
| `runners/` | Executable eval logic |
| `evaluators/` | Metrics, code checks, LLM judge |
| `experiments/` | One-variable sweeps (harness only) |
| `tracing/eval_trace.py` | Redacted JSONL traces |
| `run_baseline.py` | Full baseline + `reports/EVAL_REPORT.md` |
| `artifacts/` | Timestamped JSON results (gitignored) |

## Commands

```bash
# Existing regression (run before/after eval changes)
pytest tests/ -q

# New eval tests (FakeEmbeddings / mocks — CI-safe)
pytest tests/eval/ -q

# Full baseline report (use the same Python/venv as Streamlit — needs streamlit installed)
python3 -m eval
```

## Modes

| Mode | When | Notes |
|------|------|-------|
| **Default** | `pytest tests/eval/` | FakeEmbeddings; no network |
| **Live** | `EVAL_LIVE=1` | Optional Wikivoyage HTTP + LLM judge (`GEMINI_API_KEY` in `.env`) |

Do **not** commit `.env`. Live embedding quality is **not** measured by FakeEmbeddings tests.

## Components

1. **Terms / Policy** — `retrieve_policy_chunks`, `retrieve_from_terms_kb`, `answer_from_terms_document`
2. **Support FAQ** — `answer_support_query` routing
3. **Wikivoyage** — `retrieve_guides` (TF-IDF, separate from FAISS)
4. **Refund** — `evaluate_refund_request` (rules, not RAG)

## Observability

Production: `AgentTraceStep` (trip), `policy_rag_trace` (session). Eval: `eval/tracing/eval_trace.py` for JSONL export during runs.

External Phoenix/LangSmith: optional; not required for this harness.
