"""Tests for structure discovery engine."""

from __future__ import annotations

from unittest.mock import patch

from app.models import ParsedSection
from app.structure_discovery import (
    PageTextCache,
    TocEntry,
    _dedupe_toc_entries,
    _detect_printed_toc_line,
    _needs_part_nesting_fix,
    _normalize_flat_part_entries,
    _prepare_bookmark_entries,
    _score_toc_entries,
    _sections_from_toc_entries,
    _title_on_page,
    _validate_toc_entries,
    discover_pdf_structure,
)


class _FakePage:
    def __init__(self, text: str, links: list[dict[str, object]] | None = None) -> None:
        self._text = text
        self._links = links or []

    def get_text(self, *args: object, **kwargs: object) -> str:
        if args and args[0] == "dict":
            return {"blocks": []}
        return self._text

    def get_links(self) -> list[dict[str, object]]:
        return self._links


class _FakeDoc:
    def __init__(self, pages: list[_FakePage]) -> None:
        self.page_count = len(pages)
        self._pages = pages

    def __getitem__(self, index: int) -> _FakePage:
        return self._pages[index]


class _CountingFakePage:
    def __init__(self, text: str) -> None:
        self._text = text
        self.get_text_calls = 0

    def get_text(self, *args: object, **kwargs: object) -> str:
        self.get_text_calls += 1
        return self._text


class _CountingFakeDoc:
    def __init__(self, pages: list[_CountingFakePage]) -> None:
        self.page_count = len(pages)
        self._pages = pages

    def __getitem__(self, index: int) -> _CountingFakePage:
        return self._pages[index]


class _DiscoveryFakeDoc(_FakeDoc):
    def __init__(self, pages: list[_FakePage], toc: list[list[object]]) -> None:
        super().__init__(pages)
        self._toc = toc

    def get_toc(self, simple: bool = True) -> list[list[object]]:
        return self._toc


def _page_cache(doc: _FakeDoc) -> PageTextCache:
    return PageTextCache.from_document(doc)


def test_parse_printed_toc_line_dot_leaders() -> None:
    parsed = _detect_printed_toc_line(
        "Chapter 1: Introduction to Machine Learning . . . . 5",
        page_count=20,
    )
    assert parsed is not None
    assert parsed[0].startswith("Chapter 1")
    assert parsed[1] == 5


def test_part_nesting_normalization() -> None:
    flat = [
        TocEntry(1, "Part I. Units", 2),
        TocEntry(1, "1. First Chapter", 2),
        TocEntry(1, "Part II. Equations", 4),
        TocEntry(1, "2. Second Chapter", 4),
    ]
    assert _needs_part_nesting_fix(flat) is True
    normalized = _normalize_flat_part_entries(flat)
    assert [entry.level for entry in normalized] == [1, 2, 1, 2]


def test_validate_toc_entries_accepts_in_range_pages() -> None:
    doc = _FakeDoc([_FakePage("Chapter 1 body"), _FakePage("Chapter 2 body")])
    entries = [
        TocEntry(1, "Chapter 1", 1),
        TocEntry(1, "Chapter 2", 2),
    ]
    ok, warnings = _validate_toc_entries(entries, _page_cache(doc))
    assert ok is True
    assert warnings == []


def test_sections_from_toc_assigns_page_range_and_indexable() -> None:
    doc = _FakeDoc([_FakePage("one"), _FakePage("two"), _FakePage("three")])
    sections = _sections_from_toc_entries(
        [TocEntry(1, "Chapter 1", 1), TocEntry(1, "Chapter 2", 2)],
        _page_cache(doc),
    )
    assert sections[0].page_range == [1, 1]
    assert sections[1].page_range == [2, 3]
    assert sections[0].indexable is True
    assert sections[0].node_kind == "chapter"


def test_front_matter_not_indexable() -> None:
    doc = _FakeDoc([_FakePage("Preface text"), _FakePage("Chapter 1")])
    sections = _sections_from_toc_entries(
        [TocEntry(1, "Preface", 1), TocEntry(1, "Chapter 1", 2)],
        _page_cache(doc),
    )
    assert sections[0].node_kind == "front_matter"
    assert sections[0].indexable is False
    assert sections[1].indexable is True


def test_score_builtin_toc_higher_than_thin_outline() -> None:
    doc = _FakeDoc([_FakePage("a"), _FakePage("b")])
    rich = [TocEntry(1, f"Chapter {index}", index) for index in range(1, 6)]
    thin = [TocEntry(1, "A", 1), TocEntry(1, "B", 2)]
    assert _score_toc_entries(rich, doc, source="builtin_toc") > _score_toc_entries(
        thin, doc, source="printed_toc"
    )


def test_prepare_bookmark_entries_applies_part_fix() -> None:
    flat = [
        TocEntry(1, "Part I. Units", 2),
        TocEntry(1, "1. First Chapter", 2),
        TocEntry(1, "Part II. Equations", 4),
        TocEntry(1, "2. Second Chapter", 4),
    ]
    prepared = _prepare_bookmark_entries(flat)
    assert prepared[1].level == 2
    assert prepared[3].level == 2


def test_dedupe_toc_entries_preserves_first_seen_order() -> None:
    entries = [
        TocEntry(1, "Chapter Z", 5),
        TocEntry(1, "Chapter A", 5),
        TocEntry(1, "Chapter M", 5),
    ]
    deduped = _dedupe_toc_entries(entries)
    assert [entry.title for entry in deduped] == ["Chapter Z", "Chapter A", "Chapter M"]


def test_page_text_cache_reuses_prefetched_text() -> None:
    pages = [_CountingFakePage("alpha"), _CountingFakePage("beta")]
    doc = _CountingFakeDoc(pages)
    cache = PageTextCache.from_prefetched(["alpha", "beta"])

    assert cache.get_page_text(0) == "alpha"
    assert cache.get_page_text(1) == "beta"
    assert cache.slice_text_range(0, 1) == "alpha\nbeta"
    assert _title_on_page(cache, 2, "beta") is True
    assert pages[0].get_text_calls == 0
    assert pages[1].get_text_calls == 0

    uncached = PageTextCache.from_document(doc)
    assert uncached.get_page_text(0) == "alpha"
    assert pages[0].get_text_calls == 1


def test_discover_pdf_structure_tries_next_candidate_after_validation_failure() -> None:
    toc_page_text = "\n".join(
        [
            "Table of Contents",
            "Chapter 1 . . . . . 2",
            "Chapter 2 . . . . . 3",
            "Chapter 3 . . . . . 4",
            "Chapter 4 . . . . . 5",
            "Chapter 5 . . . . . 6",
        ]
    )
    pages = [
        _FakePage(toc_page_text),
        _FakePage("Chapter 1 introduction text"),
        _FakePage("Chapter 2 methods text"),
        _FakePage("Chapter 3 results text"),
        _FakePage("Chapter 4 discussion text"),
        _FakePage("Chapter 5 conclusion text"),
    ]
    bad_bookmarks = [
        [1, "Totally Wrong Title A", 2],
        [1, "Totally Wrong Title B", 3],
    ]
    doc = _DiscoveryFakeDoc(pages, bad_bookmarks)
    page_texts = [page.get_text() for page in pages]

    result = discover_pdf_structure(
        doc,
        markdown="# fallback",
        build_markdown_sections=lambda markdown: [],
        page_texts=page_texts,
    )

    assert result.structure_source == "printed_toc"
    assert result.structure_validated is True
    assert result.sections[0].heading.startswith("Chapter 1")


def test_discover_pdf_structure_uses_next_scored_candidate_when_top_fails() -> None:
    doc = _FakeDoc(
        [
            _FakePage("noise only"),
            _FakePage("Chapter 1 printed body"),
            _FakePage("Chapter 2 printed body"),
        ]
    )

    noisy_bookmarks = [TocEntry(1, "Missing title xyz", 1), TocEntry(1, "Also missing", 2)]
    printed_entries = [TocEntry(1, "Chapter 1", 2), TocEntry(1, "Chapter 2", 3)]

    def fake_markdown_sections(_markdown: str) -> list[ParsedSection]:
        return [
            ParsedSection(
                heading="Fallback",
                heading_level=1,
                section_path="Fallback",
                content="fallback",
            )
        ]

    with (
        patch(
            "app.structure_discovery._read_bookmark_entries",
            return_value=noisy_bookmarks,
        ),
        patch(
            "app.structure_discovery._detect_link_toc_entries",
            return_value=[],
        ),
        patch(
            "app.structure_discovery._detect_printed_toc_entries",
            return_value=printed_entries,
        ),
        patch(
            "app.structure_discovery._score_toc_entries",
            side_effect=[0.9, 0.5],
        ),
    ):
        result = discover_pdf_structure(
            doc,
            "markdown",
            build_markdown_sections=fake_markdown_sections,
            page_texts=["noise", "Chapter 1 printed body", "Chapter 2 printed body"],
        )

    assert result.structure_source == "printed_toc"
    assert result.structure_validated is True
    assert [section.heading for section in result.sections] == ["Chapter 1", "Chapter 2"]
