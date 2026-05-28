from synthetic_response_metrics import DispersionConfig, ResponseRecord, compute_dispersion
from synthetic_response_metrics.normalization import normalize_token_list


def test_duplicate_responses_have_max_similarity_one():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text="useful affordable service"),
        ResponseRecord(question_id="q1", agent_id="a2", text="useful affordable service"),
    ]

    result = compute_dispersion(records).to_dict()

    assert result["by_question"]["q1"]["max_jaccard_similarity"] == 1.0
    assert result["summary"]["convergence_alert"] is True


def test_empty_normalized_responses_are_excluded():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text="the and for"),
        ResponseRecord(question_id="q1", agent_id="a2", text="!!!"),
        ResponseRecord(question_id="q1", agent_id="a3", text="alpha beta"),
    ]

    result = compute_dispersion(records).to_dict()
    q1 = result["by_question"]["q1"]

    assert q1["status"] == "insufficient_data"
    assert q1["answers_count"] == 1
    assert q1["raw_answers_count"] == 3
    assert q1["excluded_empty_after_normalization"] == 2


def test_lexical_unique_ratio_uses_global_token_ratio():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text="alpha beta beta"),
        ResponseRecord(question_id="q1", agent_id="a2", text="alpha gamma"),
    ]

    result = compute_dispersion(records).to_dict()

    assert result["by_question"]["q1"]["avg_jaccard_similarity"] == 0.333
    assert result["by_question"]["q1"]["lexical_unique_ratio"] == 0.6
    assert result["summary"]["overall_avg_lexical_unique_ratio"] == 0.6


def test_alert_logic_depends_on_max_jaccard_similarity():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text="alpha beta"),
        ResponseRecord(question_id="q1", agent_id="a2", text="alpha beta gamma"),
        ResponseRecord(question_id="q1", agent_id="a3", text="delta epsilon"),
    ]

    result = compute_dispersion(
        records,
        DispersionConfig(threshold_max_similarity=0.66),
    ).to_dict()

    assert result["by_question"]["q1"]["avg_jaccard_similarity"] == 0.222
    assert result["by_question"]["q1"]["max_jaccard_similarity"] == 0.667
    assert result["by_question"]["q1"]["alert"] is True
    assert result["summary"]["questions_alerted"] == 1


def test_empty_text_records_are_counted_as_raw_and_excluded():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text=""),
        ResponseRecord(question_id="q1", agent_id="a2", text="alpha beta"),
    ]

    result = compute_dispersion(records).to_dict()
    q1 = result["by_question"]["q1"]

    assert q1["status"] == "insufficient_data"
    assert q1["raw_answers_count"] == 2
    assert q1["answers_count"] == 1
    assert q1["excluded_empty_after_normalization"] == 1
    assert q1["missing_text_count"] == 1
    assert result["summary"]["missing_text_count"] == 1


def test_duplicate_records_are_counted_with_latest_policy():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text="alpha beta"),
        ResponseRecord(question_id="q1", agent_id="a1", text="gamma delta"),
        ResponseRecord(question_id="q1", agent_id="a2", text="alpha beta"),
    ]

    result = compute_dispersion(records).to_dict()
    q1 = result["by_question"]["q1"]

    assert q1["raw_answers_count"] == 3
    assert q1["answers_count"] == 2
    assert q1["duplicate_records_count"] == 1
    assert result["summary"]["duplicate_records_count"] == 1
    assert q1["max_jaccard_similarity"] == 0.0


def test_duplicate_error_policy_raises():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text="alpha beta"),
        ResponseRecord(question_id="q1", agent_id="a1", text="gamma delta"),
    ]

    try:
        compute_dispersion(records, DispersionConfig(duplicate_policy="error"))
    except ValueError as exc:
        assert "Duplicate response" in str(exc)
    else:
        raise AssertionError("expected duplicate policy to raise")


def test_include_pairs_adds_top_similar_pairs():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text="alpha beta"),
        ResponseRecord(question_id="q1", agent_id="a2", text="alpha beta"),
        ResponseRecord(question_id="q1", agent_id="a3", text="gamma delta"),
    ]

    result = compute_dispersion(records, DispersionConfig(include_pairs=True)).to_dict()
    q1 = result["by_question"]["q1"]

    assert q1["exact_duplicate_count"] == 1
    assert q1["exact_duplicate_ratio"] == 0.333
    assert q1["top_similar_pairs"][0]["jaccard_similarity"] == 1.0
    assert {q1["top_similar_pairs"][0]["agent_id_a"], q1["top_similar_pairs"][0]["agent_id_b"]} == {
        "a1",
        "a2",
    }


def test_config_validation_rejects_invalid_values():
    invalid_kwargs = [
        {"threshold_max_similarity": 1.1},
        {"min_answers": 1},
        {"min_token_length": 0},
        {"language": "fr"},
        {"duplicate_policy": "unknown"},
        {"top_pairs_limit": -1},
    ]

    for kwargs in invalid_kwargs:
        try:
            DispersionConfig(**kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected invalid config to fail: {kwargs}")


def test_unicode_normalization_preserves_accents():
    tokens = normalize_token_list("acción útil español naive über café año")

    assert tokens == ["acción", "útil", "español", "naive", "über", "café", "año"]


def test_additional_lexical_metrics_are_reported():
    records = [
        ResponseRecord(question_id="q1", agent_id="a1", text="alpha beta beta"),
        ResponseRecord(question_id="q1", agent_id="a2", text="alpha beta gamma"),
        ResponseRecord(question_id="q1", agent_id="a3", text="delta epsilon"),
    ]

    q1 = compute_dispersion(records).to_dict()["by_question"]["q1"]

    assert "median_jaccard_similarity" in q1
    assert "p90_jaccard_similarity" in q1
    assert "std_jaccard_similarity" in q1
    assert "distinct_1" in q1
    assert "distinct_2" in q1
    assert "token_entropy" in q1
    assert "max_containment_similarity" in q1
