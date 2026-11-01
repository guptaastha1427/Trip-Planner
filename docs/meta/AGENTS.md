# AGENTS.md — rules for AI assistants

**Extend-only** capstone Streamlit app unless the user gives a scoped exception.

## Stack (verified)

| Layer | Implementation |
|-------|----------------|
| UI | Streamlit — `streamlit run app.py` |
| Trip | Gemini + tools — `services/trip/agent.py` |
| Policy RAG | LangChain + FAISS in memory — `services/rag/website_rag.py` |
| Trip context (optional) | Wikivoyage TF-IDF — `services/rag/wikivoyage_rag.py` (**not** FAISS) |
| Persistence | JSON/JSONL under `data/` — **no SQL/Chroma** |
| HTTP API | **None** inbound |

FAISS built in memory (`@st.cache_resource`); don’t delete user `data/` or “rebuild” without approval.

## Non-negotiable

1. **No scratch rewrite** — surgical edits.
2. **Don’t change** working features, **prompts**, UI behavior, or data flow unless explicitly requested.
3. **Keep FAISS** — no Chroma/Pinecone/pgvector swap.
4. **Keep stack** — Gemini, Streamlit, LangChain as used; no dependency bumps without asking.
5. **No structural churn** — folders/renames/refactors need approval.
6. **Don’t destroy data** — no wipe of `data/*`, caches, indices without user OK.
7. **Secrets** — never commit/print `.env`, secrets.toml, live JSON.
8. **Before behavioral changes** — read source, propose minimal diff, **wait for approval** if UX/prompts/retrieval/persistence change.
9. **Smallest diff** — no drive-by cleanup.
10. **After changes** — list files touched, summary, **checks actually run**.

Conflicts with above → stop and ask. **Docs-only tasks** must not touch code/config/data.

## Source of truth

| Topic | Files |
|-------|--------|
| Product | `PRD.md` |
| Architecture | `ARCHITECTURE.md` |
| UI | `DESIGN.md` |
| Data/FAISS | `DATABASE.md` |
| Interfaces | `API.md` |
| Run | `../README.md`, `using.md`, `SETUP.md` |
| Deep | `info.md`, `/dev` |
| Config | `config.py`, `.env.example` |

Code wins over stale docs.

## Conventions

Match `app.py` + `pages/` + `services/{core,trip,rag,portal,ui}/` layout; lazy imports where used; dataclasses for results; broad `except` with user strings is intentional; `st.session_state` + persistence modules; RAG via `similarity_search_with_score` — no new LCEL unless asked; `ui_copy.polish_ui_copy` where siblings do.

Git: commit **only when user asks**; no force-push main; no secrets in commits.

## Test & run

```bash
streamlit run app.py
python -m tests.portal.test_refund_eligibility
python -m tests.rag.test_terms_rag
python -m tests.trip.test_validation
python -m tests.rag.test_rag_citations
pytest tests/ -q
```

No destructive FAISS rebuilds; no logging env vars.

## Workflow

Read affected files → minimal proposal → approve if needed → implement → targeted tests → report.

**When in doubt: preserve behavior, FAISS, Gemini + LangChain, ask first.**
