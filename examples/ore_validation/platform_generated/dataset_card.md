# Dataset Card: Platform-Generated Applied Example

## Dataset name

MadSynthesis-generated applied example for the Open Research Europe response
convergence Method Article.

## Dataset status

Generated specifically for the manuscript and included in this repository as a
static applied example with normalized inputs and expected metric outputs.

## Intended use

This dataset demonstrates application of the platform-independent metrics to a
realistic synthetic-population platform export. It is intended for functional
reproducibility, inspection of output fields, and manuscript support.

## Out-of-scope use

The dataset should not be used as evidence of human-response validity, universal
threshold calibration, domain-level generalization, or platform-level quality.

## Data source

The data were generated through the MadSynthesis service layer using a fictional
city-service booking scenario, ten synthetic agents, and three open-ended survey
questions.

## Privacy and sensitivity

The dataset contains no human participant data, no client data, no confidential
business information, and no intentionally included personal data. Synthetic
agent names use generic labels rather than real names. API keys, system prompts,
and confidential platform internals are not included.

## Files

- `madsynthesis_export.csv`
- `madsynthesis_export.jsonl`
- `madsynthesis_metrics.json`
- `madsynthesis_summary.csv`
- `madsynthesis_by_question.csv`
- `madsynthesis_top_pairs.csv`
- `metadata.json`

