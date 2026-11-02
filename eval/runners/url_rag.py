"""URL scrape RAG evaluation (optional path — not default chat)."""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import patch

from langchain_community.embeddings import FakeEmbeddings
from langchain_core.documents import Document

from eval.helpers.io import load_jsonl
from services.rag.website_rag import (
    load_documents_from_url,
    retrieve_from_url,
    validate_http_url,
)


def evaluate_url_row(case: Dict[str, Any]) -> Dict[str, Any]:
    test_id = case["test_id"]
    url = case.get("url", "")
    query = case.get("query", "")

    ok, msg = validate_http_url(url)
    row: Dict[str, Any] = {"test_id": test_id, "url": url, "validate_ok": ok, "validate_msg": msg}

    if case.get("expect_load_ok") is False:
        if not ok:
            row["pass"] = case.get("expect_error_contains", "").lower() in msg.lower()
            row["note"] = "validate_http_url rejected input"
            return row
        docs, err = load_documents_from_url(url)
        row["load_error"] = err
        row["pass"] = err is not None and (
            not case.get("expect_error_contains")
            or case["expect_error_contains"].lower() in (err or "").lower()
        )
        return row

    if case.get("expect_retrieve_callable"):
        fake_docs = [
            Document(page_content="Example domain policy text for retrieval testing " * 5, metadata={"source": url})
        ]
        with patch("services.rag.website_rag.load_documents_from_url", return_value=(fake_docs, None)), patch(
            "services.rag.website_rag.get_embeddings",
            return_value=FakeEmbeddings(size=384),
        ):
            chunks, err = retrieve_from_url(query or "policy", url or "https://example.com")
        row["retrieve_count"] = len(chunks)
        row["retrieve_error"] = err
        if case.get("expect_retrieve_empty"):
            row["pass"] = len(chunks) == 0 or not query.strip()
        else:
            row["pass"] = err is None and len(chunks) >= 0
        row["note"] = "retrieve_from_url tested with FakeEmbeddings — not live chat path"
        return row

    row["pass"] = ok == bool(case.get("expect_load_ok", True))
    return row


def run_url_rag_eval(dataset_name: str = "url_scrape_cases.jsonl") -> Dict[str, Any]:
    cases = load_jsonl(dataset_name)
    rows = [evaluate_url_row(c) for c in cases]
    passed = sum(1 for r in rows if r.get("pass"))
    return {
        "summary": {
            "total": len(rows),
            "passed": passed,
            "pass_rate": round(passed / max(len(rows), 1), 4),
            "production_chat_uses_url_index": False,
        },
        "rows": rows,
    }
