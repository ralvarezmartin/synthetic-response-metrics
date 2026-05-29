"""Core public API for response-convergence metrics."""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

from synthetic_response_metrics.metrics.diversity import (
    coefficient_of_variation,
    distinct_n,
    token_entropy,
)
from synthetic_response_metrics.metrics.lexical import (
    containment_similarity,
    jaccard_similarity,
)
from synthetic_response_metrics.metrics.pairwise import (
    nearest_rank_percentile,
    rounded_mean,
    rounded_median,
    rounded_pstdev,
)
from synthetic_response_metrics.normalization import normalize_token_list, token_list_to_set
from synthetic_response_metrics.validation import validate_config


SCHEMA_VERSION = "0.2"


@dataclass(frozen=True)
class ResponseRecord:
    """Canonical platform-independent response record."""

    question_id: str
    agent_id: str
    text: str
    run_id: str | None = None
    model: str | None = None
    temperature: float | None = None
    population_id: str | None = None
    timestamp: str | int | float | None = None


@dataclass(frozen=True)
class DispersionConfig:
    """Configuration for response-convergence monitoring."""

    threshold_max_similarity: float = 0.70
    min_answers: int = 2
    language: str = "auto"
    stopwords: set[str] | None = None
    min_token_length: int = 3
    duplicate_policy: str = "latest"
    include_pairs: bool = False
    top_pairs_limit: int = 5

    def __post_init__(self) -> None:
        validate_config(self)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "threshold_max_similarity": float(self.threshold_max_similarity),
            "min_answers": int(self.min_answers),
            "language": self.language,
            "min_token_length": int(self.min_token_length),
            "duplicate_policy": self.duplicate_policy,
            "include_pairs": bool(self.include_pairs),
            "top_pairs_limit": int(self.top_pairs_limit),
        }
        if self.stopwords is not None:
            payload["stopwords_count"] = len(self.stopwords)
        return payload


@dataclass(frozen=True)
class QuestionDispersion:
    """Per-question dispersion payload."""

    answers_count: int
    raw_answers_count: int
    excluded_empty_after_normalization: int
    pairs_count: int
    status: str
    alert: bool
    unique_agents_count: int = 0
    duplicate_records_count: int = 0
    missing_text_count: int = 0
    avg_jaccard_similarity: float | None = None
    max_jaccard_similarity: float | None = None
    min_jaccard_similarity: float | None = None
    median_jaccard_similarity: float | None = None
    p90_jaccard_similarity: float | None = None
    std_jaccard_similarity: float | None = None
    max_containment_similarity: float | None = None
    lexical_unique_ratio: float | None = None
    distinct_1: float | None = None
    distinct_2: float | None = None
    token_entropy: float | None = None
    mean_response_tokens: float | None = None
    response_length_cv: float | None = None
    exact_duplicate_count: int | None = None
    exact_duplicate_ratio: float | None = None
    top_similar_pairs: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "answers_count": self.answers_count,
            "raw_answers_count": self.raw_answers_count,
            "excluded_empty_after_normalization": self.excluded_empty_after_normalization,
            "pairs_count": self.pairs_count,
            "status": self.status,
            "alert": self.alert,
            "unique_agents_count": self.unique_agents_count,
            "duplicate_records_count": self.duplicate_records_count,
            "missing_text_count": self.missing_text_count,
        }
        optional_values = {
            "avg_jaccard_similarity": self.avg_jaccard_similarity,
            "max_jaccard_similarity": self.max_jaccard_similarity,
            "min_jaccard_similarity": self.min_jaccard_similarity,
            "median_jaccard_similarity": self.median_jaccard_similarity,
            "p90_jaccard_similarity": self.p90_jaccard_similarity,
            "std_jaccard_similarity": self.std_jaccard_similarity,
            "max_containment_similarity": self.max_containment_similarity,
            "lexical_unique_ratio": self.lexical_unique_ratio,
            "distinct_1": self.distinct_1,
            "distinct_2": self.distinct_2,
            "token_entropy": self.token_entropy,
            "mean_response_tokens": self.mean_response_tokens,
            "response_length_cv": self.response_length_cv,
            "exact_duplicate_count": self.exact_duplicate_count,
            "exact_duplicate_ratio": self.exact_duplicate_ratio,
            "top_similar_pairs": self.top_similar_pairs,
        }
        for key, value in optional_values.items():
            if value is not None:
                payload[key] = value
        return payload


@dataclass(frozen=True)
class DispersionResult:
    """Full response-dispersion result."""

    summary: dict[str, Any]
    by_question: OrderedDict[str, QuestionDispersion] = field(default_factory=OrderedDict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "by_question": OrderedDict(
                (question, row.to_dict()) for question, row in self.by_question.items()
            ),
        }


@dataclass(frozen=True)
class _AnswerItem:
    agent_id: str
    text: str
    record_index: int


def _question_order(records: list[ResponseRecord]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for record in records:
        question = str(record.question_id or "").strip()
        if question and question not in seen:
            seen.add(question)
            ordered.append(question)
    return ordered


def _round(value: float | None) -> float | None:
    return round(value, 3) if value is not None else None


def _empty_question_row(
    *,
    valid_answers_count: int,
    raw_answers_count: int,
    excluded: int,
    unique_agents_count: int,
    duplicate_records_count: int,
    missing_text_count: int,
) -> QuestionDispersion:
    return QuestionDispersion(
        answers_count=valid_answers_count,
        raw_answers_count=raw_answers_count,
        excluded_empty_after_normalization=excluded,
        pairs_count=0,
        status="insufficient_data",
        alert=False,
        unique_agents_count=unique_agents_count,
        duplicate_records_count=duplicate_records_count,
        missing_text_count=missing_text_count,
    )


def compute_dispersion(
    records: list[ResponseRecord],
    config: DispersionConfig | None = None,
) -> DispersionResult:
    """Compute lexical response-dispersion and data-quality metrics."""

    started = time.perf_counter()
    cfg = config or DispersionConfig()
    questions = _question_order(records)
    answers_by_question: OrderedDict[str, OrderedDict[str, _AnswerItem]] = OrderedDict(
        (question, OrderedDict()) for question in questions
    )
    raw_counts: dict[str, int] = {question: 0 for question in questions}
    missing_text_counts: dict[str, int] = {question: 0 for question in questions}
    duplicate_counts: dict[str, int] = {question: 0 for question in questions}
    missing_question_id_count = 0
    missing_agent_id_count = 0

    for record_index, record in enumerate(records):
        question = str(record.question_id or "").strip()
        if not question:
            missing_question_id_count += 1
            continue
        answers_by_question.setdefault(question, OrderedDict())
        raw_counts.setdefault(question, 0)
        missing_text_counts.setdefault(question, 0)
        duplicate_counts.setdefault(question, 0)

        agent = str(record.agent_id or "").strip()
        if not agent:
            missing_agent_id_count += 1
            continue

        text = str(record.text or "").strip()
        raw_counts[question] += 1
        if not text:
            missing_text_counts[question] += 1

        bucket = answers_by_question[question]
        item = _AnswerItem(agent_id=agent, text=text, record_index=record_index)
        duplicate_key = agent
        if cfg.duplicate_policy == "keep_all":
            bucket[f"{agent}#{record_index}"] = item
            continue
        if duplicate_key in bucket:
            duplicate_counts[question] += 1
            if cfg.duplicate_policy == "error":
                raise ValueError(
                    f"Duplicate response for question_id={question!r} and agent_id={agent!r}"
                )
            if cfg.duplicate_policy == "first":
                continue
        bucket[duplicate_key] = item

    by_question: OrderedDict[str, QuestionDispersion] = OrderedDict()
    evaluated = 0
    alerted = 0
    avg_values: list[float] = []
    max_values: list[float] = []
    min_values: list[float] = []
    median_values: list[float] = []
    lexical_values: list[float] = []
    distinct_2_values: list[float] = []
    entropy_values: list[float] = []
    containment_values: list[float] = []

    for question, answers in answers_by_question.items():
        answer_items = list(answers.values())
        raw_answers_count = raw_counts.get(question, len(answer_items))
        duplicate_records_count = duplicate_counts.get(question, 0)
        missing_text_count = missing_text_counts.get(question, 0)
        unique_agents_count = len({item.agent_id for item in answer_items})
        normalized_items: list[tuple[_AnswerItem, list[str], set[str]]] = []
        excluded = 0

        for item in answer_items:
            token_list = normalize_token_list(
                item.text,
                language=cfg.language,
                stopwords=cfg.stopwords,
                min_token_length=cfg.min_token_length,
            )
            if not token_list:
                excluded += 1
                continue
            normalized_items.append((item, token_list, token_list_to_set(token_list)))

        valid_answers_count = len(normalized_items)
        if valid_answers_count < cfg.min_answers:
            by_question[question] = _empty_question_row(
                valid_answers_count=valid_answers_count,
                raw_answers_count=raw_answers_count,
                excluded=excluded,
                unique_agents_count=unique_agents_count,
                duplicate_records_count=duplicate_records_count,
                missing_text_count=missing_text_count,
            )
            continue

        evaluated += 1
        pair_rows: list[dict[str, Any]] = []
        pair_scores: list[float] = []
        containment_scores: list[float] = []
        exact_duplicate_count = 0
        for (item_a, tokens_a, set_a), (item_b, tokens_b, set_b) in combinations(
            normalized_items, 2
        ):
            jaccard = jaccard_similarity(set_a, set_b)
            containment = containment_similarity(set_a, set_b)
            shared_token_count = len(set_a & set_b)
            pair_scores.append(jaccard)
            containment_scores.append(containment)
            if tokens_a == tokens_b:
                exact_duplicate_count += 1
            pair_rows.append(
                {
                    "agent_id_a": item_a.agent_id,
                    "agent_id_b": item_b.agent_id,
                    "record_index_a": item_a.record_index,
                    "record_index_b": item_b.record_index,
                    "jaccard_similarity": round(jaccard, 3),
                    "containment_similarity": round(containment, 3),
                    "shared_token_count": shared_token_count,
                }
            )

        avg_sim = rounded_mean(pair_scores) or 0.0
        max_sim = round(max(pair_scores), 3) if pair_scores else 0.0
        min_sim = round(min(pair_scores), 3) if pair_scores else 0.0
        median_sim = rounded_median(pair_scores) or 0.0
        p90_sim = nearest_rank_percentile(pair_scores, 90) or 0.0
        std_sim = rounded_pstdev(pair_scores) or 0.0
        max_containment = round(max(containment_scores), 3) if containment_scores else 0.0
        all_tokens = [token for _, tokens, _ in normalized_items for token in tokens]
        token_lists = [tokens for _, tokens, _ in normalized_items]
        lengths = [len(tokens) for tokens in token_lists]
        unique_ratio = round(distinct_n(token_lists, 1), 3)
        distinct_bigram_ratio = round(distinct_n(token_lists, 2), 3)
        entropy = round(token_entropy(all_tokens), 3)
        mean_tokens = round(sum(lengths) / len(lengths), 3) if lengths else 0.0
        length_cv = round(coefficient_of_variation(lengths), 3)
        exact_duplicate_ratio = round(exact_duplicate_count / len(pair_scores), 3)
        alert = max_sim >= cfg.threshold_max_similarity

        if alert:
            alerted += 1
        avg_values.append(avg_sim)
        max_values.append(max_sim)
        min_values.append(min_sim)
        median_values.append(median_sim)
        lexical_values.append(unique_ratio)
        distinct_2_values.append(distinct_bigram_ratio)
        entropy_values.append(entropy)
        containment_values.append(max_containment)

        top_similar_pairs = None
        if cfg.include_pairs and cfg.top_pairs_limit > 0:
            top_similar_pairs = sorted(
                pair_rows,
                key=lambda row: (
                    row["jaccard_similarity"],
                    row["containment_similarity"],
                ),
                reverse=True,
            )[: cfg.top_pairs_limit]

        by_question[question] = QuestionDispersion(
            answers_count=valid_answers_count,
            raw_answers_count=raw_answers_count,
            excluded_empty_after_normalization=excluded,
            pairs_count=len(pair_scores),
            status="ok",
            alert=alert,
            unique_agents_count=unique_agents_count,
            duplicate_records_count=duplicate_records_count,
            missing_text_count=missing_text_count,
            avg_jaccard_similarity=avg_sim,
            max_jaccard_similarity=max_sim,
            min_jaccard_similarity=min_sim,
            median_jaccard_similarity=median_sim,
            p90_jaccard_similarity=p90_sim,
            std_jaccard_similarity=std_sim,
            max_containment_similarity=max_containment,
            lexical_unique_ratio=unique_ratio,
            distinct_1=unique_ratio,
            distinct_2=distinct_bigram_ratio,
            token_entropy=entropy,
            mean_response_tokens=mean_tokens,
            response_length_cv=length_cv,
            exact_duplicate_count=exact_duplicate_count,
            exact_duplicate_ratio=exact_duplicate_ratio,
            top_similar_pairs=top_similar_pairs,
        )

    runtime_ms = int((time.perf_counter() - started) * 1000)
    total_duplicate_records = sum(duplicate_counts.values())
    total_missing_text = sum(missing_text_counts.values())
    summary = {
        "schema_version": SCHEMA_VERSION,
        "config": cfg.to_dict(),
        "threshold_max_similarity": float(cfg.threshold_max_similarity),
        "min_answers_per_question": int(cfg.min_answers),
        "questions_total": len(answers_by_question),
        "questions_evaluated": evaluated,
        "questions_alerted": alerted,
        "records_total": len(records),
        "missing_question_id_count": missing_question_id_count,
        "missing_agent_id_count": missing_agent_id_count,
        "missing_text_count": total_missing_text,
        "duplicate_records_count": total_duplicate_records,
        "overall_avg_similarity": rounded_mean(avg_values),
        "overall_max_similarity": _round(max(max_values)) if max_values else None,
        "overall_min_similarity": _round(min(min_values)) if min_values else None,
        "overall_avg_median_similarity": rounded_mean(median_values),
        "overall_avg_lexical_unique_ratio": rounded_mean(lexical_values),
        "overall_avg_distinct_2": rounded_mean(distinct_2_values),
        "overall_avg_token_entropy": rounded_mean(entropy_values),
        "overall_max_containment_similarity": (
            _round(max(containment_values)) if containment_values else None
        ),
        "convergence_alert": alerted > 0,
        "runtime_ms": runtime_ms,
    }
    return DispersionResult(summary=summary, by_question=by_question)
