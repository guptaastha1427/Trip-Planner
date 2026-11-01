# MCP.md — Model Context Protocol

**Verdict: MCP is not implemented in this repository.**

No MCP servers/clients, packages, or committed config. Repo search: no `mcp` / Model Context Protocol matches in app code or `requirements.txt`.

**Outside repo:** IDE-level MCP (e.g. Cursor) is not part of the Streamlit app.

## Related: Gemini function tools (not MCP)

`services/agent.py`: `FunctionDeclaration` tools `search_pois` (OSM), `retrieve_guides` (Wikivoyage TF-IDF) via `google-genai`. Policy path: LangChain FAISS + Gemini — see `API.md`.

## Checklist (all absent)

Server entrypoints, Streamlit MCP client, committed `mcp.json`, registered tools/resources, env placeholders for MCP.

## Safe permission guidance (if you add MCP in IDE)

Least privilege; read-only default; confirm before writes to `data/`, prompts, `EMBEDDING_CACHE_VERSION`, deps; secrets in env not git; test on copy of repo.

## Optional future (not approved)

Issue trackers, doc fetch, test runner MCP — app already has HTTP/static terms; JSON-only persistence.

## Cross-refs

`API.md`, `DATABASE.md`, `AUTH_SECURITY.md`, `AGENTS.md`, `ARCHITECTURE.md`.

| Question | Answer |
|----------|--------|
| MCP in repo? | **No** |
| App uses instead? | Gemini tools, LangChain/FAISS, outbound HTTP |
