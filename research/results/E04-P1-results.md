# E04-P1 observed results

Retrospective research portfolios; after assumed allocation costs using a proportional target-weight approximation. Not an executable ETF backtest.

| Cost per dollar traded | Strategy CAGR | Benchmark CAGR | Strategy max month-end drawdown | Active mean/year | Approx. 95% interval |
|---|---:|---:|---:|---:|---:|
| 0 bp | 11.53% | 8.91% | -39.32% | 2.66% | [-0.42%, 5.73%] |
| 10 bp | 10.86% | 8.87% | -39.49% | 2.08% | [-1.02%, 5.18%] |
| 25 bp | 9.85% | 8.81% | -39.75% | 1.21% | [-1.93%, 4.35%] |

Active mean is the annualized arithmetic average of monthly strategy-minus-benchmark returns, not a funded CAGR.
Intervals use Newey-West lag 12 and a normal approximation. See the separate [E04-P2 attribution](E04-P2-results.md) for the subsequent factor diagnostic.

## Primary 10 bp scenario by period

| Period | Strategy CAGR | Benchmark CAGR | Strategy month-end drawdown | Benchmark month-end drawdown |
|---|---:|---:|---:|---:|
| 2000-2025 | 10.86% | 8.87% | -39.49% | -49.57% |
| 2000-2009 | 3.06% | 2.77% | -39.49% | -49.57% |
| 2010-2019 | 14.10% | 12.77% | -23.19% | -17.51% |
| 2020-2025 | 19.31% | 13.03% | -22.41% | -23.22% |

## Reproduction

Raw archive SHA-256: c7316c6ae07bc2028632b57ad757dfef8303a62a6956946d7aabe926aadfdeb4
Code commit: 78e992851f90f05de5f6215e4b757441b2b8176a
Source: [Kenneth French 12 Industry Portfolios CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/12_Industry_Portfolios_CSV.zip)

The run artifact contains the exact raw vintage, manifest, monthly results and report. Retain it before artifact expiry.
Monthly reallocation fees use a proportional target-weight haircut approximation, not exact self-financing transaction notionals.
They omit underlying constituent trading, fund expenses, tracking error, taxes and executable-price verification.
Subperiods slice one continuous portfolio; entry and liquidation fees are not restarted at decade boundaries.
No liquid-stock universe filter or modern GICS mapping is applied.
This fixed rule was registered before this run but the historical period is not pristine out of sample.

## Review and interpretation

[Successful run and retained artifact](https://github.com/PaulBoyko1/Stock-Movement/actions/runs/35175902119). The run passed 16 parser, timing and accounting tests. The result covers 312 months. Annual-return compounding was independently checked against reported CAGR. Tests establish implementation checks, not investment validity.

At the primary 10 bp assumed cost, the CAGR difference is approximately 1.99 percentage points, with higher annualized monthly volatility (16.83% versus 15.12%). The annualized arithmetic active mean is a different quantity: 2.08%, with an approximate interval of −1.02% to +5.18%. That interval includes zero. Full-period month-end drawdown improved but the 2010s month-end drawdown worsened. Drawdown peaks reset at each reported subperiod's start. These findings do not establish positive factor-adjusted alpha or a deployable edge.

Decision: retain the unchanged rule for further research. Do not promote it to model-backed trading alerts. The subsequent E04-P2 diagnostic evaluates market/size/value/profitability/investment/momentum exposures using the same sample and HAC lag 12. An investable ETF test with realistic execution and costs remains separate future work. No parameters were optimized from these results.

[Machine-readable results](E04-P1-results.json), [registered specification](../experiments/E04-P1-specification.md), [runner and reproduction instructions](../code/README.md).

The raw-vintage artifact expires October 17, 2026 UTC; preserve it separately for later byte-identical reproduction. The recorded SHA-256 alone cannot reconstruct a missing download.
