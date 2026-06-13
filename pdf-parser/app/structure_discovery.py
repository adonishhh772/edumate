"""Multi-signal PDF structure discovery for textbook TOC + page mapping.

Detectors (priority order after validation):
  1. PDF bookmark outline (fitz.get_toc)
  2. Internal links on Contents pages
  3. Printed Contents pages (dot leaders + trailing page numbers)
  4. Font/markdown headings (fallback — not TOC-grounded)

All detectors normalize into ParsedSection rows with page_range, node_kind, and indexable.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Literal, Protocol

from app.models import ParsedSection, StructureSource

logger = logging.getLogger(__name__)

SECTION_PATH_SEP = " > "

_PART_HEADING_PATTERN = re.compile(r"^Part\s+[IVXLC\d]+", re.IGNORECASE)
_NUMBERED_UNIT_HEADING_PATTERN = re.compile(r"^\d+\.\s+")
_CHAPTER_HEADING_PATTERN = re.compile(
    r"^(?:chapter|ch\.?)\s*\d+\b",
    re.IGNORECASE,
)
_FRONT_MATTER_PATTERN = re.compile(
    r"^(?:table of contents|contents|summary|outline|preface|foreword|"
    r"acknowledg(?:e)?ments?|dedication|copyright|about (?:the )?(?:book|author)|"
    r"accessibility statement|for students)",
    re.IGNORECASE,
)
_APPENDIX_PATTERN = re.compile(r"^appendix\b", re.IGNORECASE)
_TOC_PAGE_HINT_PATTERN = re.compile(
    r"(?:table of contents|^contents$|summary of contents)",
    re.IGNORECASE | re.MULTILINE,
)
_TOC_LINE_DOT_PATTERN = re.compile(r"^(.+?)\s+(?:\.\s*){2,}(\d+)\s*$")
_TOC_LINE_TRAIL_PATTERN = re.compile(r"^(.+?)[\s\.]{3,}(\d+)\s*$")

NodeKind = Literal["front_matter", "part", "chapter", "section", "appendix", "other"]

MIN_TOC_ENTRIES = 2
MAX_TOC_SCAN_PAGES = 20
MIN_PRINTED_TOC_LINES = 5
VALIDATION_TITLE_MATCH_RATIO = 0.5
LINK_TITLE_Y_TOLERANCE = 8.0


class PdfPage(Protocol):
    def get_text(self, *args: object, **kwargs: object) -> str: ...

    def get_links(self) -> list[dict[str, object]]: ...


class PdfDocument(Protocol):
    page_count: int

    def __getitem__(self, index: int) -> PdfPage: ...


@dataclass
class TocEntry:
    level: int
    title: str
    page: int


@dataclass
class StructureDiscoveryResult:
    sections: list[ParsedSection]
    structure_source: StructureSource
    has_table_of_contents: bool
    structure_validated: bool
    structure_warnings: list[str] = field(default_factory=list)
    book_profile: str = "unstructured"


@dataclass
class _Candidate:
    source: StructureSource
    entries: list[TocEntry]
    profile: str
    score: float


@dataclass
class PageTextCache:
    """Per-page text cache to avoid repeated get_text() on validation and section build."""

    page_count: int
    _text_by_page: dict[int, str] = field(default_factory=dict)
    _doc: PdfDocument | None = None

    @classmethod
    def from_prefetched(cls, page_texts: list[str]) -> PageTextCache:
        return cls(
            page_count=len(page_texts),
            _text_by_page={index: text for index, text in enumerate(page_texts)},
        )

    @classmethod
    def from_document(cls, doc: PdfDocument) -> PageTextCache:
        return cls(page_count=doc.page_count, _doc=doc)

    def get_page_text(self, page_index: int) -> str:
        cached = self._text_by_page.get(page_index)
        if cached is not None:
            return cached
        if self._doc is None or page_index < 0 or page_index >= self.page_count:
            return ""
        text = self._doc[page_index].get_text()
        self._text_by_page[page_index] = text
        return text

    def slice_text_range(self, start_page: int, end_page: int) -> str:
        last = min(end_page, self.page_count - 1)
        parts = [
            self.get_page_text(page_num)
            for page_num in range(max(start_page, 0), last + 1)
        ]
        return "\n".join(parts).strip()


def discover_pdf_structure(
    doc: PdfDocument,
    markdown: str,
    *,
    build_markdown_sections: object,
    page_texts: list[str] | None = None,
) -> StructureDiscoveryResult:
    """Pick the best validated structure for a PDF and materialize ParsedSection rows."""
    page_cache = (
        PageTextCache.from_prefetched(page_texts)
        if page_texts is not None
        else PageTextCache.from_document(doc)
    )
    candidates: list[_Candidate] = []

    bookmark_entries = _read_bookmark_entries(doc)
    if bookmark_entries:
        normalized = _prepare_bookmark_entries(bookmark_entries)
        score = _score_toc_entries(normalized, doc, source="builtin_toc")
        candidates.append(
            _Candidate("builtin_toc", normalized, "bookmark_nested", score)
        )

    link_entries = _detect_link_toc_entries(doc, page_cache)
    if link_entries:
        score = _score_toc_entries(link_entries, doc, source="link_toc")
        candidates.append(_Candidate("link_toc", link_entries, "link_toc", score))

    printed_entries = _detect_printed_toc_entries(doc, page_cache)
    if printed_entries:
        score = _score_toc_entries(printed_entries, doc, source="printed_toc")
        candidates.append(
            _Candidate("printed_toc", printed_entries, "printed_dot_leader", score)
        )

    for candidate in _ranked_candidates(candidates):
        if candidate.score < _min_accept_score(candidate.source):
            continue
        validated, warnings = _validate_toc_entries(candidate.entries, page_cache)
        if validated:
            sections = _sections_from_toc_entries(candidate.entries, page_cache)
            return StructureDiscoveryResult(
                sections=sections,
                structure_source=candidate.source,
                has_table_of_contents=True,
                structure_validated=True,
                structure_warnings=warnings,
                book_profile=candidate.profile,
            )
        logger.info(
            "[StructureDiscovery] %s failed validation (%d warnings) — trying next candidate",
            candidate.source,
            len(warnings),
        )

    markdown_sections: list[ParsedSection] = build_markdown_sections(markdown)
    if _has_real_structure(markdown_sections):
        for section in markdown_sections:
            section.node_kind = _classify_node_kind(section.heading)
            section.indexable = _is_indexable(section.node_kind, "font_heuristic")
        return StructureDiscoveryResult(
            sections=markdown_sections,
            structure_source="font_heuristic",
            has_table_of_contents=False,
            structure_validated=False,
            structure_warnings=["structure_fallback_font_heuristic"],
            book_profile="heading_only",
        )

    return StructureDiscoveryResult(
        sections=markdown_sections,
        structure_source="none",
        has_table_of_contents=False,
        structure_validated=False,
        structure_warnings=["no_structure_detected"],
        book_profile="unstructured",
    )


def _read_bookmark_entries(doc: PdfDocument) -> list[TocEntry]:
    get_toc = getattr(doc, "get_toc", None)
    if get_toc is None:
        return []
    try:
        raw = get_toc(simple=True)
    except Exception:
        return []
    entries: list[TocEntry] = []
    for row in raw:
        if len(row) < 3:
            continue
        title = str(row[1]).strip()
        if not title:
            continue
        try:
            page = int(row[2])
        except (TypeError, ValueError):
            continue
        level = min(max(int(row[0]), 1), 6)
        entries.append(TocEntry(level=level, title=title, page=page))
    if len(entries) < MIN_TOC_ENTRIES:
        return []
    return entries


def _prepare_bookmark_entries(entries: list[TocEntry]) -> list[TocEntry]:
    if not _needs_part_nesting_fix(entries):
        return entries
    logger.info("[StructureDiscovery] Normalizing flat Part/numbered-unit bookmark levels")
    return _normalize_flat_part_entries(entries)


def _needs_part_nesting_fix(entries: list[TocEntry]) -> bool:
    part_count = 0
    inside_part = False
    numbered_after_part = 0
    flat_numbered_after_part = 0

    for entry in entries:
        if _is_part_heading(entry.title):
            part_count += 1
            inside_part = True
            continue
        if inside_part and _is_numbered_unit_heading(entry.title):
            numbered_after_part += 1
            if entry.level <= 1:
                flat_numbered_after_part += 1

    return part_count >= 2 and numbered_after_part >= 2 and flat_numbered_after_part >= 2


def _normalize_flat_part_entries(entries: list[TocEntry]) -> list[TocEntry]:
    normalized: list[TocEntry] = []
    inside_part = False
    for entry in entries:
        if _is_part_heading(entry.title):
            new_level = 1
            inside_part = True
        elif inside_part and _is_numbered_unit_heading(entry.title):
            new_level = 2
        else:
            new_level = 1
            inside_part = False
        normalized.append(TocEntry(level=new_level, title=entry.title, page=entry.page))
    return normalized


def _detect_link_toc_entries(
    doc: PdfDocument,
    page_cache: PageTextCache,
) -> list[TocEntry]:
    entries: list[TocEntry] = []
    for page_index in range(min(doc.page_count, MAX_TOC_SCAN_PAGES)):
        page_text = page_cache.get_page_text(page_index)
        if not _TOC_PAGE_HINT_PATTERN.search(page_text):
            continue
        page = doc[page_index]
        line_positions = _page_lines_by_vertical_position(page)
        for link in page.get_links():
            kind = link.get("kind")
            page_num = link.get("page")
            if kind is None or page_num is None:
                continue
            if int(kind) != 1:  # fitz.LINK_GOTO
                continue
            target_page = int(page_num) + 1
            title = _title_for_link_rect(line_positions, link.get("from"), page_text)
            if not title or len(title) < 3:
                continue
            entries.append(TocEntry(level=1, title=title, page=target_page))
    return _dedupe_toc_entries(entries)


def _page_lines_by_vertical_position(page: PdfPage) -> list[tuple[float, str]]:
    try:
        blocks = page.get_text("dict")["blocks"]
    except Exception:
        return []

    lines: list[tuple[float, str]] = []
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans_text = "".join(
                str(span.get("text", "")) for span in line.get("spans", [])
            )
            stripped = spans_text.strip()
            if not stripped:
                continue
            bbox = line.get("bbox")
            if not isinstance(bbox, (list, tuple)) or len(bbox) < 2:
                continue
            lines.append((float(bbox[1]), stripped))
    lines.sort(key=lambda item: item[0])
    return lines


def _title_for_link_rect(
    line_positions: list[tuple[float, str]],
    rect: object,
    page_text: str,
) -> str:
    if rect is None:
        return ""

    if line_positions:
        try:
            rect_values = list(rect) if isinstance(rect, (list, tuple)) else []
            if len(rect_values) >= 4:
                link_y = (float(rect_values[1]) + float(rect_values[3])) / 2.0
                nearest_line = min(
                    line_positions,
                    key=lambda item: abs(item[0] - link_y),
                )
                if abs(nearest_line[0] - link_y) <= LINK_TITLE_Y_TOLERANCE:
                    return nearest_line[1]
        except (TypeError, ValueError):
            pass

    stripped_lines = [line.strip() for line in page_text.split("\n") if line.strip()]
    return stripped_lines[0] if stripped_lines else ""


def _detect_printed_toc_entries(
    doc: PdfDocument,
    page_cache: PageTextCache,
) -> list[TocEntry]:
    entries: list[TocEntry] = []
    for page_index in range(min(doc.page_count, MAX_TOC_SCAN_PAGES)):
        page_text = page_cache.get_page_text(page_index)
        if not _TOC_PAGE_HINT_PATTERN.search(page_text) and not _looks_like_toc_page(
            page_text
        ):
            continue
        for line in page_text.split("\n"):
            parsed = _parse_printed_toc_line(line, doc.page_count)
            if parsed is not None:
                entries.append(TocEntry(level=1, title=parsed[0], page=parsed[1]))
    entries = _dedupe_toc_entries(entries)
    if len(entries) < MIN_PRINTED_TOC_LINES:
        return []
    return entries


def _looks_like_toc_page(page_text: str) -> bool:
    matched_lines = 0
    for line in page_text.split("\n"):
        if _parse_printed_toc_line(line, 10_000) is not None:
            matched_lines += 1
    return matched_lines >= MIN_PRINTED_TOC_LINES


def _detect_printed_toc_line(line: str, page_count: int) -> tuple[str, int] | None:
    """Parse a single printed TOC line (exported for unit tests)."""
    return _parse_printed_toc_line(line, page_count)


def _parse_printed_toc_line(line: str, page_count: int) -> tuple[str, int] | None:
    stripped = line.strip()
    if len(stripped) < 4:
        return None
    if _FRONT_MATTER_PATTERN.match(stripped) and "chapter" not in stripped.lower():
        return None
    match = _TOC_LINE_DOT_PATTERN.match(stripped) or _TOC_LINE_TRAIL_PATTERN.match(
        stripped
    )
    if not match:
        return None
    title = re.sub(r"\s*\.\s*$", "", match.group(1).strip())
    title = re.sub(r"\s+\.\s+(\s*\.\s*)+", " ", title).strip()
    if len(title) < 3:
        return None
    try:
        page = int(match.group(2))
    except ValueError:
        return None
    if page < 1 or page > page_count:
        return None
    return title, page


def _dedupe_toc_entries(entries: list[TocEntry]) -> list[TocEntry]:
    seen: set[tuple[str, int]] = set()
    unique: list[TocEntry] = []
    for entry in entries:
        key = (entry.title.lower(), entry.page)
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def _ranked_candidates(candidates: list[_Candidate]) -> list[_Candidate]:
    return sorted(candidates, key=lambda item: item.score, reverse=True)


def _min_accept_score(source: StructureSource) -> float:
    if source == "builtin_toc":
        return 0.45
    if source in ("link_toc", "printed_toc"):
        return 0.35
    return 1.0


def _score_toc_entries(
    entries: list[TocEntry],
    doc: PdfDocument,
    *,
    source: StructureSource,
) -> float:
    if len(entries) < MIN_TOC_ENTRIES:
        return 0.0
    score = 0.2
    score += min(len(entries) / 40.0, 0.25)

    valid_pages = sum(1 for entry in entries if 1 <= entry.page <= doc.page_count)
    score += (valid_pages / len(entries)) * 0.25

    monotonic = 0
    prev = 0
    for entry in entries:
        if entry.page >= prev:
            monotonic += 1
        prev = entry.page
    score += (monotonic / len(entries)) * 0.15

    if source == "builtin_toc":
        score += 0.15

    return min(score, 1.0)


def _validate_toc_entries(
    entries: list[TocEntry],
    page_cache: PageTextCache,
) -> tuple[bool, list[str]]:
    warnings: list[str] = []
    if len(entries) < MIN_TOC_ENTRIES:
        warnings.append("too_few_toc_entries")
        return False, warnings

    invalid_pages = [
        entry for entry in entries if entry.page < 1 or entry.page > page_cache.page_count
    ]
    if invalid_pages:
        warnings.append(f"invalid_page_refs:{len(invalid_pages)}")

    title_checks = 0
    title_matches = 0
    for entry in entries[: min(len(entries), 30)]:
        title_checks += 1
        if _title_on_page(page_cache, entry.page, entry.title):
            title_matches += 1
    if title_checks > 0:
        ratio = title_matches / title_checks
        if ratio < VALIDATION_TITLE_MATCH_RATIO:
            warnings.append(f"low_title_page_match:{ratio:.2f}")
    else:
        ratio = 0.0

    if invalid_pages:
        return False, warnings
    if title_checks > 0 and ratio < VALIDATION_TITLE_MATCH_RATIO:
        return False, warnings
    return True, warnings


def _title_on_page(page_cache: PageTextCache, page_number: int, title: str) -> bool:
    if page_number < 1 or page_number > page_cache.page_count:
        return False
    page_text = page_cache.get_page_text(page_number - 1).lower()
    probe = re.sub(r"\s+", " ", title.lower()).strip()
    if len(probe) < 4:
        return True
    short_probe = probe[: min(len(probe), 24)]
    return short_probe in page_text


def _sections_from_toc_entries(
    entries: list[TocEntry],
    page_cache: PageTextCache,
) -> list[ParsedSection]:
    sections: list[ParsedSection] = []
    stack: list[str] = []
    page_count = page_cache.page_count

    for idx, entry in enumerate(entries):
        level = min(max(entry.level, 1), 6)
        stack = stack[: level - 1]
        stack.append(entry.title)
        section_path = SECTION_PATH_SEP.join(stack)

        next_page = entries[idx + 1].page if idx + 1 < len(entries) else page_count + 1
        content = page_cache.slice_text_range(entry.page - 1, next_page - 2)
        node_kind = _classify_node_kind(entry.title)
        indexable = _is_indexable(node_kind, "builtin_toc")

        sections.append(
            ParsedSection(
                heading=entry.title,
                heading_level=level,
                section_path=section_path,
                content=content,
                content_type=_detect_content_type(content) if content else "paragraph",
                page_range=[entry.page, max(entry.page, next_page - 1)],
                node_kind=node_kind,
                indexable=indexable,
            )
        )
    return sections


def _classify_node_kind(title: str) -> NodeKind:
    stripped = title.strip()
    if _FRONT_MATTER_PATTERN.match(stripped):
        return "front_matter"
    if _APPENDIX_PATTERN.match(stripped):
        return "appendix"
    if _is_part_heading(stripped):
        return "part"
    if _CHAPTER_HEADING_PATTERN.match(stripped) or _is_numbered_unit_heading(stripped):
        return "chapter"
    return "section"


def _is_indexable(node_kind: NodeKind, source: StructureSource) -> bool:
    if source in ("builtin_toc", "link_toc", "printed_toc"):
        return node_kind in ("part", "chapter", "section", "appendix")
    return node_kind != "front_matter"


def _is_part_heading(title: str) -> bool:
    return bool(_PART_HEADING_PATTERN.match(title.strip()))


def _is_numbered_unit_heading(title: str) -> bool:
    return bool(_NUMBERED_UNIT_HEADING_PATTERN.match(title.strip()))


def _detect_content_type(content: str) -> Literal["paragraph", "table", "list", "mixed"]:
    stripped = content.strip()
    if stripped.startswith("|") and "|" in stripped[1:]:
        return "table"
    if re.search(r"^[-*+]\s|^\d+\.\s", stripped, re.MULTILINE):
        return "list"
    return "paragraph"


def _has_real_structure(sections: list[ParsedSection]) -> bool:
    return not (len(sections) == 1 and sections[0].heading == "Document")
