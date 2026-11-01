# How to Use This Application

Capstone **prototype** — not a real agency or payment system.

## Before you start

1. `pip install -r requirements.txt` (see `../README.md`).
2. `.env`: `GEMINI_API_KEY`, `OSM_CONTACT_EMAIL`.
3. `streamlit run app.py` → usually `http://localhost:8501`.
4. Use **sidebar** for pages.

**Dashboard (top of sidebar):** **👤 User** = customer (planner, bookings, refunds). **🔧 Admin** = back-office menu; customer refund submit blocked on bookings.

## Feature overview

**Trip:** Form → create itinerary (OSM + AI) → itinerary / map / travel; feedback; nearby swap; change one day; history; book package; policy chat; export JSON; agent trace.

**Portal:** Switch demo users; book package; refunds + track requests; Refund Assistant; account appeals; support FAQ/bot/tickets; terms.

**Admin:** Console tabs (refunds, tickets, accounts, audit). Passphrase **`demo_admin`** (training only — treat as public in class).

## If you are a user

1. **Trip Planner:** Fill form → **Create my itinerary** → wait (can take a minute) → tabs; optional swap, single-day, download JSON; **Trip history** in sidebar.
2. **Portal:** Pick sidebar account → **My Bookings & Refunds** (book / refund / track) → **Refund Assistant** → **Account** → **Support** → **Terms**.
3. **Docs:** `/dev` or Developer docs → `info.md`.

## If you are an admin

1. Sidebar **Admin** or `/admin`.
2. Passphrase **`demo_admin`** if prompted.
3. Process refunds/tickets; set account status; read audit log. Data in `data/customer_portal_state.json`.

Admins don’t edit trip history or feedback in UI — those live in `app_state.json` / `feedback.jsonl`.

## URL map

| Page | Path |
|------|------|
| Trip Planner | `/` |
| Bookings | `/bookings` |
| Refund Assistant | `/refund-assistant` |
| Account | `/account` |
| Support | `/support` |
| Terms | `/terms` |
| Admin | `/admin` |
| Developer docs | `/dev` |

## Tips

First plan for a new city is slower; switch demo users to test scenarios; don’t enter real payment/PII.

More: `../README.md`, `info.md`, in-app **Developer docs**.
