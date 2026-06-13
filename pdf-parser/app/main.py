"""uok-doc-parser — structured document parsing service using Docling.

Provides a single endpoint POST /parse that converts binary documents
(PDF, DOCX, PPTX, HTML) into structured sections with headings, content types,
and metadata. Used by uok-be file-processing pipeline for smart syllabus assets.
"""

import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.parser import parse_document
from app.models import ParseResponse

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="uok-doc-parser",
    description="Structured document parsing service (Docling + PyMuPDF)",
    version="1.0.0",
)

MINIMAL_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 10 10]>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n0\n%%EOF\n"
)

_docling_ready = False
_pymupdf_version: str | None = None


@app.on_event("startup")
async def startup_event() -> None:
    """Warm up Docling models and verify PyMuPDF availability."""
    global _docling_ready, _pymupdf_version

    try:
        import fitz  # type: ignore[import]

        fitz.open(stream=MINIMAL_PDF_BYTES, filetype="pdf").close()
        _pymupdf_version = fitz.__version__
        logger.info("PyMuPDF %s available and functional", _pymupdf_version)
    except Exception as exc:
        _pymupdf_version = None
        logger.error("PyMuPDF import/open smoke check failed: %s", exc)

    try:
        from docling.document_converter import DocumentConverter

        DocumentConverter()
        _docling_ready = True
        logger.info("Docling models loaded and ready")
    except Exception as exc:
        logger.error("Failed to load Docling models: %s", exc)
        _docling_ready = False


@app.get("/health")
async def health() -> JSONResponse:
    """Health check — verifies PyMuPDF is importable/functional and Docling models are loaded."""
    if _pymupdf_version is None:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "detail": "PyMuPDF (fitz) is not available — PDF parsing will fail",
            },
        )
    if not _docling_ready:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "detail": "Docling models not loaded",
                "pymupdf_version": _pymupdf_version,
            },
        )
    return JSONResponse(
        content={
            "status": "ok",
            "service": "uok-doc-parser",
            "pymupdf_version": _pymupdf_version,
        }
    )


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(content={"service": "uok-doc-parser", "health": "/health"})


@app.post("/parse", response_model=ParseResponse, response_model_by_alias=True)
async def parse(
    file: UploadFile = File(...),
    mimetype: str = Form(default=""),
) -> ParseResponse:
    """Parse a document into structured sections.

    Accepts any file that Docling supports (PDF, DOCX, PPTX, HTML, Markdown, images).
    Returns structured markdown, section tree, and document metadata.
    """
    if _pymupdf_version is None:
        raise HTTPException(
            status_code=503,
            detail="PyMuPDF (fitz) is not available — PDF parsing will fail",
        )
    if not _docling_ready:
        raise HTTPException(
            status_code=503,
            detail="Parser not ready — Docling models are loading",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    effective_mime = mimetype or file.content_type or "application/octet-stream"
    suffix = _mime_to_suffix(effective_mime) or Path(file.filename or "doc").suffix or ".pdf"

    logger.info(
        "[DocParser] /parse request: filename=%r mime=%s size=%.1fKB",
        file.filename,
        effective_mime,
        len(content) / 1024,
    )

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = await parse_document(tmp_path, effective_mime)
        return result
    except Exception as exc:
        logger.exception(f"Parse failed for {file.filename}: {exc}")
        raise HTTPException(status_code=500, detail=f"Parse error: {exc}") from exc
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


def _mime_to_suffix(mimetype: str) -> str:
    mime_map = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
        "text/html": ".html",
        "text/markdown": ".md",
        "text/plain": ".txt",
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/tiff": ".tiff",
    }
    return mime_map.get(mimetype, "")
