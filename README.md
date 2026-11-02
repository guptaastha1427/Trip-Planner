# Trip Planner AI Agent

**Streamlit capstone:** multi-day trips via **Gemini + OpenStreetMap**; **demo portal** (bookings/refunds/support); **policy Q&A** via **LangChain + in-memory FAISS**. Not a real travel agency — no real payments.

## Features (short)

**Trip Planner:** Form (1–14 days, pace, interests) → **Create my itinerary** → itinerary / map / travel tabs; nearby swap; 👍/👎 → `feedback.jsonl`; single-day update; package prefill; policy FAB; export JSON; agent trace; trip history (User sidebar); balloons on generate.

**Portal:** `/bookings`, refund assistant (rules), account, support (FAQ + FAISS bot + tickets), terms, sign-in, admin (`demo_admin`).

**Optional / gaps:** Wikivoyage tool off by default; no full-itinerary refine button; Document Assistant menu helpers not on a route.

## Stack

Streamlit · Python · `google-genai` · LangChain + **faiss-cpu** · PyDeck · JSON under `data/` (no SQL/Chroma) · no REST server.

## Layout

```
app.py, config.py, pages/{dev.py,portal/}, services/{core,trip,rag,portal,ui}/, data/, tests/, docs/, README.md
```

Runtime (gitignored): `app_state.json`, `feedback.jsonl`, `customer_portal_state.json`, rag auth JSON.

## Setup

```bash
python -m venv trip-planner-env && source trip-planner-env/bin/activate
pip install -r requirements.txt
cp .env.example .env   # GEMINI_API_KEY + OSM_CONTACT_EMAIL required
streamlit run app.py   # http://localhost:8501
```

Optional: `.streamlit/secrets.toml` for Gemini key.

## Policy RAG (summary)

`website_rag.py`: terms strings → chunk 1100/180 → Gemini embed → FAISS in memory → retrieve (≥0.42) → `generate_grounded_answer`. Chat entry: `support_faq.answer_support_query`.

## Trip flow

Load `app_state.json` → validate → `run_agent` (OSM POIs + Gemini JSON) → validate `poi_id`s → UI + persist + history.

## External services

Gemini (key); Nominatim/Overpass (User-Agent email); Wikivoyage (optional); Open-Meteo; Wikipedia. Default model `gemini-3.5-flash-lite`.

## Tests

```bash
python -m tests.portal.test_refund_eligibility
python -m tests.trip.test_validation
python -m tests.trip.test_map_tooltip
pytest tests/ -q   # needs pytest
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Env warning | Set `.env` keys |
| Policy search fails | Key + embed model; restart Streamlit |
| No POIs | OSM email; destination spelling |
| Admin locked | Admin sidebar or `demo_admin` |
| Stale terms in search | Restart or bump `EMBEDDING_CACHE_VERSION` (intentional) |

## Docs

| File | Role |
|------|------|
| `docs/runbooks/using.md` | User/admin steps |
| `docs/guides/info.md` / `/dev` | Deep guide |
| `docs/product/`, `docs/architecture/`, … | Product & tech |
| `docs/meta/AGENTS.md` (symlink at root) | AI edit rules |

Credits: OSM, Wikivoyage, Open-Meteo, Wikipedia, Google Gemini.
