# DocAudit AI — Milestone 2

Local-first, deterministic technical documentation auditing. Python 3.11 or newer.

## Install and launch

From this directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
streamlit run app.py
```

Open the localhost URL shown by Streamlit. The committed Streamlit configuration binds to 127.0.0.1, disables usage telemetry, and caps uploads at 10 MiB (10 × 1024 × 1024 bytes). Run from the project root so Streamlit loads that configuration. Dependency installation requires internet access; application analysis does not. No cloud services, authentication, database, or inference are included.

## Profiles and rule configuration

Select **Technical guide** (25-word sentence limit), **Academic writing** (40 words), or **Custom style guide** in the UI. Profile changes clear the previous result. Built-in profiles are `config/technical.yaml` and `config/academic.yaml`; custom mode loads `config/style_guide.yaml`. Edit local YAML to tailor rules; configuration uploads and automatic document-type inference are not included.

Built-in profiles exclude References, Bibliography, Works Cited, and References and Bibliography, including nested subheadings. Exclusion matching is case-insensitive, strips leading section numbers, and supports shell-style wildcards. Original section indices and source locations remain intact. Readability metrics cover only included sections; exports show total, analyzed, and excluded section counts.

`terminology` contains literal deprecated terms and replacements. `preferred_terms` supplies canonical names, spelling variants, and optional capitalization enforcement. Preferences are explicit examples, not universal writing rules: for example, technical mode prefers “sign in” over “login,” which may need tailoring for noun usage. Duplicate variants within one preference do not create duplicate findings.

Acronym checks flag the first unrecognized use once per token, preserving that warning if a definition appears later. Supported definitions include **long form (ABC)**, **ABC (long form)**, versioned parentheticals such as **AI RMF 1.0**, connector words in expansions, **ABC: long form**, and adjacent DOCX glossary cells in the same row. Initials must match the expansion. Heading definitions are recognized; undefined acronym warnings are limited to prose, not headings or all-uppercase labels. Built-in allowlists include common technical acronyms and uppercase labels. Numbered control IDs such as AC-1(SI) are skipped.

```yaml
profile: organization-guide
max_sentence_words: 30
excluded_headings: ["References", "Appendix*"]
terminology:
  - term: utilize
    replacement: use
preferred_terms:
  - preferred: DocAudit AI
    variants: [DocAuditAI, Doc Audit AI]
    enforce_case: true
acronyms:
  enabled: true
  allowlist: [AI, API, UI, NIST]
```

## Engine interface

```python
from docaudit import parse_document, load_profile, audit
result = audit(parse_document(b"Utilize the tool.", "guide.txt"),
               load_profile("technical", "config"))
print(result.model_dump_json(indent=2))
```

The engine never imports Streamlit or reads UI state. Pydantic validates configuration and outputs. Findings are deterministically sorted; results contain no timestamps or document body. Finding offsets are zero-based, end-exclusive positions inside a section. TXT sections are nonempty source lines; Markdown sections are prose blocks, headings, list items, and table rows; DOCX sections are paragraphs with heading context. Markdown markup is replaced by spaces to preserve block-relative offsets and original line numbers. Finding locations identify the line where the match starts. Locations are one-based. Configure literal whole words or phrases in `config/style_guide.yaml`; whitespace within phrases is flexible, including wrapped paragraph lines, and matches do not cross sections. Sentence limits flag counts strictly greater than the configured maximum.

## Security and diagnostics

Uploads are processed in memory and never saved or executed. UTF-8 text is strict and rejects binary control characters. DOCX packages are checked for validity, duplicate/unsafe archive entries, encryption, macros, embedded objects, ActiveX, DTD/entity declarations, NUL-containing XML (including UTF-16 XML), and expansion limits (40 MiB, 2,000 entries, 20 nested table levels). Archives are never extracted; external document relationships are not fetched. Application code makes no external network requests. Readability uses shared deterministic sentence spans, textstat lexical checks, and a bundled Pyphen en_GB syllable dictionary with standard Flesch formulas; textstat's downloading syllable functions are never called. Tests disable socket connections.

The UI displays generic errors. Developer logs include only exception category and a parser diagnostic code, never filenames, document text, exception messages, or tracebacks. JSON exports contain locations, full validated configuration, rule messages, and acronym tokens identified in findings; treat exports as potentially sensitive. Uploaded content stays in Streamlit process memory during the browser session. Normal analysis does not persist documents.

## Limitations

English readability scores are heuristics, especially for short text, tables, and technical vocabulary; they do not measure correctness. Empty text returns null readability scores. Sentence splitting handles common abbreviations, initials, decimals, version numbers, URLs, and closing quotation marks, but remains heuristic: ambiguous abbreviations at sentence ends and unusual punctuation can be misclassified. Readability and long-sentence flags use the same sentence boundaries.

Markdown supports ATX and Setext headings, wrapped paragraphs, list markers, block quotes, and pipe-table rows. Fenced/indented code and reference definitions are excluded. Inline code, emphasis delimiters, HTML tags, and inline link destinations are masked; link labels remain readable. It is a conservative extractor, not a full CommonMark parser: complex nested markup, reference links, escaped pipes, and HTML block contents can be imperfect. Table rows are analyzed as prose; any line containing a pipe is treated as a table row. TXT findings remain line-based.

Reports display readability cards and findings with priority, word count, heading context, source location, suggestion, and matched text. Sentence priority is minor up to 20% over the configured limit, review through twice the limit, and high above twice the limit. Terminology defaults to review. These are review priorities, not correctness judgments. Default sorting places high priority first and longer sentences first within each priority; document-order and longest-sentence sorting are also available. Heading grouping, heading/rule/priority filters, and an inspector with surrounding paragraph text support navigation. Paragraph numbers are parser traversal positions including tables, not Word page or paragraph labels. Rule filters affect display only; JSON exports retain all findings. Schema 2.0 records the complete validated configuration, analysis scope, priorities, sentence word counts, and undefined-acronym findings. Older exports can still be read with default values, but lack profile/scope provenance; rerun the original document to obtain accurate metadata. Matched snippets remain in session memory and are never logged or added to the JSON export.

DOCX supports body paragraphs, heading context, and tables including nested tables, in document order. Merged cells are deduplicated. Headers, footers, comments, text boxes, footnotes, tracked-change text, drawings, and layout/page coordinates are not supported. Protected/encrypted Word files, legacy DOC, and macro-enabled DOCM are unsupported. Structural locations are provided, not Word page numbers. Validation reduces risk but is not a malware scanner or an isolated parser sandbox.

## Samples, validation, and next steps

`samples/clean.md`, `samples/problematic.txt`, and `samples/structured.md` demonstrate prose checks. `samples/milestone2-clean.docx` and `samples/milestone2-problematic.docx` exercise profile exclusions, terminology variants, and acronym warnings. Tests use synthetic DOCX fixtures rather than copying private documents into the repository.

Acronym detection is heuristic, limited to uppercase alphabetic tokens of 2–10 letters. It does not fully interpret plurals, dotted acronyms, mixed-case forms, contractions such as geographic abbreviations, arbitrary cross-paragraph definitions, or acronym semantics. Ordinary uppercase words and domain-specific codes can be false positives: review the candidate and customize the profile allowlist. Definitions in excluded sections do not suppress warnings in included prose. A later glossary does not erase a genuine earlier use.

Milestone 2 also checks the two DOCX files in the user's `ebu.ac` directory under both profiles. Result artifacts contain no full paragraphs and source files are unchanged. Structural/count verification confirms parser consistency, not technical accuracy or universal style correctness.

Next: test more representative DOCX documents and tune domain profiles based on reviewed findings. Ollama inference belongs to Milestone 3 and should remain behind a separate engine interface.
