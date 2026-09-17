"""E04-P1: retrospective industry allocation research; Python standard library only."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import statistics
import urllib.request
import zipfile

SOURCE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/12_Industry_Portfolios_CSV.zip"
INDUSTRIES = ("NoDur", "Durbl", "Manuf", "Enrgy", "Chems", "BusEq",
              "Telcm", "Utils", "Shops", "Hlth", "Money", "Other")
START, END = 200001, 202512
COSTS = (0, 10, 25)
VERSION = "E04-P1-1"
MAX_BYTES = 10_000_000


def month_number(value):
    year, month = divmod(int(value), 100)
    if not 1900 <= year <= 2200 or not 1 <= month <= 12:
        raise ValueError("Invalid month: " + str(value))
    return year * 12 + month - 1


def validate_rows(rows):
    if not rows:
        raise ValueError("No monthly data")
    previous = None
    for date, values in rows:
        number = month_number(date)
        if previous is not None and number != previous + 1:
            raise ValueError("Duplicate, unordered or missing month: " + str(date))
        if len(values) != len(INDUSTRIES):
            raise ValueError("Expected exactly 12 industries")
        if any(not math.isfinite(v) or v <= -1 for v in values):
            raise ValueError("Invalid return or bankrupt industry")
        previous = number


def parse_monthly(text):
    lines = text.lstrip("\ufeff").splitlines()
    marker = next((i for i, line in enumerate(lines)
                   if "average value weighted returns -- monthly" in line.lower()), None)
    if marker is None:
        raise ValueError("Value-weighted monthly section not found")
    names, rows = None, []
    for fields in csv.reader(lines[marker + 1:]):
        fields = [f.strip() for f in fields]
        if not fields or not any(fields):
            continue
        if names is None:
            if fields[0] == "" and tuple(fields[1:]) == INDUSTRIES:
                names = tuple(fields[1:])
                continue
            raise ValueError("Changed industry header: " + repr(fields))
        if not re.fullmatch(r"\d{6}", fields[0]):
            if rows and fields[0].lower() == "average equal weighted returns -- monthly":
                break
            raise ValueError("Unexpected monthly section terminator: " + repr(fields))
        if len(fields) != len(INDUSTRIES) + 1:
            raise ValueError("Malformed monthly row")
        raw = [float(x) for x in fields[1:]]
        if any(x in (-99.99, -999.0) for x in raw):
            raise ValueError("Missing return in " + fields[0])
        rows.append((int(fields[0]), [x / 100 for x in raw]))
    validate_rows(rows)
    return names, rows


def momentum_scores(rows, holding_index):
    if holding_index < 12:
        raise ValueError("Twelve prior months required")
    # h-12 through h-2: 11 monthly returns, excludes h-1 and h.
    history = rows[holding_index - 12:holding_index - 1]
    return [math.prod(1 + item[1][j] for item in history) - 1
            for j in range(len(INDUSTRIES))]


def simulate(rows, cost_bps, top_k=3, start=START, end=END):
    validate_rows(rows)
    if not math.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("Invalid costs")
    if top_k not in (3, 12):
        raise ValueError("Only preregistered strategy or benchmark allowed")
    indices = [i for i, (date, _) in enumerate(rows) if start <= date <= end]
    if not indices or rows[indices[0]][0] != start or rows[indices[-1]][0] != end:
        raise ValueError("Evaluation endpoints missing")
    if indices[0] < 12:
        raise ValueError("Insufficient formation history")
    c = cost_bps / 10000
    drifted = [0.0] * len(INDUSTRIES)
    result = []
    for i in indices:
        date, returns = rows[i]
        scores = momentum_scores(rows, i)
        chosen = sorted(range(len(INDUSTRIES)), key=lambda j: (-scores[j], j))[:top_k]
        weights = [1 / top_k if j in chosen else 0.0 for j in range(len(INDUSTRIES))]
        traded = sum(abs(w - old) for w, old in zip(weights, drifted))
        fee = c * traded
        gross = sum(w * r for w, r in zip(weights, returns))
        terminal = i == indices[-1]
        if fee >= 1 or c >= 1 or gross <= -1:
            raise ValueError("Nonpositive portfolio wealth")
        net = (1 - fee) * (1 + gross) * (1 - c if terminal else 1) - 1
        result.append({
            "month": date, "signal_start": rows[i - 12][0],
            "signal_end": rows[i - 2][0], "skipped_month": rows[i - 1][0],
            "selected": [INDUSTRIES[j] for j in chosen],
            "weights": weights, "gross_return": gross,
            "net_return": net, "rebalance_notional": traded,
            "terminal_liquidation_notional": 1.0 if terminal else 0.0,
        })
        # Proportional fee haircuts do not alter relative invested weights.
        drifted = [w * (1 + r) / (1 + gross) for w, r in zip(weights, returns)]
    return result


def max_drawdown(returns):
    nav = peak = 1.0
    worst = 0.0
    for value in returns:
        nav *= 1 + value
        peak = max(peak, nav)
        worst = min(worst, nav / peak - 1)
    return worst


def nw_mean_interval(values, lag=12):
    n = len(values)
    if n < 2:
        raise ValueError("Too few observations for uncertainty")
    mean = statistics.mean(values)
    centered = [v - mean for v in values]
    gamma0 = sum(x * x for x in centered) / n
    long_variance = gamma0
    actual_lag = min(lag, n - 1)
    for k in range(1, actual_lag + 1):
        gamma = sum(centered[t] * centered[t-k] for t in range(k, n)) / n
        long_variance += 2 * (1 - k / (actual_lag + 1)) * gamma
    se = math.sqrt(max(0, long_variance) / n)
    return {"lag": actual_lag, "monthly_mean": mean, "monthly_se": se,
            "annual_arithmetic_mean": 12 * mean,
            "annual_arithmetic_95pct_interval": [12*(mean-1.96*se), 12*(mean+1.96*se)]}


def metrics(points, key="net_return"):
    returns = [p[key] for p in points]
    years = {}
    for point in points:
        year = str(point["month"] // 100)
        years[year] = years.get(year, 1.0) * (1 + point[key])
    return {
        "months": len(returns),
        "cagr": math.prod(1 + r for r in returns) ** (12 / len(returns)) - 1,
        "annualized_volatility": statistics.stdev(returns) * math.sqrt(12),
        "max_month_end_drawdown": max_drawdown(returns),
        "annualized_traded_notional": 12 * statistics.mean(
            p["rebalance_notional"] + p["terminal_liquidation_notional"] for p in points),
        "annual_returns": {year: value - 1 for year, value in years.items()},
    }


def comparisons(strategy, benchmark):
    if [p["month"] for p in strategy] != [p["month"] for p in benchmark]:
        raise ValueError("Unmatched comparison dates")
    periods = {"2000-2025": (200001, 202512), "2000-2009": (200001, 200912),
               "2010-2019": (201001, 201912), "2020-2025": (202001, 202512)}
    result = {}
    for name, (start, end) in periods.items():
        s = [p for p in strategy if start <= p["month"] <= end]
        b = [p for p in benchmark if start <= p["month"] <= end]
        active = [x["net_return"] - y["net_return"] for x, y in zip(s, b)]
        sd = statistics.stdev(active)
        result[name] = {
            "strategy": metrics(s), "benchmark": metrics(b),
            "active": {**nw_mean_interval(active),
                       "information_ratio": statistics.mean(active) / sd * math.sqrt(12) if sd else None},
        }
    return result


def read_source(input_zip=None, expected_sha256=None):
    if input_zip:
        blob = Path(input_zip).read_bytes()
    else:
        request = urllib.request.Request(SOURCE, headers={"User-Agent": "Stock-Movement-research/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            blob = response.read(MAX_BYTES + 1)
    if len(blob) > MAX_BYTES:
        raise ValueError("Unexpectedly large archive")
    digest = hashlib.sha256(blob).hexdigest()
    if expected_sha256 and digest != expected_sha256:
        raise ValueError("Source SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        matches = [entry for entry in archive.infolist()
                   if entry.filename.lower().endswith(".csv")]
        if len(matches) != 1 or matches[0].file_size > MAX_BYTES:
            raise ValueError("Unexpected archive structure")
        text = archive.read(matches[0]).decode("utf-8-sig")
    manifest = {
        "source_url": SOURCE, "retrieved_or_replayed_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": digest, "zip_member": matches[0].filename,
        "source_header": text.split("Average Value Weighted Returns")[0].strip(),
        "mode": "replay" if input_zip else "download",
    }
    return blob, text, manifest


def build_report(result):
    lines = ["# E04-P1 observed results", "",
             "Retrospective research portfolios; after assumed allocation costs using a proportional target-weight approximation. Not an executable ETF backtest.", "",
             "| Cost per dollar traded | Strategy CAGR | Benchmark CAGR | Strategy max drawdown | Active mean/year | Approx. 95% interval |",
             "|---|---:|---:|---:|---:|---:|"]
    for cost, data in result["scenarios"].items():
        period = data["2000-2025"]
        s, b, a = period["strategy"], period["benchmark"], period["active"]
        lo, hi = a["annual_arithmetic_95pct_interval"]
        lines.append(f"| {cost} bp | {s['cagr']:.2%} | {b['cagr']:.2%} | {s['max_month_end_drawdown']:.2%} | "
                     f"{a['annual_arithmetic_mean']:.2%} | [{lo:.2%}, {hi:.2%}] |")
    lines += ["", "Active mean is the annualized arithmetic average of monthly strategy-minus-benchmark returns, not a funded CAGR.",
              "Intervals use Newey-West lag 12 and a normal approximation; factor-adjusted attribution remains outstanding.", "",
              "## Primary 10 bp scenario by period", "",
              "| Period | Strategy CAGR | Benchmark CAGR | Strategy drawdown | Benchmark drawdown |",
              "|---|---:|---:|---:|---:|"]
    for name, period in result["scenarios"]["10"].items():
        s, b = period["strategy"], period["benchmark"]
        lines.append(f"| {name} | {s['cagr']:.2%} | {b['cagr']:.2%} | {s['max_month_end_drawdown']:.2%} | {b['max_month_end_drawdown']:.2%} |")
    lines += ["", "## Reproduction", "",
              "Raw archive SHA-256: " + result["source"]["sha256"],
              "Code commit: " + result["code_commit"],
              "Source: " + SOURCE, "",
              "The run artifact contains the exact raw vintage, manifest, monthly results and report. Retain it before artifact expiry.",
              "Monthly reallocation fees use a proportional target-weight haircut approximation, not exact self-financing transaction notionals.",
              "They omit underlying constituent trading, fund expenses, tracking error, taxes and executable-price verification.",
              "Subperiods slice one continuous portfolio; entry and liquidation fees are not restarted at decade boundaries.",
              "No liquid-stock universe filter or modern GICS mapping is applied.",
              "This fixed rule was registered before this run but the historical period is not pristine out of sample.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-zip", help="Replay an archived official ZIP")
    parser.add_argument("--expected-sha256", help="Require a particular raw-data vintage")
    parser.add_argument("--output-dir", default="work/e04-p1")
    args = parser.parse_args()
    blob, text, manifest = read_source(args.input_zip, args.expected_sha256)
    names, rows = parse_monthly(text)
    manifest.update({"data_start": rows[0][0], "data_end": rows[-1][0],
                     "industries": list(names), "monthly_observations": len(rows)})
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "source.zip").write_bytes(blob)
    result = {
        "experiment": VERSION, "source": manifest,
        "code_commit": os.environ.get("GITHUB_SHA", "local-unrecorded"),
        "settings": {"start": START, "end": END, "formation_month_offsets": list(range(2, 13)),
                     "top_k": 3, "cost_bps_per_dollar_traded": list(COSTS),
                     "nw_lag": 12, "terminal_liquidation": True},
        "scenarios": {},
    }
    all_monthly = []
    for cost in COSTS:
        strategy, benchmark = simulate(rows, cost, 3), simulate(rows, cost, 12)
        result["scenarios"][str(cost)] = comparisons(strategy, benchmark)
        for name, points in (("strategy", strategy), ("benchmark", benchmark)):
            for point in points:
                all_monthly.append({"cost_bps": cost, "portfolio": name, **point})
    (output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    (output / "monthly.json").write_text(json.dumps(all_monthly, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    with (output / "monthly.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(all_monthly[0]))
        writer.writeheader()
        for item in all_monthly:
            writer.writerow({**item, "selected": ";".join(item["selected"]),
                             "weights": json.dumps(item["weights"])})
    report = build_report(result)
    (output / "report.md").write_text(report, encoding="utf-8")
    print(report)
    print("RESULT_JSON_BEGIN")
    print(json.dumps(result, allow_nan=False))
    print("RESULT_JSON_END")


if __name__ == "__main__":
    main()
