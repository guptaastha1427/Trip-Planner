# AUTH_SECURITY.md — AS-IS review

Static review Nov 2025. **No fixes applied.** `.env` not opened. **Prototype — high risk if public-hosted.**

## Summary

| Area | Status |
|------|--------|
| Auth | Local PBKDF2 accounts (`rag_chat_auth.py`); not IdP/MFA |
| Roles | **No RBAC** — Admin = sidebar mode + `admin_unlocked` + passphrase `demo_admin` |
| Sessions | Token in JSON + 30-day cookie; **no server TTL** |
| Secrets | `.env` / optional `st.secrets`; gitignored runtime JSON |
| Uploads | **No** file uploader; optional URL scrape only |
| Production | Treat as **training demo only** |

## Authentication

Register: username ≥2, email regex, password ≥8. PBKDF2-SHA256 260k iter. Stores: `rag_chat_users.json`, sessions in `rag_chat_sessions.json`, cookie `trip_planner_auth`, portal `rag_session_token`.

**Missing:** OAuth, reset, CAPTCHA, rate limits, lockout.

Policy bots: `require_login=False` at all call sites.

## Authorization

| Concept | Enforcement |
|---------|-------------|
| Logged-in | Maps portal id via `portal_user_context` |
| Guest | Can **switch demo user** in sidebar — preview any demo customer data |
| Admin mode | Selecting 🔧 Admin sets `admin_unlocked` **without passphrase** |
| Admin console | UI gate `demo_admin` or prior unlock |
| Store mutations | `customer_portal_store` **no server-side admin check** (`admin` param ignored in places) |

Support bot checks booking `user_id` vs active portal id — but guests pick id.

## Sessions

Opaque token; server row `{email, created_at}` only; logout clears cookie + JSON.

**Risk:** stolen token valid until manual delete.

## Secrets

`get_gemini_api_key()` → agent, embeddings, RAG. `.gitignore` covers `.env`, secrets, auth JSON. UI shows key **names** not values. Agent errors may include `str(exc)` from Gemini.

## Documents & input

Terms RAG = static Python strings. URL fetch: http(s) + host only — **no** private IP blocklist (SSRF risk if exposed). Trip form text to agent; chat to embeddings + Gemini.

## Prompt injection / XSS

Grounding + system prompts reduce but don’t eliminate bypass. LLM body may render with `unsafe_allow_html=True` when citations present — **model HTML not escaped** (C-6).

## Errors & `/dev`

`last_error`, embedding errors may leak API detail. `/dev` shows `info.md` **without auth**.

## Validation present

Auth email/password; URL scheme; trip days 1–14; ticket length mins.

**Absent:** SSRF controls, CSP, CSRF tokens, rate limits, pinned deps audit in repo.

## Confirmed issues (hosted severity)

| ID | Issue |
|----|--------|
| C-1 | Guest can switch demo users — view/submit as others |
| C-2 | Admin mode without passphrase |
| C-3 | Hardcoded `demo_admin` |
| C-4 | No server-side auth on portal mutations |
| C-5 | Sessions without server expiry |
| C-6 | XSS path with citations + LLM HTML |
| C-7 | URL fetch SSRF-style |
| C-8 | Exception text in UI |

C-1–C4 acceptable for solo local capstone; not for multi-user product.

## Potential risks (P-1–P-8)

Prompt injection; Google data handling; file permissions; cookie flags; brute force; Streamlit session model; supply chain; open `/dev`.

## Suggestions (approval required)

Real IdP/RBAC; gate guest switching; remove auto admin unlock; enforce store authorization; session TTL; SSRF blocklist; escape LLM HTML; sanitize errors; optional login for bots; pin deps + audit; protect `/dev`; secret manager for keys.

## Module map

Auth: `rag_chat_auth`, `rag_chat_ui`, `sign_in.py`. Portal: `portal_user_context`, `portal_ui`. Admin: `demo_dashboard`, `admin_console`. RAG/URL: `website_rag`, `policy_bot_ui`. Support: `support_faq`, `customer_portal_store`. Trip: `agent.py`, `app.py`.

*Update when security-relevant code changes.*
