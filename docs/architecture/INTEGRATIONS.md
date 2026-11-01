# INTEGRATIONS.md — external services (as implemented)

Derived from source + `requirements.txt`. No secret values. Installed versions **unknown** unless you `pip freeze`.

## Overview

| Integration | Auth | Modules |
|-------------|------|---------|
| Google Gemini | `GEMINI_API_KEY` | `agent.py`, `website_rag.py`, `destination_guide.py` |
| Gemini embeddings (LangChain) | Same key | `website_rag.py` |
| LangChain + FAISS | In-process | `website_rag.py` |
| Nominatim / Overpass | User-Agent (`OSM_CONTACT_EMAIL`) | `geocoding`, `poi_search`, `travel_hints` |
| Wikivoyage API | User-Agent | `wikivoyage_rag.py` |
| Wikipedia | User-Agent | `place_images`, `destination_guide` |
| Open-Meteo | None | `weather.py` |
| HTTP(S) URLs | None | `WebBaseLoader` in `website_rag` |

**Absent:** OpenAI, Anthropic, Stripe, SMTP, S3, payment APIs, in-repo REST server.

**Local:** JSON `data/`, Streamlit, sklearn TF-IDF, pydeck, auth cookies.

## Gemini (`google-genai` ≥1.0)

Uses: trip agent, grounded RAG answers, optional destination guide JSON.

Env: `GEMINI_API_KEY` (required), optional `GEMINI_EMBEDDING_MODEL`, `DESTINATION_GUIDE_AI`. Models from `config.py` (`DEFAULT_MODEL`, fallbacks).

Behavior: `genai.Client`; tool loop with `search_pois` / `retrieve_guides`; RAG `temperature=0.1`; model fallback on invalid model id; agent retries 429/503 via `retry_utils` (max 2). No app-side Gemini quota caps.

**Safe test:** `test_terms_rag` patches key + FakeEmbeddings; manual smoke with dedicated key.

## LangChain + FAISS

Packages: langchain-core/community/google-genai/text-splitters, faiss-cpu.

Flow: static terms → split 1100/180 → embed → `FAISS.from_documents` → `similarity_search_with_score` (no LCEL). URL loader 20s timeout; **answers use Terms index**.

Cache: `@st.cache_resource`; rebuild on restart / `EMBEDDING_CACHE_VERSION`.

**Safe test:** `pytest tests/test_terms_rag.py`, `test_rag_citations.py`.

## Nominatim

GET search; 15s timeout; 2 retries; **1.05s** min spacing when limited. Missing email → empty User-Agent → failures + UI warning.

**Safe test:** `connections.test_nominatim(user_agent)` or one manual trip.

## Overpass

POST to `overpass-api.de`; 15s; retries; `@st.cache_data` on queries. Errors → `Overpass API failed: …`.

**Safe test:** `connections.test_overpass(user_agent)`.

## Wikivoyage

Default **off** (`ENABLE_WIKIVOYAGE_RAG=false`). Query + parse HTML → TF-IDF chunks. Article cache TTL 24h.

**Safe test:** leave off; enable env for one manual run if needed.

## Wikipedia / Open-Meteo

Standard GET JSON for images, extracts, forecast — User-Agent where required.

## URL scrape

`validate_http_url` (scheme + host only); `load_documents_from_url`; product = scrape test panel, not default answers.

## HTTP client summary

`REQUEST_TIMEOUT_SEC=15`, `MAX_RETRIES=2`, Nominatim throttle in `http_client.py`. Gemini uses SDK defaults.

## Safe testing summary

| Integration | Offline |
|-------------|---------|
| FAISS/terms | FakeEmbeddings tests |
| Refunds/validation | `-m` modules |
| OSM/Gemini full trip | Manual sparingly |
| Wikivoyage | Default skip |

See `TESTING.md` §10 for destructive/costly actions.

## Cross-refs

`API.md`, `DATABASE.md`, `AUTH_SECURITY.md` (URL SSRF note).
