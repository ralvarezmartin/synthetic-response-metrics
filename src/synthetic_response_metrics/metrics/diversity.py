"""Token diversity metrics for response sets."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from statistics import mean, pstdev


def distinct_n(token_lists: Sequence[Sequence[str]], n: int) -> float:
    """Return unique n-grams divided by total n-grams."""

    if n < 1:
        raise ValueError("n must be >= 1")
    total = 0
    unique: set[tuple[str, ...]] = set()
    for tokens in token_lists:
        if len(tokens) < n:
            continue
        for idx in range(len(tokens) - n + 1):
            total += 1
            unique.add(tuple(tokens[idx : idx + n]))
    return len(unique) / total if total else 0.0


def token_entropy(tokens: Sequence[str]) -> float:
    """Return Shannon entropy over normalized tokens."""

    if not tokens:
        return 0.0
    counts = Counter(tokens)
    total = len(tokens)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def coefficient_of_variation(values: Sequence[int | float]) -> float:
    """Return population standard deviation divided by mean."""

    if not values:
        return 0.0
    avg = mean(values)
    if avg == 0:
        return 0.0
    return pstdev(values) / avg
