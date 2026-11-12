# ARCHITECTURE.md — as implemented

Multi-page **Streamlit** app combining Gemini trip agent, **LangChain + in-memory FAISS** policy RAG, optional **Wikivoyage TF-IDF**, OSM/PyDeck, JSON persistence. Unverified items marked **unknown**.

## Overview

| Concern | Implementation |
|---------|----------------|
| Trip planning | `google-genai` tool loop — `services/agent.py` |
| Policy Q&A | LangChain split/embed/FAISS + Gemini answers — `website_rag.py` |
| Destination context (optional) | Wikivoyage + TF-IDF — `wikivoyage_rag.py` |
| Demo portal | JSON under `data/` |

**One** LangChain FAISS pipeline; trip agent does **not** use LangChain for generation.

<style>
.arch-flow-diagram { position: relative; margin: 1rem 0 1.25rem; max-width: 100%; }
.arch-flow-diagram img { width: 100%; display: block; border: 1px solid #e2e8f0; border-radius: 12px; background: #fff; }
.arch-flow-expand { position: absolute; top: 12px; right: 12px; z-index: 2; width: 2.25rem; height: 2.25rem; border-radius: 0.5rem; border: 1px solid #475569; background-color: rgba(30, 41, 59, 0.92); background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round'%3E%3Cpath d='M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: center; text-decoration: none; }
.arch-flow-expand:hover { border-color: #94a3b8; background-color: rgba(51, 65, 85, 0.95); }
</style>

## Stack (`requirements.txt` mins)

Streamlit, `extra-streamlit-components`, `google-genai`, dotenv, pydeck, requests, sklearn, numpy/pandas, langchain-core/community/google-genai/text-splitters, **faiss-cpu**.

**Models (`config.py`):** chat `gemini-3.5-flash-lite` + fallbacks; embedding candidates + `GEMINI_EMBEDDING_MODEL`; `EMBEDDING_CACHE_VERSION=4`.

**Streamlit:** `.streamlit/config.toml` — light theme, headless, static serving.

## Layout

```
app.py, config.py, pages/, services/, data/, tests/, app/static/
```

**Pages:** `dev`, `bookings_refunds`, `refund_assistant`, `terms_policies`, `account_status`, `support`, `sign_in`, `admin_demo`.

**Key services:** `agent`, `website_rag`, `terms_rag`, `support_faq`, `policy_bot_ui`, `wikivoyage_rag`, `poi_search`/`geocoding`, `persistence`, `customer_portal_store`, `rag_chat_auth`, `feedback`, refunds/bookings, `portal_ui`, UI/map/trace modules.

## Runtime (`app.main`)

1. Page config wide  
2. RAG auth cookie + session + portal sync  
3. UI inject + dashboard switch  
4. `st.navigation` → `pg.run()`  
5. Global sidebar every run  

**Model:** full rerun on widgets; long work in handlers.

## FAISS policy pipeline

**Corpus:** `terms_content.py`, `FAQ_ITEMS`, `POLICIES` → `Document` → strip markdown → split **1100/180** (`RecursiveCharacterTextSplitter`).

**Optional URL:** `WebBaseLoader` 20s; ≥40 chars; same splitter; **chat answers still use Terms index**.

**Embed:** `GoogleGenerativeAIEmbeddings`, probe `healthcheck`, `@st.cache_resource`.

**Index:** `FAISS.from_documents` in memory — **no disk `.faiss`**.

**Retrieve:** `similarity_search_with_score`, score `1/(1+d)`, filter **MIN_RELEVANCE_SCORE 0.42**, `top_k` 3–4.

**Answer:** `generate_grounded_answer` — Gemini + `GROUNDED_SYSTEM_INSTRUCTION`; chunk markdown fallback.

**UI path:** `policy_bot_ui` → `answer_support_query` → `answer_from_terms_document` → retrieve + generate. History in `policy_bot_messages_*` (session only).

**Gap:** `rag_chat_ui.render_page_menu` not on any route.

### Help & Support routing (`answer_support_query`)

Support page and shared `policy_bot_ui`: **booking/refund** questions fetch live portal data and prepare a direct answer; **policy** questions follow Terms RAG → FAISS → grounded Gemini (pipeline above).

<div class="arch-flow-diagram">
<a class="arch-flow-expand" href="assets/dev-flows/support.png" target="_blank" rel="noopener noreferrer" title="Full screen" aria-label="Expand diagram"></a>
<img src="assets/dev-flows/support.png" alt="Help and Support flow" />
</div>

## Customer portal — refund evaluation

Bookings & Refunds, Refund Assistant: load booking + user from `customer_portal_store`, then rule-based `evaluate_refund_request` (`refund_eligibility.py`) — status, departure window, cancellation fee, eligibility — **not** FAISS or LLM.

<div class="arch-flow-diagram">
<a class="arch-flow-expand" href="assets/dev-flows/refund.png" target="_blank" rel="noopener noreferrer" title="Full screen" aria-label="Expand diagram"></a>
<img src="assets/dev-flows/refund.png" alt="Customer Portal refund flow" />
</div>

## Trip agent (not FAISS)

Form → `validate_trip_inputs` → `run_agent` → `search_pois` (OSM + feedback boosts) → optional `retrieve_guides` (Wikivoyage if enabled & not fast mode) → Gemini JSON → validate/enrich → UI + `app_state.json`.

Fast mode default; `FAST_MODE_MAX_STEPS=4`. Tools via `google.genai` function calling, not LangChain agents.

`app.py` calls `run_agent` on Generate / Update with `mode`, `fast_mode`, `rag_enabled`, and prior `tool_state` / itinerary.

### Trip routing (`run_agent`)

Entry in `services/trip/agent.py`. Refine paths delegate to `_run_fast_refine` (detail below). Fast generate can fall through to the tool loop on soft failure (not geocoding/Overpass hard errors).

<div class="arch-flow-diagram">
<a class="arch-flow-expand" href="assets/dev-flows/run_agent.png" target="_blank" rel="noopener noreferrer" title="Full screen" aria-label="Expand diagram"></a>
<img src="assets/dev-flows/run_agent.png" alt="run_agent routing" />
</div>

### Place refinement (`_run_fast_refine`)

Refine and single-day edits (`services/trip/agent.py`, `refine_itinerary.py`): seed POIs from the current itinerary, try a local surgical add when possible, enrich the catalog via OSM/geocode, then Gemini only if needed.

```mermaid
%%{init: {'flowchart': {'rankSpacing': 22, 'nodeSpacing': 28, 'padding': 10}}}%%
flowchart TB
  REQ([User request e.g. Add Hawa Mahal on Day 2]) --> RFR[_run_fast_refine]
  RFR --> SEED[_seed_pois_from_itinerary] --> PHR[_refine_search_phrase] --> ADD{is_add_only_request?}
  ADD -- yes --> SR1[try_surgical_refine] --> SR1OK{surgical OK?}
  OSM[search_pois + merge POIs]
  ADD -- no --> OSM
  SR1OK -- yes --> OK
  SR1OK -- no --> OSM --> GEO[_add_geocoded_place] --> POI{POIs in catalog?}
  POI -- no --> ERR1([Error no POIs])
  POI -- yes --> SR2[try_surgical_refine] --> SR2OK{surgical OK?}
  SR2OK -- yes --> OK
  SR2OK -- no --> ADD2{is_add_only_request?}
  ADD2 -- yes --> ERC[ensure_refinement_changed local add] --> ERCOK{changed?}
  ERCOK -- yes --> OK
  ERCOK -- no --> ERR2([Error could not add])
  ADD2 -- no --> CAT[_compact_poi_catalog] --> GEM[Gemini generate_content up to 3 tries]
  GEM --> FIN[_finalize_itinerary] --> JSON{valid JSON?}
  JSON -- no --> GEM
  JSON -- yes --> ENS[ensure_refinement_changed] --> ENSOK{valid changes?}
  ENSOK -- yes --> OK
  ENSOK -- no --> ERR3([Error])
  OK([AgentResult ok])
```

## Wikivoyage (orthogonal)

MediaWiki → chunk 800–1000 → TF-IDF cosine; module `_RAG_CACHE`; not FAISS.

### Destination guide retrieval (`retrieve_guides`)

Trip agent tool (when `ENABLE_WIKIVOYAGE_RAG`); Travel tab `build_destination_guide` can pull the same chunks. Wikivoyage HTML → text chunks → TF-IDF + cosine top‑k → Gemini for grounded copy (itinerary context or destination Q&A).

<div class="arch-flow-diagram">
<a class="arch-flow-expand" href="assets/dev-flows/destination.png" target="_blank" rel="noopener noreferrer" title="Full screen" aria-label="Expand diagram"></a>
<img src="assets/dev-flows/destination.png" alt="Destination guide flow" />
</div>

## Env & paths

Required: `GEMINI_API_KEY`, `OSM_CONTACT_EMAIL`. Optional: embed override, `ENABLE_WIKIVOYAGE_RAG`, `DESTINATION_GUIDE_AI`.

**Data:** see `DATABASE.md` — `app_state`, feedback, demo bookings, portal state, RAG auth JSON.

## Session vs persistence

| Data | Where |
|------|--------|
| Itinerary/forms | session + `app_state.json` |
| Policy chat | session only |
| FAISS/embeddings | `@st.cache_resource` |
| Portal | `customer_portal_store` |
| Auth | JSON + cookie |

## External HTTP

Gemini (SDK); Nominatim/Overpass (User-Agent); Wikivoyage; Wikipedia/weather; optional URL GET. Resilience: `http_client` 15s, 2 retries, Nominatim 1 req/s; agent `retry_utils`.

## Errors

Broad `except` + user strings; RAG layered fallbacks; corrupt JSON → empty defaults.

## Tests

`test_terms_rag` (HuggingFace FAISS), `test_rag_citations`, `test_refund_eligibility`, `test_validation`, others — **CI unknown**.

## Known debt (code-verified)

Dual retrieval stacks; narrow LangChain scope; URL FAISS unused in chat; Document Assistant UI gap; volatile in-memory FAISS; demo auth; `get_openai_api_key` alias; Refund Assistant = rules not FAISS; distance metric comment vs L2 heuristic.

```mermaid
flowchart TB
  UI[Streamlit] --> AG[run_agent]
  AG --> POI[OSM]
  AG --> WV[TF-IDF optional]
  AG --> GEM1[Gemini]
  UI --> SF[support_faq]
  SF --> TR[terms_rag]
  TR --> FAISS[FAISS in-memory]
  FAISS --> GEM2[grounded Gemini]
```

*Re-verify after substantive code changes.*
