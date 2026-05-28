# Verification Notes

## Publication-safety checks

- [ ] Review generated responses for accidental sensitive content.
- [ ] Confirm no client, confidential, or personal data are present.
- [ ] Confirm no API keys, system prompts, or production identifiers are written.
- [ ] Confirm Madison approval before Zenodo deposit.

## Method checks

- [ ] Confirm `madsynthesis_export.csv` has `question_id`, `agent_id`, and `text`.
- [ ] Confirm optional metadata fields are present where available.
- [ ] Confirm `madsynthesis_metrics.json` contains `summary` and `by_question`.
- [ ] Confirm `top_similar_pairs` exists when `--include-pairs` is enabled.
- [ ] Confirm the example is described as an applied example, not a validation baseline.
