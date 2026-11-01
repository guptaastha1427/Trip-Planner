# PRD — Trip Planner AI Agent (as implemented)

**Entry:** `streamlit run app.py` · **Verified:** Nov 2026 · **Scope:** Current code only — no roadmap.

## Summary

Streamlit capstone: (1) **AI trip planning** — OSM POIs + Gemini itineraries, maps, weather, local persistence; (2) **Demo customer portal** — packages, refund rules, tickets, appeals; (3) **Demo admin** — queues, audit (`demo_admin`). **Not** production payments or secure identity.

## Users

| Persona | Use |
|---------|-----|
| Traveler / demo customer | User mode: Trip Planner, bookings, support, sign-in |
| Instructor / reviewer | Admin mode, sample users, `/dev` |
| Developer / grader | Tests, `info.md`, docs |

## Goals / non-goals

**Goals:** Valid itinerary JSON (`poi_id` ∈ tool catalog); persist `app_state.json`; POI feedback ranking; portal + **Terms FAISS RAG** (`website_rag`, `terms_rag`, `support_faq`).

**In scope:** Streamlit nav, Gemini, OSM, Open-Meteo, optional Wikivoyage (TF-IDF, not FAISS), JSON under `data/`.

**Non-goals:** Real money/refunds; production auth; invented POIs.

## Stack

| Layer | Tech |
|-------|------|
| UI | Streamlit ≥1.33, `st.navigation` |
| Trip agent | `google-genai`, `services/agent.py`, default `gemini-3.5-flash-lite` |
| Policy RAG | LangChain + FAISS + Gemini embeddings (`website_rag.py`) |
| Optional trip context | Wikivoyage + sklearn TF-IDF (`wikivoyage_rag.py`; off unless `ENABLE_WIKIVOYAGE_RAG=true`) |
| Maps / weather | PyDeck, Open-Meteo |
| Secrets | `.env`, optional `st.secrets["GEMINI_API_KEY"]` |

## Pages & sidebar

| Page | Path | Module |
|------|------|--------|
| Trip Planner (default) | `/` | `app.py` |
| Bookings & Refunds | `/bookings` | `pages/bookings_refunds.py` |
| Refund Assistant | `/refund-assistant` | `pages/refund_assistant.py` |
| Account Status | `/account` | `pages/account_status.py` |
| Help & Support | `/support` | `pages/support.py` |
| Terms & Policies | `/terms` | `pages/terms_policies.py` |
| Sign in | `/sign-in` | `pages/sign_in.py` (nav hidden via CSS) |
| Admin | `/admin` | `pages/admin_demo.py` |
| Developer docs | `/dev` | `pages/dev.py` → `info.md` |

**Global sidebar:** Dashboard User/Admin; trip history (User); policy popover; profile dock.

**Admin mode:** Admin nav; Trip Planner shows admin home; **blocks customer refund submit** on bookings.

## Feature highlights

**Trip Planner:** Form (days 1–14, pace, interests); generate; itinerary/map/travel tabs; 👍/👎 → `feedback.jsonl`; nearby swap (no Gemini); single-day update; package prefill; export JSON; agent trace; balloons on generate; policy FAB.

**Not in UI:** full `mode="refine"`; `_show_refinement_diff` never called (`pending_refinement_compare` unused).

**Portal:** Demo users; packages (`BK-PKG-*`); refunds via `evaluate_refund_request`; Refund Assistant (rules, not FAISS); tickets; appeals; FAQ + support bot.

**Policy chat:** Support bot, FAB, sidebar — `answer_support_query` → terms FAISS. Sign-in = local RAG auth (`rag_chat_users.json`). URL scrape test only; answers use Terms index.

**Partial:** `render_page_menu` / full Document Assistant Chat shell **not mounted** on any route; “Go to Chat” sets session only.

**Admin:** Passphrase `demo_admin`; tabs Overview / Refunds / Tickets / Accounts / Audit.

## Journeys (short)

1. **Plan:** Form → generate → progress/spinner → tabs or `last_error` → optional history/feedback/swap/single-day.
2. **Package from planner:** Book as travel package → `/bookings` prefill.
3. **Refund:** Demo user → booking expander → eligibility → `RR-*` track tab.
4. **Support:** Bot → FAISS + live demo JSON; tickets subject ≥3, body ≥10.
5. **Sign-in:** PBKDF2 local accounts; separate from demo user radio.
6. **Admin:** Admin mode or `/admin` + `demo_admin`.

## Validation

| Area | Rules |
|------|--------|
| Trip form | Destination, interests non-empty; days 1–14; pace ∈ relaxed/moderate/packed |
| Itinerary | JSON days; all `poi_id` in `tool_state.pois`; single-day unchanged other days |
| Refunds | Single source: `refund_eligibility.evaluate_refund_request` |
| RAG register | Password ≥8, terms checkbox |

## Loading / errors / limits

Progress + spinner on generate; policy chat disables input (“Searching…”). Missing env warnings; agent `st.error`; embedding failures in bot copy. **Prototype** security; first new city slow; Wikivoyage off by default; **25 queries/day** in terms text only — **not enforced in code**; trip history cap 30 on legacy migrate.

## Data files

`app_state.json`, `feedback.jsonl`, `demo_bookings.json`, `customer_portal_state.json`, `rag_chat_users.json`, `rag_chat_sessions.json` — see `data/*.example`.

## Config

| Variable | Required | Effect |
|----------|----------|--------|
| `GEMINI_API_KEY` | Yes | Gemini + embeddings |
| `OSM_CONTACT_EMAIL` | Yes | OSM User-Agent |
| `ENABLE_WIKIVOYAGE_RAG` | No | Agent tool |
| `DESTINATION_GUIDE_AI` | No | Extra guide Gemini |
| `GEMINI_EMBEDDING_MODEL` | No | Embed override |

Defaults: `config.py` (`FAST_POI_LIMIT` 45, boosts ±0.25/0.35, `EMBEDDING_CACHE_VERSION` 4).

## Open questions

Production target **not confirmed**; Document Assistant route partial; `scripts/strip_demo_word.py` mentions `travel_admin` but runtime gate uses **`demo_admin`**.

## Related docs

`../README.md`, `using.md`, `info.md`, `.env.example`.
