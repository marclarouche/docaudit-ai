"""UI-independent prioritization and source-context helpers."""
from .models import Document, Finding


def sentence_priority(count: int, limit: int) -> str:
    if count > 2 * limit:
        return "high"
    if count <= 1.2 * limit:
        return "minor"
    return "review"


def prioritized_findings(findings):
    rank = {"high": 0, "review": 1, "minor": 2}
    return sorted(findings, key=lambda f: (rank[f.priority], -(f.word_count or 0), f.section_index, f.start, f.rule))


def finding_context(document: Document, finding: Finding) -> dict[str, str]:
    section = document.sections[finding.section_index]
    if finding.end > len(section.text) or finding.start > finding.end:
        raise ValueError("finding_span_out_of_bounds")
    return {"heading": section.title, "matched_text": section.text[finding.start:finding.end],
            "section_text": section.text,
            "location": ", ".join(f"{key} {value}" for key, value in finding.location.model_dump().items() if value is not None),
            "characters": f"{finding.start}–{finding.end} (zero-based, end-exclusive)"}
