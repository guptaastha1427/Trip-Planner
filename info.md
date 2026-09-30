# Trip Planner — पूरा project guide (info.md)

> **Is file ka goal:** Sirf yeh padh kar tumhe samajh aa jaye — app kya karti hai, code ka flow kya hai, data kahan jaata hai, aur AI/OSM ka role kya hai.  
> **Chalane ke liye:** project root se `streamlit run app.py`

---

## Table of contents

1. [30-second summary](#1-30-second-summary)
2. [Simple story — user ki nazar se](#2-simple-story--user-ki-nazar-se)
3. [Big picture flowchart](#3-big-picture-flowchart)
4. [Code map — kaunsi file kya karti hai](#4-code-map--kaunsi-file-kya-karti-hai)
5. [Streamlit app flow (`app.py`)](#5-streamlit-app-flow-apppy)
6. [Agent flow — itinerary kaise banti hai](#6-agent-flow--itinerary-kaise-banti-hai)
7. [POI search flow (OpenStreetMap)](#7-poi-search-flow-openstreetmap)
8. [Validation flow](#8-validation-flow)
9. [Single-day update & nearby swap](#9-single-day-update--nearby-swap)
10. [Feedback loop](#10-feedback-loop)
11. [Travel tab extras (weather, guide, hotels)](#11-travel-tab-extras)
12. [Optional Wikivoyage RAG](#12-optional-wikivoyage-rag)
13. [Data files & memory](#13-data-files--memory)
14. [Itinerary JSON shape](#14-itinerary-json-shape)
15. [Config & APIs](#15-config--apis)
16. [Errors & retries](#16-errors--retries)
17. [Glossary](#17-glossary)

---

## 1. 30-second summary

| Question | Answer |
|----------|--------|
| **Yeh app kya hai?** | Multi-day trip planner: real places (OSM) + Gemini AI day-by-day schedule |
| **UI** | Streamlit — form, 3 tabs (Itinerary / Map / Travel), sidebar history |
| **AI** | Google Gemini — JSON itinerary banata hai; sirf wahi `poi_id` use kar sakta hai jo pehle OSM se aaye |
| **Places** | Nominatim (city location) + Overpass (museums, food, parks, …) |
| **Save kahan?** | `data/app_state.json` (trip + forms), `data/feedback.jsonl` (👍/👎) |

**Golden rule:** Model **khud se jagah invent nahi kar sakta**. Har stop ka `poi_id` `tool_state.pois` dictionary mein hona chahiye.

---

## 2. Simple story — user ki nazar se

1. Browser mein app kholo → purana trip (agar tha) disk se load ho jata hai.
2. **From / To / Days / Interests** bharo → **Create my itinerary**.
3. Peeche: city geocode → OSM se places list → Gemini un places ko morning/afternoon/evening mein arrange karta hai.
4. Tumhe days dikhte hain, map par route, Travel tab par weather + airports + hotels.
5. Pasand na aaye to **ek din update** kar sakte ho, ya **nearby place swap** (bina AI).
6. 👍/👎 likho — agli baar us city mein search par ranking badal jati hai.
7. Sidebar se purane trips dubara load kar sakte ho.

```mermaid
flowchart LR
  subgraph You["Tum (user)"]
    F[Form bharo]
    V[Itinerary dekho]
    E[Edit / feedback]
  end

  subgraph App["App (Streamlit)"]
    S[Session + disk save]
    T[Tabs: Plan / Map / Travel]
  end

  subgraph Brain["Planning"]
    A[agent.py]
    G[Gemini]
  end

  subgraph World["Real world data"]
    OSM[OpenStreetMap]
  end

  F --> A
  A --> OSM
  A --> G
  G --> S
  S --> T
  T --> V
  V --> E
  E --> S
```

---

## 3. Big picture flowchart

Poora system ek diagram mein:

```mermaid
flowchart TB
  subgraph UI["Presentation — app.py"]
    Form[Trip form]
    Tabs[Itinerary / Map / Travel tabs]
    FB[Feedback per stop]
    Hist[Trip history sidebar]
  end

  subgraph Core["Orchestration"]
    Agent[services/agent.py]
    Val[services/validation.py]
  end

  subgraph Tools["Agent tools & OSM"]
    POI[services/poi_search.py]
    RAG[services/wikivoyage_rag.py]
    Geo[services/geocoding.py]
  end

  subgraph Post["After itinerary — UI enrich"]
    Hints[services/travel_hints.py]
    Guide[services/destination_guide.py]
    Wx[services/weather.py]
    Photos[services/place_images.py]
    Map[services/map_viz.py]
  end

  subgraph External["Internet APIs"]
    Gemini[Google Gemini]
    NOM[Nominatim]
    OV[Overpass]
    WV[Wikivoyage]
    OM[Open-Meteo]
  end

  subgraph Disk["Files on disk"]
    State[(app_state.json)]
    Feed[(feedback.jsonl)]
  end

  Form --> Agent
  Agent --> Gemini
  Agent --> POI
  Agent --> RAG
  POI --> Geo --> NOM
  POI --> OV
  RAG --> WV
  POI --> Feed
  Agent --> Val
  Val --> Tabs
  Tabs --> Hints
  Tabs --> Guide
  Tabs --> Wx --> OM
  Tabs --> Photos
  Tabs --> Map
  UI --> State
  FB --> Feed
  Hist --> State
```

**Layers samjho:**

- **UI** — sirf dikhana, buttons, save session.
- **Agent** — Gemini + tools; yahi itinerary JSON banata/ update karta hai.
- **Post** — itinerary ke baad weather, photos, map (agent ke andar nahi, page render par).

---

## 4. Code map — kaunsi file kya karti hai

```
Travel_Planner/
├── app.py              ← Streamlit: form, buttons, tabs, persist
├── config.py           ← .env, paths, model name, boost scores
├── info.md             ← Yeh document
├── data/
│   ├── app_state.json  ← Last trip + forms + history
│   └── feedback.jsonl  ← Har 👍/👎 ek line
└── services/           ← Asli logic (neeche table)
```

### `app.py` — main functions (padhne ka order)

| Function | Kaam |
|----------|------|
| `main()` | Page setup, form, tabs, har run par `_persist()` |
| `_init_session()` | Pehli baar `app_state.json` → `st.session_state` |
| `_persist()` | Session → disk (history preserve) |
| `_run_generation(mode)` | Validate → `run_agent` → session update → history |
| `_render_itinerary()` | Days, feedback, nearby swap |
| `_render_route_map()` | PyDeck map |
| `_render_beginner_travel_guide()` | Travel tab content |

### `services/` — ek nazar mein

| File | Short role |
|------|------------|
| `agent.py` | Gemini + fast/tool paths, trace |
| `poi_search.py` | `search_pois` — Overpass + ranking + feedback |
| `geocoding.py` | City → lat/lon (Nominatim) |
| `validation.py` | Form + JSON + poi_id checks |
| `refine_itinerary.py` | Bina LLM chhote edits, add place |
| `feedback.py` | JSONL votes → boost map |
| `persistence.py` | Read/write `app_state.json` |
| `trip_history.py` | Sidebar saved trips |
| `travel_hints.py` | Airports, budget hotels, tips |
| `destination_guide.py` | City blurb, seasons |
| `weather.py` | Open-Meteo |
| `map_viz.py` | PyDeck route |
| `nearby_pois.py` | Paas ki jagah suggest |
| `place_images.py` | Stop/hint images |
| `wikivoyage_rag.py` | Optional guide chunks |
| `http_client.py` | HTTP + User-Agent |
| `retry_utils.py` | Gemini retries |
| `ui_components.py` / `ui_animations.py` / `trace_view.py` | UI helpers |

---

## 5. Streamlit app flow (`app.py`)

Har baar tum page refresh / button dabate ho, Streamlit **poora script dubara** chalata hai. Isliye state `st.session_state` + disk par rakhi hai.

```mermaid
flowchart TD
  Start([streamlit run app.py]) --> Main[main]
  Main --> Init[_init_session]
  Init -->|first time| LoadDisk[load app_state.json]
  Init --> Sidebar[Trip history sidebar]
  Main --> Form[Plan your trip form]
  Form --> Btn{Create my itinerary?}
  Btn -->|yes| Gen[_run_generation generate]
  Btn -->|no| HasItin{itinerary in session?}
  Gen --> HasItin
  HasItin -->|yes| Enrich[attach hints, guide, weather, photos]
  Enrich --> Tabs[Tab: Itinerary / Map / Travel]
  Tabs --> Single{Update this day?}
  Single -->|yes| DayGen[_run_generation single_day]
  DayGen --> Tabs
  HasItin -->|no| Trace[Agent trace expander]
  Tabs --> Trace
  Trace --> Persist[_persist → app_state.json]
  Persist --> End([Wait for next user action])
```

**Important design choice:** Itinerary + map **button ke bahar** render hote hain — warna map filter change par poora plan gayab ho sakta tha (capstone requirement).

### Session vs disk

```mermaid
flowchart LR
  Browser[Browser session] <-->|every rerun| SS[st.session_state]
  SS <-->|_init_session / _persist| JSON[(app_state.json)]
  FB[(feedback.jsonl)] -->|read on POI search| POI[search_pois]
  UI[👍 button] -->|append line| FB
```

---

## 6. Agent flow — itinerary kaise banti hai

Entry: `services/agent.py` → `run_agent(...)`.

### 6.1 Decision tree — kaunsa path chalega?

```mermaid
flowchart TD
  RA[run_agent called] --> Mode{mode?}
  Mode -->|refine or single_day| FR[_run_fast_refine]
  Mode -->|generate| Fast{fast_mode?}
  Fast -->|yes| FG[_run_fast_generate]
  FG --> OK{success?}
  OK -->|yes| Done([AgentResult ok])
  OK -->|hard OSM fail| Fail([return error])
  OK -->|soft fail JSON etc| TL[Tool loop fallback]
  Fast -->|no| TL
  TL --> Loop[Gemini + function calls]
  Loop --> Done
  FR --> Done
```

| Mode | UI se kaise trigger |
|------|---------------------|
| `generate` | **Create my itinerary** |
| `single_day` | **Update this day** + text |
| `refine` | Code support hai; full-trip refine UI optional |

Default: **`fast_mode=True`** (`app.py` → `_agent_settings()`).

### 6.2 Fast generate (default path) — step flowchart

```mermaid
flowchart TD
  A[Start fast generate] --> B[search_pois once]
  B --> C{POI ok?}
  C -->|no| E[Error: geocode/Overpass]
  C -->|yes| D[Build compact POI catalog JSON]
  D --> F[Gemini: single generate_content]
  F --> G[Model returns text]
  G --> H[extract_json + validate structure]
  H --> I{Every poi_id in catalog?}
  I -->|no| J[Retry once: ask fix JSON]
  J --> F
  I -->|yes| K[enrich_itinerary_from_pois]
  K --> L[attach_travel_hints]
  L --> M[Return itinerary + tool_state + trace]
```

**Gemini ko kya milta hai:** trip days, pace, interests, constraints, aur **sirf allowed POI list** (id + name + category).

**Gemini kya deta hai:** ek JSON object — `days[]` with `morning` / `afternoon` / `evening` arrays.

### 6.3 Tool loop (fallback) — flowchart

Jab fast path fail ho (JSON/tools) ya fast mode off ho:

```mermaid
flowchart TD
  T0[Tool loop start] --> T1[Gemini with tools:
search_pois, retrieve_guides]
  T1 --> T2{Response type?}
  T2 -->|function_call| T3[Run tool locally]
  T3 --> T4[Merge into tool_state.pois / chunks]
  T4 --> T5[Send function_response back to Gemini]
  T5 --> T1
  T2 -->|text JSON| T6[_finalize_itinerary]
  T6 --> T7{Valid?}
  T7 -->|no| T8[Retry prompt with error]
  T8 --> T1
  T7 -->|yes| T9[Done]
  T1 --> Max{max steps?}
  Max -->|exceeded| Err[Error: no final itinerary]
```

Tools declare: `agent.py` → `_gemini_tools()`.

### 6.4 Sequence diagram — generate button

```mermaid
sequenceDiagram
  participant U as User
  participant App as app.py
  participant Val as validation
  participant Ag as agent.run_agent
  participant POI as search_pois
  participant GM as Gemini

  U->>App: Create my itinerary
  App->>Val: validate_trip_inputs + API keys
  App->>Ag: mode=generate, fast_mode=True
  Ag->>POI: geocode + Overpass + rank
  POI-->>Ag: pois, city_meta
  Ag->>GM: catalog + trip rules
  GM-->>Ag: itinerary JSON text
  Ag->>Val: parse + poi_id check + enrich
  Ag-->>App: AgentResult
  App->>App: trip_history + _persist
  App->>U: Tabs + trace
```

### 6.5 Fast refine / single day — flowchart

```mermaid
flowchart TD
  R[User request text] --> S[Seed POIs from old itinerary]
  S --> Surg{Surgical add possible?}
  Surg -->|yes| Out[New itinerary without LLM]
  Surg -->|no| P1[Broad search_pois]
  P1 --> P2[Targeted search_pois + query phrase]
  P2 --> G[Geocode named places into catalog]
  G --> Surg2{Surgical again?}
  Surg2 -->|yes| Out
  Surg2 -->|no| LLM[Gemini: full itinerary + minimal change rules]
  LLM --> V[Validate + ensure something changed]
  V --> SD{single_day mode?}
  SD -->|yes| Check[verify_single_day_unchanged in app.py]
  SD -->|no| Out
  Check --> Out
  Out --> Done[Save session]
```

---

## 7. POI search flow (OpenStreetMap)

`search_pois(city, interests, user_agent, limit, query_text?, fast?)`

```mermaid
flowchart TD
  Start[search_pois] --> Geo[geocode_city → Nominatim]
  Geo --> BB[Bounding box around city]
  BB --> Int[normalize_interests]
  Int --> Tags[INTEREST_TO_TAGS → Overpass regex filters]
  Tags --> Q1[Build Overpass QL query]
  Q1 --> OV[POST Overpass API]
  OV --> LM[Optional landmarks query]
  LM --> Parse[Parse elements → poi_id, name, lat, lon]
  Parse --> Score[_base_score + feedback boosts]
  Score --> Rank[Sort, apply limit]
  Rank --> Filter{query_text set?}
  Filter -->|yes| NameMatch[Filter/rank by name match]
  Filter -->|no| Ret[Return pois dict + city_meta]
  NameMatch --> Ret
```

**Interest examples (UI text → OSM):**

| User interest | OSM idea |
|---------------|----------|
| museums | `tourism=museum|gallery` |
| food | `amenity=restaurant|cafe|…` |
| outdoors | parks, beaches, peaks |
| history | `historic`, attractions |

Agar kuch match na ho → default mix: museums, food, outdoors.

**poi_id format:** `osm_node_123`, `osm_way_456`, … (validation isi se match karti hai).

```mermaid
flowchart LR
  I[Interests] --> N[normalize]
  G[Geocode] --> B[Bbox]
  N --> O[Overpass]
  B --> O
  F[feedback.jsonl] --> S[Score]
  O --> S
  S --> C[tool_state.pois]
```

---

## 8. Validation flow

Do jagah validation:

**A) Form (button se pehle)** — `validate_trip_inputs`

```mermaid
flowchart TD
  V[validate_trip_inputs] --> D{destination non-empty?}
  D -->|no| E1[Error]
  D -->|yes| Days{1 ≤ days ≤ 14?}
  Days -->|no| E2[Error]
  Days -->|yes| P{pace valid?}
  P -->|no| E3[Error]
  P -->|yes| I{interests non-empty?}
  I -->|no| E4[Error]
  I -->|yes| OK[Proceed to agent]
```

**B) Model output (agent ke baad)** — `_finalize_itinerary`

```mermaid
flowchart TD
  Raw[Model text] --> EX[extract_json strip markdown]
  EX --> ST[validate_itinerary_structure days/blocks]
  ST --> ID[validate_itinerary_poi_ids ⊆ tool_state.pois]
  ID --> EN[enrich_itinerary_from_pois lat/lon/url]
  EN --> OK[Valid itinerary]
  EX -->|fail| ERR[ValueError → retry or show error]
  ST --> ERR
  ID --> ERR
```

---

## 9. Single-day update & nearby swap

### Single day (AI)

User: day number + “What should change?” → `_run_generation("single_day", ...)`.

Same refine pipeline; **extra guard:** baaki din byte-for-byte same hone chahiye (`verify_single_day_unchanged`).

### Nearby swap (no AI)

```mermaid
flowchart TD
  Stop[User on one itinerary stop] --> Near[nearby_pois within ~4.5 km]
  Near --> List[Show scroll cards]
  List --> Use[User clicks Use · Place]
  Use --> Swap[_apply_stop_swap]
  Swap --> Cat[Copy POI from catalog into that slot]
  Cat --> Persist[_persist]
```

Yahan Gemini call **nahi** hoti — sirf catalog se ek entry replace hoti hai.

---

## 10. Feedback loop

```mermaid
flowchart TD
  U[User 👍 or 👎 on a stop] --> A[append_feedback]
  A --> J[One JSON line in feedback.jsonl]
  J --> X[Current itinerary unchanged]
  N[Next trip / search_pois for same city_key]
  N --> R[Read all events for city]
  R --> B[Sum boosts per poi_id]
  B --> S[Re-rank POI list before Gemini sees it]
```

| Vote | Score change (per event) |
|------|---------------------------|
| 👍 up | +0.25 |
| 👎 down | −0.35 |

Scoped by **`city_key`** from geocode metadata — same POI id do cities mein alag count hota hai.

---

## 11. Travel tab extras

Itinerary banne ke **baad**, har page render par (cache keys se optimize):

```mermaid
flowchart TD
  Has[Itinerary exists] --> H[attach_travel_hints airports hotels]
  Has --> G[attach_destination_guide blurb seasons]
  Has --> W[attach_weather Open-Meteo]
  Has --> P[enrich photos for stops + hints]
  H --> Tab[Travel & stays tab]
  G --> Tab
  W --> Tab
  P --> Tab
```

| Cache key in tool_state | Kab refresh |
|-------------------------|-------------|
| `_hints_key` | `origin|dest` change |
| `_photos_key` | hints key change |
| `_guide_key` | destination change |
| `_weather_key` | `dest|trip_days` change |

**Map tab** alag: `map_viz.build_deck` — green start, purple dest, pink airport, orange visit path.

---

## 12. Optional Wikivoyage RAG

Off by default (`ENABLE_WIKIVOYAGE_RAG` in `.env`). Fast agent mode mein RAG band.

```mermaid
flowchart TD
  En{ENABLE_WIKIVOYAGE_RAG?} -->|no| Skip[retrieve_guides returns empty]
  En -->|yes| GM[Gemini calls retrieve_guides in tool loop]
  GM --> API[Wikivoyage MediaWiki API]
  API --> HTML[Strip HTML]
  HTML --> CH[Chunks 800-1000 chars]
  CH --> TF[TfidfVectorizer + cosine sim]
  TF --> Top[Top K chunks → tool_state.chunks]
  Top --> GM2[Gemini uses text in next turn]
```

---

## 13. Data files & memory

### `app_state.json` — kya store hota hai

| Key | Meaning |
|-----|---------|
| `itinerary` | Current plan JSON |
| `tool_state` | POI catalog + hints + weather + cache keys |
| `agent_trace` | Debug timeline of last agent run |
| `form_destination`, `form_origin`, … | Form defaults |
| `trip_history[]` | Past trips snapshots |

### `tool_state` — planner + UI ke liye

| Key | Meaning |
|-----|---------|
| `pois` | All known places by id |
| `city_meta` | Includes `city_key` for feedback |
| `travel_hints`, `destination_guide`, `weather` | Travel tab |
| `chunks` | Wikivoyage RAG (if any) |

### User journey on disk

```mermaid
flowchart TD
  A[Open app] --> B[Load app_state.json]
  B --> C[Fill trip form]
  C --> D[Create my itinerary]
  D --> E[Gemini + OSM]
  E --> G[Save itinerary + append trip_history]
  G --> H[UI + map]
  H --> I[Feedback → feedback.jsonl]
  I --> J[Next search uses boosts]
  B --> K[Sidebar: restore old trip]
```

---

## 14. Itinerary JSON shape

```json
{
  "destination": "Goa",
  "days": [
    {
      "day": 1,
      "morning": [
        {
          "poi_id": "osm_node_12345",
          "name": "Place name",
          "why": "One short sentence in English"
        }
      ],
      "afternoon": [],
      "evening": []
    }
  ]
}
```

Har din mein **teen blocks** fixed hain: `morning`, `afternoon`, `evening` (khaali list allowed).

Enrichment ke baad: `lat`, `lon`, `category`, `url`, kabhi `image_url`.

---

## 15. Config & APIs

### Setup

1. `python -m venv trip-planner-env` → activate → `pip install -r requirements.txt`
2. Copy `.env.example` → `.env`
3. `streamlit run app.py`

### Environment

| Variable | Required | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | Yes | Gemini |
| `OSM_CONTACT_EMAIL` | Yes | OSM User-Agent (policy) |
| `ENABLE_WIKIVOYAGE_RAG` | No | `true` = RAG in tool loop |

### External services

| Service | Key? | Use |
|---------|------|-----|
| Google Gemini | Yes | Itinerary JSON |
| Nominatim / Overpass | No (email) | Geocode + POIs |
| Wikivoyage | No | Optional RAG |
| Open-Meteo | No | Weather |

### Important `config.py` numbers

| Setting | Value |
|---------|--------|
| `DEFAULT_MODEL` | `gemini-3.5-flash-lite` (+ fallbacks) |
| `FAST_POI_LIMIT` | 45 |
| `UPVOTE_BOOST` / `DOWNVOTE_BOOST` | 0.25 / −0.35 |

---

## 16. Errors & retries

```mermaid
flowchart TD
  E[Something fails] --> T{Type?}
  T -->|Gemini 429/5xx| R[call_with_retries]
  T -->|Wrong model id| M[MODEL_FALLBACKS chain]
  T -->|Bad JSON| P[Re-prompt model with error text]
  T -->|Invalid poi_id| P
  T -->|OSM hard fail| H[Show error, no fallback]
  T -->|single_day changed other days| V[verify_single_day_unchanged error]
```

User ko **`st.error(last_error)`** dikhta hai; kabhi **Export & advanced** mein raw model output.

**Agent trace** (page ke neeche expander): har step — tool name, ms, detail — debugging ke liye.

---

## 17. Glossary

| Term | Matlab |
|------|--------|
| **POI** | Point of interest — museum, restaurant, park, … |
| **poi_id** | OSM-based stable id string in catalog |
| **tool_state** | Agent + UI shared memory (especially `pois`) |
| **Fast mode** | Kam steps: direct OSM + 1 Gemini call (default) |
| **Tool loop** | Gemini khud `search_pois` / `retrieve_guides` call karta hai |
| **RAG** | Retrieval: Wikivoyage text chunks model ko extra context |
| **city_key** | Feedback scope — usually normalized city name |
| **Surgical refine** | Chhota code-only edit, LLM ke bina |
| **Session rerun** | Streamlit har interaction par script dubara chalata hai |

---

## Credits

OpenStreetMap contributors, Wikivoyage, Google Gemini API, Open-Meteo.

---

## Document updates

| When | What |
|------|------|
| Initial | Full architecture + flowcharts + Hindi/English guide tone |

*Naye features aane par is file ke relevant section + flowchart update karna.*
