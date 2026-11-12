# TESTING.md — safe testing

Test without unnecessary Gemini calls or wiping FAISS/user `data/`. FAISS is **in-memory** only (`website_rag.py`).

## Layout

| Pattern | How |
|---------|-----|
| A | `python -m tests.<module>` with `main()` |
| B | `test_*` functions need **`pytest`** (not in `requirements.txt`) |

| Module | Runner | Network | Touches `data/` |
|--------|--------|---------|-----------------|
| `test_validation` | `-m` | No | No |
| `test_refund_eligibility` | `-m` | No | Reads `demo_bookings.json` |
| `test_terms_rag` | pytest | No — FakeEmbeddings | No |
| `test_rag_citations` | pytest | No | No |
| `test_package_details` | pytest | No | No |
| `test_info_markdown_view` | pytest | No | Reads `info.md` |
| `test_map_tooltip` | `-m` | No | May read `app_state.json` |

**Note:** `python -m tests.test_terms_rag` imports only — use pytest for tests.

## Commands

```bash
pip install -r requirements.txt && pip install pytest
python -m tests.trip.test_validation
python -m tests.portal.test_refund_eligibility
python -m tests.trip.test_map_tooltip
pytest tests/ -q
streamlit run app.py   # manual — needs .env; mutates data/
```

## Critical journeys (manual)

| ID | Journey | RAG/Gemini |
|----|---------|------------|
| J-1 | Create itinerary | Gemini + OSM |
| J-2–J-3 | Policy / support bot | FAISS + embed + Gemini |
| J-4 | Terms page | Static corpus |
| J-5 | Sign in | Local JSON |
| J-6–J-7 | Refunds / Refund Assistant | Rules only |
| J-8 | Admin | Portal JSON |
| J-9 | URL scrape test | HTTP + optional URL FAISS |
| J-10–J-11 | Export / trip history | `app_state.json` |

Default agent: `fast_mode=True`, Wikivoyage off.

## Pipeline checks (automated where noted)

Terms docs → split → FakeEmbeddings FAISS in tests; live embed needs key; retrieval `test_retrieve_package_policy`; LLM mocked via `get_gemini_api_key=None` → markdown fallback; citations in `test_rag_citations`.

**Not default path:** `retrieve_from_url`.

## Mocking

Patch `get_gemini_api_key`, inject fake FAISS store (`test_terms_rag`). No HTTP mocks in repo yet. Importing `website_rag` needs Streamlit installed.

## Regression matrix

| Area | Auto | Manual |
|------|------|--------|
| Validation | `test_validation` | Single-day planner |
| Refunds | `test_refund_eligibility` | Refund Assistant |
| Terms RAG | pytest terms_rag | Policy question |
| Citations | pytest rag_citations | Support bot cites |
| Packages | pytest package_details | Book package |
| Dev page | pytest info_markdown | `/dev` |
| Map | test_map_tooltip | Map hover |
| Full trip | — | Short J-1 |

Preserve prompts, FAISS stack, and `data/` unless approved.

## Expected failures

Missing key → warnings / no index; embed fail → bot error with `_embedding_init_error`; low score → escalate; geocode/Overpass fail → agent error; bad JSON → `last_error`.

## Manual QA checklist (abbrev)

Env + venv → unit tests → short trip generate → policy cite answer → portal refund once → admin on throwaway state → optional sign-in (writes auth JSON).

## Ask before

Many itinerary runs, arbitrary URL scrapes, editing/deleting `data/*`, bumping `EMBEDDING_CACHE_VERSION`, shared production-like `data/`.

## Cross-refs

`INTEGRATIONS.md`, `DATABASE.md`, `FEATURES.md`, `SETUP.md`, `AGENTS.md`.
