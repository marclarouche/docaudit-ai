"""Thin local UI; analysis lives exclusively in docaudit."""
import logging
from pathlib import Path
import streamlit as st
from docaudit import audit, load_config, parse_document, load_profile
from docaudit.reporting import prioritized_findings, finding_context

logger = logging.getLogger("docaudit.ui")
st.set_page_config(page_title="DocAudit AI", layout="wide")
def clear_result():
    st.session_state.pop("audit_result", None)
    st.session_state.pop("audit_document", None)

st.title("DocAudit AI — Milestone 2")
st.caption("Local deterministic documentation checks. English readability; no AI inference.")
profile_choice = st.radio("Document profile", ["Technical guide", "Academic writing", "Custom style guide"], horizontal=True, on_change=clear_result)
st.caption("Technical: 25-word sentence limit. Academic: 40 words. Built-in profiles exclude reference headings and check terminology and acronym definitions.")
upload = st.file_uploader("Upload TXT, Markdown, or DOCX (maximum 10 MB)", type=["txt", "md", "docx"], on_change=clear_result)
if st.button("Analyze", disabled=upload is None):
    st.session_state.pop("audit_result", None)
    st.session_state.pop("audit_document", None)
    try:
        document = parse_document(upload.getvalue(), upload.name)
        configuration = (load_config(Path(__file__).parent / "config/style_guide.yaml") if profile_choice == "Custom style guide" else
                         load_profile("technical" if profile_choice == "Technical guide" else "academic", Path(__file__).parent / "config"))
        st.session_state.audit_result = audit(document, configuration)
        st.session_state.audit_document = document
    except Exception as error:
        # Exception messages and tracebacks may contain untrusted text; never log them.
        code = str(error) if type(error).__name__ == "DocumentError" else "analysis_failed"
        logger.error("Audit failed: category=%s code=%s", type(error).__name__, code)
        st.error("Unable to analyze this file. Check its format and size, then try again.")
result = st.session_state.get("audit_result")
if result is not None:
    st.caption(f"Profile: {result.configuration.profile} · sentence limit: {result.configuration.max_sentence_words} · analyzed sections: {result.analyzed_section_count} · excluded sections: {result.excluded_section_count}")
    metrics = result.metrics
    columns = st.columns(4)
    columns[0].metric("Words", metrics.word_count)
    columns[1].metric("Reading ease", metrics.flesch_reading_ease if metrics.flesch_reading_ease is not None else "N/A")
    columns[2].metric("Grade level", metrics.flesch_kincaid_grade if metrics.flesch_kincaid_grade is not None else "N/A")
    columns[3].metric("Findings", len(result.findings))
    st.caption("English readability estimates; higher reading ease generally means easier prose.")
    if result.findings:
        selected = st.selectbox("Show findings", ["All", "Terminology", "Long sentences", "Undefined acronyms"])
        rule = {"Terminology": "terminology", "Long sentences": "long_sentence", "Undefined acronyms": "undefined_acronym"}.get(selected)
        visible = [finding for finding in result.findings if rule is None or finding.rule == rule]
        document = st.session_state.get("audit_document")
        priorities = st.multiselect("Priority", ["high", "review", "minor"], default=["high", "review", "minor"])
        visible = [finding for finding in visible if finding.priority in priorities]
        st.caption("High: more than twice the sentence limit. Minor: up to 20% over. Review: other overruns, terminology, or undefined acronyms. These are review priorities, not correctness judgments.")
        headings = list(dict.fromkeys(document.sections[f.section_index].title for f in visible)) if document else []
        selected_heading = st.selectbox("Section heading", ["All sections"] + headings)
        if document and selected_heading != "All sections":
            visible = [f for f in visible if document.sections[f.section_index].title == selected_heading]
        ordering = st.radio("Sort findings", ["Priority", "Longest sentence", "Document order"], horizontal=True)
        if ordering == "Priority":
            visible = prioritized_findings(visible)
        elif ordering == "Longest sentence":
            visible = sorted(visible, key=lambda f: (-(f.word_count or 0), f.section_index, f.start))
        grouped = st.checkbox("Group by section heading", value=True)
        rows = []
        for finding in visible:
            context = finding_context(document, finding) if document else {}
            rows.append({"Priority": finding.priority.title(), "Words": finding.word_count,
                         "Limit": finding.word_limit, "Rule": finding.rule.replace("_", " ").title(),
                         "Section": context.get("heading", str(finding.section_index + 1)),
                         "Location": context.get("location", ""), "Suggestion": finding.message,
                         "Matched text": context.get("matched_text", "")})
        if grouped:
            for heading in dict.fromkeys(row["Section"] for row in rows):
                section_rows = [row for row in rows if row["Section"] == heading]
                # Render untrusted headings as plain text, never HTML or Markdown.
                st.text(f"{heading} — {len(section_rows)} findings")
                st.dataframe(section_rows, hide_index=True, width="stretch")
        elif rows:
            st.dataframe(rows, hide_index=True, width="stretch")
        if visible and document:
            chosen = st.selectbox("Inspect finding", range(len(visible)),
                                  format_func=lambda i: f"{i + 1}. {visible[i].priority.title()} · {visible[i].rule.replace('_', ' ')} · {visible[i].word_count or 'term'}")
            context = finding_context(document, visible[chosen])
            st.text(f"{context['heading']} | {context['location']} | Characters {context['characters']}")
            st.text(context["matched_text"])
            with st.expander("Surrounding paragraph or source block"):
                st.text(context["section_text"])
        elif not visible:
            st.info("No findings match the selected filters.")
        st.caption(f"Showing {len(visible)} of {len(result.findings)} findings. JSON exports always include all findings, with priority and word counts, and exclude document text.")
    else:
        st.success("No configured rule violations found.")
    st.download_button("Export JSON", result.model_dump_json(indent=2), "docaudit-result.json", "application/json")
