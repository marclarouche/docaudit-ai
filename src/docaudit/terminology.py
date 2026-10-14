"""Literal whole-word/phrase matching with section-relative offsets."""
import re
from .models import AuditConfig, Document, Finding

def terminology_findings(document: Document, config: AuditConfig) -> list[Finding]:
    findings = []
    for rule in config.terminology:
        pieces = rule.term.split()
        if not pieces:
            continue
        pattern = re.compile(r"(?<!\w)" + r"\s+".join(re.escape(p) for p in pieces) + r"(?!\w)",
                             0 if rule.case_sensitive else re.IGNORECASE)
        for index, section in enumerate(document.sections):
            for match in pattern.finditer(section.text):
                findings.append(Finding(rule="terminology", message=f"Prefer '{rule.replacement}' to '{rule.term}'.",
                    section_index=index, location=section.location_at(match.start()), start=match.start(), end=match.end()))
    return findings


def preferred_term_findings(document: Document, config: AuditConfig) -> list[Finding]:
    findings = []
    seen = set()
    for rule in config.preferred_terms:
        terms = list(rule.variants) + ([rule.preferred] if rule.enforce_case else [])
        for term in terms:
            pattern = re.compile(r"(?<!\w)" + r"\s+".join(re.escape(piece) for piece in term.split()) + r"(?!\w)", re.IGNORECASE)
            for index, section in enumerate(document.sections):
                for match in pattern.finditer(section.text):
                    canonical = " ".join(match.group().split())
                    if canonical == rule.preferred or (not rule.enforce_case and canonical.casefold() == rule.preferred.casefold()):
                        continue
                    key = (index, match.start(), match.end(), rule.preferred)
                    if key in seen:
                        continue
                    seen.add(key)
                    findings.append(Finding(rule="terminology", message=f"Use the preferred term '{rule.preferred}' consistently.",
                                            section_index=index, location=section.location_at(match.start()), start=match.start(), end=match.end()))
    return findings
