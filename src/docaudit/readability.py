"""English readability with offline Pyphen syllable counting."""
import re
from textstat.textstat import textstatistics as Textstat
from pyphen import Pyphen
from .models import Document, Finding, ReadabilityMetrics
from .sentences import sentence_spans
from .reporting import sentence_priority

WORD = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)

def word_count(text: str) -> int:
    return len(WORD.findall(text))

def calculate_readability(document: Document) -> ReadabilityMetrics:
    text = "\n".join(section.text for section in document.sections)
    count = word_count(text)
    if not count:
        return ReadabilityMetrics(word_count=0, flesch_reading_ease=None, flesch_kincaid_grade=None)
    # Never call textstat's syllable metrics: they can download NLTK data.
    # Pyphen loads its packaged English dictionary entirely from disk.
    dictionary = Pyphen(lang="en_GB")
    syllables = sum(len(dictionary.positions(word)) + 1 for word in WORD.findall(text))
    calculator = Textstat()
    sentences = max(1, sum(1 for section in document.sections for a, b in sentence_spans(section.text) if calculator.lexicon_count(section.text[a:b], removepunct=True)))
    ease = 206.835 - 1.015 * count / sentences - 84.6 * syllables / count
    grade = 0.39 * count / sentences + 11.8 * syllables / count - 15.59
    return ReadabilityMetrics(word_count=count, flesch_reading_ease=round(ease, 2),
                              flesch_kincaid_grade=round(grade, 2))

def long_sentence_findings(document: Document, maximum: int) -> list[Finding]:
    findings = []
    for index, section in enumerate(document.sections):
        for start, end in sentence_spans(section.text):
            count = word_count(section.text[start:end])
            if count > maximum:
                findings.append(Finding(rule="long_sentence", priority=sentence_priority(count, maximum), word_count=count, word_limit=maximum, message=f"Sentence has {count} words; limit is {maximum}.",
                    section_index=index, location=section.location_at(start), start=start, end=end))
    return findings
