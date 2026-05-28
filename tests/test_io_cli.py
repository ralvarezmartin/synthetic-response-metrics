import json
from pathlib import Path
from uuid import uuid4

from synthetic_response_metrics.cli import main
from synthetic_response_metrics.io import load_records


def _runtime_path(name: str) -> Path:
    runtime_dir = Path(__file__).parent / "_runtime"
    runtime_dir.mkdir(exist_ok=True)
    return runtime_dir / f"{uuid4().hex}_{name}"


def test_csv_and_json_inputs_produce_same_result():
    csv_path = _runtime_path("responses.csv")
    json_path = _runtime_path("responses.json")

    csv_path.write_text(
        "question_id,agent_id,text\n"
        "q1,a1,alpha beta\n"
        "q1,a2,alpha beta gamma\n",
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            [
                {"question_id": "q1", "agent_id": "a1", "text": "alpha beta"},
                {"question_id": "q1", "agent_id": "a2", "text": "alpha beta gamma"},
            ]
        ),
        encoding="utf-8",
    )

    csv_records = load_records(csv_path)
    json_records = load_records(json_path)

    assert csv_records == json_records


def test_cli_output_contains_summary_and_by_question():
    input_path = _runtime_path("responses.json")
    output_path = _runtime_path("result.json")
    input_path.write_text(
        json.dumps(
            [
                {"question_id": "q1", "agent_id": "a1", "text": "alpha beta"},
                {"question_id": "q1", "agent_id": "a2", "text": "alpha beta"},
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["compute", str(input_path), "--output", str(output_path)])
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "summary" in payload
    assert "by_question" in payload
    assert payload["summary"]["convergence_alert"] is True
    assert payload["summary"]["schema_version"] == "0.2"


def test_loads_interactions_export():
    path = _runtime_path("interactions.json")
    path.write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "interactions": [
                    {
                        "role": "interviewer",
                        "agentId": "a1",
                        "content": "Q1",
                        "timestamp": 1,
                    },
                    {
                        "role": "agent",
                        "agentId": "a1",
                        "content": "alpha beta",
                        "timestamp": 2,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    records = load_records(path)

    assert len(records) == 1
    assert records[0].run_id == "run-1"
    assert records[0].question_id == "Q1"
    assert records[0].agent_id == "a1"


def test_loads_global_interviewer_question():
    path = _runtime_path("interactions.json")
    path.write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "interactions": [
                    {"role": "interviewer", "content": "Global Q1", "timestamp": 1},
                    {
                        "role": "agent",
                        "agentId": "a1",
                        "content": "alpha beta",
                        "message_type": "assistant",
                        "timestamp": 2,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    records = load_records(path)

    assert len(records) == 1
    assert records[0].question_id == "Global Q1"


def test_jsonl_error_reports_line_number():
    path = _runtime_path("responses.jsonl")
    path.write_text(
        '{"question_id":"q1","agent_id":"a1","text":"alpha"}\n'
        '{"question_id": bad json}\n',
        encoding="utf-8",
    )

    try:
        load_records(path)
    except ValueError as exc:
        assert "line 2" in str(exc)
    else:
        raise AssertionError("expected JSONL parse error")


def test_cli_returns_clean_error_for_invalid_config(capsys):
    input_path = _runtime_path("responses.json")
    input_path.write_text(
        json.dumps(
            [
                {"question_id": "q1", "agent_id": "a1", "text": "alpha beta"},
                {"question_id": "q1", "agent_id": "a2", "text": "alpha beta"},
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["compute", str(input_path), "--threshold", "2"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "threshold_max_similarity" in captured.err
