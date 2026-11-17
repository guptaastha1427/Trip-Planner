# Trip Planner — Project Handbook

**Read this first** when you return to the repo and need the full technical picture.  
**Run:** `streamlit run app.py` → [http://localhost:8501](http://localhost:8501)

---

## How to use this handbook

| If you want… | Jump to |
|--------------|---------|
| What this app is in one minute | [§1 Project snapshot](#1-project-snapshot) |
| Run it locally | [§2 Quick start](#2-quick-start) |
| Where code lives | [§3 Repository map](#3-repository-map) |
| What happens when a user plans a trip | [§4 Trip planner flow](#4-trip-planner-flow) |
| How policy / support Q&A works | [§5 Policy RAG flow](#5-policy-rag-flow) |
| Portal, refunds, admin | [§6 Customer portal](#6-customer-portal) |
| Files on disk | [§7 Data & persistence](#7-data--persistence) |
| Env flags and toggles | [§8 Configuration cheat sheet](#8-configuration-cheat-sheet) |
| Offline RAG / agent metrics | [§9 Evaluation harness](#9-evaluation-harness) |
| What is broken or unfinished | [§10 Known gaps](#10-known-gaps) |
| Common failures | [§11 Troubleshooting](#11-troubleshooting) |
| Other markdown files | [§12 Document index](#12-document-index) |
| Typical questions from past work on this repo | [§13 Question map](#13-question-map-past-conversations) |

**Deeper dives (already in repo):** flow diagrams → `Architecture.md`, `/dev` in the app, `rag-pipelines.md`.  
**Day-to-day usage (non-dev):** `How_To_Use.md`.

---

## 1. Project snapshot

### What it is

- A **Streamlit capstone**: multi-day **AI trip planner** + **simulated travel customer portal** (bookings, refunds, support, admin).
- **Not** a production travel agency — no real payments, no hosted backend API.

### Three independent “brains” (do not merge mentally)

| Brain | Technology | Purpose |
|-------|------------|---------|
| **Trip planner** | Gemini + OpenStreetMap (Nominatim + Overpass) | Build JSON itineraries from real POIs |
| **Policy / support Q&A** | LangChain + in-memory FAISS + Gemini embeddings | Answers grounded in in-app terms / FAQ |
| **Portal rules** | Python (`refund_eligibility.py`) | Refund eligibility — **no LLM override** |

Optional fourth path: **Wikivoyage TF-IDF** (`wikivoyage_rag.py`) as an agent tool only — **not** the same as policy FAISS.

### Golden rule (trip planning)

> The model **must not invent places**. Every stop’s `poi_id` must exist in `tool_state.pois` from OSM search before the itinerary is accepted.

### What problem it solves

- **Fake itineraries** — ties days to a verified POI catalog instead of hallucinated attractions.
- **Split experience** — one UI for plan, map, travel hints, history, export, and policy chat.
- **Unsafe policy chat** — retrieval + grounded generation on terms instead of guessing refund rules.
- **Demo-ready capstone** — full UX without SQL, payments, or a separate API server.

---

## 2. Quick start

### Prerequisites

- Python 3.10+ recommended  
- `GEMINI_API_KEY`, `OSM_CONTACT_EMAIL` in `.env`  
- Network for Gemini and OpenStreetMap

### Commands

```bash
cd /path/to/Travel_Planner
python -m venv trip-planner-env && source trip-planner-env/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit keys locally — never commit
streamlit run app.py
```

Details: `SETUP.md`, `README.md`.

### First smoke test

1. Home → fill trip form → **Create my itinerary** (may take ~1 min).  
2. Support or Trip policy FAB → ask a terms question (first call builds FAISS in memory).  
3. Sidebar **User** → Bookings → try Refund Assistant on a demo booking.

---

## 3. Repository map

```
Travel_Planner/
├── app.py                 # Streamlit entry: navigation, trip UI, generation handlers
├── config.py              # Paths, models, timeouts, feature flags from .env
├── pages/                 # Portal routes (bookings, support, admin, dev, …)
├── services/
│   ├── trip/              # Agent, POI search, map, weather, refine, feedback, …
│   ├── rag/               # website_rag, terms_rag, support_faq, semantic_cache, …
│   ├── portal/            # Bookings, refunds, admin, demo users, packages
│   ├── core/              # persistence, http, retry, shared validation
│   └── ui/                # Policy bot, dev markdown viewer, theme, package UI
├── data/                  # JSON persistence (runtime files often gitignored)
├── tests/                 # Unit / integration tests
├── eval/                  # Offline RAG & routing evaluation harness
└── docs/                  # Architecture, testing, this handbook
```

### Entry points worth memorizing

| File | Role |
|------|------|
| `app.py` | `main()`, `_run_generation`, itinerary/map/travel tabs, persist flush |
| `services/trip/agent.py` | `run_agent()` — fast generate, tool loop, refine / single-day |
| `services/trip/poi_search.py` | Geocode + Overpass → ranked POI catalog |
| `services/rag/website_rag.py` | Chunk, embed, FAISS, `generate_grounded_answer` |
| `services/rag/support_faq.py` | Route support query → rules data **or** terms RAG |
| `services/portal/refund_eligibility.py` | Refund decision table |
| `services/core/persistence.py` | Load/save `app_state.json` |

### Pages (URL → file)

| Path | Purpose |
|------|---------|
| `/` | Trip planner |
| `/bookings` | Bookings & refunds |
| `/refund-assistant` | Guided refund Q&A (rules) |
| `/support` | FAQ + policy bot + tickets |
| `/terms` | Terms & policies |
| `/admin` | Admin console (`demo_admin`) |
| `/dev` | Developer docs (renders markdown + flow assets) |
| `/sign_in` | Local auth (demo) |

Full user map: `How_To_Use.md`.

---

## 4. Trip planner flow

### User journey (happy path)

1. User submits form → `validate_trip_inputs`.  
2. `run_agent(..., mode="generate", fast_mode=True)` (default).  
3. **Fast generate:** `search_pois` → Gemini produces itinerary JSON.  
4. `_finalize_itinerary`: parse JSON, validate every `poi_id`, enrich photos/hints.  
5. UI: itinerary tabs, map (PyDeck), travel/weather; append **trip history**; persist `app_state.json`.

### `run_agent` routing (simplified)

```
run_agent
├── mode refine / single_day → _run_fast_refine (see below)
├── fast_mode + generate
│   ├── _run_fast_generate → search_pois → Gemini JSON
│   └── on soft failure → fall back to tool loop (not on hard OSM errors)
└── tool loop (slow path)
    └── Gemini calls search_pois, optional retrieve_guides → JSON
```

**When is fast generate used?**  
`fast_mode=True` and `mode="generate"` → tries one-shot OSM + Gemini without multi-step tool loop.

**When is tool calling used?**  
Fast path fails softly, or `fast_mode=False`, or non-generate modes that need tools.

Refine path (`_run_fast_refine`): seed POIs from current plan → optional **surgical local add** → more OSM/geocode → Gemini only if needed. Diagram: `Architecture.md` § Place refinement.

### Itinerary JSON shape

```json
{
  "destination": "Goa",
  "days": [{
    "day": 1,
    "morning": [{ "poi_id": "…", "name": "…", "why": "…" }],
    "afternoon": [],
    "evening": []
  }]
}
```

Enrichment may add `lat`, `lon`, `category`, `url`, `image_url`.

### Feedback loop

👍/👎 on stops → `data/feedback.jsonl` → score boosts on next `search_pois` for that `city_key`.

### Streamlit model

Every widget interaction **reruns the whole script**. State lives in `st.session_state` + disk when dirty. See `info.md` §5–6.

---

## 5. Policy RAG flow

### Corpus → index → answer

1. **Sources:** `terms_content.py`, FAQ, `refund_policy_config.POLICIES`.  
2. **Chunk:** 1100 chars, overlap 180 (`RecursiveCharacterTextSplitter`).  
3. **Embed:** `GoogleGenerativeAIEmbeddings` (Gemini).  
4. **Index:** `FAISS.from_documents` — **in memory only** (`@st.cache_resource`), rebuilt on process restart or embedding cache version bump.  
5. **Retrieve:** similarity search, score filter (~`MIN_RELEVANCE_SCORE` 0.42).  
6. **Generate:** `generate_grounded_answer` with system instruction grounded in chunks.

### Support routing (`answer_support_query`)

| Question type | Path |
|---------------|------|
| Booking / refund status (keyword / intent) | Live portal data — **no FAISS** |
| Policy / terms | Terms RAG → optional **semantic cache** (retrieved chunks only) → FAISS → Gemini |

Shared UI: `policy_bot_ui` (Support page, trip sidebar/FAB).

### Wikivoyage (trip agent only)

- Flag: `ENABLE_WIKIVOYAGE_RAG=true`.  
- TF-IDF + cosine on guide chunks — **not FAISS**.  
- Disabled in default fast generate; used when agent tool loop calls `retrieve_guides`.

### URL scrape index

`website_rag` can build a per-URL FAISS index for **testing**; **chat answers still use the Terms index** (gap G-5 in `docs/PLAN.md`).

---

## 6. Customer portal

### Scope

Demo users (sidebar), package catalog, fake bookings, refund requests, support tickets, account appeals, admin audit — all in JSON.

### Refund rule engine

```
User question → load booking + account
             → evaluate_refund_request()
             → eligibility, fees, reason codes
             → display (Refund Assistant / bookings UI)
```

**Invariant:** UI and bots must not contradict `refund_eligibility.py`.

### Admin

- Passphrase: `demo_admin` (training only — treat as public).  
- Mutates `customer_portal_state.json` + audit log.  
- Admin dashboard hides customer-only actions (e.g. customer refund submit on bookings).

---

## 7. Data & persistence

### Primary files

| File | Holds |
|------|--------|
| `data/app_state.json` | Current itinerary, forms, `tool_state` (POIs), trace tail, `trip_history` |
| `data/feedback.jsonl` | POI votes |
| `data/demo_bookings.json` | Static booking catalog (committed example) |
| `data/customer_portal_state.json` | Refunds, tickets, packages, appeals, audit |
| `data/rag_retrieval_cache.jsonl` | Semantic cache entries (if enabled) |
| RAG auth JSON | Local users/sessions (often gitignored) |

### What is **not** on disk

- FAISS index files (rebuilt in RAM).  
- Policy chat message history (session-only).  
- Most Streamlit widget state (except what you flush to JSON).

Schema detail: `docs/DATABASE.md`, `info.md` §13.

---

## 8. Configuration cheat sheet

| Variable / constant | Default / notes | Effect |
|---------------------|-----------------|--------|
| `GEMINI_API_KEY` | required | Trip + embeddings + RAG answers |
| `OSM_CONTACT_EMAIL` | required | User-Agent for Nominatim/Overpass |
| `ENABLE_WIKIVOYAGE_RAG` | false | Agent `retrieve_guides` tool |
| `SEMANTIC_CACHE_ENABLED` | false (see `config.py` / `.env`) | Cache **retrieved policy chunks**, not final replies |
| `GEMINI_PROMPT_CACHE_ENABLED` | false | CachedContent for grounded system prompt only |
| `DEFAULT_MODEL` | `gemini-3.5-flash-lite` | Chat / generation |
| `EMBEDDING_CACHE_VERSION` | bumped on embed changes | Invalidates Streamlit embed cache |
| `FAST_MODE_MAX_STEPS` | 4 | Tool loop cap in fast mode |
| `FAST_POI_LIMIT` | 45 | POIs passed to model in fast path |

**Performance tip:** First trip for a new city is slow (OSM + Gemini). Policy first question is slow (embed entire terms corpus). Overpass outages cause hard failures — see troubleshooting.

---

## 9. Evaluation harness

Offline evaluation under `eval/` — does not replace `pytest tests/`.

| Component | Dataset | Runner |
|-----------|---------|--------|
| Terms RAG | `eval/datasets/terms_rag_golden.jsonl` | `eval/runners/terms_retrieval.py` |
| Support routing | `support_faq_routing.jsonl` | `support_faq` runner |
| Refund rules | `refund_decision_table.jsonl` | `refund_rules` |
| Wikivoyage (optional) | `wikivoyage_golden.jsonl` | `wikivoyage` |

**Primary command:**

```bash
pytest tests/ -q
python3 -m eval.run_pipeline --refresh-baseline
```

Metrics: MRR, hit@k, NDCG, groundedness, hallucination rate, Ragas-aligned fields — see `Architecture.md` (metrics section) and `eval/README.md`.

---

## 10. Known gaps

Authoritative lists: `FEATURES.md` (implemented vs incomplete), `docs/PLAN.md` (maintenance gaps).

| ID | Issue |
|----|--------|
| U-1 / G-3 | No UI for full `mode="refine"` |
| U-2 / G-1 | Refinement compare UI not wired |
| U-4 / G-4 | Document Assistant shell not mounted on a route |
| U-5 / G-5 | URL FAISS not used in live chat answers |
| G-14 | `require_login` always false (demo) |
| G-11 | Demo security — admin passphrase is not secret |

**Regression hotspots** (change with care): `website_rag` thresholds/prompts, `EMBEDDING_CACHE_VERSION`, `agent` fast mode, `support_faq` branches, portal JSON schema, `app_state` shape.

---

## 11. Troubleshooting

| Symptom | Likely cause | What to check |
|---------|----------------|---------------|
| Overpass 502 / timeout | Public API overload | `config.OVERPASS_FALLBACK_URLS`, retries; retry later |
| “No POIs” / geocode fail | Bad destination or OSM block | `OSM_CONTACT_EMAIL`, logs in agent trace |
| Policy bot empty / slow first hit | FAISS cold build | Wait once; restart clears in-memory index |
| Itinerary invalid JSON | Model parse fail | Agent trace, `last_error`, export raw text |
| Streamlit page not found | Navigation / `pages/` mismatch | `app.py` `st.navigation` registry |
| `/dev` layout broken | Theme CSS from trip pages | `services/ui/dev_document_view.py` |
| Chat UI resets on send | Rerun clears partial state | Two-phase chat pattern in policy UI |
| Eval vs prod embed mismatch | Eval may use HF embeddings | `eval/helpers/real_embeddings.py` vs prod Gemini |

---

## 12. Document index

| Document | Use when |
|----------|----------|
| **This file** (`docs/PROJECT_HANDBOOK.md`) | Full re-onboarding |
| `README.md` | Install, stack, one-page overview |
| `info.md` | In-app developer guide (linked from `/dev`) |
| `How_To_Use.md` | End-user / demo script |
| `Architecture.md` | Flowcharts, Mermaid, eval metric formulas |
| `docs/ARCHITECTURE.md` | Implementation-level architecture |
| `docs/DATABASE.md` | JSON + FAISS lifecycle |
| `docs/TESTING.md` | Test commands |
| `docs/PLAN.md` | Approved vs suggested work |
| `FEATURES.md` | Feature IDs and code pointers |
| `rag-pipelines.md` | Short RAG diagram-only reference |
| `eval/README.md` | Running evaluation pipeline |

---

## 13. Question map (past conversations)

From prior Cursor sessions on this repo, questions usually fell into these buckets. **Use this section when you are not sure what to read.**

### A. “Explain the system” (architecture & behavior)

- What is the project? What problem does it solve?  
- RAG architecture in layman terms + pipeline per feature  
- When does **fast generate** run vs **tool calling**?  
- What happens in **place refinement** / single-day update?  
- Resume / portfolio description for the capstone  

→ Read: §1, §4, §5, `Architecture.md`, `rag-pipelines.md`.

### B. Documentation & diagrams

- Rewrite or shorten `.md` files without losing facts  
- Add flowcharts to `/dev` or `ARCHITECTURE.md`  
- Document query flow end-to-end  

→ Read: §12, edit `info.md` / `Architecture.md` / `pages/dev.py` together.

### C. UI / UX changes

- Itinerary cards, nearby POI swap, package detail layout  
- Streamlit chat input disappearing during loading  
- Dev page not opening, diagram sizing on dev docs  

→ Start: `app.py`, `services/ui/*`, `services/ui/policy_bot_ui.py`.

### D. Features, flags, performance

- Effect of `ENABLE_WIKIVOYAGE_RAG`, semantic cache, prompt cache, CrewAI / orchestration flags  
- App feels slow — what to turn off or optimize  
- Agent trace / planning transparency  

→ Read: §8, `config.py`, `services/trip/planning_progress.py`, agent trace in UI.

### E. Bugs & errors

- Terminal stack traces pasted or “fix this error”  
- Overpass 502, CrewAI/pydantic validation, page not found  

→ Read: §11, agent trace, `services/core/retry_utils.py`, `tests/`.

### F. Evaluation & quality

- How to evaluate RAG; benefits of evals; implement eval harness  
- Threshold sweeps, Ragas, baseline CSV  

→ Read: §9, `eval/README.md`, `eval/reports/EVAL_REPORT.md`.

### G. Repo hygiene & safe refactors

- Folder structure proposals with “do not break the app”  
- Remove unused pages (e.g. document assistant)  
- Clean `data/` folders  

→ Read: `docs/PLAN.md`, run `pytest tests/ -q` before and after.

---

## 14. Mental checklist before you change code

1. **Trip change** — Will every `poi_id` still resolve against `tool_state.pois`?  
2. **Policy change** — Did retrieval threshold or chunking change? Re-run eval + spot-check Support.  
3. **Refund change** — Only `refund_eligibility.py` + portal UI; never LLM-only rules.  
4. **Persistence change** — Migration path for existing `app_state.json` / portal JSON?  
5. **Docs** — Update `FEATURES.md` or `info.md` if user-visible behavior changed.

---

*Last structured for repo state as of capstone maintenance (Streamlit + Gemini + FAISS terms RAG + JSON portal). Update §8 when `config.py` or `.env.example` changes.*