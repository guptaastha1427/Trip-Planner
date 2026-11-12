## 1) Policy / Terms RAG (Support bot, Document Assistant)

Support bot (policy path), Document Assistant chat, and Trip policy FAB share **Terms FAISS + optional semantic cache + Gemini**. Booking/refund shortcuts in Support use live portal data without FAISS.

```mermaid
flowchart LR
  A[User asks] --> B[Search Terms text]
  B --> C{Similar question<br/>cached?}
  C -->|Yes| D[Reuse old chunks]
  C -->|No| E[FAISS find<br/>matching paragraphs]
  E --> D
  D --> F[Gemini writes answer<br/>from those paragraphs]
  F --> G[Show answer<br/>+ source links]
```

## 2) Wikivoyage TF-IDF RAG (`wikivoyage_rag.py`)

Optional trip agent tool only (`retrieve_guides`). **sklearn TF-IDF + cosine** — not FAISS. Off unless `ENABLE_WIKIVOYAGE_RAG=true`.

```mermaid
flowchart LR
  A[Trip agent<br/>calls retrieve_guides] --> B{ENABLE_<br/>WIKIVOYAGE_RAG?}
  B -->|false| Z[Empty chunks<br/>tool skipped]
  B -->|true| C{Destination in<br/>_RAG_CACHE?}
  C -->|no| D[MediaWiki API<br/>fetch article HTML]
  D --> E[Strip HTML<br/>chunks ~800–1000 chars]
  E --> F[Build TF‑IDF index<br/>for that city]
  F --> G[Save in<br/>_RAG_CACHE]
  C -->|yes| G
  G --> H[Score query vs chunks<br/>cosine similarity]
  H --> I[Return top‑k chunks<br/>to agent]
  I --> J[Gemini uses chunks<br/>while planning itinerary]
```
