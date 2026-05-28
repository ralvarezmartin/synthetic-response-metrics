"""Input/output helpers for response-convergence metrics."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from synthetic_response_metrics.core import ResponseRecord


def _first(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return None


def record_from_mapping(payload: dict[str, Any]) -> ResponseRecord:
    """Build a canonical response record from a loose mapping."""

    return ResponseRecord(
        run_id=_first(payload, "run_id", "runId"),
        question_id=str(_first(payload, "question_id", "questionId", "question") or ""),
        agent_id=str(_first(payload, "agent_id", "agentId", "persona_id", "personaId") or ""),
        text=str(_first(payload, "text", "content", "answer", "response") or ""),
        model=_first(payload, "model"),
        temperature=_coerce_float(_first(payload, "temperature")),
        population_id=_first(payload, "population_id", "populationId"),
        timestamp=_first(payload, "timestamp"),
    )


def _coerce_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _records_from_interaction_export(payload: dict[str, Any]) -> list[ResponseRecord]:
    interactions = payload.get("interactions")
    if not isinstance(interactions, list):
        return []

    current_question_by_agent: dict[str, str] = {}
    current_global_question: str | None = None
    records: list[ResponseRecord] = []
    run_id = payload.get("run_id") or payload.get("runId")

    for message in interactions:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        agent_id = _first(
            message,
            "agent_id",
            "agentId",
            "participant_id",
            "participantId",
            "persona_id",
            "personaId",
        )
        content = str(message.get("content") or "").strip()
        if not content:
            continue
        if role == "interviewer":
            if agent_id:
                current_question_by_agent[str(agent_id)] = content
            else:
                current_global_question = content
            continue
        if role not in ("agent", "participant", "respondent", "persona") or not agent_id:
            continue
        if message.get("message_type") not in (None, "assistant"):
            continue
        if message.get("reasoning") is True:
            continue
        question = current_question_by_agent.get(str(agent_id)) or current_global_question
        if not question:
            continue
        records.append(
            ResponseRecord(
                run_id=run_id,
                question_id=question,
                agent_id=str(agent_id),
                text=content,
                timestamp=message.get("timestamp"),
                population_id=message.get("populationId") or message.get("population_id"),
            )
        )

    return records


def load_records(path: str | Path) -> list[ResponseRecord]:
    """Load response records from CSV, JSON, or JSONL."""

    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            return [record_from_mapping(row) for row in csv.DictReader(handle)]
    if suffix == ".jsonl":
        records: list[ResponseRecord] = []
        with source.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(record_from_mapping(json.loads(line)))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at line {line_number}: {exc.msg}") from exc
        return records
    if suffix == ".json":
        with source.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            return [record_from_mapping(item) for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("records", "responses", "data"):
                items = payload.get(key)
                if isinstance(items, list):
                    return [record_from_mapping(item) for item in items if isinstance(item, dict)]
            records = _records_from_interaction_export(payload)
            if records:
                return records
        raise ValueError(f"Unsupported JSON response schema in {source}")
    raise ValueError(f"Unsupported input format: {source.suffix}")


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
