"""Document parsing logic — PyMuPDF for PDFs, Docling for other supported formats."""

import asyncio
import logging
import re
import time
from functools import partial
from pathlib import Path

from app.models import DocumentMetadata, ParseResponse, ParsedSection
from app.structure_discovery import (
    PageTextCache,
    TocEntry,
    discover_pdf_structure,
    _prepare_bookmark_entries,
    _sections_from_toc_entries,
)

logger = logging.getLogger(__name__)

_HEADING_PATTERN = re.compile(r"^\s*(#{1,6})\s+(.+)$")


async def parse_document(file_path: str, mimetype: str) -> ParseResponse:
    """Parse a document file into structured sections."""
    file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0
    logger.info(
        "[DocParser] Starting parse: file=%s mime=%s size=%.1fKB",
        Path(file_path).name,
        mimetype,
        file_size / 1024,
    )
    t_start = time.monotonic()

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, partial(_parse_sync, file_path, mimetype))

    elapsed = time.monotonic() - t_start
    logger.info(
        "[DocParser] Parse complete: sections=%d markdown_chars=%d elapsed=%.2fs",
        len(result.sections),
        len(result.markdown),
        elapsed,
    )
    return result


def _parse_sync(file_path: str, mimetype: str) -> ParseResponse:
    is_pdf = mimetype == "application/pdf" or file_path.lower().endswith(".pdf")

    if is_pdf:
        logger.info("[DocParser] PDF — using PyMuPDF extraction (no Docling)")
        return _parse_with_pymupdf(file_path)

    try:
        return _parse_with_docling_text_only(file_path, mimetype)
    except Exception as exc:
        logger.warning("[DocParser] Docling failed (%s)", exc)
        raise


def _parse_with_pymupdf(file_path: str) -> ParseResponse:
    """Extract structured text from PDF using PyMuPDF (fast, no ML)."""
    import fitz  # type: ignore[import]

    logger.info("[DocParser] PyMuPDF: opening %s", file_path)
    t0 = time.monotonic()

    doc = fitz.open(file_path)
    page_count = doc.page_count
    logger.info("[DocParser] PyMuPDF: %d pages, extracting text...", page_count)

    font_sizes: list[float] = []
    try:
        for page_num in range(min(page_count, 10)):
            blocks = doc[page_num].get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            font_sizes.append(span.get("size", 10))
    except Exception:
        pass

    if font_sizes:
        from collections import Counter

        counts = Counter(font_sizes)
        body_size = counts.most_common(1)[0][0] if counts else 10
        logger.info("[DocParser] PyMuPDF: detected body_size=%.1f", body_size)
    else:
        body_size = 10

    full_text_parts: list[str] = []
    page_texts: list[str] = []
    for page_num in range(page_count):
        page = doc[page_num]
        page_plain_parts: list[str] = []
        try:
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_LIGATURES)["blocks"]
            for block in blocks:
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        line_text = ""
                        max_size = 0
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if text:
                                line_text += text + " "
                                max_size = max(max_size, span.get("size", 10))

                        line_text = line_text.strip()
                        if line_text:
                            page_plain_parts.append(line_text)
                            if max_size > body_size * 1.6:
                                full_text_parts.append(f"\n# {line_text}\n\n")
                            elif max_size > body_size * 1.3:
                                full_text_parts.append(f"\n## {line_text}\n\n")
                            elif max_size > body_size * 1.1:
                                full_text_parts.append(f"\n### {line_text}\n\n")
                            else:
                                full_text_parts.append(line_text + " ")
                    full_text_parts.append("\n\n")
            plain_page_text = "\n".join(page_plain_parts).strip()
            page_texts.append(plain_page_text if plain_page_text else page.get_text())
        except Exception as exc:
            logger.debug("[DocParser] PyMuPDF page %d failed: %s", page_num, exc)
            fallback_text = page.get_text()
            page_texts.append(fallback_text)
            full_text_parts.append(fallback_text + "\n\n")

    markdown = "".join(full_text_parts).strip()
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    logger.info(
        "[DocParser] PyMuPDF extraction done in %.2fs: %d pages, %d chars",
        time.monotonic() - t0,
        page_count,
        len(markdown),
    )

    meta_raw = doc.metadata or {}

    discovery = discover_pdf_structure(
        doc,
        markdown,
        build_markdown_sections=_extract_sections,
        page_texts=page_texts,
    )

    doc.close()

    metadata = DocumentMetadata(
        title=meta_raw.get("title") or None,
        author=meta_raw.get("author") or None,
        page_count=page_count,
        has_tables=False,
        has_figures=False,
        has_table_of_contents=discovery.has_table_of_contents,
        structure_source=discovery.structure_source,
        structure_validated=discovery.structure_validated,
        structure_warnings=discovery.structure_warnings,
        book_profile=discovery.book_profile,
    )
    logger.info(
        "[DocParser] Metadata: title=%r pages=%d source=%s validated=%s profile=%s",
        metadata.title,
        page_count,
        metadata.structure_source,
        metadata.structure_validated,
        metadata.book_profile,
    )

    logger.info("[DocParser] Sections extracted: %d", len(discovery.sections))
    for index, section in enumerate(discovery.sections[:5]):
        logger.debug(
            "[DocParser]   [%d] %r (%s, pages=%s, indexable=%s, %dc)",
            section.heading_level,
            section.heading[:50],
            section.content_type,
            section.page_range,
            section.indexable,
            len(section.content),
        )
    if len(discovery.sections) > 5:
        logger.debug("[DocParser]   ... (%d more sections)", len(discovery.sections) - 5)

    return ParseResponse(markdown=markdown, sections=discovery.sections, metadata=metadata)


def _parse_with_docling_text_only(file_path: str, mimetype: str) -> ParseResponse:
    """Use Docling with all ML disabled — text layer extraction only."""
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    logger.info("[DocParser] Docling text-layer mode (no ML)...")
    t0 = time.monotonic()

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = False
    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = False

    converter = DocumentConverter(
        format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
    )
    logger.info("[DocParser] Docling converter ready in %.2fs", time.monotonic() - t0)

    t1 = time.monotonic()
    result = converter.convert(file_path)
    doc = result.document
    logger.info("[DocParser] Docling conversion in %.2fs", time.monotonic() - t1)

    markdown = doc.export_to_markdown()
    logger.info("[DocParser] Markdown: %d chars", len(markdown))

    metadata = _extract_metadata(doc)
    sections = _extract_sections(markdown)
    logger.info("[DocParser] Sections: %d", len(sections))

    metadata.has_table_of_contents = False
    metadata.structure_source = "markup_headings" if _has_real_structure(sections) else "none"
    metadata.structure_validated = metadata.structure_source == "markup_headings"

    return ParseResponse(markdown=markdown, sections=sections, metadata=metadata)


def _extract_metadata(doc: object) -> DocumentMetadata:
    """Extract document metadata from Docling document object."""
    title = author = None
    page_count = None
    has_tables = has_figures = False

    try:
        if hasattr(doc, "metadata") and doc.metadata:
            metadata_obj = doc.metadata
            title = getattr(metadata_obj, "title", None) or getattr(metadata_obj, "Title", None)
            author = getattr(metadata_obj, "author", None) or getattr(metadata_obj, "Author", None)
    except Exception:
        pass

    try:
        if hasattr(doc, "pages"):
            page_count = len(doc.pages) if doc.pages else None
    except Exception:
        pass

    try:
        if hasattr(doc, "tables") and doc.tables:
            has_tables = True
        if hasattr(doc, "figures") and doc.figures:
            has_figures = True
    except Exception:
        pass

    return DocumentMetadata(
        title=str(title) if title else None,
        author=str(author) if author else None,
        page_count=page_count,
        has_tables=has_tables,
        has_figures=has_figures,
    )


def _extract_sections(markdown: str) -> list[ParsedSection]:
    """Extract hierarchical sections from markdown output."""
    sections: list[ParsedSection] = []
    lines = markdown.split("\n")
    heading_positions: list[tuple[int, int, str]] = []

    for line_index, line in enumerate(lines):
        match = _HEADING_PATTERN.match(line)
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            heading_positions.append((line_index, level, heading_text))
        elif line.strip().startswith("#"):
            logger.debug("[DocParser] Skipping line starting with # (no match): %r", line)

    logger.info("[DocParser] Found %d headings in %d lines", len(heading_positions), len(lines))

    if not heading_positions:
        if markdown.strip():
            sections.append(
                ParsedSection(
                    heading="Document",
                    heading_level=1,
                    section_path="Document",
                    content=markdown.strip(),
                    content_type=_detect_content_type(markdown),
                    indexable=True,
                )
            )
        return sections

    heading_stack: list[str] = []

    for idx, (line_no, level, heading_text) in enumerate(heading_positions):
        heading_stack = heading_stack[: level - 1]
        heading_stack.append(heading_text)
        section_path = " > ".join(heading_stack)

        next_line_no = (
            heading_positions[idx + 1][0] if idx + 1 < len(heading_positions) else len(lines)
        )
        content = "\n".join(lines[line_no + 1 : next_line_no]).strip()

        if not content:
            continue

        sections.append(
            ParsedSection(
                heading=heading_text,
                heading_level=level,
                section_path=section_path,
                content=content,
                content_type=_detect_content_type(content),
                indexable=True,
            )
        )

    return sections


def _detect_content_type(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("|") and "|" in stripped[1:]:
        return "table"
    if re.search(r"^[-*+]\s|^\d+\.\s", stripped, re.MULTILINE):
        return "list"
    return "paragraph"


def _has_real_structure(sections: list[ParsedSection]) -> bool:
    """True when extraction produced real headings, not the synthetic 'Document' fallback."""
    return not (len(sections) == 1 and sections[0].heading == "Document")


def _toc_is_usable(toc: list) -> bool:
    """A PDF bookmark outline counts as a usable ToC when it has >=2 non-empty titled entries."""
    titled = [entry for entry in toc if len(entry) >= 2 and str(entry[1]).strip()]
    return len(titled) >= 2


def _sections_from_toc(toc: list, doc: object) -> list[ParsedSection]:
    """Build sections from a PDF bookmark outline (tests and backward compatibility)."""
    entries: list[TocEntry] = []
    for row in toc:
        if len(row) < 3:
            continue
        title = str(row[1]).strip()
        if not title:
            continue
        entries.append(
            TocEntry(level=min(max(int(row[0]), 1), 6), title=title, page=int(row[2]))
        )
    prepared = _prepare_bookmark_entries(entries)
    page_cache = PageTextCache.from_document(doc)
    return _sections_from_toc_entries(prepared, page_cache)
