"""Deterministic English sentence spans with common technical exceptions."""
import re

ABBREVIATIONS = {"e.g.", "i.e.", "dr.", "mr.", "mrs.", "ms.", "prof.", "vs.", "fig.", "no.", "approx."}


def sentence_spans(text: str):
    """Yield trimmed (start, end) spans; offsets reference the input text."""
    start = 0
    for match in re.finditer(r'[.!?]+["\u201d\u2019\')\]]*(?=\s|$)', text):
        end = match.end()
        punctuation = match.start()
        token = text[max(0, punctuation - 100):punctuation + 1].split()[-1].lower()
        if match.group().startswith(".") and (token in ABBREVIATIONS or re.fullmatch(r"(?:[a-z]\.)+", token)):
            continue
        a = start
        while a < end and text[a].isspace():
            a += 1
        if a < end:
            yield a, end
        start = end
    while start < len(text) and text[start].isspace():
        start += 1
    if start < len(text):
        yield start, len(text.rstrip())
