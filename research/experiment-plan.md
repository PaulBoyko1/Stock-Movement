# Experiment plan and research backlog

Status: the E01–E10 designs below remain the broader research backlog. A separately frozen E04-P1 industry-allocation proxy has now run; see the [results and limitations](results/E04-P1-results.md). It does not complete the planned executable ETF or liquid-stock tests. Parameter values below are initial specifications to preregister; they are not proven or optimized settings. See the [evidence register](evidence-register.md) for paper motivations and [calculation audit](calculation-audit.json) for the limited checks actually executed.

## A common protocol

**Universe.** A starting stock universe is U.S. common equities with prior-close price at least $5 and trailing 60-session median dollar volume at least $20 million, retaining at most the 1,000 most liquid eligible names at each monthly selection. These thresholds are engineering hypotheses. Preserve historical membership, failed/delisted securities, corporate actions and stable IDs. Separate financial companies for accounting features. Define ETF membership, inception and benchmark histories independently.

**Timing.** Store market-event time, publication time, provider receipt time and feature availability. At each decision, include only inputs already available and apply a processing delay. After-close features cannot obtain that same closing price. A future reaction window must finish before an entry using its result.

**Targets.** Distinguish raw return, market excess return, industry excess return and net portfolio return. Use dividend-aware returns. For event tests, use entry at the next eligible executable price after the information delay and exit at the same clock time 5, 20 or 60 trading sessions later. Overnight and intraday portions should be reported separately when relevant. Keep training targets distinct from realized portfolio accounting.

**Overlapping event portfolios.** Begin with event-level predictive results; do not label their average a portfolio return. Before portfolio testing, freeze the entry-selection threshold/ranking in development. Initial accounting proposal: separate portfolios for each holding horizon, with 20 sessions primary for earnings tests; long-only entries target 2% of pre-trade NAV; at most 50 simultaneous names; no leverage; suppress additional signals in an issuer until its existing position exits. Process scheduled exits before new entries. Allocate remaining cash pro rata across simultaneous eligible entrants when constrained, with no allocation above the entry target. Mark positions daily, accrue the chosen cash rate, retain dividends/corporate actions, and apply costs on actual simulated transactions. Preserve position IDs and event cohorts; record capacity-rejected signals separately. Other horizon portfolios are independent diagnostics, never combined as if they shared unlimited capital. These are starting accounting rules to preregister, not validated sizing choices.

**Splits.** Use chronological training, validation and untouched subsequent test periods, with all stocks on the same calendar split. Fit imputations, normalizations, feature selection and hyperparameters only on training data. Purge training observations whose outcome windows extend into evaluation periods; apply a predeclared gap for overlapping event labels. Never randomly split rows from neighboring dates and call that a deployment simulation.

Historical holdouts are imperfect when a published paper already used those years. Report original-sample, post-publication and recent performance separately. Choose final dates after auditing data coverage, before inspecting strategy results. Record every attempted variant, including failures. When testing 252-session outcomes, account for that full overlap in split design.

**Costs.** Track commissions/fees, half-spread on each aggressive fill, impact, latency slippage and financing/borrow where applicable. Do not double-count spread when execution already occurs at bid/ask. Show net development results while selecting strategies, then stress costs at 2× and 3× baseline. With daily-only data, costs are scenarios rather than verified intraday fills. Report turnover with an explicit one-way/two-way convention and apply costs consistently.

**Benchmarks.** Use a passive market benchmark, an equal-/value-weight same-universe benchmark as appropriate, a sector-matched comparison, and the simplest relevant signal. Compare both absolute performance and incremental performance; matching volatility/exposure helps distinguish alpha from additional market risk. Cash returns need a stated contemporaneous rate.

**Inference.** Report net return, drawdown, volatility, turnover, concentration, beta/industry exposure, performance by year, and uncertainty. Cluster or block inference by date and issuer where appropriate; overlapping horizons are not independent observations. Include probability calibration and Brier score for probabilistic forecasts. Hit rate alone cannot determine profitability. Correct for multiple hypotheses/parameter searches and inspect stability rather than only a best Sharpe ratio.

## E01 — Liquid-stock momentum baseline

Motivation: R01, R05 and R12. Formation feature: total-return index at t−21 divided by its value at t−252, minus one. Rank eligible stocks monthly after the final session closes. Trade at the next session's open under stated cost assumptions; rebalance monthly. Initial portfolio: equally weighted top quintile, long only. Compare against the same-universe equal-weight portfolio, market benchmark and sector-matched momentum construction.

The long-short quintile spread is a separate research diagnostic, not a free implementation assumption. If examined, include borrow availability, fees and gross exposure.

Primary question: does the adapted liquid-universe signal retain useful net performance and rank information? Show rebound-period drawdowns. Do not optimize a regime filter before establishing the baseline.

## E02 — Earnings information beyond momentum

Motivation: R09–R11. Keep consensus surprise separate from accounting surprise. A consensus feature can be (reported EPS − last eligible pre-release consensus EPS) / pre-release share price, with matching fiscal period, accounting definition, currency and split basis. A historical alternative is seasonal EPS change standardized by variability of prior seasonal changes; label it “accounting surprise,” never “beat versus expectations.”

Start with momentum, market/industry and volatility controls. Add surprise, then guidance, then revisions separately. Measure 5/20/60-session returns after a feasible entry. Evaluate initially on liquid stocks, including weak/negative events; do not pick only recognizable winners.

For an analyst-revision feature accumulated over five sessions, enter only after those five sessions. Never assign it announcement-day returns. Compare immediate and delayed models as distinct experiments.

## E03 — Comparable guidance changes

Motivation: R10 and R13. Store prior and new guidance ranges for the same fiscal period and definition. Measure growth-guidance midpoint changes in percentage points; preserve EPS revisions in dollars per share, using a predeclared scale such as pre-release share price for cross-company modeling. Treat withdrawn/initiated guidance separately from ordinary numerical revisions.

Test guidance alone, baseline plus guidance, and guidance plus initial price reaction. Fix the reaction window (for example the first full regular session after release) before testing; enter no earlier than the next executable observation. Separate currency, acquisition and accounting-basis changes.

Core failure mode: a raise can already be expected, smaller than hoped, or driven by nonoperating factors. A weak initial reaction does not automatically imply mispricing.

## E04 — Sector relative strength and fundamental breadth

Motivation: R12. First test a simple monthly sector momentum baseline, with sector total returns relative to a market benchmark and next-session execution. Compare a top-three equal-weight sector basket with an equal-weight basket of all eligible sector ETFs and the market benchmark, plus exposure-matched comparisons.

Use only funds available then; do not give newer sectors synthetic tradable histories. A common-inception ETF sample is an adapted experiment; older industry portfolios can support a separate historical replication but are not the same instruments.

Add the acceleration feature defined in the overview only after the momentum baseline is fixed. Evaluate whether quadrant transitions improve forecasts/net results over momentum alone.

Later, add industry-specific operating breadth: fraction of eligible reporting peers with improvement in comparable metrics. Record observation age, reporting coverage and historical classification. Exclude the target company when forecasting its stock from “peer” information. Compare additive breadth with momentum × breadth. Control for stale or unevenly reporting sectors.

## E05 — Late-session ETF continuation

Motivation: R21–R22. Start with SPY and use QQQ as a separately declared replication instrument. Compare previous-close-to-10:00 ET return and previous-close-to-15:30 ET return as predictors of the remaining session. The first predictor includes the overnight move.

Decide at 15:30 using received information; simulate entry no earlier than 15:30:01 with latency stress tests. Use executable quotes and exit at 15:59:50 rather than assuming access to the official closing print. Handle shortened sessions separately. Compare with always-long over exactly the same interval, an unconditional-mean forecast, and cash.

A candidate split is rolling five-year training, one-year validation and subsequent one-year testing, subject to sufficient data. Stress an additional 1/2/5 basis points per side beyond a clearly defined baseline cost model. Benchmark both probabilities and economic returns. Without quotes around the decision/exit, report only a coarse feasibility study.

## E06 — Do chart patterns add information?

Motivation: R19, R26–R27. Freeze an algorithm before return testing. A candidate double-bottom definition could use troughs confirmed by two later bars, separated by 5–30 sessions, within 3% of each other, followed by a close above the intervening peak. These numbers are arbitrary initial hypotheses. Record that each pivot becomes known only after its confirmation bars.

Compare momentum, short reversal, volatility, liquidity and industry controls against that baseline plus the pattern. Evaluate 5/20-session outcomes with next-session entry. Keep any threshold sweep in the experiment registry and adjust for the whole search. Retain a pattern only if it adds incremental, stable, net value. Similar care applies to breakouts and support/resistance.

## E07 — Quality, valuation and investment

Motivation: R01, R03–R06. Start with sector-aware profitability, valuation and investment measures using original filing/release availability. Evaluate 60/120/252-session outcomes and portfolio implementations with moderate turnover. Define handling of negative earnings/book equity and missing values before fitting.

Separate general corporate and financial-company models. Compare each family alone, additively, and then with momentum interactions. Financial-statement restatements must not rewrite what a past decision could know. For long-term decision support, supplement empirical rankings with transparent growth/margin/valuation scenarios; scenario assumptions are not model probabilities. The initial 3–5-year view is scenario-only. The 252-session endpoint cannot validate multi-year probabilities; those require separate preregistered outcomes, much longer histories, and appropriate handling of overlapping multi-year labels.

## E08 — Reversal as execution support

Motivation: R20 and R25. Use prior half-hour market/industry-adjusted midpoint return, current spread, and same-clock-time history to forecast the next half-hour. Test an extra round-trip strategy separately from scheduling an independently specified parent order.

The latter endpoint is implementation shortfall against a fixed schedule, with completion obligations and missed-fill costs. A model may help execution even if its standalone strategy loses after spread. Do not use final-day volume to determine earlier eligibility or future-smoothed latent states as live predictors.

## E09 — Order-book research, later

Motivation: R23–R24. At causal fixed/event times, compute queue imbalance (bid depth − ask depth)/(bid depth + ask depth), lagged OFI, spread and depth. Compare logistic regression with simple thresholds for next midpoint direction and 1/5/30-second returns.

Use chronological holdouts plus held-out stocks. Aggressive execution needs received data and latency; passive execution needs queue position, fill probability and adverse selection. A correct midpoint prediction is not a realized profit. Without reliable depth and execution information, keep this as research diagnostics.

## E10 — Document changes, later

Motivation: R08. Compare new filings/releases with the previous comparable document; extract changes in guidance, risks, customer concentration, inventory, debt, dilution and segment narrative. Preserve source spans, numeric definitions and document version.

Compare financial-domain text baselines with a structured extractor. Evaluate extraction accuracy on human-checked records before forecasting returns. For historical tests using present-day language models, consider memorized outcomes and training-data contamination; forward-only evaluation is cleaner. Do not let explanations quietly incorporate future filings or current knowledge.

## Four interactions to brainstorm

| Hypothesis | Feasibility | Clean comparison and main concern |
|---|---|---|
| Momentum × earnings quality | Earliest candidate with point-in-time accounting | Baseline → additive momentum + quality → interaction; control industry/profitability/valuation overlap |
| Capex acceleration × cash conversion | Moderate | Define conversion independently of capex, e.g. OCF/revenue; using FCF creates a mechanical subtraction relationship |
| Guidance raise × weak reaction | Moderate; precise timestamps required | Compare additive inputs with interaction; enter after the reaction window, account for expected guidance |
| Sector strength × peer operating breadth | Hardest initial data task | Additive breadth before interaction; historical peers, coverage and staleness can manufacture a result |

These are our proposals, not conclusions of a cited paper.

## Promotion criteria

Before a candidate becomes a model-backed alert, require a reproducible dataset/version, reviewed feature timing, faithful baseline, chronological incremental results, cost stress tests, exposure/concentration analysis and acceptable probability calibration where applicable. Specify tolerances before opening the final test results.

Forward paper trading must then compare expected and observed fills, costs, calibration and drift. Paper trading itself cannot guarantee live fills. Automated execution is a later decision requiring separate controls, limits, reconciliations, operational failure tests and user authorization.

## Checks actually completed in this review

1. Recomputed Microsoft's annual operating cash flow minus cash property/equipment additions: $71.611 billion versus $74.071 billion, −3.32%.
2. Recomputed Walmart's guidance midpoint changes: +0.75 percentage points for sales growth and +$0.02 for adjusted EPS.
3. Synthetic cost arithmetic: a hypothetical 10 bp gross edge becomes +5/0/−10 bp after assumed total round-trip costs of 5/10/20 bp.
4. Synthetic hit-rate arithmetic: 55% wins of 20 bp and 45% losses of 25 bp yield −0.25 bp before costs, or −5.25 bp after 5 bp costs.

The first two are document arithmetic, the last two are hypothetical sensitivity checks. None measures investment performance. Local execution tools failed to start, and no point-in-time price/consensus dataset was loaded. Those statements describe the September 15 initial review. On September 16, E04-P1 added a historical industry-portfolio proxy backtest and descriptive uncertainty interval. No calibrated stock forecast or validated tradable edge is claimed.
