"""Deterministic text normalization for lightweight lexical metrics."""

from __future__ import annotations

import re
from collections.abc import Iterable


ENGLISH_STOPWORDS = {
    "would",
    "this",
    "that",
    "with",
    "from",
    "your",
    "their",
    "about",
    "into",
    "very",
    "have",
    "has",
    "will",
    "just",
    "they",
    "them",
    "you",
    "the",
    "and",
    "for",
}

SPANISH_STOPWORDS = {
    "que",
    "para",
    "con",
    "una",
    "este",
    "esta",
    "como",
    "del",
    "las",
    "los",
    "por",
    "sin",
    "muy",
    "entre",
    "sobre",
    "sus",
    "tiene",
    "tener",
    "ser",
    "estoy",
    "esto",
}

DEFAULT_STOPWORDS = ENGLISH_STOPWORDS | SPANISH_STOPWORDS
STOPWORDS_BY_LANGUAGE = {
    "auto": DEFAULT_STOPWORDS,
    "en": ENGLISH_STOPWORDS,
    "es": SPANISH_STOPWORDS,
}


_TOKEN_CLEANUP_RE = re.compile(r"[^0-9A-Za-zÀ-ÿ ]+", re.UNICODE)


def resolve_stopwords(
    *,
    language: str = "auto",
    stopwords: Iterable[str] | None = None,
) -> set[str]:
    """Resolve and normalize stopwords for the requested language."""

    if stopwords is not None:
        return {str(word).casefold() for word in stopwords}
    return set(STOPWORDS_BY_LANGUAGE.get(language, DEFAULT_STOPWORDS))


def normalize_token_list(
    text: str,
    *,
    language: str = "auto",
    stopwords: Iterable[str] | None = None,
    min_token_length: int = 3,
) -> list[str]:
    """Return normalized lexical tokens for response-dispersion metrics."""

    configured_stopwords = resolve_stopwords(language=language, stopwords=stopwords)
    cleaned = _TOKEN_CLEANUP_RE.sub(" ", (text or "").casefold())
    return [
        token
        for token in cleaned.split()
        if len(token) >= min_token_length and token not in configured_stopwords
    ]


def token_list_to_set(tokens: Iterable[str]) -> set[str]:
    """Convert normalized tokens into a set for Jaccard similarity."""

    return set(tokens)
