# Generic CSV example

Run:

```powershell
srm compute examples/generic_csv_example/responses.csv --include-pairs --output examples/generic_csv_example/results.json
```

The first question intentionally contains duplicate responses, so the maximum
Jaccard similarity should trigger the default convergence alert. Pair reporting
is enabled so the output also shows which two agents produced the top overlap.
