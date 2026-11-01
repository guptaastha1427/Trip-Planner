# DESIGN.md — Streamlit UI (as implemented)

**Entry:** `streamlit run app.py` · wide layout · title **Trip Planner AI Agent**. From `app.py`, `pages/`, `services/ui_*`, `.streamlit/config.toml` only.

## Shell

| Aspect | Detail |
|--------|--------|
| Main column | max **1100px** centered |
| Background | `hero-travel-bg.jpg` + gradient (`ui_animations`) |
| Sidebar | Frosted; Sign in link **hidden** in nav CSS (`href*="sign-in"`) |
| Font | Plus Jakarta Sans; theme light indigo (`.streamlit/config.toml`) |

**Nav groups:** User = Trip planning + Bookings & support + Docs; Admin = Admin + customer preview + Docs.

**Shared sidebar:** Dashboard User/Admin radio → may switch page; User: trip history expander (240px), policy popover; Admin: caption only; **profile dock** bottom (sign in/out, demo user radio).

## Visual system

Brand indigo/lavender; section headings `.trip-h--plan|itinerary|map|travel`; bordered cards 22px radius; pill tabs; 3D primary buttons; portal `.portal-hero`, `.status-pill--*`, `.pkg-*`, `.rag-*` cites, chat card borders.

## Trip Planner (`/`)

**Admin mode on planner:** `render_admin_home_dashboard` + link to console — no form.

**Customer:** Title, env warnings, **Plan your trip** form → **Create my itinerary**; progress + spinner on run; `st.error` for `last_error`; balloons on generate success.

**With itinerary:** stats row; **Book as travel package**; tabs **Itinerary | Map | Travel & stays**.

- **Itinerary:** day blocks 🌅/☀️/🌙; stop cards; nearby horizontal swap; 👍/👎 toast; expander **Change one day only**.
- **Map:** day filter, light/dark, PyDeck ≥420px, turn-by-turn expander.
- **Travel:** guide, weather, OSM hints (hotels, flights, transit).
- **Export & advanced:** JSON download, feedback stats, raw model on error.
- **Agent trace** bordered; **Policy FAB** 🤖 dialog (mutual exclusion with sidebar popover).

**Refine UI:** single-day wired; full refine button **none**; `_show_refinement_diff` **uncalled**; `pending_refinement_compare` / `refine_success` session keys not rendered.

## Portal pages (`portal_page_setup`)

Hero + context strip; admin preview strips when Admin mode.

| Page | UI |
|------|-----|
| Bookings | Tabs: Book package (metrics, confirm, balloons), My bookings (refund forms), Refund requests (nested expanders); admin blocks refund submit |
| Refund Assistant | Booking/reason → eligibility → metrics; chat = rule engine |
| Account | status badge, restrictions, appeal form |
| Support | FAQ expanders; policy bot + optional URL test; tickets + escalation |
| Terms | Tabbed copy + link to Sign in |
| Sign in | Sign up/in tabs; logged-in summary + **Go to Chat** (menu state only — **no** `render_page_menu` route) |
| Admin | Warning; passphrase `demo_admin`; console tabs with filters/actions |
| Dev | Slate docs chrome 920px; renders `info.md` + Mermaid |

## Policy bot (`render_policy_bot_chat`)

Support page, sidebar popover, FAB dialog. Intro; optional URL expander; scroll chat 300–420px; `st.chat_input` disabled pending (**Searching…**); `require_login=False` everywhere. Citations may use `unsafe_allow_html`. **`_render_typing_indicator` never called.**

## Interaction states

Submit → inline success/error + rerun; generate loading = progress/spinner; empty lists = `st.info`/captions; admin locked = passphrase gate.

## Responsive (CSS)

1100/640/720px breakpoints; sidebar collapsed hides dock; horizontal scroll on nearby/hints.

## Accessibility (partial)

Decorative `aria-hidden`; typing indicator ARIA exists but unused; some `focus-visible`; **no** full widget ARIA audit.

## Source map (primary)

`app.py`, `ui_animations`/`ui_travel_theme`, `ui_components`, `demo_dashboard`, `portal_ui`, `role_dashboard`, `trace_view`, `map_viz`, `policy_bot_ui`, `rag_chat_*`, `terms_page_ui`, `pages/*`, `package_*`, `admin_console`, `info_markdown_view`, `rag_citations`.

*Matches Streamlit full-rerun model.*
