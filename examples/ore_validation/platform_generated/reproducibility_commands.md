# Reproducibility Commands

Run from the workspace root:

```powershell
python OpenResearchEurope\Articulo\scripts\generate_platform_generated_example.py
```

This generates a new platform-produced synthetic survey run, writes normalized
CSV/JSONL inputs, computes metric outputs, and creates compact summary tables.

To recompute metrics from an existing normalized CSV after installing the
package:

```powershell
srm compute OpenResearchEurope\synthetic-response-metrics\examples\ore_validation\platform_generated\madsynthesis_export.csv --include-pairs --language en --output OpenResearchEurope\synthetic-response-metrics\examples\ore_validation\platform_generated\madsynthesis_metrics.json
```

To recompute metrics without installing the package:

```powershell
cd OpenResearchEurope\synthetic-response-metrics
$env:PYTHONPATH = "src"
python -m synthetic_response_metrics.cli compute examples\ore_validation\platform_generated\madsynthesis_export.csv --include-pairs --language en --output examples\ore_validation\platform_generated\madsynthesis_metrics.json
```

The generation command requires a configured local MadSynthesis environment and
an available LLM provider key. Secrets are read from the local environment and
are not written to the generated artifacts.
