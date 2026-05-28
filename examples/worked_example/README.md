# Worked example

This example is intentionally small and diagnostic. It contains:

- one exact duplicate response pair;
- one repeated `question_id`/`agent_id` record handled by the default `latest` policy;
- empty response texts that are counted in the data-quality fields;
- two questions with different similarity patterns.

Run:

```powershell
srm compute examples/worked_example/responses.csv --include-pairs --output examples/worked_example/results.json
```

The resulting JSON is used as the manuscript's generic worked example.
