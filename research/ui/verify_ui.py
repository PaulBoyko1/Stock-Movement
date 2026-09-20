"""Browser checks for the offline research concept; no external services."""
import base64
import hashlib
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

OUTPUT = Path("work/ui")
OUTPUT.mkdir(parents=True, exist_ok=True)
checks = []
errors = []
network = []

def check(name, condition):
    if not condition:
        (OUTPUT / "failure.json").write_text(json.dumps({"failed": name, "passed": checks}, indent=2))
        page.screenshot(path=str(OUTPUT / "failure.jpg"), type="jpeg", quality=65, full_page=True)
        print("OVERFLOW_DIAGNOSTICS", page.evaluate("Array.from(document.querySelectorAll('body *')).filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,id:e.id,class:e.className,width:e.getBoundingClientRect().width})).slice(0,30)"))
        raise AssertionError(name)
    checks.append(name)

def snapshot(page, name, full_page=True):
    page.evaluate("window.scrollTo(0,0)")
    page.evaluate("new Promise(requestAnimationFrame)")
    path = OUTPUT / (name + ".jpg")
    page.screenshot(path=str(path), type="jpeg", quality=65, full_page=full_page,
                    animations="disabled")
    if os.environ.get("EMIT_IMAGE_DATA") == "1":
        print("UI_IMAGE_BEGIN:" + name)
        print(base64.b64encode(path.read_bytes()).decode("ascii"))
        print("UI_IMAGE_END:" + name)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("request", lambda req: network.append(req.url) if req.url.startswith(("http:", "https:")) else None)
    page.goto(Path("research/ui/index.html").resolve().as_uri())
    expect(page).to_have_title("Stock-Movement · Research workspace")
    page.keyboard.press("Tab")
    expect(page.locator(".skip")).to_be_focused()
    page.keyboard.press("Enter")
    check("skip link targets main content", page.evaluate("location.hash") == "#main")

    views = ["overview", "evidence", "rotation", "lab", "backtest", "inbox"]
    for name in views:
        page.locator("#nav-" + name).click()
        expect(page.locator("#view-" + name)).to_be_visible()
        expect(page.locator("#nav-" + name)).to_have_attribute("aria-current", "page")
        check("single visible view: " + name, page.locator(".view:visible").count() == 1)
        check("view receives keyboard focus: " + name, page.evaluate("document.activeElement.id") == "view-" + name)

    for horizon, phrase in [("today", "Intraday models unavailable"), ("weeks", "Hypotheses"),
                            ("months", "Preliminary evidence"), ("years", "Scenario-only")]:
        page.locator("#horizon-" + horizon).click()
        expect(page.locator("#horizon-" + horizon)).to_have_attribute("aria-pressed", "true")
        expect(page.locator("#horizon-notice-text")).to_contain_text(phrase)
        check("one horizon selected: " + horizon,
              page.locator("[data-horizon][aria-pressed=true]").count() == 1)
    page.locator("#horizon-months").click()

    page.locator("#advanced-toggle").focus()
    page.keyboard.press("Space")
    expect(page.locator("#advanced-toggle")).to_have_attribute("aria-checked", "true")
    check("keyboard enables advanced content", page.locator("[data-advanced]").evaluate_all("(els)=>els.every(e=>!e.hidden)"))
    page.keyboard.press("Space")
    check("keyboard hides advanced content", page.locator("[data-advanced]").evaluate_all("(els)=>els.every(e=>e.hidden)"))
    page.locator("#theme-toggle").click()
    expect(page.locator("body")).to_have_attribute("data-theme", "dark")
    page.locator("#theme-toggle").click()
    expect(page.locator("body")).to_have_attribute("data-theme", "light")
    checks.append("both themes toggle")

    sources = {"msft": ("Microsoft", "https://www.microsoft.com/"),
               "wmt": ("Walmart", "https://stock.walmart.com/"),
               "jpm": ("JPMorgan Chase", "https://www.jpmorganchase.com/"),
               "cat": ("Caterpillar", "https://www.caterpillar.com/")}
    page.locator("#nav-evidence").click()
    for key, (name, prefix) in sources.items():
        page.locator("#company-" + key).click()
        expect(page.locator("#company-name")).to_have_text(name)
        check("company source: " + key, page.locator("#company-source").get_attribute("href").startswith(prefix))
        check("three source observations: " + key, page.locator("#company-metrics .observation").count() == 3)
        expect(page.locator("#company-counter")).not_to_be_empty()

    catalog_path = Path("research/evidence-catalog.json")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    page.locator("#evidence-tab-papers").click()
    expect(page.locator("#evidence-companies")).to_be_hidden()
    check("all 27 screened papers available", page.locator("[data-paper-id]").count() == 27)
    expect(page.locator("#paper-count")).to_have_text("27 of 27 papers")
    page.locator("#paper-search").fill("r11")
    expect(page.locator("#paper-count")).to_have_text("1 of 27 papers")
    expect(page.locator("#paper-id")).to_have_text("R11")
    expect(page.locator("#paper-limitation")).not_to_be_empty()
    expected_source = next(p["source_url"] for p in catalog["papers"] if p["id"] == "R11")
    expect(page.locator("#paper-source")).to_have_attribute("href", expected_source)
    check("paper source follows selected record", True)
    page.locator("#paper-reset").click()
    page.locator("#paper-horizon").select_option("intraday")
    expected_ids = {p["id"] for p in catalog["papers"] if "intraday" in p["horizons"]}
    shown_ids = set(page.locator("[data-paper-id]").evaluate_all("els=>els.map(e=>e.dataset.paperId)"))
    check("application filter matches catalog without promoting evidence", shown_ids == expected_ids)
    selected = next(p for p in catalog["papers"] if p["id"] in expected_ids)
    page.locator("#paper-family").select_option(selected["family"])
    combined = {p["id"] for p in catalog["papers"] if p["family"] == selected["family"] and "intraday" in p["horizons"]}
    check("application and family filters intersect", set(page.locator("[data-paper-id]").evaluate_all("els=>els.map(e=>e.dataset.paperId)")) == combined)
    page.locator("#paper-search").fill("<img src=x onerror=alert(1)> no matching paper")
    expect(page.locator("#paper-empty")).to_be_visible()
    expect(page.locator("#paper-detail")).to_be_hidden()
    expect(page.locator("#paper-count")).to_have_text("0 of 27 papers")
    check("empty search hides stale paper and creates no markup", page.locator("#paper-list img").count() == 0)
    page.locator("#paper-reset").click()
    page.locator('[data-paper-id="R21"]').focus()
    page.keyboard.press("Enter")
    expect(page.locator("#paper-id")).to_have_text("R21")
    check("paper selection supports keyboard", True)
    page.locator("#nav-overview").click()
    page.locator('[data-company="wmt"]').click()
    expect(page.locator("#evidence-companies")).to_be_visible()
    expect(page.locator("#company-name")).to_have_text("Walmart")
    check("overview report card exits literature mode", True)

    page.locator("#nav-rotation").click()
    expect(page.locator("#view-rotation")).to_contain_text("ILLUSTRATIVE COORDINATES")
    for sector in ["industrials", "technology", "healthcare", "utilities"]:
        page.locator("#sector-select").select_option(sector)
        expect(page.locator("#sector-name")).to_have_text(sector.capitalize())
        expect(page.locator("#point-" + sector)).to_have_attribute("class", "map-focus")
        check("one selected sector: " + sector, page.locator(".map-focus").count() == 1)

    page.locator("#nav-lab").click()
    expect(page.locator("#lab-results")).to_contain_text("Largest month-end drawdown")
    expect(page.locator("#lab-risk-note")).to_be_visible()
    expect(page.locator("#lab-risk-note")).to_contain_text("2010s")
    expect(page.locator("#factor-card")).to_contain_text("−2.67% to +3.24%")
    expect(page.locator("#factor-card")).to_contain_text("do not establish positive")
    expect(page.locator("#etf-readiness")).to_contain_text("DATA VALIDATION INCOMPLETE")
    checks.append("uncertainty and counterevidence visible in simple mode")

    page.locator("#nav-backtest").click()
    expect(page.locator("#view-backtest")).to_contain_text("monthly")
    expect(page.locator("#backtest-export")).to_be_disabled()
    page.locator("#backtest-run").click()
    expect(page.locator('[data-metric="strategy.cagr"]')).to_have_text("10.86%")
    expect(page.locator('[data-metric="benchmark.cagr"]')).to_have_text("8.87%")
    expect(page.locator('[data-metric="strategy.maxDrawdown"]')).to_have_text("-39.49%")
    expect(page.locator("#backtest-run-count")).to_have_text("1 run completed")
    original_path = page.locator("#backtest-wealth-chart .strategy-line").get_attribute("d")
    check("backtest draws both wealth and drawdown comparisons", page.locator("#backtest-results svg path").count() == 4)
    page.locator("#backtest-observation").focus()
    page.keyboard.press("ArrowRight")
    expect(page.locator("#backtest-observation-details")).to_contain_text("2000-02")
    check("keyboard month inspector moves chart markers", page.locator("#backtest-results .observation-dot").count() == 4)
    page.locator("#backtest-lookback").fill("6")
    expect(page.locator("#backtest-results")).to_have_attribute("data-stale", "true")
    expect(page.locator("#backtest-export")).to_be_disabled()
    page.locator("#backtest-run").click()
    expect(page.locator("#backtest-results")).to_have_attribute("data-stale", "false")
    check("changing formation window recalculates wealth", page.locator("#backtest-wealth-chart .strategy-line").get_attribute("d") != original_path)
    expect(page.locator("#backtest-run-count")).to_have_text("2 runs completed")
    with page.expect_download() as download_info:
        page.locator("#backtest-export").click()
    exported = json.loads(Path(download_info.value.path()).read_text(encoding="utf-8"))
    # The export includes a reproducible result and the session's attempted settings.
    exported_result = exported["current"]
    check("export preserves actual settings, data provenance and observations",
          exported_result["params"]["lookback"] == 6 and len(exported_result["points"]) == 312
          and exported_result["sourceSha256"] == "c7316c6ae07bc2028632b57ad757dfef8303a62a6956946d7aabe926aadfdeb4")
    check("export records session trials and source vintage", len(exported["history"]) == 2
          and exported["dataset"]["sourceHeader"].startswith("This file was created using the 202607"))
    for field, value, error in [("lookback", "1.5", "integer"), ("skip", "", "required"),
                                ("top-k", "13", "integer"), ("cost-bps", "-1", "between")]:
        page.locator("#backtest-baseline").click()
        page.locator("#backtest-" + field).fill(value)
        page.locator("#backtest-run").click()
        expect(page.locator("#backtest-error")).to_contain_text(error)
        expect(page.locator("#backtest-export")).to_be_disabled()
        check("invalid input is rejected without silent correction: " + field, page.locator("#backtest-" + field).input_value() == value)
    page.locator("#backtest-baseline").click()
    page.locator("#backtest-start").fill("2010-01")
    page.locator("#backtest-end").fill("2019-12")
    page.locator("#backtest-skip").fill("2")
    page.locator("#backtest-cost-bps").fill("25")
    page.locator("#backtest-run").click()
    expect(page.locator("#backtest-status")).to_contain_text("120 monthly")
    expect(page.locator("#backtest-applied")).to_contain_text("skip 2")
    expect(page.locator("#backtest-applied")).to_contain_text("25 bp")
    check("date, skip and cost inputs apply to the displayed run", "2010-01" in page.locator("#backtest-applied").inner_text())
    page.locator("#backtest-end").fill("2009-12")
    page.locator("#backtest-run").click()
    expect(page.locator("#backtest-error")).to_contain_text("Start must precede end")
    page.locator("#backtest-baseline").click()
    page.locator("#backtest-start").fill("1994-01")
    page.locator("#backtest-run").click()
    expect(page.locator("#backtest-error")).to_contain_text("Insufficient history")
    expect(page.locator("#backtest-export")).to_be_disabled()
    expect(page.locator('[data-metric="strategy.cagr"]')).to_have_text("—")
    check("invalid warmup clears result and prevents export", page.locator("#backtest-wealth-chart path").count() == 0)
    page.locator("#backtest-baseline").click()
    expect(page.locator("#backtest-lookback")).to_have_value("11")
    expect(page.locator("#backtest-start")).to_have_value("2000-01")
    page.locator("#backtest-run").click()
    check("restore baseline reproduces original curve", page.locator("#backtest-wealth-chart .strategy-line").get_attribute("d") == original_path)
    page.locator("#backtest-top-k").fill("12")
    page.locator("#backtest-run").click()
    check("holding all industries matches comparison in UI",
          page.locator('[data-metric="strategy.cagr"]').inner_text() == page.locator('[data-metric="benchmark.cagr"]').inner_text())
    page.locator("#backtest-baseline").click()
    page.locator("#backtest-run").click()
    page.locator("#advanced-toggle").click()
    page.locator(".backtest-advanced-controls summary").click()
    page.locator("#backtest-capital").fill("20000")
    page.locator("#backtest-frequency").select_option("3")
    page.locator("#backtest-run").click()
    expect(page.locator("#backtest-applied")).to_contain_text("$20,000")
    expect(page.locator("#backtest-applied")).to_contain_text("every 3 months")
    page.locator("#backtest-observation").focus()
    page.keyboard.press("ArrowRight")
    expect(page.locator("#backtest-observation-details")).to_contain_text("No")
    check("advanced capital and rebalance settings apply", "2000-02" in page.locator("#backtest-observation-details").inner_text())
    page.locator("#advanced-toggle").click()
    page.locator("#backtest-baseline").click()
    page.locator("#backtest-run").click()
    for theme in ["dark", "light"]:
        page.locator("#theme-toggle").click()
        colors = page.locator("#backtest-run").evaluate("el=>{let s=getComputedStyle(el);return [s.color,s.backgroundColor].map(c=>c.match(/[0-9.]+/g).slice(0,3).map(Number));}")
        def luminance(rgb):
            scaled = [v / 255 for v in rgb]
            linear = [v / 12.92 if v <= 0.04045 else ((v + .055) / 1.055) ** 2.4 for v in scaled]
            return sum(v * w for v, w in zip(linear, [.2126, .7152, .0722]))
        a, b = sorted(luminance(c) for c in colors)
        check("run button contrast >= 4.5:1 in " + theme, (b + .05) / (a + .05) >= 4.5)

    page.locator("#nav-inbox").click()
    page.locator("#idea-preview-button").click()
    expect(page.locator("#idea-status")).to_contain_text("Enter a note")
    payload = '<img src=x onerror="window.__injected=true"><script>window.__injected=true</script>'
    page.locator("#idea-input").fill(payload)
    page.locator("#idea-preview-button").click()
    expect(page.locator("#idea-preview-text")).to_have_text(payload)
    check("inbox renders literal text", page.locator("#idea-preview-text img, #idea-preview-text script").count() == 0)
    check("inbox does not execute input", page.evaluate("window.__injected === undefined"))
    page.locator("#idea-input").fill("Revised hypothesis")
    expect(page.locator("#idea-preview")).to_be_hidden()
    page.locator("#idea-preview-button").click()
    expect(page.locator("#idea-preview-text")).to_have_text("Revised hypothesis")
    page.locator("#idea-clear-button").click()
    expect(page.locator("#idea-input")).to_have_value("")
    expect(page.locator("#idea-preview")).to_be_hidden()
    page.locator("#idea-input").fill("This must disappear on reload")
    page.locator("#idea-preview-button").click()
    page.reload()
    page.locator("#nav-backtest").click()
    expect(page.locator("#backtest-run-count")).to_have_text("0 runs completed")
    expect(page.locator("#backtest-export")).to_be_disabled()
    page.locator("#backtest-run").click()
    check("backtest history resets on reload", page.locator("#backtest-history li").count() == 1)
    page.locator("#nav-inbox").click()
    expect(page.locator("#idea-input")).to_have_value("")
    expect(page.locator("#idea-preview")).to_be_hidden()
    check("no browser persistent storage", page.evaluate("localStorage.length === 0 && sessionStorage.length === 0"))

    for width in [320, 390, 768, 1440]:
        page.set_viewport_size({"width": width, "height": 900})
        for name in views:
            page.locator("#nav-" + name).click()
            for advanced in [True, False]:
                if page.locator("#advanced-toggle").get_attribute("aria-checked") != str(advanced).lower():
                    page.locator("#advanced-toggle").click()
                dimensions = page.evaluate("({doc:document.documentElement.scrollWidth, viewport:innerWidth})")
                check(f"no page overflow: {width}px {name} advanced={advanced}",
                      dimensions["doc"] <= dimensions["viewport"] + 1)
        page.locator("#nav-evidence").click()
        page.locator("#evidence-tab-papers").click()
        for advanced in [True, False]:
            if page.locator("#advanced-toggle").get_attribute("aria-checked") != str(advanced).lower():
                page.locator("#advanced-toggle").click()
            dimensions = page.evaluate("({doc:document.documentElement.scrollWidth, viewport:innerWidth})")
            check(f"no paper-library overflow: {width}px advanced={advanced}", dimensions["doc"] <= dimensions["viewport"] + 1)
        page.locator("#evidence-tab-companies").click()

    page.set_viewport_size({"width": 1440, "height": 1000})
    page.locator("#nav-overview").click()
    snapshot(page, "overview-desktop")
    page.locator("#nav-evidence").click()
    page.locator("#evidence-tab-papers").click()
    page.locator("#paper-search").fill("momentum")
    page.locator('[data-paper-id="R12"]').click()
    snapshot(page, "papers-desktop")
    page.locator("#evidence-tab-companies").click()
    page.locator("#nav-rotation").click()
    page.locator("#sector-select").select_option("industrials")
    snapshot(page, "rotation-desktop")
    page.locator("#theme-toggle").click()
    page.locator("#nav-lab").click()
    snapshot(page, "lab-dark")
    page.locator("#theme-toggle").click()
    page.locator("#nav-backtest").click()
    snapshot(page, "backtest-desktop")
    page.locator("#theme-toggle").click()
    snapshot(page, "backtest-dark")
    page.locator("#theme-toggle").click()
    page.set_viewport_size({"width": 390, "height": 844})
    snapshot(page, "backtest-mobile")
    page.locator("#nav-evidence").click()
    page.locator("#company-wmt").click()
    snapshot(page, "evidence-mobile")
    page.locator("#evidence-tab-papers").click()
    snapshot(page, "papers-mobile")
    page.goto(Path("research/ui/index.html").resolve().as_uri() + "#backtest")
    expect(page.locator("#view-backtest")).to_be_visible()
    check("backtest direct link opens the workbench", page.locator("#nav-backtest").get_attribute("aria-current") == "page")
    check("no JavaScript errors", not errors)
    check("no external network requests", not network)
    result = {"status": "passed", "code_commit": os.environ.get("GITHUB_SHA", "local"),
              "html_sha256": hashlib.sha256(Path("research/ui/index.html").read_bytes()).hexdigest(),
              "catalog_sha256": hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
              "checks": checks, "count": len(checks), "page_errors": errors,
              "external_requests": network, "browser": browser.version,
              "widths_checked": [320,390,768,1440]}
    (OUTPUT / "checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print("UI_CHECKS_JSON_BEGIN")
    print(json.dumps(result))
    print("UI_CHECKS_JSON_END")
    browser.close()
