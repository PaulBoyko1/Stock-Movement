# Historical earnings case studies

These deliberately historical 2025 releases are examples for extraction and hypothesis design, not current trading signals. All growth below is year over year unless stated otherwise. No earnings surprise is claimed without contemporaneous consensus. Exact release times still need verification before an intraday event study.

## Microsoft: FY2025 Q4 and full year

Quarter/year ended June 30, 2025; release dated July 30, 2025. Quarterly revenue was $76.4 billion, up 18%; operating income rose 23%; Azure and other cloud services revenue rose 39%.

Annual operating cash flow rose from $118.548 billion to $136.162 billion. Cash property/equipment additions rose from $44.477 billion to $64.551 billion. Calculated cash flow after those expenditures fell from $74.071 billion to $71.611 billion (−3.32%). Cash capex consumed 47.41% of operating cash flow versus 37.52%. This definition excludes noncash lease additions. Prior-period segment amounts were partly recast. [Official release and financial statements](https://www.microsoft.com/en-us/Investor/earnings/FY-2025-Q4/press-release-webcast)

Hypothesis: operating growth and investment intensity may provide different information; test both. Preserve annual versus quarterly scope. Higher investment could support future growth, so falling cash flow alone is not a bearish conclusion.

## Walmart: FY2026 Q2

Quarter ended July 31, 2025; released August 21, 2025. Revenue rose 4.8% to $177.4 billion and global e-commerce grew 25%. Operating income fell 8.2%; adjusted operating income grew 0.4% in constant currency. EPS of $0.88 included a $0.26 after-tax investment gain; adjusted EPS was $0.68 after additional legal/restructuring adjustments. Cash-flow improvement partly reflected payment timing and lower cash taxes. [Official earnings release](https://stock.walmart.com/sec-filings/all-sec-filings/content/0000104169-25-000120/earningsreleasefy26q2.htm)

Full-year constant-currency sales-growth guidance moved from 3–4% to 3.75–4.75%, a 0.75-percentage-point midpoint increase. Adjusted EPS guidance rose from $2.50–2.60 to $2.52–2.62, but adjusted operating-income guidance did not change. The anticipated currency headwind also eased, illustrating why a raised EPS forecast need not represent stronger underlying operations. [Official presentation, guidance table](https://stock.walmart.com/sec-filings/all-sec-filings/content/0000104169-25-000120/earningspresentationfy26.htm)

Hypothesis: distinguish sales, operating-profit and EPS revisions. Preserve reported versus constant-currency bases and all reconciliation items rather than treating adjusted results as automatically superior.

## JPMorgan Chase: Q2 2025

Quarter ended June 30, 2025; released July 15, 2025. EPS was $5.24; excluding a $774 million tax benefit contributing $0.28 per share, EPS was $4.96. Net interest income grew 2%, while the measure excluding Markets fell 1%. Credit costs of $2.8 billion included approximately $2.4 billion of net charge-offs and a $439 million reserve build. A prior-year Visa-related gain complicated comparisons. [Official earnings release](https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/quarterly-earnings/2025/2nd-quarter/ac5b7d95-9133-4fea-959c-2fa6d8fd8c5b.pdf)

Hypothesis: recurring interest income, realized credit losses and reserve changes may have separate predictive content. Use bank-specific measures and distinguish reported from managed results. Corporate free-cash-flow ratios should not be applied mechanically to banks.

## Caterpillar: Q2 2025

Quarter ended June 30, 2025; released August 5, 2025. Revenue fell 1% to $16.6 billion. A $414 million pricing headwind outweighed a $237 million volume contribution. Operating margin fell from 20.9% to 17.3%. [Official release](https://www.caterpillar.com/en/news/corporate-press-releases/h/2q25-results-caterpillar-inc.html)

Segment sales diverged: Construction Industries −7%, Resource Industries −4%, Energy & Transportation +7%. Higher tariffs contributed to manufacturing-cost pressure; dealer-inventory movements complicated volume interpretation. [Detailed release](https://www.caterpillar.com/content/dam/caterpillarDotCom/releases/2q25/2q25-caterpillar-inc-financial-results.pdf)

Hypothesis: segment breadth, pricing power and end-user demand may add information beyond consolidated sales. One company cannot establish a sector trend.

## Extraction record to implement

Each numeric or textual observation should retain: stable company ID; ticker as of that date; fiscal start/end; actual release/availability timestamp and timezone; document URL/hash/version; source passage/table; metric and units; GAAP/non-GAAP status; currency and constant-currency basis; segment; quarter/year/YTD scope; current/prior values; and restatement/recast marker.

Actuals, management guidance and consensus are separate records. Missing consensus remains missing. Preserve original values alongside normalized values. Reconcile cumulative cash-flow statements before deriving standalone quarters. Distinguish release dates from fiscal period ends and transcript availability from call time.

The four releases are hand-selected fixtures, not a representative validation sample. A useful next research dataset spans multiple sectors, changing market conditions, and both positive and negative operating outcomes. Every return test must begin after the required information and reaction window are available.

## Completed checks

The calculation audit verifies Microsoft's cash-flow arithmetic and Walmart's guidance-midpoint changes. No price-return backtest or causal inference was performed. The next stage should verify extraction across many reports before assessing predictive performance.
