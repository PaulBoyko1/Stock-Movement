# E04-P1: frozen first industry-momentum experiment

Registered September 16, 2026, before running or viewing this implementation's return results. This is a retrospective proxy study, not pristine out-of-sample validation.

Source: Kenneth French [12 Industry Portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_12_ind_port.html), monthly value-weighted total-return panel. [CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/12_Industry_Portfolios_CSV.zip). Use all 12 series; fail on missing values/months or changed schema. Record retrieval time, raw SHA-256, source header, code commit, and fixed settings. Retain the raw downloaded vintage in the run artifact.

Evaluation: January 2000–December 2025 inclusive. Report continuous-portfolio subperiods 2000–2009, 2010–2019, 2020–2025; no parameter selection from these reports.

For holding month h, compound the eleven monthly returns h−12 through h−2. Omit h−1. Thus January 2000 ranks January–November 1999, skips December 1999 and receives January 2000's return. Select three highest ranks, tie-breaking by original industry-column order, equal weight, long only, fully invested, monthly rebalanced.

Benchmark: all 12 industries equal-weighted and rebalanced monthly with the same dates and cost convention. Industry portfolios themselves are value-weighted; our allocation across them is equal-weighted.

Before rebalancing, drift prior weights using the prior month's realized returns. Traded-notional fraction D = sum(abs(target − drifted weights)). Initial holdings are cash (D=1 for full entry). A full replacement trades D=2. Cost scenarios: 0, 10 (primary), 25 bp per dollar bought OR sold. Monthly wealth multiplier: (1 − cD) × (1 + gross return). Terminal liquidation multiplies the last month's wealth by (1 − c); include it for strategy and benchmark. Costs use a proportional target-weight haircut approximation; they are not exact self-financing charges on executed notionals. For example, cash entry uses 1−c rather than the exact 1/(1+c). This convention is fixed for this proxy experiment; an exact-cost variant would be a separate specification. Subperiod statistics retain their slice of the continuous run rather than creating artificial liquidation/re-entry at decade boundaries.

Report CAGR, annualized monthly volatility, maximum month-end drawdown, annual returns, traded-notional turnover, monthly active return (strategy minus benchmark), annualized arithmetic mean active return, and information ratio. Do not compound active differences as a funded portfolio. Use Newey-West lag 12 and a normal 95% interval for the mean monthly active return, annualized arithmetically; this approximate descriptive interval is not a discovery certificate. No model training, hyperparameter search, cash filter, leverage, stop-loss or post-result rule changes.

Limits: reconstructed research portfolios, not investable ETFs or modern GICS sectors; no liquid-stock-only restriction; historical data revisions; monthly boundary fills unverified; constituent trading, tracking error, taxes and fund fees excluded. Describe results as “after assumed allocation costs,” never as a validated executable edge. The contemporary ETF replication, factor-adjusted attribution and forward monitoring remain separate later tests.

References: [momentum construction](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html), [data vintage/reconstruction notes](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).
