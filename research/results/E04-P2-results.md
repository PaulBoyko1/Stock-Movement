# E04-P2 factor attribution

Historical conditional attribution of industry momentum minus the equal-industry benchmark. Not a forecast or causal estimate.

| Allocation cost | Annualized arithmetic alpha | Approximate 95% HAC interval | R-squared |
|---|---:|---:|---:|
| 0 bp | 0.84% | [-2.08%, 3.77%] | 0.431 |
| 10 bp | 0.29% | [-2.67%, 3.24%] | 0.430 |
| 25 bp | -0.55% | [-3.54%, 2.45%] | 0.427 |

Alpha is 12 times the monthly regression intercept; it is not the CAGR difference or a future return forecast.
Dependent variable: strategy minus benchmark; RF is not subtracted again.
Six contemporaneous factors: market excess return, size, value, profitability, investment and stock momentum.
HAC: Bartlett lag 12, n/(n-7) correction, normal 95% interval.

## Primary 10 bp factor exposures

| Factor | Coefficient | HAC standard error |
|---|---:|---:|
| Mkt-RF | 0.1128 | 0.0483 |
| SMB | 0.0643 | 0.0659 |
| HML | -0.0506 | 0.0683 |
| RMW | 0.0138 | 0.0880 |
| CMA | 0.0664 | 0.0881 |
| Mom | 0.3455 | 0.0356 |

The primary interval includes zero: these data do not establish positive factor-adjusted alpha.

The frozen P1 return series was reproduced against its committed source hash and aggregate statistics.
Manual OLS/HAC calculations matched statsmodels. Both raw factor archives and dependency versions are retained in the run artifact.
Constant exposures, omitted factors, reconstructed data and approximate trading costs limit interpretation.
No strategy parameters, factors, sample periods or HAC settings were selected from these attribution results.

Code commit: 911ebd15224e7cac7637dc2a5b168f66c0cea33a

## Validation and reproduction

The [successful run with 33 tests](https://github.com/PaulBoyko1/Stock-Movement/actions/runs/35304302447) reproduced the committed E04-P1 results from the same industry archive. It passed 16 baseline tests, 16 attribution tests, and a serial-correlation uncertainty test with four sample/lag fixtures. The production calculation also matched statsmodels for coefficients and the full HAC covariance matrix.

The attribution tests include known coefficient recovery, lag-zero covariance versus HC1, zero active returns, rank deficiency, output scaling, factor-column permutation, percentage conversion, calendar alignment, duplicate/missing rows and invalid values. These are implementation checks, not investment validation.

The [specification](../experiments/E04-P2-specification.md) was committed at `ba08ab791f75fc4fa327890c36f155a5dcd40258` before viewing attribution results. E04-P1 performance was already known. The first diagnostic run used code `8193a2882bb0c5df2b89691b6e4d9090a5538696`; the final run added tests and an explicit mean decomposition without changing the specified model or estimates.

## Primary mean decomposition

This is an algebraic decomposition of the in-sample arithmetic active mean. It does not assign causal contributions or measure predictive value.

| Term | Percentage points per year |
|---|---:|
| Regression intercept | 0.2869 |
| Mkt-RF: average factor return × fitted exposure | 0.8295 |
| SMB: average factor return × fitted exposure | 0.1244 |
| HML: average factor return × fitted exposure | -0.1196 |
| RMW: average factor return × fitted exposure | 0.0657 |
| CMA: average factor return × fitted exposure | 0.1684 |
| Mom: average factor return × fitted exposure | 0.7238 |
| Total arithmetic active mean | 2.0790 |

The annualized residual mean is effectively zero. R² = 0.4295 measures the fraction of historical active-return variation fitted by this regression. It is neither forecast accuracy nor the fraction of average performance explained.

## Source provenance

Both factor files identify the July 2026 CRSP database vintage; data after December 2025 were excluded from the regression.

| Input | Raw ZIP SHA-256 |
|---|---|
| 12 industry portfolios | `c7316c6ae07bc2028632b57ad757dfef8303a62a6956946d7aabe926aadfdeb4` |
| FF5 | `b8653b411cc5e28917e7ef643bb42f6d2d3703f84bc170eb6ae38d5267c65807` |
| Momentum | `7ee14e892b0f7044902fdbc4e25cfaf175b73d4eda0ae6f4a0354a4433afe065` |

Official sources: [FF5 archive](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip), [Momentum archive](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip). Full source headers, retrieval times, covariance matrices, dependency versions and diagnostics are in [the machine-readable result](E04-P2-results.json).

The run's `e04-research` artifact (ID 10530881610) includes all three raw archives, P1 monthly returns, P2 aligned factor/return CSVs, reports and dependency versions. It expires **2026-10-18T03:44:27Z**. Retain the downloaded artifact outside temporary Actions storage for longer reproducibility; hashes alone cannot recreate its bytes. [Replay instructions](../code/README.md).

Decision: retain the unchanged baseline in research. Positive conditional alpha is not established at any of the three stated cost scenarios. The next useful step is a separately specified investable-universe test, with actual fund history, point-in-time eligibility, execution assumptions and costs. These results do not support promoting this rule to model-backed trading alerts.
