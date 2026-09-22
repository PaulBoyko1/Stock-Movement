# Backtest workbench

The workbench is a small monthly research instrument for inspecting a fixed industry-momentum rule. It supports transparent exploration of the supplied panel; it does not turn a retrospective result into a live signal, investment recommendation, or executable ETF/stock backtest.

## Visible controls

The main form keeps these controls together:

| Control | Meaning |
| --- | --- |
| Start and end month | Inclusive evaluation months. |
| Formation momentum months (`L`) | Number of monthly returns used for each rank. |
| Skipped recent months (`S`) | Number of months between the signal window and the holding month. |
| Holdings (`K`) | Number of strongest industries, equally weighted long-only. |
| Cost (bp per dollar traded) | Proportional allocation-change cost assumption. |

Advanced detail exposes starting capital and rebalancing every one or three months. The simple view uses the last applied settings for these controls. Equal weights at rebalance, long-only fully invested holdings, deterministic tie-breaking, and the comparison universe are fixed. Starting capital scales wealth without changing returns.

## Dataset and defaults

The embedded dataset is the `french-12-industry-202607-1994-2025` vintage: 12 historical value-weighted industry research portfolios, monthly decimal total returns, 1994-01 through 2025-12. The source is the Kenneth French Data Library 12 Industry Portfolios file. The embedded metadata records retrieval `2026-09-20T22:44:28.892392+00:00` and SHA-256 `c7316c6ae07bc2028632b57ad757dfef8303a62a6956946d7aabe926aadfdeb4`; retain and display the source URL, timestamp, source header, and hash.

The default run is the P1 parity configuration: 2000-01 through 2025-12, `L = 11`, `S = 1`, `K = 3`, and 10 bp. The earlier 1994-01 through 1999-12 observations provide warmup history; they are not default evaluation months. Allow dates only within the data coverage, require at least 12 evaluation months, and reject a start that lacks `L + S` prior observations. Never fill missing months or silently move a requested date.

## Formation and portfolio calculation

For each holding month `h` and industry `j`, the formation index is:

```text
score[h,j] = product(1 + r[t,j]) - 1
             for t = h - S - L through h - S - 1
```

Thus the default January 2000 signal compounds January-November 1999, skips December 1999, and applies to January 2000. Rank scores descending; break exact ties by the original source-column order. Select the top `K`, set each selected target weight to `1/K`, and set all others to zero.

At each rebalance, compare the new target to the prior portfolio after it drifted through the preceding month's realized returns. Let `w_drift` be those normalized weights and let `w_target` be the new target. Traded notional is `D = sum(abs(w_target - w_drift))`. Initial cash entry has `D = 1`; a full replacement is approximately `D = 2`. With `c = cost_bp / 10,000`, calculate

```text
gross = sum(w_target[j] * r[h,j])
net   = (1 - c * D) * (1 + gross) - 1
```

The haircut covers entry, exits, substitutions, and drift-driven trades. On the final month, apply one additional `(1 - c)` terminal liquidation haircut to both strategy and benchmark. This is a proportional target-weight approximation, not exact self-financing execution; state that distinction next to cost results.

## Benchmark and outputs

The benchmark is equal weight across all 12 industries, rebalanced on the same schedule, with the same drift, cost, and terminal-exit convention. It is the primary same-frequency comparison, not a stock index or ETF substitute. Three-month rebalancing starts at the selected start month (January then April, for example); between rebalances both portfolios keep their drifted weights and incur no rebalancing costs.

Show strategy and benchmark growth, month-end drawdown, CAGR, annualized monthly volatility, final wealth, and annualized traded-notional turnover. Allow inspection of each returned month, selected industries, signal window, and strategy/benchmark return. Any active difference is descriptive; do not label it alpha or imply a forecast. The existing E04-P2 factor attribution is a separate diagnostic with stated uncertainty and does not validate this workbench result.

## Exploration, frozen interpretation, and session handling

Changing a control creates an exploratory candidate and marks the displayed result stale until an explicit run. The P1 parity defaults reproduce the frozen rule's dates and conventions, but an exploratory UI run is not a new frozen experiment or a preregistration. A frozen interpretation requires the dataset vintage/hash, all five inputs, engine version, and output artifact to be recorded together outside the UI.

Successful-run history and strategy/benchmark comparisons are session-only and discarded on page close or refresh. There is no server or repository persistence. Export explicitly downloads the current successful result, parameters, provenance metadata, timestamp and successful-run summaries. Failed validation attempts have no performance result and do not increment the completed-run count. Changed or failed inputs disable export until a successful rerun. Repeated parameter trials are exploratory selection; choosing the best historical result does not demonstrate an edge.

## Data boundary and later user data

This panel is monthly and ends in 2025. It contains reconstructed industry portfolios, not daily or intraday observations, stock prices, ETF prices, modern fixed sectors, or a live feed. Historical source data can be revised; constituent trading, taxes, tracking error, fund fees, and verified boundary fills are outside this instrument.

Later user-supplied data can be assessed in a private local/session workflow after checking the same schema, monthly continuity, return units, date range, warmup, and provenance fields. Keep private raw files outside this public repository by default. The UI may receive a local derived panel and export metadata or results, but should not embed, commit, or upload the raw private file without an explicit separate decision.
