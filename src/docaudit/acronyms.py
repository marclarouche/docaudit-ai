"""Conservative first-use acronym checks; no inference or external data."""
import re
from .models import Document, AuditConfig, Finding

TOKEN = re.compile(r"(?<![\w-])[A-Z]{2,10}(?![\w-])")
EXPANSION_WORD = re.compile(r"[A-Za-z]+")
CONNECTORS = {"a", "an", "and", "of", "the", "for", "to", "in", "on", "or", "with"}


def expansion_matches(expansion: str, acronym: str) -> bool:
    words = EXPANSION_WORD.findall(expansion)
    if len(words) < 2:
        return False
    target = acronym.replace("-", "")
    if not target.isalpha():
        return False
    initials = "".join(w[0].upper() for w in words)
    important = "".join(w[0].upper() for w in words if w.lower() not in CONNECTORS)
    return target in {initials, important}


def defined_here(text: str, start: int, end: int, acronym: str) -> bool:
    # Long form (ABC): test suffixes of up to 12 preceding words.
    opening = re.search(r"\((?:[A-Z]{2,10}\s+)*$", text[max(0, start - 60):start])
    closing = re.match(r"(?:\s+[A-Z]{2,10})*(?:\s+\d+(?:\.\d+)*)?\)", text[end:end + 60])
    if opening and closing:
        parenthesis = max(0, start - 60) + opening.start()
        prefix = re.split(r"[.!?;:\n]", text[max(0, parenthesis - 300):parenthesis])[-1]
        words = EXPANSION_WORD.findall(prefix)
        if any(expansion_matches(" ".join(words[-n:]), acronym) for n in range(2, min(12, len(words)) + 1)):
            return True
    # ABC (long form).
    after = re.match(r"\s*\(([^()\n]{2,300})\)", text[end: end + 305])
    if after and expansion_matches(after.group(1), acronym):
        return True
    # Two-column glossary-style text, kept intentionally conservative.
    before = start > 300 or bool(text[:start].strip())
    after = text[end:end + 301].strip()
    if not before and len(text) - end <= 300:
        expansion = re.sub(r"^(?:[:=]|[–—-])\s*", "", after)
        if expansion_matches(expansion, acronym):
            return True
    return False


def acronym_findings(document: Document, config: AuditConfig) -> list[Finding]:
    if not config.acronyms.enabled:
        return []
    known = set(config.acronyms.allowlist)
    reported = set()
    findings = []
    for index, section in enumerate(document.sections):
        token_cell = TOKEN.fullmatch(section.text.strip())
        if token_cell and section.location.table is not None and index + 1 < len(document.sections):
            following = document.sections[index + 1]
            if (following.location.table == section.location.table and following.location.row == section.location.row
                    and following.location.column != section.location.column
                    and len(following.text) <= 300 and expansion_matches(following.text, token_cell.group())):
                known.add(token_cell.group())
        tokens = list(TOKEN.finditer(section.text))
        skip_reports = section.kind == "heading" or (tokens and not any(c.islower() for c in section.text))
        for match in tokens:
            token = match.group()
            if defined_here(section.text, match.start(), match.end(), token):
                known.add(token)
                continue
            if skip_reports or re.search(r"[A-Z]+-\d+\($", section.text[max(0, match.start()-30):match.start()]):
                continue
            if token in known or token in reported:
                continue
            findings.append(Finding(rule="undefined_acronym", message=f"Define '{token}' at or before its first use, or add it to the profile allowlist.",
                                    section_index=index, location=section.location_at(match.start()), start=match.start(), end=match.end()))
            reported.add(token)
    return findings
