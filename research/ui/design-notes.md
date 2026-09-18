# Stock-Movement UI concept v0.1

This is a self-contained, offline, conceptual research interface in `index.html`. It is not a production application, trading model, or live market dashboard. No dependencies, external fonts, network requests, analytics, backend, cookies, local storage or persistence are used. External source links are followed only when the user chooses them.

## Product decision

Lead with a research question and an explanation of what changed. Put evidence quality and uncertainty beside any result. The simple view should answer: what changed, over what horizon, what supports the interpretation, what could contradict it, and which checks are still missing. Advanced detail reveals measurement definitions and validation requirements; it never promotes an untested signal into a stronger claim.

A quiet, editorial workspace uses a persistent left navigation, restrained forest green, warm neutral surfaces, compact status labels and readable report cards. Light and dark themes share the same hierarchy. Green indicates evidence or emphasis, not a recommendation to buy. Mobile navigation becomes a horizontal row, cards stack, tables retain horizontal scrolling, and keyboard focus remains visible.

## Five views

| View | Purpose | Working interaction |
|---|---|---|
| Overview | Connect the research question, historical report fixtures and preliminary baseline | Report cards open the relevant company; calls to action open Evidence, Lab or Inbox |
| Evidence | Separate sourced observations, working hypotheses and counterarguments | MSFT, WMT, JPM and CAT selectors replace the report, metrics, caveats and official source link |
| Rotation | Explain relative strength and acceleration without a mystery score | Sector selector changes the highlighted illustrative point and interpretation |
| Research lab | Keep performance, comparison, assumptions and uncertainty together | Advanced mode reveals universe, allocation and cost details |
| Idea inbox | Preview how rough material could become a testable claim | Text preview, editing invalidation, explicit clear and reload reset; no saved record |

## Horizon behavior

The global horizon control changes the question, overview narrative and availability notice. It does not transform the fixed underlying historical fixtures or recompute a backtest.

- **Today:** intraday models unavailable. Precise report availability, timestamped prices, spreads and executable costs have not been loaded.
- **Weeks:** earnings and guidance hypotheses; no consensus or event-return model is loaded.
- **Months:** preliminary industry momentum evidence; no current ranking or validated ETF model.
- **Years:** scenario-only research about business durability, reinvestment and valuation assumptions; no validated long-term return model.

Showing the unchanged historical result with its dates prevents the horizon switch from silently relabeling one model as four models. A production implementation should route each horizon to its own explicitly validated model and eligible data.

## Historical evidence boundaries

The four report fixtures and official links come from [earnings-case-studies.md](../earnings-case-studies.md). They are deliberately selected historical 2025 reports, not current signals or a representative validation sample.

- MSFT: annual operating cash flow, cash property/equipment additions, and calculated cash flow after those expenditures. Noncash lease additions are excluded.
- WMT: full-year guidance presented with FY2026 Q2. Constant-currency sales guidance, adjusted EPS and adjusted operating income retain separate bases.
- JPM: quarterly EPS, tax benefit and credit costs. Bank-specific comparability is preserved.
- CAT: quarterly segment sales and their divergence. One company cannot establish sector breadth.

Release dates are displayed; exact release timestamps remain unverified. Consensus is absent, so the UI does not claim an earnings surprise.

The rotation map uses **fictional coordinates and trails**. Every position is explicitly illustrative and no market date is attached. It is an original concept, not a reproduction of proprietary RRG formulas. Advanced mode specifies a proposed, unvalidated definition: q(t) = log(sector total-return index / benchmark total-return index); horizontal = q(t) − q(t−63); vertical = [q(t) − q(t−21)] − [q(t−21) − q(t−42)]. These match the research proposal and remain unvalidated. Quadrants describe relative positions, not future paths.

## Lab snapshot

The interface carries the supplied E04-P1 results, 2000–2025. It selects three of twelve Kenneth French value-weighted research industry portfolios using monthly 12–1 momentum. The comparison equally weights all twelve industries. The universe has no liquid-stock eligibility filter; it is not an ETF backtest.

Primary results include a 10 bp proportional allocation-change cost approximation:

| Metric | Momentum | Benchmark |
|---|---:|---:|
| CAGR | 10.86% | 8.87% |
| Annualized volatility | 16.83% | 15.12% |
| Largest month-end drawdown | −39.49% | −49.57% |

The annualized arithmetic mean active return is 2.08%, with a 95% interval of [−1.02%, 5.18%]. The interval includes zero. This is **not** an interval for the CAGR difference, a factor-adjusted alpha, a future-return range, or a probability of success.

The simple view notes that the 2010s drawdown was worse for the strategy (−23.19%) than the benchmark (−17.51%). The full-period drawdown is not a general safety claim. No historical wealth curve is fabricated from summary statistics. The results page is a fixed snapshot, and controls never suggest they rerun research.

The subsequent E04-P2 six-factor diagnostic is displayed separately: annualized arithmetic alpha 0.29%, approximate 95% HAC interval [−2.67%, 3.24%], also including zero. R² 0.430 describes variation explained in historical active returns; it is not forecasting accuracy. [Results and reproduction](../results/E04-P2-results.md).

## Intake and privacy

The inbox is a textarea and a literal-text preview. It performs no upload, classification model call, verification or saving. Editing hides the stale preview. Clear erases both text and preview. The page-show event clears restored form content as well, keeping the stated reload behavior accurate. Raw text is rendered with `textContent`, not interpreted as HTML.

For a future import feature, preserve private original files separately from publishable summaries. The intake record should include the source, usage permission, collection date, claim, horizon, universe, proposed features, baseline, failure condition, verification state and related experiment. Publishing user-supplied material must be a deliberate destination choice; a real backend needs an explicit access-control design.

## Stable selector contract

| Behavior | Selector / expected result |
|---|---|
| Navigate | `#nav-overview`, `#nav-evidence`, `#nav-rotation`, `#nav-lab`, `#nav-inbox` |
| Visible view | Exactly one `#view-overview/evidence/rotation/lab/inbox` lacks `hidden` |
| Active navigation | The matching navigation button has `aria-current="page"` |
| Horizon | `#horizon-today/weeks/months/years`; selected button has `aria-pressed="true"` |
| Horizon caveat | `#horizon-notice-text` |
| Advanced switch | `#advanced-toggle`, role `switch`, `aria-checked` |
| Advanced content | `[data-advanced]` toggles `hidden` |
| Theme | `#theme-toggle` changes `body[data-theme]` between `light` and `dark` |
| Company selection | `#company-msft/wmt/jpm/cat` |
| Company content | `#company-name`, `#company-period`, `#company-thesis`, `#company-metrics`, `#company-source` |
| Company details | `#company-hypothesis`, `#company-counter`, `#company-measurement` |
| Sector | `#sector-select` accepts `industrials/technology/healthcare/utilities` |
| Sector output | `#sector-name`, `#sector-position`, `#sector-description`, `#sector-question` |
| Map highlight | `#point-industrials/technology/healthcare/utilities`; selected point class `map-focus` |
| Results | `#lab-results` |
| Inbox input | `#idea-input`, max length 12000 |
| Preview / clear | `#idea-preview-button`, `#idea-clear-button` |
| Preview result | `#idea-preview` visibility, `#idea-preview-text` literal content |
| Inbox status | `#idea-status` live status, `#idea-count` character count |

Suggested QA: navigate all five views; check only one is visible; exercise all horizons and their caveats; switch advanced on/off in each view; check both themes; inspect all four company source URLs; inspect all four sectors; paste HTML-looking text into the inbox and verify literal rendering; edit, clear and reload; verify mobile layout and table overflow; check keyboard focus, skip link and console errors. Network inspection should show no requests from the prototype itself.

## Next implementation questions

1. Which sourced observations deserve reusable cards, and which need a sector-specific detail panel?
2. What validation threshold allows a research result to appear beside a current instrument?
3. Can every forecast carry its horizon, benchmark, data cutoff, calibration and known limitations without overwhelming the simple view?
4. Which fields are required before the user's collected material can become a reproducible experiment?
5. What real-time data and point-in-time historical coverage are affordable and legally usable for each horizon?

Keep actual security selection, forecast probabilities, trade execution, persisted imports and user accounts outside this prototype until their inputs and contracts exist.
