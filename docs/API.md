# API.md — interfaces as implemented

**No REST server** — only Streamlit (`streamlit run app.py`, ~`:8501`) + outbound HTTP/SDKs. Never log secrets.

## Entry & routes

`app.main()`: page config, auth bootstrap, navigation, global sidebar.

| Title | `url_path` | Module |
|-------|------------|--------|
| Trip Planner | default | `app.trip_planner_page` |
| Bookings | `bookings` | `pages/bookings_refunds.py` |
| Refund Assistant | `refund-assistant` | `pages/refund_assistant.py` |
| Account | `account` | `pages/account_status.py` |
| Support | `support` | `pages/support.py` |
| Terms | `terms` | `pages/terms_policies.py` |
| Sign in | `sign-in` | `pages/sign_in.py` |
| Admin | `admin` | `pages/admin_demo.py` |
| Dev docs | `dev` | `pages/dev.py` |

State: `st.session_state` + `data/*.json`.

## UI → backend

| Action | Callable |
|--------|----------|
| Create itinerary | `_run_generation("generate")` → `run_agent` |
| Single day | `_run_generation("single_day", …)` |
| Swap stop | `_apply_stop_swap` |
| POI feedback | `feedback.append_feedback` |
| Policy chat | `support_faq.answer_support_query` → `terms_rag.answer_from_terms_document` |
| URL test | `website_rag.load_documents_from_url` |
| Refund | `refund_eligibility.evaluate_refund_request` |
| Package | `bookings.create_package_booking` |
| Auth | `rag_chat_auth.register_user` / `login_user` |
| Admin | `customer_portal_store.*`, `admin_console` |

**Not wired in UI:** `run_agent(mode="refine")`; `retrieve_from_url` for chat.

## `run_agent` → `AgentResult`

Inputs: destination, days, pace, interests, constraints, `user_agent`, `fast_mode`, `max_steps`, `rag_enabled`, `mode` (`generate`|`refine`|`single_day`), existing itinerary, `on_progress`, etc.

Output: `ok`, `itinerary`, `tool_state`, `trace`, `raw_final_text`, `error`.

Routing: refine/single_day → `_run_fast_refine`; fast generate → `_run_fast_generate` or tool loop; tools `search_pois`, `retrieve_guides`.

## Gemini tools

| Tool | Backend |
|------|---------|
| `search_pois` | Nominatim + Overpass |
| `retrieve_guides` | Wikivoyage TF-IDF |

`generate_content_with_fallback`: primary model + `MODEL_FALLBACKS`; retries via `retry_utils` on transient errors.

Other Gemini: grounded RAG (`temperature=0.1`), optional destination guide JSON (`0.3`).

Key: `get_gemini_api_key()` or `st.secrets`.

## LangChain (no LCEL)

`website_rag.py`: `Document`, `RecursiveCharacterTextSplitter` 1100/180, `WebBaseLoader`, `GoogleGenerativeAIEmbeddings`, `FAISS`. Prompts are plain strings to **google.genai**, not LangChain LLM chains.

## FAISS retrieval

`similarity_search_with_score`, filter **0.42**, score `1/(1+d)`.

| Function | Default top_k |
|----------|-------------|
| `retrieve_from_terms_kb` | 4 |
| `answer_from_terms_document` | 3 |

`generate_grounded_answer`: Gemini or chunk markdown fallback. **No disk persist.**

## Wikivoyage

`retrieve_guides` → TF-IDF chunks; not FAISS.

## Rules & portal I/O

`evaluate_refund_request` → `RefundEvaluation.to_dict()`.

`answer_support_query` → reply, escalate, sources.

Persistence: `persistence`, `customer_portal_store`, `feedback`, `rag_chat_auth`, static `demo_bookings.json`.

## Auth API

`register_user`, `login_user`, `logout_user`, `current_user`, `is_logged_in` — PBKDF2 + session JSON + cookie.

## Outbound HTTP (`http_client`)

| Service | Used by |
|---------|---------|
| Nominatim | geocoding |
| Overpass | POI, travel_hints |
| Wikivoyage | wikivoyage_rag |
| Wikipedia / Open-Meteo | images, weather, guide |
| User URL | WebBaseLoader |

15s timeout, 2 retries; OSM User-Agent from `OSM_CONTACT_EMAIL`.

## Helpers

`validate_trip_inputs`, `get_gemini_embedding_model_candidates`, `is_wikivoyage_rag_enabled`, `validate_http_url`.

## Example policy flow

User question → `answer_support_query` → `retrieve_from_terms_kb` (k=3, ≥0.42) → `generate_grounded_answer` with context + `GROUNDED_SYSTEM_INSTRUCTION` → citations via `rag_citations`.

## Unknowns

No Chroma/SQL; FAISS index type not named; embed dimension not in config; full refine UI absent.

## Source index

`app.py`, `pages/*`, `agent.py`, `website_rag.py`, `terms_rag.py`, `support_faq.py`, `wikivoyage_rag.py`, `refund_eligibility.py`, `rag_chat_auth.py`, `config.py`, `tests/test_terms_rag.py`.
