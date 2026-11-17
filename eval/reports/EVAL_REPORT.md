# Travel Planner — Evaluation Report

_Generated: 2026-11-12T10:56:54.616198+00:00_
_Source: `eval.run_pipeline` · `evaluation_mode`: **heuristic_offline**_

## Status legend
- **Passed** / **Failed** — automated eval result
- **Requires API credentials** — set `EVAL_LIVE=1` and `GEMINI_API_KEY` for live embed/judge
- **Requires human review** — complex policy interpretation

## 1. Architecture (verified)
Separate stacks: Terms FAISS+Gemini, Support FAQ rules+RAG, Wikivoyage TF-IDF, Refund rules engine.

### High-level eval flow

```mermaid
flowchart TB
  subgraph datasets["Golden data"]
    D1[terms_rag_golden.jsonl]
    D2[support_faq_routing.jsonl]
    D3[wikivoyage_golden.jsonl]
    D4[refund_decision_table.jsonl]
  end

  subgraph entry["Entry points (use one refresh path)"]
    PY[pytest tests/eval/]
    PL[python3 -m eval.run_pipeline --refresh-baseline --report]
    LEG[python -m eval — sweep + legacy JSON only]
  end

  subgraph runners["runners/"]
    RP[ragas_pipeline Terms RAG]
    TR[terms_retrieval]
    TG[terms_generation]
    SF[support_faq]
    WV[wikivoyage]
    RF[refund_rules]
  end

  subgraph out["Outputs"]
    ART[artifacts/baseline_*.json + .csv]
    RPT[reports/EVAL_REPORT.md]
  end

  datasets --> runners
  PY --> runners
  PL --> RP
  PL --> ART
  PL --> RPT
  LEG --> TR
  LEG --> TG
  LEG --> ART
  RP --> SF
  RP --> WV
  RP --> RF
```

## 2. Terms / Policy RAG (pipeline — retrieval + generation)
- Retrieval profile: **hybrid_rerank_v1** (hybrid=True)
- Embedding (eval): HuggingFace:sentence-transformers/all-MiniLM-L6-v2
- Cases: 40 · passed: 38/40 (rate 0.95)
- MRR: 0.7311
- Hit@3: 0.8684
- NDCG@3: 0.7348
- Answer correctness (mean): 0.8712
- Context utilization (mean): 0.8917
- Groundedness (mean): 0.8083
- Hallucination rate (mean): 0.1917

### Ragas-aligned means (offline mapping unless `EVAL_LIVE` + ragas)
- Faithfulness: 0.8083
- Answer relevance: 0.8712
- Context precision: 0.8917
- Context recall: 0.6842

## 3. Support FAQ routing
- Routing accuracy: 0.9615
- Pass rate: 0.8846 (23/26)

## 4. Wikivoyage RAG
- Mode: mocked_wikivoyage_html
- Pass rate: 0.9375 (15/16)

## 5. Refund rules engine
- Pass rate: 1.0 (16/16)

## 6. Threshold experiment (legacy baseline only)
Run `python3 -m eval` (`run_baseline.py`) for `experiments.min_relevance_sweep` in a separate JSON artifact.

## 7. LLM-as-Judge / official Ragas
- `official_ragas_requested`: False
- Live: `EVAL_LIVE=1`, `pip install -r eval/requirements-eval.txt`, optional `EVAL_RAGAS=0` for judge-only.

## 8. Production vs eval embeddings
Eval defaults to HuggingFace MiniLM; production Terms path uses Gemini embeddings unless `EVAL_EMBEDDINGS=gemini`.

Full JSON artifact: `eval/artifacts/baseline_20261112T105743Z.json`

## Failure analysis
- Failed Terms cases: T-R25, T-R40
- Inspect per-case `failure_analysis` in the JSON artifact.
- Per-case detail: `cases.terms_rag[]` in the artifact JSON.

## Appendix — Terms RAG pipeline (per golden case)

Run: `python -m eval.run_pipeline` (default dataset: `eval/datasets/terms_rag_golden.jsonl`).
Each JSONL row runs retrieve → answer → score → pass/fail; summary and artifact are written once after all rows.
Add `--auxiliary` to include Support FAQ, Wikivoyage, and Refund evals in the same artifact (not in this loop).

```mermaid
flowchart TB
  START(["Run eval<br/>python -m eval.run_pipeline"])
  DATA["Load golden questions<br/>eval/datasets/terms_rag_golden.jsonl"]
  START --> DATA

  DATA --> LOOP{{"Each test question"}}

  LOOP --> RET["Retrieve policy chunks<br/>FAISS over Terms & Policies<br/>eval: HuggingFace index, cache OFF"]
  RET --> ANS["Build answer<br/>answer_from_terms_document<br/>(same path as Policy / Support bot)"]

  ANS --> GEN_OK{"Answer produced?"}
  GEN_OK -->|No| FAIL["Case FAILED + reason"]
  GEN_OK -->|Yes| SCORE["Score this case"]

  SCORE --> R["Retrieval metrics<br/>MRR, Hit@K, NDCG<br/>vs expected_sources"]
  SCORE --> Q["Answer quality<br/>keywords, citations, groundedness<br/>(Ragas-style metrics)"]

  R --> DECIDE{"Meets thresholds?"}
  Q --> DECIDE

  DECIDE -->|Yes| OK["Case PASSED"]
  DECIDE -->|No| FAIL

  OK --> NEXT
  FAIL --> NEXT
  NEXT{{"Another row in JSONL?"}}
  NEXT -->|Yes| LOOP
  NEXT -->|No| SUM["Summary<br/>pass rate, average scores"]

  SUM --> SAVE["Save artifact<br/>eval/artifacts/*.json (+ optional .csv / report)"]

  AUX["Optional: --auxiliary<br/>support_faq, wikivoyage, refund_rules"]
  SAVE -.-> AUX
```

## Appendix — `eval/artifacts/` files (reference)

New runs add timestamped `evaluation_run_*.json` or `baseline_*.json` (often gitignored).
Look for Ragas eval under `summary.terms_rag_pipeline` / `cases.terms_rag`;
Support / Wikivoyage / Refund under `summary.support_faq`, `summary.wikivoyage`, `summary.refund_rules`.

| File | Source / type | What's inside |
|------|----------------|---------------|
| **`baseline_20261112T105743Z.json`** | `run_pipeline --refresh-baseline` | **All four:** Ragas Terms RAG (`cases.terms_rag[]`) + support_faq + wikivoyage + refund summaries |
| **`baseline_20261112T092643Z.json`** | Full baseline run | Same — Ragas pipeline + support + wikivoyage + refund |
| **`evaluation_run_real_embeddings.json`** | `run_pipeline` (no `--auxiliary`) | **Ragas / Terms only** — no support / wikivoyage / refund |
| **`baseline_20261112T092947Z.json`** | Legacy `run_baseline.py` | **Not Ragas:** `terms_retrieval` + `terms_generation`, support, wikivoyage, refund, `min_relevance_sweep` |
| **`baseline_20261112T105743Z.csv`** | Companion to `105743Z.json` | **One row** — Terms RAG / Ragas means only (MRR, Hit@3, faithfulness, pass_rate, …) |

## Appendix — RAGAS pipeline architecture (detailed)

Code path: `eval/run_pipeline.py` → `eval/runners/ragas_pipeline.py`.
Diagram source: `eval/reports/ragas_pipeline_architecture.mmd`.

```mermaid
flowchart TB
  subgraph ENTRY["Entry: python -m eval.run_pipeline"]
    CLI["argparse: --dataset, --k, --min-answer-correctness,<br/>--auxiliary, --baseline, --refresh-baseline, --report"]
    TH["MetricThresholds(k, ndcg_at_k, answer_correctness, …)"]
    CLI --> TH
    TH --> BUILD["build_payload()"]
  end

  subgraph CORE["Core runner: run_terms_rag_pipeline()"]
    DS["load_jsonl(dataset)<br/>default: eval/datasets/terms_rag_golden.jsonl"]
    LOOP["For each golden case"]
    ROW["evaluate_terms_rag_pipeline_row(case, thresholds)"]
    AGG["_aggregate_pipeline_rows(rows, k)"]
    OUT["return { summary, thresholds, rows }"]
    DS --> LOOP --> ROW --> AGG --> OUT
  end

  BUILD --> CORE

  subgraph CASE["Per case: evaluate_terms_rag_pipeline_row"]
    INP["Input from JSONL:<br/>test_id, question,<br/>expected_sources, expected_keywords,<br/>expected_behavior, expect_escalate"]
    EMB["build_terms_vector_store_with_huggingface()<br/>EVAL_EMBEDDINGS=gemini → production index"]
    PATCH["unittest.mock.patch:<br/>get_terms_vector_store → eval FAISS store"]
    INP --> EMB --> PATCH
  end

  ROW --> CASE

  subgraph RET_RAW["Raw retrieval (ranking ground truth)"]
    RAW["raw_similarity_ranked(question, store, top_k=raw_k=10)"]
    RLIST["retrieved_contexts[]: rank, source, score, text preview"]
    RSRC["raw_sources = chunk source labels"]
    RAW --> RLIST
    RAW --> RSRC
  end

  PATCH --> RET_RAW

  subgraph RET_PROD["Production retrieval path (patched)"]
    PATCH2["patch MIN_RELEVANCE_SCORE = min_score<br/>patch get_gemini_api_key → None (typical offline eval)"]
    KB["retrieve_from_terms_kb(question, top_k=4,<br/>allow_semantic_cache=False)"]
    KBIN["get_terms_vector_store → eval FAISS"]
    NOCACHE["Skip semantic_cache.lookup/store"]
    SS["similarity_search → RetrievedChunk list"]
    CTX["chunks_to_context(kb_chunks) → filtered_context_text"]
    PATCH2 --> KB
    KB --> KBIN --> NOCACHE --> SS --> CTX
  end

  PATCH --> PATCH2

  subgraph GEN["Generation path: answer_from_terms_document"]
    AFTD["answer_from_terms_document(question,<br/>min_score=0.0, top_k)"]
    RKB2["retrieve_from_terms_kb (again inside terms_rag)"]
    STRONG["Filter chunks with score ≥ min_score"]
    GGA["generate_grounded_answer(query, strong)"]
    NOKEY{"GEMINI_API_KEY<br/>present?"}
    MD["format_chunks_as_markdown(chunks)<br/>(offline eval default)"]
    GEM["Gemini generate_content_with_fallback<br/>+ GROUNDED_SYSTEM_INSTRUCTION"]
    POLISH["polish_ui_copy + embed_sources_in_reply<br/>(rag-inline-cite citations)"]
    ESC["escalate = low_confidence(top1 vs min_score+0.08)"]
    AFTD --> RKB2 --> STRONG --> GGA
    GGA --> NOKEY
    NOKEY -->|No| MD
    NOKEY -->|Yes| GEM
    MD --> POLISH
    GEM --> POLISH
    POLISH --> ESC
  end

  PATCH2 --> GEN

  subgraph CODE["Deterministic code checks"]
    GCS["generation_code_score(answer)"]
    KW["keywords_ok vs expected_keywords"]
    CIT["citation_ok: rag-inline-cite"]
    TERM["terms_attribution_ok"]
    PKG["package_math_hints (heuristic)"]
    GCS --> KW & CIT & TERM & PKG
  end

  POLISH --> CODE

  subgraph QUALITY["compute_answer_quality_metrics()"]
    HEU["Heuristic offline (always computed):<br/>answer_correctness, context_utilization,<br/>hallucination_rate, groundedness<br/>evaluation_mode = heuristic_offline"]
    LIVE{"EVAL_LIVE=1 +<br/>GEMINI_API_KEY?"}
    RAGASLIB{"ragas package +<br/>EVAL_RAGAS≠0?"}
    TRYL["try_ragas_evaluate()<br/>faithfulness, answer_correctness,<br/>context_precision → mapped fields"]
    JUDGE["run_llm_judge() → 1–5 scores<br/>_judge_to_ragas_fields()"]
    MODE["evaluation_mode:<br/>heuristic_offline | ragas_library |<br/>llm_judge_live | mixed_live (run aggregate)"]
    HEU --> LIVE
    LIVE -->|No| MODE
    LIVE -->|Yes| RAGASLIB
    RAGASLIB -->|Success| TRYL --> MODE
    RAGASLIB -->|Fail / missing| JUDGE --> MODE
  end

  CODE --> QUALITY
  CTX --> QUALITY

  subgraph RET_MET["Retrieval metrics (labeled cases only)"]
    MRR["mrr = mean_reciprocal_rank(expected_sources, raw_sources)"]
    HIT["hit_at_k, hit_rate_at_k"]
    NDCG["ndcg_at_k"]
    REC["recall_at_3"]
    CONF["top1_score, low_confidence,<br/>retrieve_error, retrieved_sources_ranked"]
    RSRC --> MRR & HIT & NDCG & REC & CONF
  end

  subgraph CANON["Ragas canonical mapping (artifact names)"]
    MAP["ragas_canonical_metrics():<br/>faithfulness ← groundedness<br/>answer_relevance ← answer_correctness<br/>context_precision ← context_utilization<br/>context_recall ← retrieval recall@K"]
  end

  QUALITY --> CANON
  RET_MET --> CANON

  subgraph PASS["Pass / fail per case"]
    FAIL["_build_failure_analysis():<br/>generation_error, retrieval thresholds,<br/>answer_correctness, ndcg, groundedness,<br/>hallucination_rate"]
    OK["passed = no generation_error AND<br/>failure_analysis == 'All configured metrics met thresholds.'"]
    RECORD["Case record: input, output,<br/>retrieval_metrics, ragas_metrics,<br/>thresholds_applied, failure_analysis"]
    FAIL --> OK --> RECORD
  end

  CANON --> FAIL

  subgraph SUMMARY["Run summary: _aggregate_pipeline_rows"]
    MEANS["Means: mrr_mean, hit_rate_at_k, ndcg_at_k_mean,<br/>answer_correctness_mean, groundedness_mean, …<br/>ragas_canonical_mean{faithfulness, …}"]
    PR["pass_rate, embedding_mode,<br/>evaluation_mode via aggregate_evaluation_mode(rows)"]
    MEANS --> PR
  end

  RECORD --> SUMMARY

  subgraph ARTIFACT["Artifacts & optional extras"]
    CTXBLK["run_context_block():<br/>evaluation_mode, official_ragas_requested,<br/>retrieval_profile, artifact_lineage"]
    JSON["eval/artifacts/evaluation_run_*.json<br/>or baseline_*.json"]
    CSV["Companion .csv (one-row summary)"]
    REP["--report → eval/reports/EVAL_REPORT.md"]
    AUX{"--auxiliary / refresh-baseline?"}
    SF["run_support_faq_eval()"]
    WV["run_wikivoyage_eval()"]
    RF["run_refund_rules_eval()"]
    BUILD --> CTXBLK
    OUT --> CTXBLK
    CTXBLK --> JSON --> CSV
    JSON --> REP
    BUILD --> AUX
    AUX -->|Yes| SF & WV & RF
  end

  subgraph REG["Regression (tests / CI)"]
    RT["eval/regression_thresholds.json<br/>terms_rag_pipeline: MRR, hit@3, nDCG,<br/>groundedness, ragas_canonical_mean"]
    RT -.->|"pytest test_regression_thresholds"| JSON
  end
```

## Appendix — Auxiliary eval workflows (Support, Wikivoyage, Refund)

Triggered by `python -m eval.run_pipeline --auxiliary`, `run_baseline.py`, or `pytest tests/eval/`.
Bundled into the same artifact as Terms RAG when `--auxiliary` or `--refresh-baseline` is used.

### 1. `support_faq_routing.jsonl` → `run_support_faq_eval()`

**Runner:** `eval/runners/support_faq.py`

| Step | What happens |
|------|----------------|
| 1 | Load row: `user_id`, `message`, `expected_route`, `expect_escalate` |
| 2 | Patch `answer_from_terms_document` to count RAG calls and run real Terms RAG with eval FAISS (HuggingFace) |
| 3 | Call production `answer_support_query(user_id, message)` (greeting, account, refund status, booking BK-…, or terms RAG) |
| 4 | `_classify_route` on message + reply + RAG call count → `actual_route` (e.g. `terms_rag`, `booking_lookup`) |
| 5 | Compare `actual_route` to `expected_route` (small relaxations for `terms_rag` / `no_match_or_loose`) |
| 6 | Escalation: for most routes, `escalate` must match `expect_escalate`; greeting/empty/booking/refund_status → routing only |
| 7 | Aggregate: `routing_accuracy`, `pass_rate` |

**Pass** = correct branch (+ escalation when required). Does **not** grade answer text quality.

### 2. `wikivoyage_golden.jsonl` → `run_wikivoyage_eval()`

**Runner:** `eval/runners/wikivoyage.py` · Default mode: **`mocked_wikivoyage_html`** (no real HTTP).

| Step | What happens |
|------|----------------|
| 1 | Load row: `destination`, `query`, `expected_keywords`, `min_chunks`, `expect_ok`, … |
| 2 | Clear `_RAG_CACHE` |
| 3 | Patch `_fetch_wikivoyage_article` → fake HTML for that city (or `None` for bad titles) |
| 4 | `retrieve_guides(..., enabled=True)` → TF-IDF build/search → chunks + scores |
| 5 | `retrieve_guides(..., enabled=False)` → must return **no chunks** |
| 6 | Check: `ok`, chunk count ≥ `min_chunks`, keywords appear in chunk text (or destination) |
| 7 | Aggregate: `pass_rate`, `mode: mocked_wikivoyage_html` |

Optional: `EVAL_LIVE=1` + `live_network=True` → real API; logs `ok` + chunk count only.

**Pass** = retrieval behaves when RAG is on and off; optional keyword/chunk checks.

### 3. `refund_decision_table.jsonl` → `run_refund_rules_eval()`

**Runner:** `eval/runners/refund_rules.py` · **No RAG, no LLM.**

| Step | What happens |
|------|----------------|
| 1 | Load row: `booking_id`, `user_id`, `now`, `account_status`, `reason`, `expected_eligibility`, optional refund bounds |
| 2 | `get_booking(booking_id)` from demo portal data |
| 3 | If missing → pass only if case expects `missing_booking` error |
| 4 | `evaluate_refund_request(...)` — pure rules (policy, timing, fees) |
| 5 | Compare `ev.eligibility` to `expected_eligibility`; optional min/max `estimated_refund` |
| 6 | Aggregate: `pass_rate` |

**Pass** = rule engine output matches the golden row.
