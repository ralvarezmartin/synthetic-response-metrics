"""Validation helpers for public configuration."""

from __future__ import annotations

from typing import Any


SUPPORTED_LANGUAGES = {"auto", "en", "es"}
DUPLICATE_POLICIES = {"latest", "first", "error", "keep_all"}


def validate_config(config: Any) -> None:
    """Validate a DispersionConfig-like object."""

    threshold = float(config.threshold_max_similarity)
    if threshold < 0.0 or threshold > 1.0:
        raise ValueError("threshold_max_similarity must be between 0 and 1")

    if int(config.min_answers) < 2:
        raise ValueError("min_answers must be >= 2 for pairwise metrics")

    if int(config.min_token_length) < 1:
        raise ValueError("min_token_length must be >= 1")

    if str(config.language) not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise ValueError(f"language must be one of: {supported}")

    if str(config.duplicate_policy) not in DUPLICATE_POLICIES:
        supported = ", ".join(sorted(DUPLICATE_POLICIES))
        raise ValueError(f"duplicate_policy must be one of: {supported}")

    if int(config.top_pairs_limit) < 0:
        raise ValueError("top_pairs_limit must be >= 0")
