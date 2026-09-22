"""Cross-check the browser backtest engine against the frozen Python baseline."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "research" / "ui" / "backtest-data.json"


def load_baseline():
    path = ROOT / "research" / "code" / "industry_baseline.py"
    spec = importlib.util.spec_from_file_location("industry_baseline", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load baseline module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_js(costs):
    script = r'''
const fs = require("fs");
const { run } = require("./research/ui/backtest-engine.js");
const data = JSON.parse(fs.readFileSync("./research/ui/backtest-data.json", "utf8"));
const costs = JSON.parse(process.argv[1]);
const result = {};
for (const costBps of costs) {
  result[String(costBps)] = run(data, {
    start: "2000-01", end: "2025-12", lookback: 11, skip: 1,
    topK: 3, costBps, initialCapital: 10000, rebalanceEvery: 1,
  });
}
process.stdout.write(JSON.stringify(result));
'''
    completed = subprocess.run(
        ["node", "-e", script, json.dumps(list(costs))],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def month_string(value):
    value = int(value)
    return f"{value // 100:04d}-{value % 100:02d}"


def close(actual, expected, where):
    if not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10):
        raise AssertionError(f"{where}: actual={actual!r}, expected={expected!r}")


def check_monthly(js, strategy, benchmark, capital, cost):
    if len(js["points"]) != len(strategy) or len(strategy) != len(benchmark):
        raise AssertionError(
            f"cost {cost}: monthly lengths differ: JS={len(js['points'])}, "
            f"strategy={len(strategy)}, benchmark={len(benchmark)}"
        )

    strategy_wealth = benchmark_wealth = capital
    strategy_peak = benchmark_peak = capital
    for index, (s, b, point) in enumerate(zip(strategy, benchmark, js["points"])):
        where = f"cost {cost}, month {index} ({point.get('month')})"
        expected_month = month_string(s["month"])
        if point["month"] != expected_month or point["month"] != month_string(b["month"]):
            raise AssertionError(f"{where}: date mismatch; expected {expected_month}")

        strategy_wealth *= 1 + s["net_return"]
        benchmark_wealth *= 1 + b["net_return"]
        strategy_peak = max(strategy_peak, strategy_wealth)
        benchmark_peak = max(benchmark_peak, benchmark_wealth)
        strategy_drawdown = strategy_wealth / strategy_peak - 1
        benchmark_drawdown = benchmark_wealth / benchmark_peak - 1

        close(point["strategyReturn"], s["net_return"], f"{where} strategy return")
        close(point["benchmarkReturn"], b["net_return"], f"{where} benchmark return")
        close(point["strategyWealth"], strategy_wealth, f"{where} strategy wealth")
        close(point["benchmarkWealth"], benchmark_wealth, f"{where} benchmark wealth")
        close(point["strategyDrawdown"], strategy_drawdown, f"{where} strategy drawdown")
        close(point["benchmarkDrawdown"], benchmark_drawdown, f"{where} benchmark drawdown")
        if point["selected"] != s["selected"]:
            raise AssertionError(f"{where} selected: actual={point['selected']!r}, expected={s['selected']!r}")
        if len(point["weights"]) != len(s["weights"]):
            raise AssertionError(f"{where}: weight vector length mismatch")
        for actual, expected in zip(point["weights"], s["weights"]):
            close(actual, expected, f"{where} strategy weight")

        close(
            point["turnover"],
            s["rebalance_notional"] + s["terminal_liquidation_notional"],
            f"{where} strategy turnover",
        )
        close(
            point["benchmarkTurnover"],
            b["rebalance_notional"] + b["terminal_liquidation_notional"],
            f"{where} benchmark turnover",
        )
        expected_signal_start = month_string(s["signal_start"])
        expected_signal_end = month_string(s["signal_end"])
        if point["signalStart"] != expected_signal_start:
            raise AssertionError(f"{where} signalStart: actual={point['signalStart']!r}, expected={expected_signal_start!r}")
        if point["signalEnd"] != expected_signal_end:
            raise AssertionError(f"{where} signalEnd: actual={point['signalEnd']!r}, expected={expected_signal_end!r}")


def expected_metrics(points, capital):
    summary = model.metrics(points)
    wealth = capital
    for point in points:
        wealth *= 1 + point["net_return"]
    return {
        "cagr": summary["cagr"],
        "volatility": summary["annualized_volatility"],
        "maxDrawdown": summary["max_month_end_drawdown"],
        "finalWealth": wealth,
        "turnover": summary["annualized_traded_notional"],
    }


def check_metrics(js, strategy, benchmark, capital, cost):
    for portfolio, expected_points in (("strategy", strategy), ("benchmark", benchmark)):
        actual = js["metrics"][portfolio]
        expected = expected_metrics(expected_points, capital)
        for name, value in expected.items():
            close(actual[name], value, f"cost {cost} {portfolio} metric {name}")


def check_frozen_result(js_runs, path):
    frozen = json.loads(path.read_text(encoding="utf-8"))
    for cost, js in js_runs.items():
        try:
            period = frozen["scenarios"][cost]["2000-2025"]
        except KeyError as exc:
            raise AssertionError(f"Frozen result has no cost scenario {cost}: {path}") from exc
        for portfolio in ("strategy", "benchmark"):
            expected = period[portfolio]
            actual = js["metrics"][portfolio]
            close(actual["cagr"], expected["cagr"], f"frozen {path} cost {cost} {portfolio} CAGR")
            close(actual["volatility"], expected["annualized_volatility"], f"frozen {path} cost {cost} {portfolio} volatility")
            close(actual["maxDrawdown"], expected["max_month_end_drawdown"], f"frozen {path} cost {cost} {portfolio} drawdown")
            close(actual["turnover"], expected["annualized_traded_notional"], f"frozen {path} cost {cost} {portfolio} turnover")


def main():
    global model
    model = load_baseline()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    frozen_path = ROOT / "research/results/E04-P1-results.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if data["meta"]["sourceSha256"] != frozen["source"]["sha256"]:
        raise AssertionError("Source fingerprint differs from frozen research archive")
    if [series["id"] for series in data["series"]] != list(model.INDUSTRIES):
        raise AssertionError("Industry order differs from the frozen baseline")
    rows = [(int(row["month"].replace("-", "")), row["returns"]) for row in data["rows"]]
    costs = (0, 10, 25)
    js_runs = run_js(costs)
    for cost in costs:
        strategy = model.simulate(rows, cost, top_k=3, start=200001, end=202512)
        benchmark = model.simulate(rows, cost, top_k=12, start=200001, end=202512)
        check_monthly(js_runs[str(cost)], strategy, benchmark, 10000, cost)
        check_metrics(js_runs[str(cost)], strategy, benchmark, 10000, cost)

    check_frozen_result(js_runs, frozen_path)
    frozen_message = f"; frozen aggregate {frozen_path.relative_to(ROOT)}"
    print(f"verified JS/Python monthly ledgers and aggregates for costs {list(costs)} over 312 months{frozen_message}")


if __name__ == "__main__":
    main()
