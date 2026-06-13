from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

NodeKind = Literal["front_matter", "part", "chapter", "section", "appendix", "other"]

StructureSource = Literal[
    "builtin_toc",
    "printed_toc",
    "link_toc",
    "numbered_headings",
    "markup_headings",
    "font_heuristic",
    "none",
]


class ParsedSection(BaseModel):
    """Single structured section from a parsed document."""
    model_config = ConfigDict(populate_by_name=True)

    heading: str
    heading_level: int = Field(ge=1, le=6, alias="headingLevel", serialization_alias="headingLevel")
    section_path: str = Field(..., alias="sectionPath", serialization_alias="sectionPath")
    content: str
    content_type: Literal["paragraph", "table", "list", "mixed"] = Field(
        "paragraph", alias="contentType", serialization_alias="contentType"
    )
    page_range: list[int] | None = Field(None, alias="pageRange", serialization_alias="pageRange")
    node_kind: NodeKind | None = Field(None, alias="nodeKind", serialization_alias="nodeKind")
    indexable: bool = Field(True, alias="indexable", serialization_alias="indexable")
    children: list["ParsedSection"] = Field(default_factory=list)


class DocumentMetadata(BaseModel):
    """Metadata extracted from the document."""
    model_config = ConfigDict(populate_by_name=True)

    title: str | None = None
    author: str | None = None
    page_count: int | None = Field(None, alias="pageCount", serialization_alias="pageCount")
    has_tables: bool = Field(False, alias="hasTables", serialization_alias="hasTables")
    has_figures: bool = Field(False, alias="hasFigures", serialization_alias="hasFigures")
    has_table_of_contents: bool = Field(
        False, alias="hasTableOfContents", serialization_alias="hasTableOfContents"
    )
    structure_source: StructureSource = Field(
        "none", alias="structureSource", serialization_alias="structureSource"
    )
    structure_validated: bool = Field(
        False, alias="structureValidated", serialization_alias="structureValidated"
    )
    structure_warnings: list[str] = Field(
        default_factory=list, alias="structureWarnings", serialization_alias="structureWarnings"
    )
    book_profile: str | None = Field(None, alias="bookProfile", serialization_alias="bookProfile")


class ParseResponse(BaseModel):
    """Response from POST /parse."""
    model_config = ConfigDict(populate_by_name=True)

    markdown: str
    sections: list[ParsedSection]
    metadata: DocumentMetadata
    parse_mode: str = Field("structured", alias="parseMode", serialization_alias="parseMode")
