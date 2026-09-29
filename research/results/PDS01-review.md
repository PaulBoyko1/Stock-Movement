# PDS01 — independent results review

Source run: https://github.com/PaulBoyko1/Stock-Movement/actions/runs/36375746801
Source commit: fb8d60537b5bc1825dbc5c955d922d8b300ed231

Collected 1,534,118 nonmissing source return/adjusted-close observations, including 206,567 rows across 36 actual ETF histories. The remaining observations are reconstructed industry/factor returns, not individual-stock prices.
Ran 1,377 signal configurations across three panels, each at four costs: 5,508 strategy/cost evaluations. All 14 pre-download contract tests passed. No recorded collection or trial failures.

## Main result

No panel passed the exploratory search-adjusted maximum-active-mean test. This is not proof that every strategy has zero value: it means this broad screen did not establish an edge after its search. All selected active-return intervals include zero. Previously inspected 2020–2025 is retrospective robustness, not an untouched holdout.

### Configurations selected using 2015–2019 only; 10bp per dollar traded

| Panel | Rule | 2020–25 CAGR | Matched benchmark CAGR | 2020–25 drawdown | Annual active mean | 21-day block interval |
|---|---|---:|---:|---:|---:|---|
| industry49 | reversal; 10d lookback, 1 holdings, 5d rebalance, SMA 200 | 3.29% | 13.56% | -67.02% | -5.08% | -29.56% to 17.91% |
| sectors9 | reversal; 21d lookback, 5 holdings, 21d rebalance, SMA 0 | 14.76% | 12.60% | -41.05% | 2.26% | -2.11% to 6.51% |
| broad7 | reversal; 21d lookback, 1 holdings, 21d rebalance, SMA 0 | 12.25% | 12.92% | -40.26% | 0.11% | -7.01% to 6.91% |

The benchmark uses the same universe and rebalance cadence. Active mean is an arithmetic return difference, not CAGR difference or factor alpha.

## Full-grid behavior at 10bp, 2020–2025

| Panel | Family | Configurations | Positive mean active return | Median annual active mean |
|---|---|---:|---:|---:|
| industry49 | all | 459 | 49.89% | -0.04% |
| industry49 | momentum | 324 | 64.81% | 2.57% |
| industry49 | reversal | 135 | 14.07% | -11.11% |
| sectors9 | all | 459 | 12.85% | -5.63% |
| sectors9 | momentum | 324 | 15.43% | -4.45% |
| sectors9 | reversal | 135 | 6.67% | -10.92% |
| broad7 | all | 459 | 15.69% | -3.64% |
| broad7 | momentum | 324 | 19.75% | -3.09% |
| broad7 | reversal | 135 | 5.93% | -6.24% |

## Cost sensitivity of the validation-selected rule

| Panel | 0bp CAGR | 5bp CAGR | 10bp CAGR | 25bp CAGR |
|---|---:|---:|---:|---:|
| industry49 | 11.53% | 7.33% | 3.29% | -7.93% |
| sectors9 | 16.14% | 15.45% | 14.76% | 12.73% |
| broad7 | 14.31% | 13.27% | 12.25% | 9.22% |

## Search-adjusted diagnostics

| Panel | 21-day block p | 63-day block p | Validation-positive configurations still positive later |
|---|---:|---:|---:|
| industry49 | 0.408 | 0.412 | 51/86 |
| sectors9 | 0.628 | 0.596 | 20/71 |
| broad7 | 0.892 | 0.880 | 20/35 |

These are nonstudentized, within-panel circular block-bootstrap diagnostics with 499 draws. They depend on stationarity, are not adjusted across all project research and must not be interpreted as live success probabilities.

## Data and implementation limits

- Current surviving ETF list, not a point-in-time census; no individual-stock or intraday claims.
- Vendor-adjusted total-return levels with a full-session delay before assumed closing fills; no validated bid/ask or cash-distribution receivable ledger.
- Zero flags in a 20bp ordinary-return reconciliation is a limited consistency check, not independent corporate-action validation.
- Costs and RF cash yield are modeling assumptions; no capacity or auction-execution validation.
- French history is reconstructed and revisable. Acquisition counts include older/newer observations outside the evaluation periods.
- Raw and normalized vendor downloads stayed in the temporary first runner. This review uses retained summaries only. Raw bytes were not durably preserved and cannot be reconstructed from hashes alone.
- Summary artifacts expire December 27, 2026 unless retained elsewhere. Source manifests and machine-readable findings are preserved with this report.

## Checks

- All 5,508 distinct strategy/cost entries present
- 459 signal variants per panel
- All 36 downloaded ETF datasets have zero invalid OHLC rows
- No ordinary return reconciliation differences above 20bp recorded
- Original validation selection independently reproduced for all panels
- Higher costs never increased a candidate's CAGR in any period
- Three period returns multiply to the full-period return at zero costs
- Drawdown and exposure ranges checked
- Canonical data copies excluded from source-observation counts
- Raw snapshots unavailable here: no new validation of provider history, corporate actions or full daily ledgers


The complete grid is in the downloadable `public-data-study-summaries` artifact on the source run. The [independent review workflow](https://github.com/PaulBoyko1/Stock-Movement/actions/runs/36525035427) passed all summary consistency checks. No application files were changed.
