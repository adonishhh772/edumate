"""Tests for structure-source detection (Phase 1).

Covers the table-of-contents detection added to the PDF path and the path-agnostic
structure classifier. Pure helpers are tested directly; the full PyMuPDF path is
exercised against in-memory PDFs built with fitz (skipped when fitz is unavailable).

The Docling path is not exercised here — it loads heavy ML bundles — but its
classification reuses `_has_real_structure`, which is covered directly.
"""

from __future__ import annotations

import pytest

from app.models import ParsedSection
from app.parser import (
    _has_real_structure,
    _parse_with_pymupdf,
    _sections_from_toc,
    _toc_is_usable,
)


@pytest.fixture()
def fitz_module():
    """PyMuPDF (fitz) or skip the test when it is not installed."""
    return pytest.importorskip("fitz")


def _section(heading: str, level: int = 1, content: str = "x") -> ParsedSection:
    return ParsedSection(
        heading=heading,
        heading_level=level,
        section_path=heading,
        content=content,
    )


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_has_real_structure_false_for_document_fallback() -> None:
    assert _has_real_structure([_section("Document")]) is False


def test_has_real_structure_true_for_real_headings() -> None:
    assert _has_real_structure([_section("Introduction"), _section("Methods")]) is True


def test_toc_is_usable_requires_two_titled_entries() -> None:
    assert _toc_is_usable([[1, "Chapter 1", 1], [1, "Chapter 2", 2]]) is True
    assert _toc_is_usable([[1, "Only one", 1]]) is False
    assert _toc_is_usable([[1, "", 1], [1, "   ", 2]]) is False


class _FakePage:
    def __init__(self, index: int, text: str) -> None:
        self._index = index
        self._text = text

    def get_text(self) -> str:
        return self._text


class _FakeDoc:
    """Minimal stand-in for a fitz.Document for pure _sections_from_toc tests."""

    def __init__(self, page_count: int, page_text: str = "body") -> None:
        self.page_count = page_count
        self._page_text = page_text

    def __getitem__(self, index: int) -> _FakePage:
        return _FakePage(index, self._page_text)


def test_sections_from_toc_preserves_raw_levels_and_builds_path() -> None:
    # Skipped level (1 -> 3): raw levels are preserved here; densification happens in the
    # uok-be mapper. The heading stack still produces a correct path.
    sections = _sections_from_toc([[1, "A", 1], [3, "C", 1]], _FakeDoc(2))

    assert [s.heading for s in sections] == ["A", "C"]
    assert [s.heading_level for s in sections] == [1, 3]
    assert sections[1].section_path == "A > C"


def test_sections_from_toc_keeps_section_with_empty_content() -> None:
    sections = _sections_from_toc([[1, "A", 1], [1, "B", 1]], _FakeDoc(1, page_text=""))

    assert len(sections) == 2
    assert sections[0].content == ""
    assert sections[0].content_type == "paragraph"


def test_sections_from_toc_skips_blank_titles() -> None:
    sections = _sections_from_toc([[1, "A", 1], [1, "  ", 2]], _FakeDoc(2))

    assert [s.heading for s in sections] == ["A"]


# ---------------------------------------------------------------------------
# Full PyMuPDF path (in-memory PDFs)
# ---------------------------------------------------------------------------


def _pdf_with_bookmarks(fitz_module, tmp_path) -> str:
    doc = fitz_module.open()
    doc.new_page()
    doc.new_page()
    doc[0].insert_text((72, 72), "Chapter 1 body text", fontsize=11)
    doc[1].insert_text((72, 72), "Chapter 2 body text", fontsize=11)
    doc.set_toc([[1, "Chapter 1", 1], [2, "Section 1.1", 1], [1, "Chapter 2", 2]])
    path = tmp_path / "with_toc.pdf"
    doc.save(str(path))
    doc.close()
    return str(path)


def test_pdf_with_bookmarks_uses_builtin_toc(fitz_module, tmp_path) -> None:
    result = _parse_with_pymupdf(_pdf_with_bookmarks(fitz_module, tmp_path))

    assert result.metadata.has_table_of_contents is True
    assert result.metadata.structure_source == "builtin_toc"
    assert [s.heading for s in result.sections] == ["Chapter 1", "Section 1.1", "Chapter 2"]
    assert result.sections[1].section_path == "Chapter 1 > Section 1.1"


def test_pdf_without_bookmarks_but_large_heading_is_font_heuristic(
    fitz_module, tmp_path
) -> None:
    doc = fitz_module.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Big Heading", fontsize=24)
    for i in range(12):
        page.insert_text((72, 110 + i * 14), "normal body line of text", fontsize=11)
    path = tmp_path / "headings.pdf"
    doc.save(str(path))
    doc.close()

    result = _parse_with_pymupdf(str(path))

    assert result.metadata.has_table_of_contents is False
    assert result.metadata.structure_source == "font_heuristic"


def test_pdf_flat_text_has_no_structure(fitz_module, tmp_path) -> None:
    doc = fitz_module.open()
    page = doc.new_page()
    for i in range(15):
        page.insert_text((72, 72 + i * 14), "uniform body text line", fontsize=11)
    path = tmp_path / "flat.pdf"
    doc.save(str(path))
    doc.close()

    result = _parse_with_pymupdf(str(path))

    assert result.metadata.has_table_of_contents is False
    assert result.metadata.structure_source == "none"


def test_parse_response_serializes_structure_aliases(fitz_module, tmp_path) -> None:
    result = _parse_with_pymupdf(_pdf_with_bookmarks(fitz_module, tmp_path))

    payload = result.model_dump(by_alias=True)

    assert payload["metadata"]["hasTableOfContents"] is True
    assert payload["metadata"]["structureSource"] == "builtin_toc"
