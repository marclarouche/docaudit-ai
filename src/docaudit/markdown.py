"""Conservative Markdown prose extraction with position-preserving masking.

Masks markup with spaces, preserving block-relative offsets and line breaks.
No HTML rendering, link fetching, or code execution occurs.
"""
import re
from .models import Document, Location, Section


def prose(line: str) -> str:
    def blank(match):
        return " " * len(match.group())
    line = re.sub(r"(`+).*?\1", blank, line)
    # Keep link labels while masking destinations and surrounding punctuation.
    line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)",
                  lambda m: " " * (m.group().index("[") + 1) + m.group(1) + " " * (len(m.group()) - m.group().index("[") - 1 - len(m.group(1))), line)
    line = re.sub(r"<[^>]*>", blank, line)
    line = re.sub(r"\*\*|__|~~|(?<!\w)[*_]|[*_](?!\w)", blank, line)
    return line


def parse_markdown(text: str) -> Document:
    lines = text.splitlines()
    sections = []
    title = "Document"
    heading_stack = []
    pending = []
    start = 1
    fence = None

    def flush():
        nonlocal pending
        if pending:
            value = "\n".join(pending)
            if value.strip():
                sections.append(Section(heading_path=tuple(t for _, t in heading_stack), title=title, text=value, location=Location(line=start)))
            pending = []

    for index, line in enumerate(lines):
        number = index + 1
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence) and not marker.group(2).strip():
                fence = None
            continue
        if marker:
            flush()
            fence = marker.group(1)
            continue
        if not line.strip() or line.startswith("    ") or line.startswith("\t") or re.match(r"^ {0,3}\[[^]]+\]:", line):
            flush()
            continue
        if re.match(r"^ {0,3}(?:[-*_]\s*){3,}$", line) or re.match(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$", line):
            flush()
            continue
        heading = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+\s*)?$", line)
        setext = index + 1 < len(lines) and re.fullmatch(r" {0,3}(?:=+|-+)\s*", lines[index + 1])
        if re.fullmatch(r" {0,3}(?:=+|-+)\s*", line) and index:
            flush()
            continue
        if heading or setext:
            flush()
            title = prose(heading.group(1) if heading else line).strip()
            level = len(re.match(r"^ {0,3}(#+)", line).group(1)) if heading else (1 if lines[index + 1].lstrip().startswith("=") else 2)
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
            value = prose(line)
            if heading:
                a, b = heading.span(1)
                value = " " * a + prose(line[a:b]) + " " * (len(line) - b)
            sections.append(Section(kind="heading", heading_path=tuple(t for _, t in heading_stack), title=title, text=value, location=Location(line=number)))
            continue
        listing = re.match(r"^\s*(?:>\s*)?(?:[-+*]|\d+[.)])\s+", line)
        if listing or "|" in line:
            flush()
            value = prose(line)
            if listing:
                value = " " * listing.end() + value[listing.end():]
            else:
                value = value.replace("|", " ")
            sections.append(Section(kind="list" if listing else "table", heading_path=tuple(t for _, t in heading_stack), title=title, text=value, location=Location(line=number)))
            continue
        value = prose(line)
        quote = re.match(r"^\s*>\s?", value)
        if quote:
            value = " " * quote.end() + value[quote.end():]
        if not pending:
            start = number
        pending.append(value)
    flush()
    return Document(format="md", sections=tuple(sections))
