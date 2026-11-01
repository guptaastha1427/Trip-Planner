# SETUP.md — run locally

Matches repo files only. No required FAISS disk setup.

## Prerequisites

Python **3.8+** per README (use **3.10+** venv if wheels fail). Project root = `app.py` + `requirements.txt`. Network for Gemini, OSM, optional Open-Meteo/Wikivoyage/Wikipedia. Gemini key from [Google AI Studio](https://aistudio.google.com/apikey).

## Steps

```bash
cd /path/to/Travel_Planner
python -m venv trip-planner-env && source trip-planner-env/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit locally — never commit
streamlit run app.py   # → http://localhost:8501
```

## `.env` variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | Yes | Trip + embeddings + RAG |
| `OSM_CONTACT_EMAIL` | Yes | Nominatim/Overpass User-Agent |
| `GEMINI_EMBEDDING_MODEL` | No | Embed override |
| `ENABLE_WIKIVOYAGE_RAG` | No | Default false |
| `DESTINATION_GUIDE_AI` | No | Default false |

Loaded by `config.py`; optional `st.secrets["GEMINI_API_KEY"]` fallback in `app.py`.

## `data/` & FAISS

Created on demand. Examples in `data/*.example`; `demo_bookings.json` committed. Runtime files gitignored.

**FAISS:** Built in memory on first policy query (`get_terms_vector_store`); **no** checked-in index. Restart or `EMBEDDING_CACHE_VERSION` bump refreshes embed cache.

## First vs later runs

First: env warnings until keys set; generate needs both keys; first policy question embeds corpus.

Later: `app_state.json` loads into session; same process keeps warm FAISS cache.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Env warning on planner | Set keys in `.env`, refresh |
| Generate fails | Valid `GEMINI_API_KEY` |
| No POIs / geocode | `OSM_CONTACT_EMAIL` |
| Policy bot search fails | Key + optional `GEMINI_EMBEDDING_MODEL`; **restart** Streamlit |
| `/dev` missing file | Ensure `docs/info.md` exists |
| Port busy | Stop other Streamlit or use alternate port |

**Do not** wipe `data/` to fix FAISS — index is not on disk.

## Optional tests

```bash
python -m tests.test_refund_eligibility
python -m tests.test_terms_rag   # needs pytest for test_* functions
python -m tests.test_validation
```

See `TESTING.md`, `../README.md`.

## Related

`DATABASE.md`, `API.md`, `AGENTS.md`, `using.md`.
