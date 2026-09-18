# Review the UI concept

[Download index.html](https://raw.githubusercontent.com/PaulBoyko1/Stock-Movement/codex/research-foundation/research/ui/index.html), save it as an HTML file, and open it in a browser. GitHub's file page shows source code; it does not run the interface. No installation or server is needed.

The concept contains five working views, Today/Weeks/Months/Years research context, simple/advanced detail, light/dark themes, four historical company reports, an illustrative sector map, and a temporary idea preview. It has no live data, forecast service, saved intake or trade execution.

[Design notes](design-notes.md) explain the intended product behavior and remaining decisions.

## Preview

![Overview in light mode](previews/overview-desktop.jpg)

[Sector rotation](previews/rotation-desktop.jpg) · [Research lab in dark mode](previews/lab-dark.jpg) · [Company evidence on mobile](previews/evidence-mobile.jpg)

## Checks performed

The [successful browser run](https://github.com/PaulBoyko1/Stock-Movement/actions/runs/35304607841) used Chromium 140.0.7339.16 and Playwright 1.55.0 on code `5add7527c00ca9b1943afb466eb0c328239c4e9e`. Its [machine-readable check record](checks.json) contains 76 named checks, with additional browser assertions for content and control states.

- Navigation, keyboard focus and skip link; all four horizons; simple/advanced switching; both themes.
- All four company fixtures/source links and sector selections.
- Literal-text handling of HTML-looking inbox input, changed-note invalidation, clear, and reload reset.
- No document overflow at widths 320, 390, 768 and 1440 pixels, across every view with advanced mode both on and off.
- No JavaScript errors, external network requests or browser storage during the exercised flow.

The first browser run caught a narrow-screen Lab overflow; card sizing and mobile wrapping were corrected before the successful run. Desktop overview, rotation, dark Lab and mobile earnings screenshots were also visually inspected. Eight selected text/status color pairs were checked against their CSS colors ([ratios](contrast-checks.json)); this is not a complete accessibility audit. Other browser engines, real devices and assistive technologies have not been tested.

Screenshots in this folder are retained with the repository. The Actions artifact (ID 10531167810) expires 2026-10-18T03:49:30Z.

To rerun locally:

```sh
python -m pip install playwright==1.55.0
python -m playwright install chromium
python research/ui/verify_ui.py
```

Linux CI also installs Chromium's system dependencies. The script writes screenshots and checks to `work/ui/`; on a failed named check it retains diagnostic output. The statistical research suite is separate: [run instructions](../code/README.md).
