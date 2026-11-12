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
| `run_baseline.py` | Legacy suites + min-relevance sweep JSON (optional) |
| `run_pipeline.py` | **Primary** — Ragas + retrieval artifacts + optional report |
| `report.py` | Regenerate `EVAL_REPORT.md` from existing artifact JSON |
| `artifacts/` | Timestamped JSON + CSV summaries (gitignored); see `eval/ARTIFACTS.md` |
| `requirements-eval.txt` | Optional `ragas` / `datasets` for official live scoring |
| `ARTIFACTS.md` | Refresh workflow & pre-hybrid reference files |

## Commands

```bash
# Existing regression (run before/after eval changes)
pytest tests/ -q

# New eval tests (HuggingFace embeddings for Terms KB; mocks elsewhere)
pytest tests/eval/ -q

# Primary: artifact + CSV + human report (recommended)
python3 -m eval.run_pipeline --refresh-baseline
# --refresh-baseline implies --report → updates eval/reports/EVAL_REPORT.md

# Ragas-aligned pipeline (per-case metrics + failure analysis artifact)
python3 -m eval.run_pipeline
python3 -m eval.run_pipeline --k 5 --auxiliary --report

# Regenerate report only (no re-run) from latest pipeline baseline JSON
python3 -m eval.report
python3 -m eval.report --artifact eval/artifacts/baseline_20261112T105743Z.json

# Legacy: split retrieval/generation + min_relevance sweep (separate JSON shape)
python3 -m eval

# Phase 4 — baseline assessment artifact (regression tracking filename)
python3 -m eval.run_pipeline --baseline --auxiliary

# Refresh post–hybrid-retrieval baseline (new timestamped JSON + CSV; does not overwrite old files)
python3 -m eval.run_pipeline --refresh-baseline
# same as: python3 -m eval.run_pipeline --baseline --auxiliary --refresh-reason post_hybrid_retrieval

# Phase 5 — CI regression gates (see eval/regression_thresholds.json)
pytest tests/eval/test_regression_thresholds.py -q
pytest tests/eval/ -q -m "not eval_regression"   # fast suite (matches GitHub Actions)
```

Artifacts land in `eval/artifacts/` as `baseline_YYYYMMDDTHHMMSSZ.json` (with `--baseline`) or `evaluation_run_*.json`. Each JSON includes per-case `user_query`, `generated_response`, `retrieved_contexts`, retrieval means (MRR, Hit@K, NDCG@K), Ragas-aligned fields (`faithfulness`, `answer_relevance`, `context_precision`, `context_recall`), and `failure_analysis`.

## Modes

| `evaluation_mode` (artifact) | When | Notes |
|------------------------------|------|-------|
| `heuristic_offline` | Default pytest / `run_pipeline` | HF MiniLM FAISS + heuristic Ragas-aligned scores |
| `llm_judge_live` | `EVAL_LIVE=1` + `GEMINI_API_KEY` | Gemini judge in `eval/evaluators/llm_judge.py` |
| `ragas_library` | `EVAL_LIVE=1` + optional packages below | Official `ragas` metrics when import succeeds |
| `mixed_live` | Partial live success per case | Inspect per-case `ragas_metrics.evaluation_mode` |

### Official Ragas library (optional)

```bash
pip install -r requirements.txt
pip install -r eval/requirements-eval.txt   # ragas + datasets
export EVAL_LIVE=1
export GEMINI_API_KEY=...                   # from .env — required for live judge / some Ragas backends
# optional: EVAL_RAGAS=0 to skip ragas package and use LLM judge only
python3 -m eval.run_pipeline --refresh-baseline
```

Artifacts record top-level `evaluation_mode`, `official_ragas_requested`, `retrieval_profile`, and `artifact_lineage`. A companion CSV (`<json-stem>.csv`) is written beside each JSON.

Pre-hybrid files such as `artifacts/evaluation_run_real_embeddings.json` stay valid as references until a new run (e.g. `--refresh-baseline`) produces a timestamped replacement; see `eval/ARTIFACTS.md`.

Do **not** commit `.env`. Production Terms RAG uses **Gemini** embeddings via `get_embeddings()`. Eval defaults to **HuggingFace** unless `EVAL_EMBEDDINGS=gemini`.

## Components

1. **Terms / Policy** — `retrieve_policy_chunks`, `retrieve_from_terms_kb`, `answer_from_terms_document`
2. **Support FAQ** — `answer_support_query` routing
3. **Wikivoyage** — `retrieve_guides` (TF-IDF, separate from FAISS)
4. **Refund** — `evaluate_refund_request` (rules, not RAG)

## Observability

Production: `AgentTraceStep` (trip), `policy_rag_trace` (session). Eval: `eval/tracing/eval_trace.py` for JSONL export during runs.

External Phoenix/LangSmith: optional; not required for this harness.
