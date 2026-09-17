# Running E04-P1

Python 3.12+, standard library only:

```sh
python -m unittest discover -s research/tests -v
python research/code/industry_baseline.py --output-dir work/e04-p1
```

The runner downloads the official French ZIP, stores its exact bytes/hash, runs the fixed [specification](../experiments/E04-P1-specification.md), and writes results.json, monthly.json, monthly.csv and report.md.

To reproduce a retained data vintage:

```sh
python research/code/industry_baseline.py --input-zip PATH_TO_SOURCE_ZIP --expected-sha256 RECORDED_SHA256 --output-dir work/replay
```

The GitHub Research baseline workflow runs tests and the experiment on relevant pushes. It has read-only repository permission, uses no secrets, and cannot commit or trade. The artifact lasts 30 days; retain the raw vintage separately for longer reproducibility. A source hash identifies a vintage but does not recover missing bytes.

The strategy parameters and sample are fixed. New strategies require separate experiment IDs and a recorded specification before result inspection. The current monthly research portfolios cannot verify execution prices or a liquid-stock-only universe.
