# Stock-Movement research foundation

Research date: September 15, 2026 (Pacific). Scope agreed with the owner: liquid U.S. stocks and ETFs. Immediate purpose: research and decision support; later stages may add alerts, paper trading, and automated execution.

This is a research foundation with an executed industry-allocation proxy experiment, a subsequent factor diagnostic, and an offline UI concept. It is not an implemented stock forecasting system. The first pass screened 27 primary research papers, the original RRG guide, public data documentation, and four historical company earnings releases with supporting material. Verification means bibliographic details and the cited findings were checked against primary pages or accessible paper sections. It does not mean every paper was read end to end, replicated, or shown to work in today's market.

## Follow-up: September 16, 2026

The first [historical industry-momentum proxy result](results/E04-P1-results.md) is now recorded: 312 months, 16 implementation tests passed, and three fixed allocation-cost scenarios. This is narrower than a liquid-stock or tradable-ETF backtest. [Data and idea intake](intake/README.md) is ready as a guide and templates; no user dataset has been imported.

## Follow-up: September 17, 2026

The [preregistered E04-P2 diagnostic](experiments/E04-P2-specification.md) reproduced the baseline and assessed six contemporaneous stock factors. Primary annual arithmetic alpha is about 0.29%, with a 95% HAC interval of −2.67% to +3.24%. See the [full attribution result](results/E04-P2-results.md). This does not establish positive conditional alpha, and the unchanged rule stays in research.

The [offline interactive concept](ui/index.html) now explores Overview, Evidence, Rotation, Lab and Inbox, with horizon selection and simple/advanced detail. It uses dated historical fixtures and explicitly illustrative rotation positions. [Design notes](ui/design-notes.md) describe the interactions and what a working product still needs. No user dataset has been imported, and the prototype provides no persistent storage.

## Start here

September 18 follow-up: the UI's Evidence page now includes a searchable [27-paper catalog](evidence-catalog.json), alongside the historical company reports. Findings, caveats, proposed applications and original screening limits remain separate. The catalog inherits the existing literature screen; it is not a new replication exercise.

The [ETF data-readiness review](experiments/E04-P3-data-readiness.md) defines the next candidate test and documents an actual [issuer workbook audit](etf-source-audit.json). The inspected NAV and product-snapshot downloads do not provide the full market-price and corporate-action history required. No ETF strategy returns have been generated.

- [Evidence register](evidence-register.md): 27 papers, findings, limitations, and possible applications.
- [Earnings case studies](earnings-case-studies.md): Microsoft, Walmart, JPMorgan Chase, and Caterpillar.
- [Experiment plan](experiment-plan.md): hypotheses, data requirements, comparison models, and promotion criteria.
- [Calculation audit](calculation-audit.json): computations actually performed during this review.

The most promising first research product combines medium-horizon price momentum, industry context, earnings changes, and longer-horizon business quality. Intraday forecasting belongs in a separate research track because timestamps, spread, latency, and fills can dominate the apparent edge. This priority is a design judgment based on the literature, not a completed comparison of strategies.

## What “proven” should mean

Use precise stages: published historical result → internally reproduced → tested out of sample after costs → forward paper traded → eligible for controlled deployment. Most candidates remain at the literature/hypothesis stage. E04-P1 has one executed historical proxy test; its uncertainty interval includes zero and it has not passed executable-market or forward validation. A study can be reproducible yet impractical in a liquid-stock universe; a useful explanation of prices can also fail as a forecast.

Forecast distributions and relative rankings, not guaranteed price targets. Separate probability of a positive raw return from probability of outperforming a benchmark. A bullish market can give many stocks positive returns without any stock-selection skill.

## Match the inputs to the horizon

| Horizon | Questions the product can address | Inputs to investigate | Main limitation |
|---|---|---|---|
| Intraday: seconds to a session | Is continuation or reversal more likely? Is this a poor time to execute an already planned order? | Lagged order flow, spread/depth, time of day, market/sector moves, event timing | Small gross effects can disappear after spread, latency and impact |
| Days to weeks: 1–20 sessions | Is an earnings change being incorporated gradually? Is an unusual move persistent? | Surprise, guidance revision, initial reaction, liquidity, short reversal | Consensus availability and correct entry timing |
| Months: 1–6 months | Which stocks and industries have persistent relative strength? | 12–1 momentum, industry momentum, analyst changes, operating trends | Momentum crashes, crowding, and correlated exposures |
| Long term: 1–5 years | Is operating performance, valuation and balance-sheet resilience attractive across scenarios? | Profitability, cash conversion, valuation, investment discipline, dilution and debt | Average-return evidence does not deliver an exact future price/date |

The horizons and boundaries are product choices to test. Academic studies often use different formation and holding periods. Initial 1–5-year output is assumption-based business/valuation scenarios, not calibrated multi-year forecasts. E07 tests only through approximately one year; separate preregistered multi-year tests with sufficient history would be required before reporting 3–5-year forecast probabilities.

## Signal families and priorities

**First research tier:** stock and industry momentum; earnings/guidance changes; profitability and valuation; volatility and liquidity as risk/execution context. Prioritize simple definitions and compare each against a transparent baseline. The main motivation is evidence in [value and momentum](https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere), [industry momentum](https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00146), and [profitability](https://www.nber.org/papers/w15940), with substantial implementation caveats in the register.

**Second research tier:** earnings quality, sector operating breadth, calibrated late-session ETF continuation, mechanically defined chart patterns, and document changes. Treat these as incremental features that must improve an existing model.

**Advanced tier:** order-book forecasts, nonlinear interactions, news/transcript models, options positioning proxies, and adaptive regime models. Their data and validation burden is higher. Inferred dealer positioning must be labeled as an estimate, not a directly observed fact.

Moving averages, MACD, RSI and many breakout indicators reuse price information. Agreement among them does not automatically constitute independent confirmation. Begin with one or two representatives per information family; test incremental value rather than collecting an indicator count.

Head-and-shoulders, double bottoms, support/resistance, gaps, volume expansion and volatility compression can become reproducible hypotheses. Specify what constitutes a pattern, when it becomes observable, the entry delay, the exit rule, and the failure condition. Handpicked chart examples establish none of these.

## Sector rotation without false precision

Show both absolute performance and performance relative to a chosen market benchmark. A sector can lead its benchmark while still losing money.

The [original RRG guide](https://relativerotationgraphs.com/wp-content/uploads/2024/10/Relative-Rotation-Graph-Thomson-Reuters-Guide.pdf) describes proprietary JdK formulas. A transparent initial alternative should be called “Sector relative strength,” with its own disclosed mathematics:

- Let q(s,t) = log(total-return index for sector s / total-return index for benchmark).
- Horizontal: q(s,t) − q(s,t−63), a roughly three-month relative return.
- Vertical: [q(s,t) − q(s,t−21)] − [q(s,t−21) − q(s,t−42)], acceleration of one-month relative performance.
- Add weekly historical trails, absolute return, volatility, component breadth, and observation date.

These windows are starting hypotheses, not optimized or validated settings. Crossing a quadrant is a descriptive event until it beats a plain momentum baseline in subsequent tests.

Keep price rotation separate from fundamental rotation. Fundamental breadth might measure the share of reporting peers with improving comparable operating metrics. Display the coverage denominator, stale observations, and weights. A few selected earnings reports cannot establish sector-wide rotation.

Macro context can include rates, inflation, credit conditions and commodity exposure, but a fixed “economic phase implies winning sector” clock should remain a hypothesis. Historical tests must use data as released at the time, not later revisions. Industry and sector classification changes also require historical handling.

## Simple UI

The default page should answer: what changed, over which horizon, why it matters, and how much evidence supports the interpretation.

1. Horizon selector: Today / Weeks / Months / Long term.
2. Market context: direction, volatility, breadth and upcoming major events, with observation times.
3. Watchlist: instrument, recent change, trend, earnings observations, sector context, and data/evidence status.
4. One stock page: three concise supporting observations, conflicting evidence, next known catalyst, price/volume chart, and source links.
5. Sector relative-strength map with absolute returns beside relative rankings.
6. Research journal: original thesis, information available then, expected horizon, and subsequent outcome.

Avoid an unexplained 0–100 conviction score. Before models are validated, show observations and evidence status. Later, a forecast card can show a calibrated benchmark-relative probability, expected return distribution, downside estimate, sample size, and as-of time. Missing information must remain visible; “insufficient evidence” is a valid result.

An illustrative observation is “sales outlook raised, operating-profit outlook unchanged.” It is more useful than automatically tagging the company “bullish.”

## Advanced UI

An “Advanced” switch should expose the same underlying research, including:

- Exact feature definitions, lookbacks, sector comparisons and data lineage.
- Baseline versus enhanced-model results, separate by horizon.
- Net/gross return, drawdown, turnover, factor exposure and cost sensitivity.
- Out-of-sample dates, probability calibration, uncertainty and sample counts.
- Event replay showing what was known at each timestamp.
- Experiment history, failed hypotheses, model version and drift monitoring.

Do not hide contradictory information in advanced mode. The simple view still needs the principal uncertainty and counterargument.

## How to combine signals

Use separate models by horizon. Within a horizon, start with a simple rank model or regularized regression, then add information families one at a time: market/sector → price → earnings → business quality → interactions. Train transformations only on the training period.

Test quality and momentum individually, additively, and as an interaction. Do the same for guidance and price reaction. A combined score must improve beyond both additive components; a plausible story is insufficient.

Machine learning may capture interactions, but [Gu, Kelly and Xiu](https://www.nber.org/papers/w25398) study asset risk premia, not a universal real-time trading oracle. An LLM is initially most useful for extracting source-linked claims and explaining changes. Validate every numeric extraction and keep probabilistic language grounded in actual model outputs.

## Data design before infrastructure choices

Store stable security identifiers, historical ticker mappings, original reports, fiscal periods, publication and receipt times, metric definitions, revisions, source passages, and data vintages. Release, earnings call, transcript and SEC filing can be separate information events.

[SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) provide submissions and standardized entity-level XBRL facts. Guidance, company-specific segment metrics and archived analyst consensus need additional sources. Never infer an earnings “beat” from positive year-over-year growth.

[French's data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) supports factor/industry research and baseline replication; its portfolios are not executable stock recommendations. Archive downloads: the library revises history and changed its underlying CRSP format beginning in 2025.

For production research, obtain point-in-time membership, delisting returns, corporate actions, adjusted research prices, raw executable prices, and event-time quotes appropriate to the experiment. Vendor selection, costs and licensing remain open decisions; no subscriptions or integrations were activated.

## Practical sequence

1. Establish a dated source/evidence register and hand-checked earnings extraction fixtures.
2. Reproduce simple daily/monthly baselines in the agreed liquid universe.
3. Test whether earnings and fundamental changes add value after costs.
4. Build the basic research UI on the validated data pipeline.
5. Add paper-trading alerts only for strategies with adequate out-of-sample evidence.
6. Consider automation after forward monitoring supports execution assumptions, with exposure limits, reconciliation, data-failure handling and a kill switch.

The initial review completed source screening, hypothesis design and arithmetic checks. The September 16 follow-up executed E04-P1 on reconstructed monthly industry returns. The September 17 follow-up added E04-P2 attribution and an offline UI prototype. A point-in-time liquid-stock dataset, connected application, validated earnings model and tradable edge remain outstanding.
