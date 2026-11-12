Three things which is not persist in the app_state.json

1. Chat history
2. Chunks
3. Votes

**pytest** is a popular third-party Python testing framework that simplifies writing and executing these tests.

# Application flows

Developer docs (`/dev`) show architecture flowcharts (PNG + fullscreen). Trip and Destination first; merged Terms/policy hub; portal refund; plus the two RAG pipeline charts below.


| Flow                                                    | Retrieval                                          | Gemini                 |
| ------------------------------------------------------- | -------------------------------------------------- | ---------------------- |
| Trip Planner Agent                                      | POI tools + optional RAG                           | Yes                    |
| Destination Guide                                       | TF-IDF + cosine similarity                         | Yes                    |
| Terms & policy retrieval (merged hub)                   | Policy Assistant + Support policy + Semantic cache | FAISS + cache + Gemini |
| Customer Portal → Refund                                | Python rule engine                                 | No                     |
| 1) Policy / Terms RAG (Support bot, Document Assistant) | Terms FAISS + semantic cache                       | Yes                    |
| 2) Wikivoyage TF-IDF RAG (`wikivoyage_rag.py`)          | sklearn TF-IDF + cosine (agent tool)               | Yes (itinerary)        |




## Trip Planner Agent



### Trip routing (`run_agent`)

Entry in `services/trip/agent.py`. Refine paths delegate to `_run_fast_refine` (detail below). Fast generate can fall through to the tool loop on soft failure (not geocoding/Overpass hard errors).

![run_agent routing](docs/assets/dev-flows/run_agent.png)

```mermaid
flowchart TD
  A[User Trip Request] --> B["run_agent()"]
  B --> C{Select Execution Path}
  C --> D[Tool Agent Loop]
  D --> E["_run_tool()"]
  E --> F["search_pois()"]
  E --> G["retrieve_guides()"]
  F --> H[Return Tool Result]
  G --> H
  H --> I[Send Query + Tools to Gemini]
  I --> J{Gemini Requests Tool?}
  J -->|Yes| E
  J -->|No| K[Final Itinerary JSON]
  C --> L[Fast Generate]
  L --> M["search_pois()"]
  M --> K
  C --> N[Fast Refine]
  N --> O[Update Existing Itinerary]
  O --> K
  K --> P["Parse + Validate + Enrich"]
  P --> Q[Final Itinerary + Map]
```





## Place refinement (`_run_fast_refine`)

Refine and single-day edits (`services/trip/agent.py`, `refine_itinerary.py`): seed POIs from the current itinerary, try a local surgical add when possible, enrich the catalog via OSM/geocode, then Gemini only if nee**ded.**

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





## Destination Guide(Retrival 1) Wikivoyage

```mermaid
flowchart TD
  A[User asks about Destination] --> B["retrieve_guides()"]
  B --> C[Fetch Wikivoyage Guide]
  C --> D[Extract Guide Text]
  D --> E[Split Text into Chunks]
  E --> F[TF-IDF Vectorization]
  F --> G[Cosine Similarity Search]
  G --> H[Retrieve Relevant Chunks]
  H --> I["Send Question + Chunks to Gemini"]
  I --> J[Destination Guide Answer]
```





## Terms & policy retrieval (Retrival 2) Semantic Caching

Policy Assistant, Help & Support (policy path), and Semantic retrieval cache share **Terms RAG → cache → FAISS → Gemini**; Support **booking/refund** branch uses live data (no FAISS).

```mermaid
flowchart TD
  U1[User asks Policy Question] --> PA[Policy Assistant]
  U2[User asks a question] --> ASQ["answer_support_query()"]
  ASQ --> QT{Question Type?}
  QT -->|Booking / Refund| FUD[Fetch User Data]
  FUD --> PREP[Prepare Answer]
  PREP --> DA[Display Answer]
  PA --> TR[Terms RAG]
  QT -->|Policy Question| TR
  TR --> EMB[Convert Question to Embedding]
  EMB --> SCL[Semantic Cache Lookup]
  SCL --> SQ{Similar Query Found?}
  SQ -->|Yes: Cache Hit| RCC[Return Cached Chunks]
  SQ -->|No: Cache Miss| FAISS[FAISS Similarity Search]
  RCC --> RRPP[Retrieve Relevant Policy Chunks]
  FAISS --> RRPP
  RRPP --> RSF[Relevance Score Filter]
  RSF --> G1["Gemini + Question + Chunks"]
  G1 --> GPA[Grounded Policy Answer]
  GPA --> SAC[Show Answer + Citations]
  SAC --> DA
```





## Customer Portal → Refund (Rule Based)

Separate rule engine — not merged with Terms / FAISS hub.

```mermaid
flowchart TD
  A["User: Can I get a refund?"] --> B[Customer Portal]
  B --> C[Load Booking + User Details]
  C --> D["evaluate_refund_request()"]
  D --> E[Check Booking Status]
  E --> F[Check Departure Time]
  F --> G[Calculate Cancellation Fee]
  G --> H[Check Refund Eligibility]
  H --> I[Refund Result + Reason]
  I --> J[Display Result to User]
```





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



---

`streamlit run app.py` · `README.md` · `SETUP.md` · `info.md`