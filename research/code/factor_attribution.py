"""E04-P2: fixed six-factor attribution, not a forecast."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import re
import urllib.request
import zipfile

import numpy as np
import statsmodels.api as sm

from industry_baseline import month_number

FF5_COLUMNS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
MOM_COLUMNS = ("Mom",)
FACTOR_NAMES = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "Mom")
SOURCES = {
    "ff5": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip",
    "momentum": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip",
}
EXPECTED_INDUSTRY_SHA = "c7316c6ae07bc2028632b57ad757dfef8303a62a6956946d7aabe926aadfdeb4"
Z95 = 1.959963984540054
MAX_BYTES = 10_000_000


def parse_factors(text, expected_columns):
    expected_columns = tuple(expected_columns)
    found, rows, previous = False, {}, None
    for fields in csv.reader(text.lstrip("\ufeff").splitlines()):
        fields = [value.strip() for value in fields]
        if not fields or not any(fields):
            continue
        if not found:
            if fields[0] == "":
                if tuple(fields[1:]) != expected_columns:
                    raise ValueError("Unexpected factor schema")
                found = True
            continue
        if fields[0].lower().startswith("annual factors:"):
            break
        if not re.fullmatch(r"\d{6}", fields[0]) or len(fields) != len(expected_columns) + 1:
            raise ValueError("Malformed factor row or section boundary")
        date = int(fields[0])
        number = month_number(date)
        if previous is not None and number != previous + 1:
            raise ValueError("Factor months missing, duplicated or unordered")
        values = np.array([float(value) for value in fields[1:]], dtype=float)
        if not np.isfinite(values).all() or any(value in (-99.99, -999) for value in values):
            raise ValueError("Missing/nonfinite factor")
        rows[date] = (values / 100).tolist()
        previous = number
    if not found or not rows:
        raise ValueError("No factor data found")
    return rows


def expected_months():
    return [year * 100 + month for year in range(2000, 2026) for month in range(1, 13)]


def align_months(monthly_points, ff5, mom, cost_bps):
    selected = {}
    for point in monthly_points:
        if point["cost_bps"] != cost_bps:
            continue
        name = point["portfolio"]
        if name not in ("strategy", "benchmark"):
            raise ValueError("Unknown portfolio")
        key = (name, point["month"])
        if key in selected:
            raise ValueError("Duplicate portfolio month")
        value = float(point["net_return"])
        if not np.isfinite(value):
            raise ValueError("Nonfinite portfolio return")
        selected[key] = value
    dates = expected_months()
    if set(selected) != {(name, date) for name in ("strategy", "benchmark") for date in dates}:
        raise ValueError("Require exactly 312 complete matched portfolio months")
    if any(date not in ff5 or date not in mom for date in dates):
        raise ValueError("Missing factor month")
    factors, active = [], []
    for date in dates:
        if len(ff5[date]) != 6 or len(mom[date]) != 1:
            raise ValueError("Incorrect factor dimensions")
        # RF cancels between strategy and benchmark. Do not subtract it again.
        active.append(selected[("strategy", date)] - selected[("benchmark", date)])
        factors.append(ff5[date][:5] + mom[date])
    return dates, np.asarray(active), np.asarray(factors)


def fit_model(y, factors, lag=12):
    y, factors = np.asarray(y, dtype=float), np.asarray(factors, dtype=float)
    if y.ndim != 1 or factors.ndim != 2 or factors.shape != (len(y), 6):
        raise ValueError("Require a return vector and six factor columns")
    if not np.isfinite(y).all() or not np.isfinite(factors).all():
        raise ValueError("Nonfinite regression input")
    n = len(y)
    x = np.column_stack((np.ones(n), factors))
    k = x.shape[1]
    if n <= k or not isinstance(lag, int) or lag < 0 or lag >= n:
        raise ValueError("Insufficient observations or invalid lag")
    if np.linalg.matrix_rank(x) != k:
        raise ValueError("Rank-deficient factor matrix")
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - x @ beta
    scores = x * residual[:, None]
    meat = scores.T @ scores
    for offset in range(1, lag + 1):
        cross = scores[offset:].T @ scores[:-offset]
        meat += (1 - offset / (lag + 1)) * (cross + cross.T)
    bread = np.linalg.inv(x.T @ x)
    covariance = n / (n - k) * bread @ meat @ bread
    covariance = (covariance + covariance.T) / 2
    if np.min(np.diag(covariance)) < -1e-12:
        raise ValueError("Invalid covariance")
    se = np.sqrt(np.maximum(np.diag(covariance), 0))
    reference = sm.OLS(y, x).fit(cov_type="HAC",
        cov_kwds={"maxlags": lag, "kernel": "bartlett", "use_correction": True}, use_t=False)
    np.testing.assert_allclose(beta, reference.params, rtol=1e-8, atol=1e-12)
    np.testing.assert_allclose(covariance, reference.cov_params(), rtol=1e-7, atol=1e-12)
    orthogonality = float(np.max(np.abs(x.T @ residual)))
    if orthogonality > 1e-8:
        raise ValueError("OLS residuals are not orthogonal")
    variance = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1 - float(residual @ residual) / variance if variance > 0 else None
    lag_one = None
    if np.std(residual[:-1]) > 1e-14 and np.std(residual[1:]) > 1e-14:
        lag_one = float(np.corrcoef(residual[:-1], residual[1:])[0, 1])
    return {
        "observations": n, "factor_names": list(FACTOR_NAMES),
        "params": beta.tolist(), "standard_errors": se.tolist(),
        "covariance": covariance.tolist(),
        "annual_alpha": float(12 * beta[0]),
        "annual_alpha_interval": [float(12*(beta[0]-Z95*se[0])), float(12*(beta[0]+Z95*se[0]))],
        "r_squared": r_squared,
        "residual_diagnostics": {"mean": float(residual.mean()), "lag_one_correlation": lag_one,
            "max_abs_x_transpose_residual": orthogonality,
            "mean_decomposition_error": float(y.mean() - beta[0] - factors.mean(axis=0) @ beta[1:])},
        "mean_decomposition": {"annual_active_mean": float(12*y.mean()),
            "annual_intercept": float(12*beta[0]),
            "annual_factor_contributions": dict(zip(FACTOR_NAMES, (12*factors.mean(axis=0)*beta[1:]).tolist())),
            "annual_residual_mean": float(12*residual.mean())},
        "matrix_rank": int(np.linalg.matrix_rank(x)), "matrix_condition_number": float(np.linalg.cond(x)),
        "hac": {"lag": lag, "kernel": "Bartlett", "finite_sample_multiplier": n / (n-k),
                "interval_distribution": "normal", "z95": Z95},
        "independent_statsmodels_comparison": "passed",
    }


def load_archive(name, output, input_dir=None, expected_sha=None):
    if input_dir:
        raw = (Path(input_dir) / (name + ".zip")).read_bytes()
        mode = "replay"
    else:
        request = urllib.request.Request(SOURCES[name], headers={"User-Agent": "Stock-Movement-research/0.2"})
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read(MAX_BYTES + 1)
        mode = "download"
    if len(raw) > MAX_BYTES:
        raise ValueError("Oversized source")
    sha = hashlib.sha256(raw).hexdigest()
    if expected_sha and sha != expected_sha:
        raise ValueError("Factor source vintage changed")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = [entry for entry in archive.infolist() if entry.filename.lower().endswith(".csv")]
        if len(entries) != 1 or entries[0].file_size > MAX_BYTES:
            raise ValueError("Unexpected factor archive")
        text = archive.read(entries[0]).decode("utf-8-sig")
    (output / (name + ".zip")).write_bytes(raw)
    columns = FF5_COLUMNS if name == "ff5" else MOM_COLUMNS
    data = parse_factors(text, columns)
    first_data_line = next(i for i, line in enumerate(text.splitlines()) if re.match(r"\s*\d{6},", line))
    meta = {"url": SOURCES[name], "sha256": sha, "retrieved_or_replayed_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": mode, "zip_member": entries[0].filename, "source_header": "\n".join(text.splitlines()[:first_data_line]),
            "first_month": min(data), "last_month": max(data), "columns": list(columns)}
    return data, meta


def verify_baseline(current, original):
    if current["source"]["sha256"] != EXPECTED_INDUSTRY_SHA or original["source"]["sha256"] != EXPECTED_INDUSTRY_SHA:
        raise ValueError("P1 industry vintage mismatch")
    for cost in ("0", "10", "25"):
        for portfolio in ("strategy", "benchmark"):
            now = current["scenarios"][cost]["2000-2025"][portfolio]
            before = original["scenarios"][cost]["2000-2025"][portfolio]
            if now["months"] != 312:
                raise ValueError("P1 sample changed")
            for key in ("cagr", "annualized_volatility", "max_month_end_drawdown", "annualized_traded_notional"):
                if not np.isclose(now[key], before[key], rtol=1e-10, atol=1e-12):
                    raise ValueError("P1 aggregate changed: " + key)
            if now["annual_returns"].keys() != before["annual_returns"].keys():
                raise ValueError("P1 annual sample changed")
            np.testing.assert_allclose(list(now["annual_returns"].values()),
                                       list(before["annual_returns"].values()), rtol=1e-10, atol=1e-12)


def make_report(result):
    lines = ["# E04-P2 factor attribution", "",
        "Historical conditional attribution of industry momentum minus the equal-industry benchmark. Not a forecast or causal estimate.", "",
        "| Allocation cost | Annualized arithmetic alpha | Approximate 95% HAC interval | R-squared |",
        "|---|---:|---:|---:|"]
    for cost, model in result["scenarios"].items():
        lo, hi = model["annual_alpha_interval"]
        lines.append(f"| {cost} bp | {model['annual_alpha']:.2%} | [{lo:.2%}, {hi:.2%}] | {model['r_squared']:.3f} |")
    primary = result["scenarios"]["10"]
    lines += ["", "Alpha is 12 times the monthly regression intercept; it is not the CAGR difference or a future return forecast.",
        "Dependent variable: strategy minus benchmark; RF is not subtracted again.",
        "Six contemporaneous factors: market excess return, size, value, profitability, investment and stock momentum.",
        "HAC: Bartlett lag 12, n/(n-7) correction, normal 95% interval.", "",
        "## Primary 10 bp factor exposures", "",
        "| Factor | Coefficient | HAC standard error |", "|---|---:|---:|"]
    for i, name in enumerate(FACTOR_NAMES, 1):
        lines.append(f"| {name} | {primary['params'][i]:.4f} | {primary['standard_errors'][i]:.4f} |")
    lo, hi = primary["annual_alpha_interval"]
    conclusion = ("The primary interval includes zero: these data do not establish positive factor-adjusted alpha."
                  if lo <= 0 <= hi else
                  "The primary interval excludes zero in this specified model; this remains conditional historical evidence, not an executable edge.")
    lines += ["", conclusion, "",
        "The frozen P1 return series was reproduced against its committed source hash and aggregate statistics.",
        "Manual OLS/HAC calculations matched statsmodels. Both raw factor archives and dependency versions are retained in the run artifact.",
        "Constant exposures, omitted factors, reconstructed data and approximate trading costs limit interpretation.",
        "No strategy parameters, factors, sample periods or HAC settings were selected from these attribution results.", "",
        "Code commit: " + result["code_commit"], ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-dir", default="work/e04-p1")
    parser.add_argument("--output-dir", default="work/e04-p2")
    parser.add_argument("--factor-input-dir")
    parser.add_argument("--expected-factor-results", help="Prior P2 JSON holding expected source hashes")
    args = parser.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    baseline_path = Path(args.baseline_dir)
    current = json.loads((baseline_path / "results.json").read_text())
    original = json.loads(Path("research/results/E04-P1-results.json").read_text())
    verify_baseline(current, original)
    monthly = json.loads((baseline_path / "monthly.json").read_text())
    expected = json.loads(Path(args.expected_factor_results).read_text())["sources"] if args.expected_factor_results else {}
    ff5, ff5_meta = load_archive("ff5", output, args.factor_input_dir, expected.get("ff5", {}).get("sha256"))
    mom, mom_meta = load_archive("momentum", output, args.factor_input_dir, expected.get("momentum", {}).get("sha256"))
    result = {"experiment": "E04-P2-1", "code_commit": os.environ.get("GITHUB_SHA", "local-unrecorded"),
              "sample": {"start": 200001, "end": 202512, "months": 312},
              "baseline_reproduction": "passed", "industry_sha256": EXPECTED_INDUSTRY_SHA,
              "sources": {"ff5": ff5_meta, "momentum": mom_meta},
              "versions": {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "pandas", "statsmodels")},
              "scenarios": {}}
    for cost in (0, 10, 25):
        dates, active, factors = align_months(monthly, ff5, mom, cost)
        result["scenarios"][str(cost)] = fit_model(active, factors)
        with (output / ("aligned-" + str(cost) + "bp.csv")).open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["month", "active_return", *FACTOR_NAMES])
            writer.writerows([date, float(y), *f.tolist()] for date, y, f in zip(dates, active, factors))
    (output / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    report = make_report(result)
    (output / "report.md").write_text(report)
    print(report)
    print("ATTRIBUTION_JSON_BEGIN")
    print(json.dumps(result, allow_nan=False))
    print("ATTRIBUTION_JSON_END")


if __name__ == "__main__":
    main()
