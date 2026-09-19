# Stock-Movement

Research and decision support for liquid U.S. stocks and ETFs, with a simple interface and optional advanced analysis.

- [UI preview and opening instructions](research/ui/README.md) — interactive offline concept with historical and illustrative fixtures
- [UI design and behavior](research/ui/design-notes.md)
- [Research overview](research/README.md)
- [27-paper evidence register](research/evidence-register.md)
- [Structured paper catalog](research/evidence-catalog.json) — searchable in Evidence → Research papers
- [Historical earnings case studies](research/earnings-case-studies.md)
- [Experiment backlog](research/experiment-plan.md)
- [Industry-momentum specification](research/experiments/E04-P1-specification.md) and [observed result](research/results/E04-P1-results.md)
- [Preregistered factor diagnostic](research/experiments/E04-P2-specification.md) and [attribution result](research/results/E04-P2-results.md)
- [Next ETF test: data readiness and candidate rules](research/experiments/E04-P3-data-readiness.md)
- [Run and reproduce the experiments](research/code/README.md)
- [Bring your data and ideas](research/intake/README.md)

The industry baseline and six-factor attribution cover 312 months (2000–2025). At the primary assumed 10 bp allocation cost, factor-adjusted annual arithmetic alpha is approximately 0.29%, with a 95% interval of −2.67% to +3.24%. This does not establish positive alpha or an executable trading edge. The inputs are reconstructed industry research portfolios, not a point-in-time liquid-stock or tradable-ETF universe.

Validation: [33 statistical tests](https://github.com/PaulBoyko1/Stock-Movement/actions/runs/35304302447) and [browser interaction/responsive checks](https://github.com/PaulBoyko1/Stock-Movement/actions/runs/35304607841) passed.

The UI is an offline research prototype. Forecast models, live market data, durable intake storage and automated execution remain future work. Raw future submissions default to private storage; this repository is public.

The ETF follow-up has inspected two official issuer downloads and recorded their coverage and schema. Those files alone lack the required historical market prices and distributions; no ETF strategy result has been calculated. The Lab displays this unfinished data validation explicitly.
