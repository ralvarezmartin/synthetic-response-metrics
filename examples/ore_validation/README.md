# ORE validation examples

Article-specific synthetic response datasets for the Open Research Europe Method Article.
These examples are not derived from any previous experiment. They are controlled
inputs created to exercise data-quality counters, convergence scenarios, population
size sensitivity, and pair-level diagnostics.

Example commands:

```powershell
srm compute examples/ore_validation/controlled_example/responses.csv --include-pairs --language en --output examples/ore_validation/controlled_example/results.json
srm compute examples/ore_validation/convergence_scenarios/low_convergence.csv --include-pairs --language en --output examples/ore_validation/convergence_scenarios/low_convergence_results.json
srm compute examples/ore_validation/population_size/n10.csv --include-pairs --language en --output examples/ore_validation/population_size/n10_results.json
```
