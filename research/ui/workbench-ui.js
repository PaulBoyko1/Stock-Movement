(function () {
  "use strict";

  var state = { data: null, result: null, runs: [], initialized: false, baseline: { lookback: 11, skip: 1, topK: 3, costBps: 10, initialCapital: 10000, rebalanceEvery: 1 } };
  var ids = ["backtest-start", "backtest-end", "backtest-lookback", "backtest-skip", "backtest-top-k", "backtest-cost-bps", "backtest-capital", "backtest-frequency"];
  var $ = function (id) { return document.getElementById(id); };

  function text(node, value) { if (node) node.textContent = value == null ? "" : String(value); }
  function finite(value) { return typeof value === "number" && Number.isFinite(value); }
  function number(value, fallback) { var n = Number(value); return finite(n) ? n : fallback; }
  function clampInteger(value, min, max, fallback) { var n = Math.round(number(value, fallback)); return Math.max(min, Math.min(max, n)); }
  function formatPercent(value) { return finite(value) ? (value * 100).toFixed(2) + "%" : "—"; }
  function formatCurrency(value) { return finite(value) ? new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value) : "—"; }
  function formatNumber(value) { return finite(value) ? value.toFixed(2) : "—"; }
  function formatApplied(p) { return "Applied " + p.start + " to " + p.end + " · formation " + p.lookback + " months · skip " + p.skip + " · top " + p.topK + " · " + p.costBps + " bp cost · " + formatCurrency(p.initialCapital) + " initial · rebalance every " + p.rebalanceEvery + " month" + (p.rebalanceEvery === 1 ? "" : "s"); }
  function readData() {
    var node = $("backtest-data");
    if (!node) throw new Error("Missing #backtest-data dataset.");
    var data = JSON.parse(node.textContent || "{}");
    if (!data || !Array.isArray(data.series) || !Array.isArray(data.rows)) throw new Error("Dataset must contain series[] and rows[].");
    return data;
  }
  function dataMonths(data) { return data.rows.map(function (row) { return row && row.month; }).filter(function (month) { return /^\d{4}-\d{2}$/.test(month); }); }
  function setStatus(message, kind) { var node = $("backtest-status"); text(node, message); if (node) node.dataset.kind = kind || ""; }
  function setError(message) { var node = $("backtest-error"); if (!node) return; text(node, message); node.hidden = !message; }
  function setControlsFromData(data) {
    var months = dataMonths(data);
    var meta = data.meta || {};
    var defaults = Object.assign({}, state.baseline, meta.defaultParams || {});
    state.baseline = defaults;
    if (months.length) { $("backtest-start").value = meta.defaultStart || months[0]; $("backtest-end").value = meta.defaultEnd || months[months.length - 1]; }
    $("backtest-lookback").value = defaults.lookback;
    $("backtest-skip").value = defaults.skip;
    $("backtest-top-k").value = defaults.topK;
    $("backtest-cost-bps").value = defaults.costBps;
    $("backtest-capital").value = defaults.initialCapital;
    $("backtest-frequency").value = String(defaults.rebalanceEvery);
    text($("backtest-data-status"), months.length ? data.series.length + " industries · " + months.length + " months" : "No observations");
    if (meta.sourceUrl) {
      var source = $("backtest-source");
      source.textContent = "Source trace: ";
      var link = document.createElement("a"); link.href = meta.sourceUrl; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = meta.title || "Kenneth French Data Library"; source.appendChild(link);
      source.appendChild(document.createTextNode(" · " + (meta.frequency || "monthly") + " " + (meta.returnUnits || meta.unit || "total-return") + " observations." + (meta.sourceSha256 ? " Source SHA-256: " + meta.sourceSha256 + "." : "")));
    }
    var caveat = $("backtest-caveat");
    if (meta.limitations || meta.caveat) text(caveat, meta.limitations || meta.caveat);
  }
  function requiredNumber(id, label) {
    var raw = $(id).value;
    if (raw == null || raw.trim() === "") throw new Error(label + " is required.");
    var value = Number(raw);
    if (!finite(value)) throw new Error(label + " must be a number.");
    return value;
  }
  function params() {
    return {
      start: $("backtest-start").value,
      end: $("backtest-end").value,
      lookback: requiredNumber("backtest-lookback", "Formation months"),
      skip: requiredNumber("backtest-skip", "Skipped recent months"),
      topK: requiredNumber("backtest-top-k", "Top industries"),
      costBps: requiredNumber("backtest-cost-bps", "Trading cost"),
      initialCapital: requiredNumber("backtest-capital", "Initial capital"),
      rebalanceEvery: requiredNumber("backtest-frequency", "Rebalance frequency")
    };
  }
  function clearOutput() {
    ["backtest-wealth-chart", "backtest-drawdown-chart"].forEach(function (id) { var node = $(id); while (node && node.firstChild) node.removeChild(node.firstChild); });
    ["strategy.cagr", "strategy.volatility", "strategy.maxDrawdown", "strategy.finalWealth", "strategy.turnover", "benchmark.cagr", "benchmark.volatility", "benchmark.maxDrawdown", "benchmark.finalWealth", "benchmark.turnover"].forEach(function (key) { var node = document.querySelector('[data-metric="' + key + '"]'); text(node, "—"); });
    $("backtest-observation").disabled = true; $("backtest-observation").max = "0"; text($("backtest-observation-details"), "No returned observations yet."); text($("backtest-observation-count"), "Run a backtest to enable observation selection."); $("backtest-export").disabled = true;
  }
  function metricValue(metrics, path) { var pieces = path.split("."); var value = metrics; pieces.forEach(function (piece) { value = value && value[piece]; }); return value; }
  function renderMetrics(result) {
    ["strategy.cagr", "benchmark.cagr", "strategy.volatility", "benchmark.volatility", "strategy.maxDrawdown", "benchmark.maxDrawdown", "strategy.turnover", "benchmark.turnover"].forEach(function (key) { text(document.querySelector('[data-metric="' + key + '"]'), formatPercent(metricValue(result.metrics || {}, key))); });
    ["strategy.finalWealth", "benchmark.finalWealth"].forEach(function (key) { text(document.querySelector('[data-metric="' + key + '"]'), formatCurrency(metricValue(result.metrics || {}, key))); });
  }
  function svgElement(name, attrs) { var node = document.createElementNS("http://www.w3.org/2000/svg", name); Object.keys(attrs || {}).forEach(function (key) { node.setAttribute(key, attrs[key]); }); return node; }
  function drawChart(id, points, fields, title, percentAxis) {
    var svg = $(id), W = Math.max(250, Math.round(svg.getBoundingClientRect().width) || 760), H = W < 450 ? 245 : 280;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.setAttribute("aria-label", title + "; strategy solid, all-industry benchmark dashed. Exact monthly values available in Inspect one month.");
    if (!points.length) { var note = svgElement("text", { x: 380, y: 145, "text-anchor": "middle", "class": "empty-note" }); note.textContent = "No returned observations"; svg.appendChild(note); return; }
    var initial = { month: "Start" };
    fields.forEach(function(field) { initial[field] = percentAxis ? 0 : state.result.params.initialCapital; });
    points = [initial].concat(points);
    var left = 54, right = 14, top = 18, bottom = 36, innerW = W - left - right, innerH = H - top - bottom;
    var values = []; fields.forEach(function (field) { points.forEach(function (point) { if (finite(point[field])) values.push(point[field]); }); });
    if (!values.length) { var empty = svgElement("text", { x: 380, y: 145, "text-anchor": "middle", "class": "empty-note" }); empty.textContent = "Returned result has no chart values"; svg.appendChild(empty); return; }
    var min = percentAxis ? Math.min(-0.01, Math.min.apply(Math, values)) : 0;
    var max = percentAxis ? 0 : Math.max.apply(Math, values) * 1.04;
    var x = function (i) { return left + (points.length === 1 ? innerW / 2 : i * innerW / (points.length - 1)); };
    var y = function (value) { return top + (max - value) * innerH / (max - min); };
    for (var grid = 0; grid <= 4; grid += 1) { var gy = top + grid * innerH / 4; svg.appendChild(svgElement("line", { x1: left, y1: gy, x2: W - right, y2: gy, "class": "chart-gridline" })); var label = svgElement("text", { x: left - 8, y: gy + 3, "text-anchor": "end" }); var tick = max - grid * (max - min) / 4; label.textContent = percentAxis ? (tick * 100).toFixed(0) + "%" : new Intl.NumberFormat("en-US", {notation:"compact", maximumFractionDigits:1}).format(tick); svg.appendChild(label); }
    svg.appendChild(svgElement("line", { x1: left, y1: top + innerH, x2: W - right, y2: top + innerH, "class": "chart-axis" }));
    fields.forEach(function (field, fieldIndex) { var path = []; points.forEach(function (point, index) { if (finite(point[field])) path.push((path.length ? "L" : "M") + x(index).toFixed(2) + " " + y(point[field]).toFixed(2)); }); if (path.length) svg.appendChild(svgElement("path", { d: path.join(" "), "class": fieldIndex ? "benchmark-line" : "strategy-line" })); });
    var ticks = W < 450 ? 3 : 6;
    for (var t = 0; t < ticks; t++) { var index = Math.round(t * (points.length - 1) / (ticks - 1)); var tx = svgElement("text", { x: x(index), y: H - 13, "text-anchor": t === 0 ? "start" : t === ticks - 1 ? "end" : "middle" }); tx.textContent = points[index].month; svg.appendChild(tx); }
    var selected = state.result && state.result.points ? state.result.points[state.observationIndex || 0] : null; if (selected) fields.forEach(function (field, fieldIndex) { if (finite(selected[field])) svg.appendChild(svgElement("circle", { cx: x(points.indexOf(selected)), cy: y(selected[field]), r: 4.5, "class": "observation-dot " + (fieldIndex ? "benchmark-dot" : "strategy-dot") })); });
  }
  function renderObservation() {
    if (!state.result || !state.result.points || !state.result.points.length) return;
    var points = state.result.points, index = Math.max(0, Math.min(points.length - 1, Number($("backtest-observation").value) || 0)), point = points[index]; state.observationIndex = index; $("backtest-observation").value = String(index); $("backtest-observation").setAttribute("aria-valuetext", point.month); text($("backtest-observation-count"), "Observation " + (index + 1) + " of " + points.length + " · monthly granularity");
    var details = $("backtest-observation-details"); while (details.firstChild) details.removeChild(details.firstChild);
    var grid = document.createElement("div"); grid.className = "backtest-detail-grid";
    [["Month held", point.month], ["Strategy wealth", formatCurrency(point.strategyWealth)], ["Benchmark wealth", formatCurrency(point.benchmarkWealth)], ["Strategy return", formatPercent(point.strategyReturn)], ["Benchmark return", formatPercent(point.benchmarkReturn)], ["Strategy drawdown", formatPercent(point.strategyDrawdown)], ["Benchmark drawdown", formatPercent(point.benchmarkDrawdown)], ["Turnover", formatPercent(point.turnover)], ["Rebalanced", point.rebalance ? "Yes" : "No"]].forEach(function (item) { var cell = document.createElement("div"), label = document.createElement("span"), value = document.createElement("strong"); text(label, item[0]); text(value, item[1]); cell.appendChild(label); cell.appendChild(value); grid.appendChild(cell); }); details.appendChild(grid);
    var holdings = document.createElement("p"); holdings.className = "backtest-holdings"; var selected = Array.isArray(point.selected) ? point.selected.map(function(id) { var j = state.data.series.findIndex(function(series) { return series.id === id; }); return state.data.series[j].label + " (" + formatPercent(point.weights[j]) + ")"; }).join(", ") : "Not returned"; holdings.appendChild(document.createElement("strong")); text(holdings.firstChild, "Held during this month: "); holdings.appendChild(document.createTextNode(selected)); if (point.signalStart && point.signalEnd) holdings.appendChild(document.createTextNode(" · signal window " + point.signalStart + " to " + point.signalEnd)); details.appendChild(holdings);
    drawChart("backtest-wealth-chart", points, ["strategyWealth", "benchmarkWealth"], "Wealth chart", false); drawChart("backtest-drawdown-chart", points, ["strategyDrawdown", "benchmarkDrawdown"], "Drawdown chart", true);
  }
  function renderResult(result) {
    state.result = result; state.observationIndex = 0; renderMetrics(result); var points = Array.isArray(result.points) ? result.points : []; var range = $("backtest-observation"); range.disabled = !points.length; range.max = String(Math.max(0, points.length - 1)); range.value = "0"; $("backtest-results").dataset.stale = "false"; text($("backtest-result-state"), "Latest run"); $("backtest-result-state").className = "backtest-badge"; text($("backtest-applied"), formatApplied(result.params || params())); renderObservation(); if (!points.length) clearOutput(); $("backtest-export").disabled = false; }
  function renderHistory() { var list = $("backtest-history"); while (list.firstChild) list.removeChild(list.firstChild); if (!state.runs.length) { var empty = document.createElement("li"); text(empty, "No runs yet."); list.appendChild(empty); } state.runs.forEach(function (run) { var item = document.createElement("li"); var strong = document.createElement("strong"); text(strong, run.when + " · " + run.params.start + " to " + run.params.end); item.appendChild(strong); item.appendChild(document.createTextNode(" · formation " + run.params.lookback + " / skip " + run.params.skip + " / top " + run.params.topK + " · " + run.params.costBps + " bp · " + formatCurrency(run.params.initialCapital) + " · every " + run.params.rebalanceEvery + " month" + (run.params.rebalanceEvery === 1 ? "" : "s") + " · strategy CAGR " + formatPercent(run.strategyCagr) + " vs benchmark " + formatPercent(run.benchmarkCagr) + " · drawdown " + formatPercent(run.strategyDrawdown) + " vs " + formatPercent(run.benchmarkDrawdown))); list.appendChild(item); }); text($("backtest-run-count"), state.runs.length + " run" + (state.runs.length === 1 ? "" : "s") + " completed"); }
  function invalidateResult(label) { state.result = null; clearOutput(); $("backtest-results").dataset.stale = "true"; text($("backtest-result-state"), label || "No valid run"); $("backtest-result-state").className = "backtest-badge backtest-badge-muted"; }
  function markStale() { $("backtest-export").disabled = true; if (!state.result) return; $("backtest-results").dataset.stale = "true"; text($("backtest-result-state"), "Parameters changed · rerun"); $("backtest-result-state").className = "backtest-badge backtest-badge-muted"; setStatus("Controls changed. Run the backtest to update the charts and metrics.", "stale"); }
  function run(event) { if (event) event.preventDefault(); setError(""); invalidateResult("Running…"); if (!state.data) { setError("The monthly industry dataset is unavailable."); setStatus("No dataset is available for this test.", "stale"); return; } if (!window.StockBacktest || typeof window.StockBacktest.run !== "function") { setError("The monthly backtest engine is unavailable."); setStatus("This test cannot run yet.", "stale"); return; } try { var chosen = params(); if (!chosen.start || !chosen.end) throw new Error("Start and end months are required."); var result = window.StockBacktest.run(state.data, chosen); if (!result || !Array.isArray(result.points) || !result.metrics) throw new Error("The backtest returned no valid result."); renderResult(result); state.runs.push({ timestamp: new Date().toISOString(), when: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), params: chosen, strategyCagr: metricValue(result.metrics, "strategy.cagr"), benchmarkCagr: metricValue(result.metrics, "benchmark.cagr"), strategyDrawdown: metricValue(result.metrics, "strategy.maxDrawdown"), benchmarkDrawdown: metricValue(result.metrics, "benchmark.maxDrawdown") }); renderHistory(); setStatus("Backtest complete: " + result.points.length + " monthly observations returned.", "success"); } catch (error) { invalidateResult("Run failed · correct inputs"); setError(error && error.message ? error.message : "The backtest could not run."); setStatus("Backtest failed. Correct the inputs or inspect the error above.", "stale"); } }
  function baseline() { if (!state.data) return; setControlsFromData(Object.assign({}, state.data, { meta: Object.assign({}, state.data.meta, { defaultParams: state.baseline }) })); setError(""); markStale(); setStatus("Baseline parameters restored. Run the backtest when ready.", "stale"); }
  function exportResult() { if (!state.result || $("backtest-results").dataset.stale === "true") return; var meta = state.data && state.data.meta ? state.data.meta : {}; var exportPayload = { exportedAt: new Date().toISOString(), dataset: { id: meta.id, title: meta.title, sourceUrl: meta.sourceUrl, sourceSha256: meta.sourceSha256, retrievedAtUtc: meta.retrievedAtUtc, sourceHeader: meta.sourceHeader, dataStart: meta.dataStart, dataEnd: meta.dataEnd }, current: state.result, history: state.runs }; var blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: "application/json" }); var url = URL.createObjectURL(blob), anchor = document.createElement("a"); anchor.href = url; anchor.download = "stock-movement-backtest-result.json"; document.body.appendChild(anchor); anchor.click(); anchor.remove(); setTimeout(function () { URL.revokeObjectURL(url); }, 0); }
  function init() { if (state.initialized) return; state.initialized = true; try { state.data = readData(); setControlsFromData(state.data); } catch (error) { setError(error.message); } clearOutput(); var lastWidth = 0; new ResizeObserver(function() { var width = $("backtest-wealth-chart").getBoundingClientRect().width; if (width > 0 && Math.abs(width-lastWidth) > 1) { lastWidth=width; renderObservation(); } }).observe($("backtest-wealth-chart")); ids.forEach(function (id) { var node = $(id); if (node) node.addEventListener("input", markStale); node && node.addEventListener("change", markStale); }); $("backtest-form").addEventListener("submit", run); $("backtest-baseline").addEventListener("click", baseline); $("backtest-export").addEventListener("click", exportResult); $("backtest-observation").addEventListener("input", renderObservation); setStatus(state.data && state.data.rows.length ? "Ready. Baseline is 11 formation months, 1 skipped month, top 3, and 10 bp cost." : "Load the embedded monthly industry dataset to begin."); }
  window.StockBacktestUI = { init: init };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
}());
