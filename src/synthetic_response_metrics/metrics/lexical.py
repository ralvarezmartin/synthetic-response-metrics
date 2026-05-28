"""Lexical response-dispersion metrics."""

from __future__ import annotations


def jaccard_similarity(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Compute set-level Jaccard similarity."""

    if not tokens_a and not tokens_b:
        return 1.0
    union = tokens_a | tokens_b
    if not union:
        return 0.0
    return len(tokens_a & tokens_b) / len(union)


def containment_similarity(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Compute asymmetric-overlap tolerant containment similarity."""

    if not tokens_a and not tokens_b:
        return 1.0
    denominator = min(len(tokens_a), len(tokens_b))
    if denominator == 0:
        return 0.0
    return len(tokens_a & tokens_b) / denominator
