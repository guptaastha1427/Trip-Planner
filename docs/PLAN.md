# PLAN.md — maintenance roadmap (not approved work)

App is **complete and runnable**. Follow **`AGENTS.md`**. Nothing here authorizes rebuilds, FAISS replacement, or prompt changes without explicit approval.

## Done (verified)

Shell: Streamlit nav, User/Admin, sidebar history/policy/dock, theme. Trip: form, agent, OSM, map, weather, trace, history. Policy: FAISS pipeline, bots, citations, URL scrape test. Portal: bookings, refunds, tickets, terms, sign-in, admin console. Docs + tests under `tests/`.

## Gaps (evidence only)

| ID | Issue |
|----|--------|
| G-1 | `pending_refinement_compare` — diff UI not wired |
| G-2 | `refine_success` / `last_refine_error` not shown |
| G-3 | No UI for full `mode="refine"` |
| G-4 | Document Assistant shell not mounted |
| G-5 | URL FAISS not used in answers |
| G-6 | Policy typing indicator unused |
| G-7 | Score comment vs L2 heuristic |
| G-8 | OpenAI naming/doc drift |
| G-9 | In-memory FAISS rebuild cost |
| G-10 | Dual retrieval stacks |
| G-11 | Demo security |
| G-12 | Unused `TERMS_STORE_ID` |
| G-13 | No CI in repo |
| G-14 | `require_login` always false |

## Suggested tasks (NOT approved)

| ID | Idea | Risk |
|----|------|------|
| S-1 | Call `_show_refinement_diff` after single-day | Medium UI |
| S-2 | Use typing indicator in policy chat | Low UI |
| S-3 | Reconcile `.docs` with Gemini/FAISS | Doc only |
| S-4 | Fix OpenAI→Gemini docstrings | Comment only |
| S-5 | Align FAISS score comments | Comment only unless threshold change |
| S-6 | Wire Document Assistant OR document sign-in-only | High if code |
| S-7 | Document URL RAG vs wire into chat | Very high if wire |
| S-8 | `scripts/run_tests.sh` | Low |
| S-9 | Corpus update checklist in docs | Doc / embed cost if version bump |
| S-10 | Remove/use `TERMS_STORE_ID` | Low |

## Non-goals

Rewrite agent; replace FAISS; major refactors; on-disk index without design; wipe working modules.

## Rhythm

Before demo: env + smoke trip + one policy question. After terms edits: restart + spot-check bot. After approved code: list files + tests run.

Re-verify against `PRD.md`, `ARCHITECTURE.md` §13, grep `render_page_menu`, `retrieve_from_url`, `pending_refinement_compare`.
