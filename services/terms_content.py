"""Terms, policies, and disclaimers for the demo customer portal."""

from services.travel_packages import build_travel_package_catalog_markdown

TERMS_INTRO = """
> **Demo disclaimer:** This application is a **capstone / prototype** for education. It simulates
> trip planning, a **grounded RAG policy assistant**, package booking, refunds, and support.
> It is **not** a licensed travel agency, payment processor, or legal advisor. **No real money**
> is charged or refunded. Always rely on real operator contracts for actual travel purchases.

**Last updated (demo):** Illustrative policy text for academic demonstration.

Read the **Overview**, **Document Assistant**, **Packages & tiers**, and **Bookings & legal** tabs
on this page (or in **Document Assistant → Terms & Conditions**). The chatbot retrieves from this text.
"""

# Section title groups — used for tabbed Terms UI (see services/terms_page_ui.py).
TERMS_PLATFORM_SECTION_TITLES = (
    "Application overview & purpose",
    "Core features & capabilities",
    "Why choose this platform",
    "Accessing terms & product navigation",
)

TERMS_PACKAGES_SECTION_TITLES = (
    "Service tiers & subscription models (demo)",
    "Travel package catalog & fare types (demo)",
    "Packages & booking options on the platform",
)

RAG_ASSISTANT_SECTION_TITLES = (
    "Document assistant — acceptable use",
    "Chatting, queries & source snippets",
    "URL input & scraped website data",
    "API keys & automated processing",
)

RAG_CHAT_TOC = (
    TERMS_PLATFORM_SECTION_TITLES
    + TERMS_PACKAGES_SECTION_TITLES
    + RAG_ASSISTANT_SECTION_TITLES
)

RAG_CHAT_TERMS_INTRO = """
### Document & Policy Assistant — user notice

The **Document & Policy Assistant** is a retrieval-augmented (RAG) chat experience inside this app.
It answers from the **Terms & Conditions** knowledge base (and your demo portal data when relevant).
By signing up and using **Chat**, you agree to the sections below in addition to the full platform terms.
"""

TRAVEL_PACKAGE_CATALOG_MARKDOWN = build_travel_package_catalog_markdown()

RAG_CHAT_TERMS_SECTIONS = [
    (
        "Application overview & purpose",
        """
**Trip Planner AI Agent** is an integrated Streamlit platform that combines:

1. **AI trip planning** — Multi-day itineraries grounded in **OpenStreetMap** points of interest (Gemini agent).
2. **Customer portal (demo)** — Bookings, travel packages, refunds, account status, and support tickets.
3. **Document & Policy Assistant** — A **retrieval-augmented generation (RAG)** chatbot over these Terms,
   policies, and (when relevant) your demo account data.

**Purpose:** Help learners and demo users experience **transparent, tool-grounded AI** for travel planning
and **policy Q&A** without replacing real-world operators, lawyers, or payment systems.

This software is provided **as-is** for demonstration, coursework, and UX prototyping.
        """,
    ),
    (
        "Core features & capabilities",
        """
| Capability | What you get |
|------------|----------------|
| **Website / document RAG chat** | Ask questions in natural language; answers use **semantic search** over indexed policy text, then (when configured) an LLM bound to retrieved chunks. |
| **Transparent sources** | Each assistant reply can show a **Sources** expander with exact retrieved snippets and relevance scores. |
| **Instant document querying** | No manual PDF hunting — ask about refunds, packages, accounts, or assistant rules in one chat thread. |
| **URL scrape test (optional)** | Validate that a public page can be fetched and chunked (demo pipeline); primary Q&A still uses in-app Terms. |
| **Signup-gated chat** | **Document Assistant** requires a lightweight local account before chat (session + optional JSON store). |
| **Trip Planner** | Generate, refine, map, and export itineraries; optional Wikivoyage RAG for guides. |
| **Book package** | Convert trips or catalog templates into demo **BK-PKG** bookings with live price estimates. |
| **Refund Assistant** | Rule-engine eligibility plus explanatory chat per booking. |
| **Help & Support** | FAQs, policy bot, and simulated tickets. |
| **Admin demo** | Back-office queues for refunds, tickets, and accounts (not production security). |

**Seamless interaction:** Sidebar navigation, tabbed Terms, two-column chat + tools on Document Assistant,
and consistent pastel UI — without changing underlying Python logic or RAG pipelines.
        """,
    ),
    (
        "Why choose this platform",
        """
Compared with generic chatbots, static FAQ pages, or unstructured document upload tools, this app emphasizes:

- **Grounded context retrieval** — Answers are driven by **`similarity_search`** over your Terms knowledge base,
  not free-form guessing. The model is instructed to admit when text is **not in the document**.
- **Higher transparency** — Users can **verify** replies via **Sources**, improving trust and auditability.
- **Unified travel + policy UX** — Plan trips, book demo packages, check refunds, and ask policy questions in one product shell.
- **Modern, accessible UI** — Clean light/pastel layout, card-based chat, pill CTAs, and clear navigation (Overview / RAG / Packages / Legal tabs).
- **Fast iteration** — Cached embeddings and vector indices (`@st.cache_resource`) reduce repeat latency during a session.
- **Extensible demo architecture** — Clear separation of UI, `terms_rag` / `website_rag`, rule engine, and portal state for teaching and portfolios.

**Not a claim of commercial superiority** — in production you would add formal SLAs, compliance, billing, and human review.
This prototype highlights **design patterns** for accurate, user-visible RAG in a travel context.
        """,
    ),
    (
        "Accessing terms & product navigation",
        """
You can read these Terms **without blocking** signup or chat:

| Location | How to open |
|----------|-------------|
| **Terms & Policies** | Sidebar → **Terms & Policies** → use the four tabs (Overview, RAG, Packages, Legal). |
| **Document Assistant** | Sidebar → **Document Assistant** → **Terms & Conditions** (same tabbed content). |
| **Before signup** | Document Assistant → **Sign up / Sign in** — checkbox links you to Terms; chat unlocks after acceptance + login. |
| **Support** | **Help & Support** → FAQ + bot (bot uses the same indexed Terms text). |

**Flow preserved:** Reading Terms does not reset chat session state. Switching sidebar pages does not delete
**Document Assistant** login. Demo portal user (sidebar profile) remains separate from assistant email identity.

For the shortest path to policy Q&A: **Document Assistant → Sign in → Chat**.
        """,
    ),
    (
        "Service tiers & subscription models (demo)",
        """
This repository **does not bill users**. The tiers below describe a **placeholder** commercial model
for documentation and UI copy. **Enforcement is off** unless you implement it in a fork.

### Explorer (Free — placeholder)

- **Audience:** Individual learners, try-before-upgrade.
- **Document Assistant:** Up to **25** grounded chat queries per day (placeholder).
- **URL indexes:** **1** active scraped URL test index (placeholder).
- **Trip Planner:** Up to **3** full itinerary generations per day (placeholder).
- **Support:** FAQ + bot; **no** priority queue.
- **Benefits:** Full transparency (Sources), standard latency, community/demo data only.

### Voyager Plus (placeholder)

- **Audience:** Frequent planners and power users.
- **Queries:** **200** assistant queries / day; **5** URL indexes; **15** itinerary runs / day.
- **Benefits:** Priority embedding cache warm-up (placeholder), saved chat export (placeholder),
  email digest of policy changes (placeholder).

### Team & Agency (placeholder)

- **Audience:** Small teams, classrooms, or demo agencies.
- **Queries:** **1,000** assistant queries / day; **25** URL indexes; **50** itinerary runs / day.
- **Seats:** Up to **10** registered assistant users (placeholder).
- **Benefits:** Shared Terms index versioning (placeholder), admin audit log export (placeholder),
  dedicated support SLA (placeholder).

**Current demo build:** All tiers behave as **unlimited** locally, limited only by your **Gemini API** quota and machine resources.
        """,
    ),
    (
        "Travel package catalog & fare types (demo)",
        TRAVEL_PACKAGE_CATALOG_MARKDOWN,
    ),
    (
        "Document assistant — acceptable use",
        """
You may use the assistant to:

- Ask questions about **terms, refunds, packages, bookings, accounts, and support** in this demo app.
- Review **grounded answers** that cite retrieved policy text (see **Sources** under each reply).
- Optionally **test a public URL** (Help & Support or Document Assistant) to verify that a page can be scraped and chunked.

You must **not**:

- Submit unlawful, harassing, or harmful content in chat.
- Attempt to scrape sites you do not have permission to access, or bypass robots.txt / rate limits.
- Treat assistant output as legal, financial, or travel advice for real-world purchases.
- Enter real payment cards, government IDs, or production API secrets into chat or URL fields.
        """,
    ),
    (
        "Chatting, queries & source snippets",
        """
**Chat** sends your message to a **semantic search** step over indexed policy text, then (when configured) to an **AI model** with instructions to stay within retrieved context.

- **Source snippets** in the **Sources** expander show the exact chunks used — read them to verify answers.
- If the model cannot answer from retrieved text, it should state that the information is **not in the document**.
- Chat history for registered users is kept in **Streamlit session state** for your current browser session; it is not a permanent support ticket.
- Switching demo portal users (sidebar profile) does not replace your **Document Assistant** login — those are separate identities.
        """,
    ),
    (
        "URL input & scraped website data",
        """
The optional **URL** tool loads public web pages via HTTP, strips HTML, and splits text into chunks for indexing demos.

- Only use URLs you are allowed to fetch (your own site, public documentation, or coursework examples).
- Scraped content is processed **on the machine running Streamlit**; it is **not** uploaded to a third-party storage service by this demo.
- We do not guarantee completeness, accuracy, or freshness of scraped text; layouts and paywalls may block content.
- **Policy Q&A** in production paths still defaults to the in-app **Terms & Policies** index unless a future feature explicitly queries your URL index.
- Cached embeddings may persist for the app process lifetime via Streamlit resource caches.
        """,
    ),
    (
        "API keys & automated processing",
        """
**Gemini API key (`GEMINI_API_KEY`)**

- Configured in **`.env`** on the server (or Streamlit secrets in deployment) — **not** entered in the chat UI.
- Used for **text embeddings** (semantic search) and **grounded answer generation** when available.
- If the key is missing, search may be unavailable and answers may fall back to retrieved excerpts only.

**OpenStreetMap / Wikivoyage**

- Trip Planner uses a **User-Agent** with **`OSM_CONTACT_EMAIL`** from `.env` for geocoding and POI data.
- Optional Wikivoyage RAG (`ENABLE_WIKIVOYAGE_RAG`) fetches travel articles when enabled.

You are responsible for **key security** on your deployment: never commit `.env`, rotate keys if exposed, and set provider usage limits.
        """,
    ),
    (
        "Packages & booking options on the platform",
        """
**Commerce-style flows (simulated):**

1. **Book package** — *My Bookings & Refunds* → choose catalog or Trip Planner prefill → travelers, nights, Standard/Flex → **Confirm** creates `BK-PKG-*`.
2. **Catalog tickets** — Pre-seeded bookings per demo user for refund and status demos.
3. **Refund Assistant** — Select booking + reason → rule engine → chat explains the same outcome.
4. **Support tickets** — Categories (Refund, Booking, Cancellation, Account, Technical, Other).

**Chat alignment:** The RAG assistant should cite these Terms when answering package or refund questions.
If retrieval confidence is low, the bot may suggest opening **Terms & Policies** or a support ticket.
        """,
    ),
]

TERMS_TABLE_OF_CONTENTS = [
    "Application overview & purpose",
    "Core features & capabilities",
    "Why choose this platform",
    "Service tiers & subscription models (demo)",
    "Travel package catalog & fare types (demo)",
    "General Terms & Conditions",
    "Trip Planner (AI itineraries)",
    "Demo user accounts",
    "Bookings & travel packages",
    "Package pricing & confirmation (demo)",
    "Cancellation Policy",
    "Refund Eligibility Policy",
    "Refund reasons & Refund Assistant",
    "Refund Processing Procedure",
    "Cancellation charges & amounts",
    "Non-refundable bookings",
    "Refund request time limits",
    "Duplicate booking & misuse",
    "Account status, restrictions & appeals",
    "Customer support & tickets",
    "Admin demo mode (back-office)",
    "Privacy & stored data",
    "Changes to policies",
]

TERMS_SECTIONS = [
    (
        "Travel package catalog & fare types (demo)",
        TRAVEL_PACKAGE_CATALOG_MARKDOWN,
    ),
    (
        "General Terms & Conditions",
        """
By using this application you acknowledge that:

- All **bookings**, **package purchases**, **refunds**, **support tickets**, and **account actions** are **simulated** for education and testing.
- **Trip Planner** features (maps, itineraries, AI agent) are **planning tools** unless you separately create a **demo booking** in the customer portal.
- You will not rely on this app for real travel, legal, or financial decisions.
- Continued use means you accept these demo terms and the policies in the following sections.
        """,
    ),
    (
        "Trip Planner (AI itineraries)",
        """
**Trip Planner** generates day-by-day itineraries using OpenStreetMap data and an AI agent (Gemini).

- Itineraries are **suggestions only** — not confirmed reservations for flights, hotels, trains, or activities.
- Places, times, and tips may be incomplete or outdated; verify before real travel.
- **Trip history** in the sidebar saves plans locally for your session/demo — it is not a booking record.
- The button **Book as travel package (demo)** only **prefills** the package booking form on *My Bookings & Refunds*; it does not charge you or issue a ticket until you confirm a package booking there.
        """,
    ),
    (
        "Demo user accounts",
        """
The customer portal uses **prototype login** (no real authentication).

- Choose a **demo account** from the profile control at the **bottom of the sidebar** (hover to see other accounts; click to switch).
- Each demo user has separate **bookings**, **refunds**, **tickets**, and **chat history** in this prototype.
- Account status (Active, Under Review, Temporarily Restricted, Blacklisted) affects **refund eligibility** per the rule engine — see Account status below.
- Do not enter real passwords, payment cards, or government ID numbers.
        """,
    ),
    (
        "Bookings & travel packages",
        """
**My Bookings & Refunds** shows two kinds of demo records:

1. **Catalog bookings** — pre-loaded mock flights, trains, and buses (e.g. `BK-FLT-1001`) from demo data.
2. **Travel packages you book** — created when you confirm a package on the **Book package** tab. These receive IDs like `BK-PKG-…` and are stored in your local portal state file.

**Travel packages (demo)** may include bundled items such as flights, hotels, trains, buses, tours, or transfers depending on the package template. Package names and inclusions are shown at booking time.

- Package bookings use **travel mode `package`** and a **Flex** or **Standard** fare policy (see Cancellation and Refund sections).
- Submitting a **refund request** for any booking follows the same eligibility engine as tickets; package policies apply to package bookings.
- Switching demo users does not merge bookings — each account sees only its own records.
        """,
    ),
    (
        "Package pricing & confirmation (demo)",
        """
On **Book package**, the **estimated price** updates when you change package, travelers, nights, or fare type. This is **illustrative math only**:

- **Base** = package base price per person × number of travelers.
- **Fare type:** **Standard** uses the base rate; **Flex** applies a higher demo multiplier (easier refund terms — see policies `package_standard` and `package_flex`).
- **Extra nights:** For nights beyond **2**, a demo add-on of **₹1,200 × extra nights × travelers** is added to the estimate.
- **Confirm package booking** creates a **confirmed** demo record with the shown total — **no payment gateway** is used.
- The final amount stored on the booking is the estimate at confirmation time; it is not a contract with any real operator.
        """,
    ),
    (
        "Cancellation Policy",
        """
Cancellation windows depend on **travel mode**, **ticket type**, or **package fare**. You must cancel (request a refund) **before** the minimum hours shown for that policy **before scheduled departure/journey start** (demo clock).

**Flights**

- **Flex:** cancel **24+ hours** before departure (demo).
- **Saver:** cancel **72+ hours** before; partial refund with higher fees.
- **Basic / promo:** **non-refundable** in this demo.

**Trains**

- **AC 3-tier:** **48+ hours**; partial refund.
- **Sleeper:** **24+ hours**; partial refund with higher fee.

**Bus**

- **Semi-sleeper:** **12+ hours**; partial refund.
- **Volvo AC:** **6+ hours**; refundable with moderate fee.

**Travel packages (demo)**

- **Standard (`package_standard`):** cancel **120+ hours** (5 days) before departure; **partial** refund; higher cancellation fee.
- **Flex (`package_flex`):** cancel **72+ hours** before departure; **full** refundability subject to service fee in the demo engine.

See the **policy comparison table** on this page for refundability labels and minimum hours.
        """,
    ),
    (
        "Refund Eligibility Policy",
        """
The **rule engine** (not the chat UI) decides eligibility. Automatic outcomes require **all** of the following unless a rule sends the case to manual review:

- Booking belongs to the **signed-in demo user**.
- Booking status is eligible (e.g. **confirmed**; not already **completed**, **refunded**, or invalid).
- A **valid refund policy** exists for the booking (`policy_id`).
- Current time is **before** the policy’s **minimum hours before departure** deadline.
- **No existing refund request** for the same booking.
- Account is not blocked in a way that forces **Manual Review Required** (e.g. blacklisted accounts).

**Outcomes:** **Eligible**, **Partially Eligible**, **Not Eligible**, or **Manual Review Required**.

Amounts shown (**original**, **cancellation fee**, **estimated refund**) are calculated from demo policy rates — not from a live operator.
        """,
    ),
    (
        "Refund reasons & Refund Assistant",
        """
When submitting a refund or using **Refund Assistant**, you may select a **reason** (demo):

- Cancellation of travel  
- Change of plans  
- Duplicate booking  
- Operator cancelled service  
- Other reason  

Some reasons (e.g. duplicate booking) or account flags can force **Manual Review Required** even when fare rules would otherwise allow a refund.

**Refund Assistant**

- Runs the **same rule engine** as *My Bookings & Refunds* when you click **Run policy eligibility check**.
- Shows the **policy** applied to the booking; results are valid only for the **selected booking and reason** — change either and run the check again.
- The chat **cannot override** eligibility; it explains policy-based results.
        """,
    ),
    (
        "Refund Processing Procedure",
        """
1. Open **My Bookings & Refunds** → select a booking → choose **refund reason** → **Check eligibility & submit** (user mode).
2. System validates **ownership**, **booking state**, **policy**, **timing**, **duplicates**, and **account status**.
3. If allowed, a **refund request** is created with a tracking ID (e.g. `RR-…`) and workflow status.
4. **Demo workflow statuses:** Submitted → Under Review → Approved or Rejected → Refund Processing (Demo) → Completed (Demo). No bank transfer occurs.
5. **Admin demo mode** can advance or reject requests on the **Admin dashboard** — see Admin demo mode below.
        """,
    ),
    (
        "Cancellation charges & amounts",
        """
Cancellation **fees** are a **percentage of the demo booked amount**, set per policy, for example:

- Flight flex: ~5% fee; flight saver: ~35% fee with capped refundable fraction.
- Package flex: ~8% fee; package standard: ~25% fee with ~70% max refundable fraction after fee (demo).
- Non-refundable fares: fee may equal the full amount with **₹0** estimated refund.

**Partially eligible** fares refund only a **fraction** of the amount remaining after the fee. The app displays **Original**, **Cancellation fee**, and **Est. refund (demo)** before you submit.
        """,
    ),
    (
        "Non-refundable bookings",
        """
Example: **BK-FLT-1102** (basic international promo fare) uses policy **`flight_basic`** with refundability **none**.

Promotional and basic fares are common non-refundable examples in real life; here they are **simulated**. Package **Standard** may still allow **partial** refunds if you meet the time window — **Flex** package fare has more generous demo rules than Standard.
        """,
    ),
    (
        "Refund request time limits",
        """
Refund requests must be submitted **before** the configured **hours-before-departure** threshold for that ticket or package.

Late requests are **Not Eligible** with an explanation (e.g. bus booking inside the 12-hour window for semi-sleeper). The **cancellation deadline (demo)** shown on a booking is derived from journey time minus policy minimum hours.
        """,
    ),
    (
        "Duplicate booking & misuse",
        """
- Only **one refund request per booking** is allowed in the demo.
- **Duplicate booking** as a reason may trigger **manual review**.
- Repeated misuse in the demo narrative may lead to **Under Review**, **Temporary Restriction**, or **Blacklisted** status with **documented reasons** — a **single rejected refund does not** automatically blacklist an account.
        """,
    ),
    (
        "Account status, restrictions & appeals",
        """
**Statuses:** **Active**, **Under Review**, **Temporarily Restricted**, **Blacklisted** (demo labels).

- Restrictions may list **codes**, **summaries**, **dates**, and **booking references** on **Account Status**.
- You may **submit an appeal** with a message; appeals enter a demo review queue.
- **Admin** can approve or deny appeals and change account status in the admin console (simulation only).

Restricted accounts may receive **Manual Review Required** on refunds until resolved in the demo.
        """,
    ),
    (
        "Customer support & tickets",
        """
**Help & Customer Support** provides FAQs, a **policy-aware bot**, and **support tickets** (demo).

- Create tickets with categories such as Refund Issue, Booking Issue, Cancellation, Account Restriction, Technical Problem.
- **Customers** can add messages and request escalation; **customers cannot change ticket status**.
- **Only admin demo mode** can set ticket status (Open, In Progress, Awaiting User Response, Approved, Resolved, Closed) and send **Support** replies visible on your ticket thread.
- The bot may suggest opening a ticket when it cannot answer confidently.
        """,
    ),
    (
        "Admin demo mode (back-office)",
        """
The sidebar **Demo dashboard** switch (**User** / **Admin**) is for **class demonstrations only**:

- **Admin** shows queues for refunds, tickets, appeals, and account overrides.
- Admin actions update **local demo JSON state**; there is **no real security** (e.g. passphrase `demo_admin` on the admin page).
- In **Admin** mode, use **customer preview** on portal pages to view a selected demo user’s data; submit refunds as a customer only in **User** mode.
- Admin does **not** represent a production operations environment.
        """,
    ),
    (
        "Privacy & stored data",
        """
- Demo profiles use **fictional names and emails**.
- Portal activity (refunds, tickets, appeals, **user-created package bookings**, audit log) may be stored in **`data/customer_portal_state.json`** on the machine running the app.
- Trip plans may be stored in **`data/app_state.json`** and trip history caches.
- **Do not** enter real payment card numbers, bank details, or government IDs.
- This prototype is not a privacy-compliant production system; do not use with real personal data.
        """,
    ),
    (
        "Changes to policies",
        """
Policies, package catalog, and demo data may be updated for coursework or demonstration.

- The **policy comparison table** on this page reflects configured demo rules at runtime.
- Continued use after changes constitutes acceptance of the updated **demo** terms.
- **Real operator terms** always govern actual purchases made outside this application.
        """,
    ),
]

FAQ_ITEMS = [
    {
        "q": "Are refunds real in this app?",
        "a": "No. This is an academic demo. Amounts and statuses are simulated; no payment gateway is connected.",
    },
    {
        "q": "How is refund eligibility decided?",
        "a": "A rule-based engine checks booking status, departure time, ticket policy, duplicate requests, and account flags. The Refund Assistant explains the result but cannot override the rules.",
    },
    {
        "q": "Why was my refund partially approved?",
        "a": "Saver fares, trains, and buses often have higher cancellation fees than flex air fares. See Terms & Policies for examples by travel mode.",
    },
    {
        "q": "Can a rejected refund blacklist my account?",
        "a": "No. A single rejection does not blacklist you. Restrictions are shown only for documented demo scenarios (e.g. repeated duplicate claims).",
    },
    {
        "q": "How do I appeal an account restriction?",
        "a": "Open Account Status, review the reason, and submit an appeal. You can also open a support ticket under Account Restriction.",
    },
    {
        "q": "How long do demo refunds take?",
        "a": "Processing times are illustrative (typically 2–14 business days depending on mode). Status updates are simulated in the app.",
    },
    {
        "q": "How do travel package bookings work?",
        "a": "On My Bookings & Refunds → Book package, pick a bundle, travelers, nights, and fare type. The estimate updates live; Confirm creates a demo BK-PKG booking (no real payment). See Terms & Policies for pricing and cancellation rules.",
    },
    {
        "q": "Where can I read all rules in one place?",
        "a": "Open Terms & Policies or Document Assistant → Terms & Conditions. Use the tabs: Overview, RAG, Packages, and Legal.",
    },
    {
        "q": "What makes the Document Assistant different?",
        "a": "It uses semantic search plus grounded LLM replies with a Sources expander so you can verify each answer against retrieved policy text.",
    },
    {
        "q": "What packages can I book in the demo?",
        "a": "Weekend Escape, City Explorer, Heritage Trail, Coastal Bus Getaway, and Custom trip bundle — see Terms → Packages & tiers for details and placeholder subscription limits.",
    },
]
