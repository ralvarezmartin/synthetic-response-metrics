"""Pairwise score helpers."""

from __future__ import annotations

from math import ceil
from statistics import median, pstdev


def rounded_mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def rounded_median(values: list[float]) -> float | None:
    return round(median(values), 3) if values else None


def rounded_pstdev(values: list[float]) -> float | None:
    return round(pstdev(values), 3) if len(values) > 1 else (0.0 if values else None)


def nearest_rank_percentile(values: list[float], percentile: float) -> float | None:
    """Return a nearest-rank percentile rounded to three decimals."""

    if not values:
        return None
    if percentile <= 0:
        return round(min(values), 3)
    if percentile >= 100:
        return round(max(values), 3)
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, ceil(percentile / 100 * len(ordered)) - 1))
    return round(ordered[index], 3)
