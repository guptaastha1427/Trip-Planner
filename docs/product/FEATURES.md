# FEATURES.md — implemented only (no roadmap)

Stack: Trip = **Gemini + OSM**; Policy = **LangChain + FAISS** (`website_rag`); Optional trip context = **Wikivoyage TF-IDF** (not FAISS).

## Shell (F-01–F-05)

| ID | Feature | Code / notes |
|----|---------|--------------|
| F-01 | Multipage nav | `app.py` `st.navigation` |
| F-02 | User/Admin dashboard | `demo_dashboard.py`; admin blocks customer refund submit |
| F-03 | Profile dock | Sign in/out, demo user switch; `_pending_sign_in_nav` |
| F-04 | Trip history sidebar | User mode; `trip_history` in `app_state.json`; append on generate only |
| F-05 | Developer docs | `/dev` → `info.md` |

## Trip Planner (F-10–F-19)

| ID | Feature | AI/RAG |
|----|---------|--------|
| F-10 | Trip form + validation | Pre-agent only |
| F-11 | **Create itinerary** | `run_agent` fast generate; Gemini; not FAISS |
| F-12 | Trip stats row | None |
| F-13 | Itinerary tab, nearby swap, feedback | Swap local; feedback → jsonl |
| F-14 | Single-day update | Gemini fast refine; compare UI missing (U-2) |
| F-15 | Map tab | PyDeck |
| F-16 | Travel & stays | Weather, guide, OSM hints |
| F-17 | Book as package | Nav to bookings prefill |
| F-18 | Export + agent trace | JSON download, debug timeline |
| F-19 | Policy FAB + sidebar bot | FAISS terms RAG |

## Portal (F-20–F-75)

Demo users; **Book package** / bookings / refund requests; **Refund Assistant** (rules + chat); account appeals; support FAQ + **policy bot** + tickets; terms tabs; package catalog UI.

## Sign-in (F-80)

Local register/login PBKDF2; **Go to Chat** sets menu only — full Document Assistant shell not mounted (U-4).

## Admin (F-90–F-91)

Passphrase **`demo_admin`**; console tabs (refunds, tickets, accounts, audit); embedded admin on portal pages in admin mode.

## Policy RAG (F-95)

Terms corpus → chunk 1100/180 → embed → FAISS in memory → retrieve (0.42) → `generate_grounded_answer` (Gemini 0.1). URL index separate for scrape test only.

## Optional (F-96)

Wikivoyage tool: `ENABLE_WIKIVOYAGE_RAG=false`; fast mode disables in agent.

## Incomplete / unverified

| ID | Issue |
|----|--------|
| U-1 | No UI for `mode="refine"` |
| U-2 | `pending_refinement_compare` not shown |
| U-3 | `refine_success` / `last_refine_error` not rendered |
| U-4 | `render_page_menu` not on a route |
| U-5 | `retrieve_from_url` unused in chat |
| U-6 | Typing indicator dead code |
| U-7 | `require_login` always false |
| U-8 | FAISS distance metric vs comments unverified |

## Regression hotspots

`website_rag` thresholds/prompts; `EMBEDDING_CACHE_VERSION`; `agent` fast mode; `support_faq` branches; portal JSON schema; `app_state` shape; session keys.

*Per `AGENTS.md` / `PLAN.md` — approve before changing prompts, retrieval, or persistence.*
