# Reproducibility Commands

Run from the repository root after installing the package:

```powershell
pip install -e .
srm compute examples/ore_validation/platform_generated/madsynthesis_export.csv --include-pairs --language en --output examples/ore_validation/platform_generated/madsynthesis_metrics.json
```

For local development without installation:

```powershell
$env:PYTHONPATH = "src"
python -m synthetic_response_metrics.cli compute examples/ore_validation/platform_generated/madsynthesis_export.csv --include-pairs --language en --output examples/ore_validation/platform_generated/madsynthesis_metrics.json
```

The repository includes the normalized CSV/JSONL input and the expected metric
outputs for this applied example. The original synthetic platform run was
generated outside this standalone package; reproducing the metric analysis only
requires the included normalized input file.

To analyse a new platform export, convert it to the package input schema:

- `question_id`
- `agent_id`
- `text`
- optional metadata such as `run_id`, `model`, `temperature`, `population_id`,
  and `timestamp`

Then run `srm compute` on the normalized CSV or JSONL file.
