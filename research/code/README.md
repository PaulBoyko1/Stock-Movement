# Running the frozen industry experiments

Use Python 3.12 and the pinned dependencies:

```sh
python -m pip install -r research/code/requirements.txt
python -m unittest discover -s research/tests -v
python research/code/industry_baseline.py --output-dir work/e04-p1 --expected-sha256 c7316c6ae07bc2028632b57ad757dfef8303a62a6956946d7aabe926aadfdeb4
python research/code/factor_attribution.py --baseline-dir work/e04-p1 --output-dir work/e04-p2
```

E04-P1 uses the standard library. E04-P2 adds NumPy and statsmodels to cross-check independently calculated OLS and Newey–West covariance.

The runners download the official French archives, preserve their exact bytes and hashes, and run fixed specifications ([P1](../experiments/E04-P1-specification.md), [P2](../experiments/E04-P2-specification.md)). P1 writes results.json, monthly.json, monthly.csv and report.md. P2 writes factor ZIPs, aligned regression CSVs, results.json and report.md.

To reproduce retained source vintages, first unzip the workflow artifact into a chosen directory, then run:

```sh
python research/code/industry_baseline.py --input-zip ARCHIVE/e04-p1/source.zip --expected-sha256 c7316c6ae07bc2028632b57ad757dfef8303a62a6956946d7aabe926aadfdeb4 --output-dir work/replay-p1
python research/code/factor_attribution.py --baseline-dir work/replay-p1 --factor-input-dir ARCHIVE/e04-p2 --expected-factor-results ARCHIVE/e04-p2/results.json --output-dir work/replay-p2
```

Source hashes identify vintages but do not recover missing bytes. P2 always compares the reproduced P1 full-period and annual results with the committed baseline.

The GitHub Research baseline workflow runs tests and both experiments on relevant pushes. It has read-only repository permission, uses no secrets, and cannot commit or trade. Its artifact lasts 30 days; retain the raw vintages separately for longer reproducibility. A changed industry source hash deliberately fails the frozen experiment.

Parameters and samples are fixed. New strategies require separate experiment IDs and a recorded specification before result inspection. Monthly reconstructed industry portfolios cannot verify execution prices, a liquid-stock-only universe, or intraday risk. P2 is historical factor attribution, not a predictive signal.
