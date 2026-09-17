# Bring your data and ideas as they are

Paste rough notes, upload files, or share links in the task whenever ready. Organization is optional. If known, the most useful extras are the source, approximate date, market/horizon, and what you think the material demonstrates.

Stock-Movement should preserve the original submission and then add an interpretation, evidence links, and a proposed next test. It should accept spreadsheets, CSV exports, PDFs, earnings notes, screenshots, chart setups and unfinished hypotheses.

## What happens next

1. Keep the original wording/file intact and assign an intake ID.
2. Identify observations, assumptions and hypotheses without conflating them.
3. Link duplicate or related ideas; retain disagreements and failed tests.
4. Check what the data actually contains and when each observation became available.
5. Propose the smallest useful comparison test and record its outcome.

Unknown fields remain unknown. Lack of data is not a failed strategy. Literature support does not automatically validate the submitted variant.

The simple review view is Original → Interpretation → Evidence → Next test. The source/version/transformation history can be expanded.

## Templates

- [Idea record](idea-template.json): optional structure for a note or hypothesis.
- [Data manifest](data-manifest-template.json): describes a dataset without publishing its rows.

These are starter formats, not an implemented import system. No user data has been received or imported yet.

## Data checks

| Material | What must be established before predictive testing |
|---|---|
| Prices | Raw/adjusted status, splits/dividends, currency, timezone, sessions, gaps, duplicates, later vendor revisions |
| Earnings | Fiscal period versus release time, quarterly versus YTD, units, GAAP/adjusted basis, amended/recast values |
| Estimates | Snapshot before the event, contributor/period coverage, definition, historical versus current consensus |
| Universes | Historical membership, delisted securities, identifier changes, selection rules |
| Ideas/charts | Exact trigger, when a pattern becomes knowable, horizon, comparison, disconfirming result |

Record transformations instead of silently repairing uncertainty.

## Storage boundary

This GitHub repository is public. The templates and sanitized research notes belong here. Raw future submissions default to private working storage outside the repository until their intended destination and reuse rights are established. Sharing material in this task does not authorize public publication.

The ignore rules cover common raw-data and credential paths; they are convenience safeguards, not a security boundary. No raw upload should be automatically copied or committed. Preserve a private source reference/hash where possible; publish only approved summaries or redistribution-safe data.
