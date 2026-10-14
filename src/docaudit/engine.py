"""Public deterministic audit interface; no UI, persistence, or network."""
from .models import AuditConfig, AuditResult, Document
from .readability import calculate_readability, long_sentence_findings
from .terminology import terminology_findings, preferred_term_findings
from .acronyms import acronym_findings
from .profiles import is_excluded


def audit(document: Document, config: AuditConfig) -> AuditResult:
    if not isinstance(document, Document) or not isinstance(config, AuditConfig):
        raise TypeError("audit_requires_validated_models")
    indices = [index for index, section in enumerate(document.sections) if not is_excluded(section, config)]
    active = Document(format=document.format, sections=tuple(document.sections[i] for i in indices))
    findings = (terminology_findings(active, config) + preferred_term_findings(active, config)
                + long_sentence_findings(active, config.max_sentence_words) + acronym_findings(active, config))
    findings = [f.model_copy(update={"section_index": indices[f.section_index]}) for f in findings]
    findings.sort(key=lambda item: (item.section_index, item.start, item.end, item.rule, item.message))
    return AuditResult(document_format=document.format, section_count=len(document.sections),
                       analyzed_section_count=len(indices), excluded_section_count=len(document.sections)-len(indices),
                       configuration=config, metrics=calculate_readability(active), findings=tuple(findings))
