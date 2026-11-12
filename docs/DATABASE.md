# DATABASE.md — data & vectors (as implemented)

**No SQL, ChromaDB, or on-disk FAISS files.** Policy search = **LangChain FAISS + Gemini embeddings** in memory (`@st.cache_resource`). Trip optional context = **TF-IDF Wikivoyage** (separate).

## FAISS

| Q | A |
|---|---|
| Where? | `services/website_rag.py` only (+ `FakeEmbeddings` in tests) |
| Build | `FAISS.from_documents` after split; index type **not named** (likely IndexFlatL2 via LangChain default) |
| Retrieval | `similarity_search_with_score` only — **no LCEL chains** |
| `TERMS_STORE_ID` | Constant unused elsewhere |

## Embeddings

`GoogleGenerativeAIEmbeddings`; candidates from `config.get_gemini_embedding_model_candidates()`; optional `GEMINI_EMBEDDING_MODEL`; probe `healthcheck`; cache key `EMBEDDING_CACHE_VERSION=4`; errors in `_embedding_init_error`. **Dimension not in code** (tests use 384 fake).

## Terms pipeline

**Sources:** `terms_content.py` (intro, sections, FAQ, RAG terms), `refund_policy_config.POLICIES` → `Document` + `metadata.source`.

**Chunk:** 1100 / 180, `RecursiveCharacterTextSplitter`.

**Retrieve:** top_k 4 (store) or 3 (`terms_rag`); MIN **0.42**; loose retry **0.32** in `support_faq`.

**Chain:** `policy_bot_ui` → `answer_support_query` → `answer_from_terms_document` → `retrieve_from_terms_kb` → optional `generate_grounded_answer`.

## URL FAISS (secondary)

`WebBaseLoader` 20s, ≥40 chars, same splitter, `get_url_vector_store(url)` per URL. **Chat uses Terms only**; scrape test UI only.

## Lifecycle

In-memory until process restart/cache clear. Rebuild: first query, version bump, embed model change. **Do not delete `data/` expecting FAISS files.**

## Wikivoyage (NOT FAISS)

If `ENABLE_WIKIVOYAGE_RAG=true`: chunks 800–1000, TF-IDF, `top_k=5`, fetch TTL 24h, `_RAG_CACHE`. Chunks stored in `tool_state` inside `app_state.json` when used.

## JSON files (`config.py` paths)

| File | Purpose |
|------|---------|
| `app_state.json` | Itinerary, tool_state, forms, trace tail, trip_history |
| `feedback.jsonl` | POI votes |
| `demo_bookings.json` | Sample catalog (committed) |
| `customer_portal_state.json` | Refunds, tickets, packages, appeals, audit, overrides |
| `rag_chat_users.json` / `sessions.json` | Local auth (gitignored) |

Examples: `data/*.example`. Session-only: policy chat, Streamlit widgets, `@st.cache_data` geocode/POI.

## Terms index shape (conceptual)

Flat FAISS over chunk vectors (L2 per comments) + docstore (text + `source` metadata) + cached embed function.

## Update behavior

Edit `terms_content`/`POLICIES` → **restart** or bump `EMBEDDING_CACHE_VERSION` to refresh index. Portal/feedback append on user actions.

## Limitations

Dual stacks (FAISS vs TF-IDF); volatile vectors; URL RAG not in answers; score comment drift; no per-user FAISS; Refund Assistant not vector search.

## Sources

`website_rag.py`, `terms_rag.py`, `support_faq.py`, `wikivoyage_rag.py`, `persistence.py`, `customer_portal_store.py`, `rag_chat_auth.py`, `tests/test_terms_rag.py`.
