# How to Use This Application

Easy guide for **travelers (users)** and ** administrators**. 
This app is a **student / capstone prototype**. It is **not** a real travel agency or payment system.

---

## Before you start

1. Install dependencies (see `README.md`).
2. Copy `.env.example` to `.env` and set:
 - `GEMINI_API_KEY` — for AI trip planning
 - `OSM_CONTACT_EMAIL` — for map / place data
3. Run from the project folder:

 ```bash
 streamlit run app.py
 ```

4. Open the URL shown in the terminal (usually `http://localhost:8501`).

Use the **left sidebar** to switch pages.

### Dashboard switch (User vs Admin)

At the **top of the sidebar** on every page:

- **👤 User** — customer view: trip planner, bookings, refunds, support (no admin section in the main menu).
- **🔧 Admin** — back-office view: opens the **Admin dashboard**, unlocks admin tools for the session, and shows admin-first navigation.

Use this when presenting demos so you can flip between “customer” and “admin” in one click.

**What changes with the role**

| Mode | What you see |
|------|----------------|
| **User** | Customer dashboard (bookings, refunds, tickets, account), AI trip planner, refund submit forms |
| **Admin** | Admin dashboard (queue metrics, tools), full admin console; customer pages are reference-only (no refund submit) |

---

## What the app includes (feature overview)

### Trip planning (AI)

| Feature | What it does |
|--------|----------------|
| Trip form | From, To, days, pace, interests, notes |
| Create itinerary | AI builds a day plan from **real OpenStreetMap places** |
| Itinerary tab | Morning / afternoon / evening stops, photos, 👍/👎 feedback |
| Nearby swap | Replace a stop with a nearby place (no new AI call) |
| Change one day | Ask AI to update a single day only |
| Map tab | Route map, filter by day, light/dark theme |
| Travel & stays | Weather, city guide, hotels, flights, trains (sample data from OSM) |
| Trip history | Sidebar list of past generated trips — click to reload |
| Book as travel package | Prefills **My Bookings & Refunds → Book package** from the current trip |
| Policy assistant | Floating chat on Trip Planner (terms, refunds, packages — same engine as support bot) |
| Export | Download itinerary JSON |
| Agent trace | Expandable log of how the AI run worked (debug) |
| Developer docs | Project guide from `info.md` (`/dev`) |

### Customer portal (bookings & refunds)

| Feature | What it does |
|--------|----------------|
| Accounts | Switch fake users in the sidebar (different booking scenarios) |
| My Bookings & Refunds | **Book package** tab, **My bookings**, **Refund requests** (status + booking details) |
| Refund Assistant | Rule-based eligibility check + chat grounded in policies |
| Account Status | See restrictions, submit appeals |
| Help & Support | FAQ, support bot, support tickets |
| Terms & Policies | Read these terms and policy comparison |

### Admin (back-office simulation)

| Feature | What it does |
|--------|----------------|
| Admin console | Tabs: Overview, Refunds, Tickets, Accounts, Audit log |
| Refund queue | Advance, approve, reject, or complete; see why customer raised request |
| Support tickets | Resolve with status + reply; see ticket reason and thread |
| Account controls | Set account status (active, restricted, blacklisted, etc.) |
| Audit log | Recent admin actions |

**Important:** Portal login is **fake**. Anyone can open **Admin** if they know the app passphrase. Do not use real personal or payment data.

---

## If you are a **user** (traveler + customer)

You mainly use **Trip planning** and **Bookings & support**. You do **not** need the admin page for normal use.

### A. Plan a trip (step by step)

1. In the sidebar, open **Trip Planner** (home).
2. Fill in **From**, **To**, **Days**, **Schedule**, **Interests**, and optional **Notes**.
3. Click **Create my itinerary**.
4. Wait for the progress bar (OSM + AI can take a minute or more).
5. When it finishes:
 - Read your plan under **Itinerary**.
 - Open **Map** for the route.
 - Open **Travel & stays** for weather and travel hints.
6. Optional:
 - Tap **👍** or **👎** on a stop (helps future ranking for that city).
 - Use **Nearby** cards to swap a stop.
 - Under **Change one day only**, describe what to change and click **Update this day**.
 - **Download trip (JSON)** in **Export & advanced**.
7. In the sidebar, **Trip history** lets you open an older generated trip.

### B. Use the customer portal as a user

1. Open any page under **Bookings & support** (e.g. **My Bookings & Refunds**).
2. In the sidebar, choose a **Account** (e.g. Alex, Maya, restricted users).
3. **My Bookings & Refunds** (`/bookings`):
 - **Book package** tab: choose bundle, travelers, nights, fare; **Confirm package booking** (saved as `BK-PKG-…`).
 - **My bookings** tab: open a booking, pick a refund reason, **Check eligibility & submit**.
 - **Refund requests** tab: workflow status, eligibility, booking/ticket details, timeline.
4. **Refund Assistant** (`/refund-assistant`):
 - Select booking and reason → **Run eligibility check**.
 - Read amounts and next steps; use chat for policy questions (rules are fixed in code).
5. **Account Status** (`/account`):
 - See if the app account has restrictions.
 - Submit an **Appeal** if the scenario includes violations.
6. **Help & Support** (`/support`):
 - Read **FAQ**, chat with the **Support bot**, or create a **ticket**.
7. **Terms & Policies** (`/terms`): read illustrative legal / policy text.

### C. Read technical docs (optional)

- Sidebar → **Developer docs** or go to `/dev` for architecture and flows (`info.md`).

---

## If you are an **admin** ( back-office)

In this project, “admin” means **Admin** — for classroom or review, **not** production operations.

### Step 1 — Open admin

1. Run `streamlit run app.py`.
2. Sidebar → **Admin** section → **Admin**, or visit `/admin`.

### Step 2 — Unlock (prototype only)

1. Enter passphrase: **`demo_admin`** (configured in code for training; not shown in the UI).
2. After unlock, admin tools appear for your browser session.

### Step 3 — Use the admin console

1. Open **Admin dashboard** (`/admin`) or use the full console from that page.
2. **Refunds** tab: filter queue, read customer reason and booking snapshot, advance workflow or approve/reject.
3. **Tickets** tab: read why the ticket was raised, set status, send a support reply.
4. **Accounts** tab: override account status for a profile.
5. **Audit log** tab: review recent actions.

Data is stored in `data/customer_portal_state.json` (local file).

### Step 4 — Change account status

1. Under **Account restrictions**, pick a **User** (profile).
2. Choose **Set status**: active, under review, temporarily restricted, or blacklisted.
3. Add a **Reason** (for the audit log).
4. Click **Apply account status**.

This affects how the **refund rule engine** treats that user (e.g. blocked or manual review).

### Step 5 — Review audit log

- Scroll to **Audit log (recent)** to see the last admin actions (timestamps and details).

### What admins typically do **not** use for “admin work”

- **Trip Planner** AI settings are in code / `.env`, not on the admin page.
- **Trip history** and **feedback** live in `data/app_state.json` and `data/feedback.jsonl` — not edited in Admin UI.
- To reset portal sample data, replace or edit `data/customer_portal_state.json` (see `.example` file in `data/`).

---

## Quick URL map (after `streamlit run app.py`)

| Page | Typical URL path |
|------|------------------|
| Trip Planner | `/` (home) |
| My Bookings & Refunds | `/bookings` |
| Refund Assistant | `/refund-assistant` |
| Account Status | `/account` |
| Help & Support | `/support` |
| Terms & Policies | `/terms` |
| Admin | `/admin` |
| Developer docs | `/dev` |

(Port may differ if 8501 is busy.)

---

## Tips

- **First plan for a new city** is slower (many API calls). Same city again is often faster when caches apply.
- **Switch users** in the sidebar to test refunds, restrictions, and appeals.
- **Admin passphrase** is only for training; treat it as public in a shared classroom environment.

---

## Need more detail?

- Setup and capstone layout: `README.md`
- Architecture and code flow: `info.md` or **Developer docs** in the app
