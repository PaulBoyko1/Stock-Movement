# E04-P3: original-nine ETF momentum — data readiness

Status on September 18, 2026 (Pacific): **design and data audit only; no ETF strategy returns calculated**. This follows E04-P1/P2, whose results are already known. It is a candidate implementation study, not untouched strategy discovery. A complete specification must be frozen before inspecting its performance.

## What we want to learn

Does the unchanged momentum idea remain useful when implemented with actual ETF histories, distributions, fund expenses and explicit trading assumptions? This tests a different universe and accounting model from the twelve reconstructed industry portfolios. A favorable result would still need independent evaluation and forward monitoring.

Start with a fixed set of original funds: **XLB, XLE, XLF, XLI, XLK, XLP, XLU, XLV, XLY**. The trust's [SEC prospectus](https://www.sec.gov/Archives/edgar/data/1064641/000095013508000333/b67903a1e485bpos.htm) records their investment operations beginning December 16, 1998. That is not sufficient evidence of the first tradable price; verify listing dates and actual observations per fund.

Keep XLRE and XLC out of this first fixed-universe test. Their issuer pages record later inception dates: [XLRE, October 7, 2015](https://www.ssga.com/us/en/institutional/etfs/state-street-real-estate-select-sector-spdr-etf-xlre), and [XLC, June 18, 2018](https://www.ssga.com/us/en/institutional/etfs/state-street-communication-services-select-sector-spdr-etf-xlc). An expanding-universe experiment needs its own eligibility and warm-up rules; index backfills cannot stand in for pre-launch ETF returns.

This is a universe chosen for a research question and long fund history. It is not an unbiased study of all ETFs, a point-in-time liquidity screen, or a claim that the same economic sectors existed throughout the sample.

## What was actually downloaded and inspected

The [metadata audit](../etf-source-audit.json) records retrieval time, HTTP status, raw hashes, sheet ranges, observed coverage and unresolved checks. Raw workbooks remain in ignored local research storage. No raw vendor files were published.

| Official download | Observed contents | What it cannot provide by itself |
|---|---|---|
| [XLK NAV history](https://www.ssga.com/library-content/products/fund-data/etfs/us/navhist-us-en-xlk.xlsx) | 5,738 dated observations, December 1, 2003–September 17, 2026; NAV, shares outstanding, net assets | A 2000-start sample, exchange execution prices, dated distributions, or a verified total-return series |
| [SPDR product workbook](https://www.ssga.com/library-content/products/fund-data/etfs/us/spdr-product-data-us-en.xlsx) | 180 fund rows; pricing snapshot dated September 17, 2026; current close/high/low/volume and other product fields | A daily historical series, opening prices, or a distribution ledger |

The NAV table has no observed duplicate dates, weekend dates or missing NAV values. Shares outstanding and net assets each contain 628 dash placeholders. Trading-calendar completeness and adjustment conventions remain unchecked. The product workbook's return summaries have their own date, mostly August 31, 2026; fields do not all share one information cutoff.

These findings concern **these two downloaded files only**. They do not establish that other public or licensed sources cannot supply suitable history. A provider must be selected on documented coverage and adjustment behavior before running the strategy.

## Corporate actions and changing definitions

XLF's [2016 SEC notice](https://www.sec.gov/Archives/edgar/data/1064641/000119312516699787/d246445d497.htm) describes transferring real-estate holdings to XLRE and distributing XLRE shares. A raw XLF price drop around this event is not the investor's total return. Obtain the final entitlement, effective/ex/payment dates, and actual treatment of fractional shares. Reconcile the event independently. Do not count both an adjusted-price cash equivalent and received XLRE shares in portfolio wealth.

For a fixed-nine simulation, a proposed policy is to recognize received XLRE shares as a corporate-action holding and sell them at the first permitted post-delivery execution, charging the same cost convention. This policy and available prices must be resolved before freezing the simulation. It is not permission to silently add XLRE to the ranked universe.

The funds' exposures also change. Real estate left Financials in 2016 ([S&P announcement](https://press.spglobal.com/2016-03-08-S-P-Dow-Jones-Indices-And-MSCI-Revisions-To-The-Global-Industry-Classification-Standard-GICS-Structure)); XLK's benchmark removed Communication Services before the September 24, 2018 open ([index announcement](https://www.spglobal.com/spdji/en/documents/indexnews/announcements/20180423-697354/697354_technologyselectsectorindexconsultationresults4.23.2018.pdf)). Actual fund history is still meaningful, but a rotation chart must flag these definition breaks rather than apply today's sector labels to the entire past.

## Candidate rules to freeze after data acceptance

- Target evaluation remains January 2000–December 2025. Require actual pre-evaluation prices and enough warm-up to calculate every signal. Do not silently move the start date to accommodate one convenient file; an alternate sample requires a dated amendment before results.
- For holding month h, compound total returns for h−12 through h−2, skipping h−1. January 2000 therefore uses January–November 1999. Select the strongest three funds, equally allocate available investable wealth, and rebalance monthly. Specify deterministic alphabetical ticker tie-breaking. No trend filter, leverage, shorting or parameter search.
- Benchmark: all nine funds equally allocated, rebalanced on the same schedule and with the same cash and cost rules. A broad-market ETF can be a separately labeled descriptive comparison, not a substitute primary benchmark chosen after results.
- Use exchange prices for portfolio accounting and execution. The proposed fill is the first regular-session open of month h, after signals are known. Freeze the calendar, publication cutoff, holiday handling and terminal liquidation timestamp. A daily opening print remains a fill assumption; it does not establish achievable order size or spread.
- Keep shares, available cash and distribution receivables distinct. Accrue entitlement on the correct ex-date; cash becomes spendable only on payment. Handle splits and noncash distributions explicitly. Reinvest available cash at the next scheduled rebalance. Document any fractional-share abstraction.
- Calculate costs from bought and sold notionals using a self-financing budget. The proposed 0/10/25 bp cases, with 10 bp primary, are assumptions for comparison with P1; they are not measured ETF execution costs. Charge entry and terminal liquidation. Fund expenses embedded in observed ETF returns must not be subtracted again.
- Report CAGR, volatility, daily and month-end drawdowns separately, turnover, annual returns, cost sensitivity, and arithmetic active mean with the same clearly specified HAC interval. Reconcile wealth from the holdings ledger. Do not compound active differences as a funded return series.

The full execution and corporate-action specification remains unfinished. No code should label this candidate as preregistered or executable until those choices and source definitions are committed.

## Data acceptance gate

1. Archive source/version/hash, currency, timezone, price-field definitions, adjustment method, and usage/redistribution terms. Keep historical market prices separate from NAV and midpoint figures. The [issuer's performance definitions](https://www.ssga.com/us/en/institutional/etfs/state-street-technology-select-sector-spdr-etf-xlk) describe reinvestment and midpoint conventions; those are not a next-open fill history.
2. Confirm stable identifiers, first tradable dates, complete expected exchange sessions, unique observations and full nine-fund warm-up. Reject unexplained gaps and silent forward filling.
3. Obtain ordinary distributions, splits and noncash actions with effective dates; independently reconcile XLF's 2016 event and selected normal-dividend windows. Define tolerances before reading strategy returns.
4. Verify the signal return convention against independently constructed returns and matching issuer summaries. Reconcile like-for-like NAV or market conventions; differences between them are not automatically errors.
5. Test execution timing, cash availability, entitlement accounting, budget conservation, costs, terminal valuation and missing-data failures using synthetic fixtures.
6. Commit the accepted data manifest and completed specification before the first performance run. Preserve all later amendments and failed checks.

The UI should currently show **Data validation incomplete**. The completed NAV/snapshot inspection is useful evidence about data suitability, not a failed or successful trading strategy.
