# ORE validation examples

Article-specific synthetic response datasets for the Open Research Europe Method Article.
These examples are not derived from any previous experiment. The core examples
are controlled inputs created to exercise data-quality counters, convergence
scenarios, population size sensitivity, and pair-level diagnostics.

The optional `platform_generated` folder contains a new article-specific applied
example generated from a fictional scenario through the local MadSynthesis
service layer. It demonstrates portability to a platform export and should not
be treated as primary validation or threshold calibration.

Example commands:

```powershell
srm compute examples/ore_validation/controlled_example/responses.csv --include-pairs --language en --output examples/ore_validation/controlled_example/results.json
srm compute examples/ore_validation/convergence_scenarios/low_convergence.csv --include-pairs --language en --output examples/ore_validation/convergence_scenarios/low_convergence_results.json
srm compute examples/ore_validation/population_size/n10.csv --include-pairs --language en --output examples/ore_validation/population_size/n10_results.json
srm compute examples/ore_validation/platform_generated/madsynthesis_export.csv --include-pairs --language en --output examples/ore_validation/platform_generated/madsynthesis_metrics.json
```
