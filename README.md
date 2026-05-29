# Synthetic Response Metrics

Lightweight response-convergence metrics for LLM-based synthetic populations.

This package provides a small, platform-independent implementation of
lexical response-dispersion metrics for generated agent responses:

- average pairwise Jaccard similarity;
- maximum pairwise Jaccard similarity;
- median, p90, standard deviation, and minimum Jaccard similarity;
- containment similarity for subset-like answers;
- lexical unique ratio, `distinct_1`, `distinct_2`, and token entropy;
- exact duplicate counts and optional top similar pair diagnostics;
- conservative convergence alerts based on maximum similarity;
- data-quality counters for missing text, missing ids, and duplicate records.

The package does not depend on any specific agent-orchestration framework,
embedding model, or LLM call. It accepts generic response records from CSV,
JSON, or JSONL files.

## Install locally

```powershell
pip install -e .
```

After installation, the package exposes the `srm` command-line entry point.
For development without installation, run the module with `PYTHONPATH=src`.

## CLI

```powershell
srm compute examples/generic_csv_example/responses.csv --include-pairs --output results.json
```

Example outputs are included under `examples/*/results.json`.

Useful options:

```powershell
srm compute responses.jsonl --language es --threshold 0.7 --duplicate-policy latest
srm compute responses.csv --stopwords-file stopwords.txt --include-pairs --top-pairs-limit 10
```

Equivalent local development command:

```powershell
$env:PYTHONPATH="src"; python -m synthetic_response_metrics.cli compute examples/ore_validation/population_size/n10.csv --include-pairs --language en --output examples/ore_validation/population_size/n10_results.json
```

The output contains a `summary` block and a `by_question` block:

```json
{
  "summary": {
    "schema_version": "0.2",
    "threshold_max_similarity": 0.7,
    "min_answers_per_question": 2,
    "questions_total": 2,
    "questions_evaluated": 2,
    "questions_alerted": 1,
    "overall_avg_similarity": 0.785,
    "overall_max_similarity": 1.0,
    "overall_avg_lexical_unique_ratio": 0.568,
    "overall_avg_distinct_2": 0.639,
    "duplicate_records_count": 0,
    "missing_text_count": 0,
    "convergence_alert": true,
    "runtime_ms": 0
  },
  "by_question": {
    "q1": {
      "answers_count": 2,
      "max_jaccard_similarity": 1.0,
      "median_jaccard_similarity": 1.0,
      "exact_duplicate_count": 1,
      "lexical_unique_ratio": 0.5,
      "distinct_2": 0.5,
      "token_entropy": 2.0,
      "status": "ok",
      "alert": true
    }
  }
}
```

## Python API

```python
from synthetic_response_metrics import ResponseRecord, compute_dispersion

records = [
    ResponseRecord(question_id="q1", agent_id="a1", text="Useful and affordable"),
    ResponseRecord(question_id="q1", agent_id="a2", text="Useful and affordable"),
]

result = compute_dispersion(records)
print(result.to_dict()["summary"])
```

Optional configuration:

```python
from synthetic_response_metrics import DispersionConfig

config = DispersionConfig(
    threshold_max_similarity=0.7,
    language="auto",
    duplicate_policy="latest",
    include_pairs=True,
)
```

## Input schema

The canonical record fields are:

- `question_id` or `question`;
- `agent_id` or `persona_id`;
- `text`, `content`, `answer`, or `response`;
- optional `run_id`, `model`, `temperature`, `population_id`, `timestamp`.

For interaction logs, JSON files containing an `interactions` list are also
accepted. Agent messages are mapped to response records and the preceding
interviewer message is used as the question.

## Article validation examples

The `examples/ore_validation` folder contains article-specific synthetic
validation datasets created for the Open Research Europe Method Article. They
cover:

- a controlled data-quality example with missing text, duplicate records, exact
  duplicates, and diverse answers;
- low-, moderate-, and high-convergence response scenarios;
- population-size sensitivity examples for N=3, N=5, and N=10;
- a high-convergence diagnostic case that demonstrates `top_similar_pairs`.

The optional `examples/ore_validation/platform_generated` folder contains a
new, article-specific applied example generated from a fictional scenario
through the local MadSynthesis service layer. It is included as a portability
check for platform exports, not as primary validation or threshold calibration.

Regenerate all example outputs with:

```powershell
srm compute examples/ore_validation/controlled_example/responses.csv --include-pairs --language en --output examples/ore_validation/controlled_example/results.json
srm compute examples/ore_validation/convergence_scenarios/low_convergence.csv --include-pairs --language en --output examples/ore_validation/convergence_scenarios/low_convergence_results.json
srm compute examples/ore_validation/convergence_scenarios/moderate_convergence.csv --include-pairs --language en --output examples/ore_validation/convergence_scenarios/moderate_convergence_results.json
srm compute examples/ore_validation/convergence_scenarios/high_convergence.csv --include-pairs --language en --output examples/ore_validation/convergence_scenarios/high_convergence_results.json
srm compute examples/ore_validation/population_size/n3.csv --include-pairs --language en --output examples/ore_validation/population_size/n3_results.json
srm compute examples/ore_validation/population_size/n5.csv --include-pairs --language en --output examples/ore_validation/population_size/n5_results.json
srm compute examples/ore_validation/population_size/n10.csv --include-pairs --language en --output examples/ore_validation/population_size/n10_results.json
srm compute examples/ore_validation/diagnostic_high_convergence/responses.csv --include-pairs --language en --output examples/ore_validation/diagnostic_high_convergence/results.json
srm compute examples/ore_validation/platform_generated/madsynthesis_export.csv --include-pairs --language en --output examples/ore_validation/platform_generated/madsynthesis_metrics.json
```

The included CSV, JSONL, and JSON files are sufficient to recompute the metric
outputs used by the article examples from the repository root. Manuscript tables
can be derived from these outputs without relying on project-specific local
folders.

## Citation

Please cite the archived software release and the associated Method Article
when using this package. A `CITATION.cff` file is included for software
citation metadata.

## License

This package is distributed under the MIT License. See `LICENSE`.

## Status

Version `0.2.0` is still lexical and lightweight, but it now includes data-quality
diagnostics, pairwise distribution metrics, duplicate handling, language-aware
stopwords for English/Spanish, and optional top similar pair reporting. Planned
extensions include optional semantic similarity, syntactic-template metrics, and
calibration against human-response baselines.
