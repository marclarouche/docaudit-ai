"""Validated engine inputs and serializable audit outputs."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

class Location(Schema):
    line: int | None = Field(default=None, ge=1)
    paragraph: int | None = Field(default=None, ge=1)
    table: int | None = Field(default=None, ge=1)
    row: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)

class Section(Schema):
    kind: Literal["paragraph", "heading", "list", "table"] = "paragraph"
    heading_path: tuple[str, ...] = ()
    title: str = "Document"
    text: str
    location: Location = Field(default_factory=Location)

    def location_at(self, offset: int) -> Location:
        if self.location.line is None:
            return self.location
        return self.location.model_copy(update={"line": self.location.line + self.text[:offset].count("\n")})

class Document(Schema):
    format: Literal["txt", "md", "docx"]
    sections: tuple[Section, ...]

class TerminologyRule(Schema):
    term: str = Field(min_length=1, max_length=200)
    replacement: str = Field(min_length=1, max_length=200)
    case_sensitive: bool = False

    @field_validator("term", "replacement")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("rule_text_must_not_be_blank")
        return value.strip()

class PreferredTerm(Schema):
    preferred: str = Field(min_length=1, max_length=200)
    variants: tuple[str, ...] = Field(default=(), max_length=100)
    enforce_case: bool = True

    @field_validator("preferred")
    @classmethod
    def nonblank_preferred(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("preferred_term_must_not_be_blank")
        return value.strip()

    @field_validator("variants")
    @classmethod
    def nonblank_variants(cls, values):
        if any(not v.strip() or len(v) > 200 for v in values):
            raise ValueError("invalid_term_variant")
        return tuple(v.strip() for v in values)

class AcronymConfig(Schema):
    enabled: bool = False
    allowlist: tuple[str, ...] = Field(default=(), max_length=1000)

    @field_validator("allowlist")
    @classmethod
    def valid_tokens(cls, values):
        import re
        if any(not re.fullmatch(r"[A-Z][A-Z0-9]{1,9}(?:-[A-Z0-9]+)*", value) for value in values):
            raise ValueError("invalid_acronym_allowlist")
        return values

class AuditConfig(Schema):
    profile: str = Field(default="custom", min_length=1, max_length=100)
    excluded_headings: tuple[str, ...] = Field(default=(), max_length=100)
    preferred_terms: tuple[PreferredTerm, ...] = Field(default=(), max_length=1000)
    acronyms: AcronymConfig = Field(default_factory=AcronymConfig)

    @field_validator("excluded_headings")
    @classmethod
    def valid_headings(cls, values):
        if any(not v.strip() or len(v) > 200 for v in values):
            raise ValueError("invalid_excluded_heading")
        return tuple(v.strip() for v in values)

    max_sentence_words: int = Field(default=25, ge=1, le=1000)
    terminology: tuple[TerminologyRule, ...] = Field(default=(), max_length=1000)

class Finding(Schema):
    rule: Literal["terminology", "long_sentence", "undefined_acronym"]
    severity: Literal["warning"] = "warning"
    message: str
    priority: Literal["minor", "review", "high"] = "review"
    word_count: int | None = Field(default=None, ge=0)
    word_limit: int | None = Field(default=None, ge=1)
    section_index: int = Field(ge=0)
    location: Location
    start: int = Field(ge=0)
    end: int = Field(ge=0)

class ReadabilityMetrics(Schema):
    word_count: int = Field(ge=0)
    flesch_reading_ease: float | None
    flesch_kincaid_grade: float | None

class AuditResult(Schema):
    schema_version: str = "2.0"
    document_format: Literal["txt", "md", "docx"]
    section_count: int
    analyzed_section_count: int = 0
    excluded_section_count: int = 0
    configuration: AuditConfig = Field(default_factory=AuditConfig)
    metrics: ReadabilityMetrics
    findings: tuple[Finding, ...]
