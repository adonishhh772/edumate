"""Smoke tests for the `/health` endpoint.

The goal of these tests is to guarantee that the health check fails loudly
(HTTP 503) whenever PyMuPDF or Docling are not available, so that our
orchestrator (Kubernetes / uok-be `DocParserClient`) never routes real PDF
traffic at a broken parser instance.

We **do not** invoke the FastAPI startup event here — it would try to load
Docling's heavy model bundle. Instead we patch module-level readiness flags
directly; this is exactly what the startup hook assigns in production.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import main as app_main


@pytest.fixture()
def test_client() -> TestClient:
    """TestClient WITHOUT lifespan — startup event is intentionally skipped."""
    return TestClient(app_main.app)


def _reset_readiness_flags(pymupdf_version: str | None, docling_ready: bool) -> None:
    app_main._pymupdf_version = pymupdf_version
    app_main._docling_ready = docling_ready


def test_health_returns_ok_when_all_dependencies_ready(test_client: TestClient) -> None:
    _reset_readiness_flags(pymupdf_version="1.24.14", docling_ready=True)

    response = test_client.get("/health")

    assert response.status_code == 200
    payload: dict[str, Any] = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "uok-doc-parser"
    assert payload["pymupdf_version"] == "1.24.14"


def test_health_returns_503_when_pymupdf_missing(test_client: TestClient) -> None:
    _reset_readiness_flags(pymupdf_version=None, docling_ready=True)

    response = test_client.get("/health")

    assert response.status_code == 503
    payload: dict[str, Any] = response.json()
    assert payload["status"] == "unavailable"
    assert "PyMuPDF" in payload["detail"]


def test_health_returns_503_when_docling_not_ready(test_client: TestClient) -> None:
    _reset_readiness_flags(pymupdf_version="1.24.14", docling_ready=False)

    response = test_client.get("/health")

    assert response.status_code == 503
    payload: dict[str, Any] = response.json()
    assert payload["status"] == "unavailable"
    assert "Docling" in payload["detail"]
    assert payload["pymupdf_version"] == "1.24.14"


def test_parse_returns_503_when_pymupdf_missing(test_client: TestClient) -> None:
    _reset_readiness_flags(pymupdf_version=None, docling_ready=True)

    response = test_client.post(
        "/parse",
        files={"file": ("sample.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
        data={"mimetype": "application/pdf"},
    )

    assert response.status_code == 503
    assert "PyMuPDF" in response.json()["detail"]


def test_parse_returns_503_when_docling_not_ready(test_client: TestClient) -> None:
    _reset_readiness_flags(pymupdf_version="1.24.14", docling_ready=False)

    response = test_client.post(
        "/parse",
        files={"file": ("sample.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
        data={"mimetype": "application/pdf"},
    )

    assert response.status_code == 503
    assert "Docling" in response.json()["detail"]


def test_pymupdf_can_open_minimal_pdf_fixture() -> None:
    """Guard against regression of the PyMuPDF pin — the minimal PDF used in
    the startup smoke check must always be parseable without raising."""
    fitz = pytest.importorskip("fitz")

    doc = fitz.open(stream=app_main.MINIMAL_PDF_BYTES, filetype="pdf")
    try:
        assert doc.page_count >= 1
    finally:
        doc.close()
