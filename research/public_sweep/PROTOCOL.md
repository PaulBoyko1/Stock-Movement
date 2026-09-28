# PDS01 — public-data parameter study (exploratory)
Frozen before this branch's first data run, 2026-09-27.

## Question and boundaries
How stable are simple momentum, reversal and trend-conditioned allocation rules across parameters, costs and chronological periods? No live trading, app integration, provider credentials or strategy promotion. This is a new exploratory screen, not completion or replacement of E04-P1/P2/P3.

Fetch 36 named surviving U.S.-listed equity ETFs: SPY QQQ IWM DIA XLB XLE XLF XLI XLK XLP XLU XLV XLY VOO VTI VTV VUG IWD IWF IWB MDY RSP MTUM QUAL USMV VLUE XLC XLRE SMH SOXX IGV IBB XBI IYT KRE KBE. This is a curated survivor sample, not the historical universe of all ETFs or a historical liquidity screen. Download actual available daily history from 1993 through 2025 without pre-inception backfills. Save unadjusted OHLC, adjusted close, volume and actions returned by yfinance; do not repair, forward-fill or silently drop missing rows.

Separately fetch the official Kenneth French 49-industry daily value-weighted total-return panel and daily Fama/French factors/RF, including the available older history. These are reconstructed industry research portfolios, not tradable securities or 49 individual stocks. Archive hashes identify this download vintage; French history can be revised.

## Predeclared panels
- industry49: all 49 research portfolios, evaluation 2000-01-01 through 2025-12-31, 1994 onward warmup.
- sectors9: XLB XLE XLF XLI XLK XLP XLU XLV XLY, same evaluation dates.
- broad7: SPY QQQ IWM DIA MDY RSP VTI, evaluation 2005-01-01 through 2025-12-31.
Remaining ETFs are collected and quality-audited for later independent specifications; they do not enter a data-dependent best-universe search.
Require complete evaluation and warmup observations against the dated French factor calendar (from 1994); fail the affected panel if dates/values are missing. No performance-driven substitutions.

## Grid locked in advance
Momentum: formation [21,63,126,252] sessions; skipped [0,5,21]; holdings [1,3,5]; rebalance [5,21,63] sessions; own-price SMA filter [0,100,200].
Reversal: formation [1,3,5,10,21]; skip 0; holdings [1,3,5]; rebalance [1,5,21]; same SMA filters.
324 + 135 = 459 signal variants per panel. Costs [0,5,10,25] bp per dollar traded; primary 10 bp. Three complete panels would yield 5,508 strategy/cost evaluations plus benchmarks. Cost scenarios are not independent hypotheses.

Rank by cumulative total return; stable original column order resolves ties. For an SMA filter, rank only eligible assets above their own past SMA. Invest 1/K in each selected asset; unfilled slots remain in cash. Rebalance dates are anchored to the evaluation start, not calendar weeks/months. Long-only, fractional normalized total-return units, no leverage/shorts or stops/targets.

## Information and accounting
Signal through close t; assumed fill at close t+1; first earned daily return ends t+2. Code day i uses feature index i-2. This adds a full session between signal and fill; it does not claim a guaranteed closing-auction fill. French panels use analogous lagged daily research-return allocation.
Adjusted-close returns are a vendor total-return abstraction, not a cash/share/distribution-receivable ledger. Expenses are already reflected in observed fund returns; never subtract them again. Reconciliation compares ordinary dividends against adjusted returns and reports mismatches, including corporate-action ambiguities. ETF results remain provisional and do not satisfy the separate E04-P3 corporate-action accounting specification.
Costs solve the self-financing proportional-cost equation for desired post-cost weights, with initial entry and final liquidation. Cash earns the aligned dated RF research proxy. A second zero-cash-yield sensitivity is reported for the validation-selected configuration only.
Benchmarks: equal-universe allocation rebalanced at each candidate's cadence, with matching costs/cash/accounting; also an equal-universe buy-and-hold reference.
Missing values and negative/nonfinite wealth cause failure. Save all failures. No orders or broker connections.

## Selection and evaluation
Discovery: start through 2014. Validation: 2015–2019. Previously observed retrospective robustness: 2020–2025. The latter is NOT an untouched holdout: these market years and related strategies were examined earlier in this project.
Select one configuration per panel using highest validation information ratio versus cadence-matched benchmark at 10 bp, ties by deterministic trial ID. Report that exact configuration in all periods/cost scenarios, plus the whole grid; never select on 2020–25 returns.
Positions carry across period boundaries; period statistics are slices of one continuous simulation. Terminal liquidation is charged at the final sample end.
Metrics: CAGR, annualized volatility, daily drawdown, total return, annual turnover, average invested exposure, paired active mean, information ratio, annual results and worst-five-day contribution. Active-return statistics are not factor alpha.
For the 2020–25 retrospective sample, report an exploratory centered circular block-bootstrap maximum-mean-active-return test across all 459 primary-cost configurations (499 replications, blocks 21 and 63 days, seed 20260927). Also report block-bootstrap intervals for the validation-selected mean active return. This is a nonstudentized, stationarity-dependent multiplicity diagnostic within each panel, not a universal significance certificate or cross-panel correction.
A genuine future test needs new prospective observations and a separately frozen specification.

## Integrity, retention and publishing
Record branch commit, script/spec hashes, dependency versions, retrieval times, source hashes, coverage, row counts, adjustment flags and dataset failures. Test parsers, timing/future mutation, costs, cash, drift, terminal liquidation and bootstrap logic before downloading real data.
Run under GitHub Actions with read-only repository permissions and no secrets. Upload only protocol/manifests, per-trial summarized metrics, selected annual summaries, checks and the report. Raw and normalized vendor data and per-day return matrices stay in the temporary runner, as authorized. CI artifacts also expire; exact future replay requires a private raw-data copy after local execution is restored. Do not call summary retention byte-identical raw-data reproducibility.
Keep all existing application and frozen experiment files unchanged.

## Primary documentation
- https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_49_ind_port.html
- https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html
- https://github.com/ranaroussi/yfinance (unaffiliated Yahoo client; data terms apply)
