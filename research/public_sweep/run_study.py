"""PDS01: bounded public-data collection and exploratory allocation sweeps."""
from __future__ import annotations
import csv, hashlib, io, itertools, json, os, platform, sys, time, traceback, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

ETFS = "SPY QQQ IWM DIA XLB XLE XLF XLI XLK XLP XLU XLV XLY VOO VTI VTV VUG IWD IWF IWB MDY RSP MTUM QUAL USMV VLUE XLC XLRE SMH SOXX IGV IBB XBI IYT KRE KBE".split()
ETFS = list(dict.fromkeys(ETFS))
SECTORS = "XLB XLE XLF XLI XLK XLP XLU XLV XLY".split()
BROAD = "SPY QQQ IWM DIA MDY RSP VTI".split()
COSTS = np.array([0., 5., 10., 25.])
SOURCES = {
    "industry49": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_daily_CSV.zip",
    "factors": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip",
}
ROOT = Path("work/public-sweep")
PRIVATE = ROOT / "private"
PUBLIC = ROOT / "summary"
SEED = 20260927

def stamp():
    return datetime.now(timezone.utc).isoformat()

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")

def french_csv(text, columns):
    """First daily table only; reject duplicates and preserve missing sentinels."""
    names, records, started = None, [], False
    for line in text.splitlines():
        fields = [v.strip() for v in line.split(",")]
        daily = bool(fields and len(fields[0]) == 8 and fields[0].isdigit())
        if daily:
            if names is None or len(fields) != columns + 1:
                raise ValueError("French table header/dimensions")
            date = pd.Timestamp(datetime.strptime(fields[0], "%Y%m%d"))
            raw = [float(v) for v in fields[1:]]
            if not np.isfinite(raw).all():
                raise ValueError("Nonfinite source return")
            values = [np.nan if v in (-99.99, -999.0) else v / 100 for v in raw]
            records.append((date, values))
            started = True
        elif started:
            break
        elif len(fields) == columns + 1 and not fields[0]:
            names = fields[1:]
    if not records or len(set(names)) != columns or any(not n for n in names):
        raise ValueError("No valid first daily table")
    dates = pd.DatetimeIndex([r[0] for r in records])
    if not dates.is_monotonic_increasing or dates.has_duplicates:
        raise ValueError("Unordered/duplicate source dates")
    return pd.DataFrame([r[1] for r in records], index=dates, columns=names)

def download_french(name, ncols, manifest):
    url = SOURCES[name]
    request = urllib.request.Request(url, headers={"User-Agent": "Stock-Movement-public-research/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(40_000_001)
    if len(raw) > 40_000_000:
        raise ValueError("Source exceeds download cap")
    (PRIVATE / (name + ".zip")).write_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = [v for v in archive.infolist() if v.filename.lower().endswith(".csv")]
        if len(entries) != 1 or entries[0].file_size > 100_000_000:
            raise ValueError("Unexpected source archive")
        text = archive.read(entries[0]).decode("utf-8-sig")
    frame = french_csv(text, ncols)
    frame.to_csv(PRIVATE / (name + ".csv"), index_label="date")
    manifest.append({"source": name, "url": url, "retrieved_at": stamp(), "raw_sha256": sha(raw),
        "zip_bytes": len(raw), "member": entries[0].filename, "header": text.splitlines()[:8],
        "rows": len(frame), "series": ncols, "observations": int(frame.notna().sum().sum()),
        "missing_cells": int(frame.isna().sum().sum()), "first": str(frame.index[0].date()),
        "last": str(frame.index[-1].date()), "classification": "reconstructed research returns"})
    print("DATA", name, len(frame), ncols, flush=True)
    return frame

def download_etfs(manifest, failures):
    import yfinance as yf
    frames = {}
    for ticker in ETFS:
        try:
            frame = yf.Ticker(ticker).history(start="1993-01-01", end="2026-01-01",
                interval="1d", auto_adjust=False, back_adjust=False, actions=True,
                repair=False, keepna=True, rounding=False, timeout=30, raise_errors=True)
            if frame is None or frame.empty:
                raise ValueError("Empty provider response")
            frame.index = pd.DatetimeIndex(frame.index).tz_localize(None).normalize()
            if frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
                raise ValueError("Duplicate/unordered dates")
            required = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
            if any(c not in frame for c in required):
                raise ValueError("Required OHLC/adjustment field missing")
            values = frame[required].to_numpy(float)
            invalid = (~np.isfinite(values).all(axis=1) | (values[:, :5] <= 0).any(axis=1)
                | (values[:, 5] < 0) | (values[:, 1] < np.maximum(values[:, 0], values[:, 3]))
                | (values[:, 2] > np.minimum(values[:, 0], values[:, 3])))
            raw = frame.to_csv(index_label="date").encode()
            (PRIVATE / (ticker + ".csv")).write_bytes(raw)
            div = frame.get("Dividends", pd.Series(0., index=frame.index))
            splits = frame.get("Stock Splits", pd.Series(0., index=frame.index))
            adj_return = frame["Adj Close"].pct_change(fill_method=None)
            implied = (frame["Close"] + div) / frame["Close"].shift(1) - 1
            mismatch = (adj_return - implied).abs() > .002
            mismatches = [str(d.date()) for d in frame.index[mismatch & (splits == 0)]]
            manifest.append({"source": ticker, "provider": "Yahoo via yfinance", "retrieved_at": stamp(),
                "snapshot_sha256": sha(raw), "snapshot_kind": "unrepaired provider DataFrame CSV, not HTTP wire bytes",
                "rows": len(frame), "observations": int(frame["Adj Close"].notna().sum()),
                "first": str(frame.index[0].date()), "last": str(frame.index[-1].date()),
                "invalid_rows": int(invalid.sum()), "ordinary_return_reconciliation_gt20bp_dates": mismatches,
                "dividend_events": int((div != 0).sum()), "split_events": int((splits != 0).sum()),
                "classification": "surviving ETF; vendor-adjusted total-return proxy; actions not independently reconciled"})
            if invalid.any():
                raise ValueError("Invalid OHLC rows: " + str(int(invalid.sum())))
            frames[ticker] = frame
            print("DATA", ticker, len(frame), "adjustment_flags", len(mismatches), flush=True)
        except Exception as exc:
            failures.append({"stage": "download_etf", "id": ticker, "error": str(exc)[:400]})
            print("DATA_FAILED", ticker, type(exc).__name__, flush=True)
        time.sleep(.5)
    return frames

def complete_panel(frame, calendar, start, warm_start):
    required_dates = calendar[(calendar >= pd.Timestamp(warm_start)) & (calendar <= pd.Timestamp("2025-12-31"))]
    if len(required_dates) == 0:
        raise ValueError("Empty required calendar")
    panel = frame.reindex(required_dates)
    if not np.isfinite(panel.to_numpy()).all():
        raise ValueError("Missing/nonfinite required panel observations; no filling or date deletion")
    if (panel.to_numpy() <= 0).any():
        raise ValueError("Nonpositive level")
    first_eval = int(panel.index.searchsorted(pd.Timestamp(start)))
    if first_eval < 276:
        raise ValueError("Insufficient fixed warmup")
    return panel, first_eval

def parameter_grid():
    output = []
    for look, skip, k, every, trend in itertools.product([21,63,126,252], [0,5,21], [1,3,5], [5,21,63], [0,100,200]):
        output.append(dict(family="momentum", lookback=look, skip=skip, top_k=k, every=every, trend=trend))
    for look, k, every, trend in itertools.product([1,3,5,10,21], [1,3,5], [1,5,21], [0,100,200]):
        output.append(dict(family="reversal", lookback=look, skip=0, top_k=k, every=every, trend=trend))
    return output

def self_finance(target, old, costs=COSTS / 10000):
    """Post-fee wealth / pre-fee wealth; contraction gives machine precision."""
    costs = np.asarray(costs, float)
    if (target < 0).any() or target.sum() > 1 + 1e-12 or (old < 0).any() or old.sum() > 1 + 1e-12:
        raise ValueError("Invalid long-only weights")
    g = np.ones(len(costs))
    for _ in range(10):
        g = 1 - costs * np.abs(g[:, None] * target - old).sum(axis=1)
    residual = g - (1 - costs * np.abs(g[:, None] * target - old).sum(axis=1))
    if np.max(np.abs(residual)) > 1e-12 or (g <= 0).any():
        raise ValueError("Self-financing solve failed")
    return g, np.abs(g[:, None] * target - old).sum(axis=1)

def moving_average(levels, length):
    c = np.vstack([np.zeros(levels.shape[1]), np.cumsum(levels, axis=0)])
    out = np.full_like(levels, np.nan)
    out[length-1:] = (c[length:] - c[:-length]) / length
    return out

def target_at(levels, feature, p, averages):
    n = levels.shape[1]
    if p["family"] == "equal":
        return np.full(n, 1/n)
    end = feature - p["skip"]
    start = end - p["lookback"]
    if start < 0:
        raise ValueError("Future/insufficient history")
    score = levels[end] / levels[start] - 1
    allowed = np.ones(n, bool)
    if p["trend"]:
        allowed = levels[feature] > averages[p["trend"]][feature]
    order = np.argsort(-score if p["family"] == "momentum" else score, kind="stable")
    selected = [i for i in order if allowed[i]][:p["top_k"]]
    target = np.zeros(n)
    target[selected] = 1/p["top_k"]
    return target

def simulate(levels, rf, start, p, averages=None, costs=COSTS / 10000):
    levels, rf, costs = np.asarray(levels, float), np.asarray(rf, float), np.asarray(costs, float)
    if len(rf) != len(levels) or not np.isfinite(levels).all() or (levels <= 0).any() or not np.isfinite(rf).all() or (rf <= -1).any():
        raise ValueError("Invalid levels/cash")
    if start < 2 or start >= len(levels):
        raise ValueError("Invalid start")
    averages = averages if averages is not None else {v:moving_average(levels, v) for v in [100,200]}
    ret = levels[1:] / levels[:-1] - 1
    n = len(levels) - start
    result = np.zeros((n, len(costs)))
    turnover = np.zeros_like(result)
    exposure = np.zeros(n)
    weights = np.zeros(levels.shape[1])
    for row, i in enumerate(range(start, len(levels))):
        trade = row % p["every"] == 0
        g = np.ones(len(costs))
        if trade:
            target = target_at(levels, i-2, p, averages)
            g, turnover[row] = self_finance(target, weights, costs)
            weights = target
        cash = max(0., 1 - weights.sum())
        gross = float(weights @ ret[i-1] + cash * rf[i])
        exposure[row] = weights.sum()
        if 1 + gross <= 0:
            raise ValueError("Nonpositive gross wealth")
        end_weights = weights * (1 + ret[i-1]) / (1 + gross)
        result[row] = g * (1 + gross) - 1
        if row == n-1:
            liquidation = end_weights.sum()
            result[row] = (1 + result[row]) * (1 - costs * liquidation) - 1
            turnover[row] += liquidation * g * (1 + gross)
        weights = end_weights
    if not np.isfinite(result).all() or (result <= -1).any():
        raise ValueError("Invalid net return")
    return result, turnover, exposure

def metrics(returns, benchmark, turnover, exposure):
    r, b = np.asarray(returns), np.asarray(benchmark)
    n = len(r)
    wealth = np.cumprod(1+r)
    peak = np.maximum.accumulate(np.r_[1., wealth])[1:]
    active = r-b
    vol = float(np.std(r, ddof=1) * np.sqrt(252))
    avol = float(np.std(active, ddof=1) * np.sqrt(252))
    return {"days": n, "cagr": float(wealth[-1] ** (252/n)-1), "total_return": float(wealth[-1]-1),
        "volatility": vol, "max_drawdown": float(np.min(wealth/peak-1)),
        "annual_turnover": float(np.sum(turnover)*252/n), "mean_invested": float(np.mean(exposure)),
        "annual_active_mean": float(np.mean(active)*252),
        "information_ratio": float(np.mean(active)*252/avol) if avol > 1e-12 else None,
        "worst_five_daily_log_return_sum": float(np.sort(np.log1p(r))[:5].sum())}

def periods(dates):
    return {"discovery": dates < pd.Timestamp("2015-01-01"),
        "validation": (dates >= pd.Timestamp("2015-01-01")) & (dates < pd.Timestamp("2020-01-01")),
        "retrospective_2020_2025": dates >= pd.Timestamp("2020-01-01"),
        "full": np.ones(len(dates), bool)}

def block_diagnostic(active, chosen, block, reps=499, seed=SEED):
    x = np.asarray(active, float)
    n, k = x.shape
    if n < 2*block or not np.isfinite(x).all():
        raise ValueError("Invalid bootstrap matrix")
    rng = np.random.default_rng(seed + block)
    # Circular moving blocks; same sampled dates for every candidate.
    extended = np.concatenate([x, x[:block]], axis=0)
    cumulative = np.vstack([np.zeros(k), np.cumsum(extended, axis=0)])
    full, tail = divmod(n, block)
    draws = np.empty((reps, k))
    for rep in range(reps):
        starts = rng.integers(0, n, size=full)
        total = (cumulative[starts+block]-cumulative[starts]).sum(axis=0)
        if tail:
            s = int(rng.integers(0, n))
            total += cumulative[s+tail]-cumulative[s]
        draws[rep] = total/n
    means = x.mean(axis=0)
    observed = max(0., float(means.max()))
    null_max = np.maximum(0., (draws-means).max(axis=1))
    return {"block_days":block, "replications":reps, "trials":k,
        "max_annual_active_mean":observed*252,
        "centered_max_mean_p":float((1+(null_max>=observed-1e-15).sum())/(reps+1)),
        "selected_annual_active_mean":float(means[chosen]*252),
        "selected_annual_mean_interval":(np.quantile(draws[:,chosen],[.025,.975])*252).tolist(),
        "scope":"exploratory within-panel nonstudentized circular-block diagnostic; not factor alpha or untouched holdout"}

def run_panel(name, panel, rf, start, failures):
    dates, levels = panel.index[start:], panel.to_numpy()
    rf = rf.reindex(panel.index).to_numpy()
    if not np.isfinite(rf).all():
        raise ValueError("Missing cash-rate dates")
    averages = {v:moving_average(levels,v) for v in [100,200]}
    grid = parameter_grid()
    benchmarks = {}
    for every in [1,5,21,63,len(levels)+1]:
        p = dict(family="equal", every=every)
        benchmarks[every] = simulate(levels, rf, start, p, averages)
    masks = periods(dates)
    all_rows, all_active, successful, chosen, best_score = [], [], [], None, -float("inf")
    for serial, p in enumerate(grid):
        trial = name + "-" + str(serial+1).zfill(4)
        try:
            r, traded, exposure = simulate(levels, rf, start, p, averages)
            b = benchmarks[p["every"]][0]
            for c, cost in enumerate(COSTS):
                row = {"trial":trial, "dataset":name, **p, "cost_bps":int(cost)}
                for label, mask in masks.items():
                    row[label] = metrics(r[mask,c],b[mask,c],traded[mask,c],exposure[mask])
                all_rows.append(row)
            validation = metrics(r[masks["validation"],2],b[masks["validation"],2],
                traded[masks["validation"],2],exposure[masks["validation"]])
            score = validation["information_ratio"]
            if score is not None and score > best_score:
                best_score, chosen = score, len(successful)
            all_active.append((r-b)[masks["retrospective_2020_2025"],2])
            successful.append((trial,p))
        except Exception as exc:
            failures.append({"stage":"trial","dataset":name,"trial":trial,"params":p,"error":str(exc)[:400]})
        if serial % 100 == 0:
            print("SWEEP", name, serial, "of", len(grid), flush=True)
    if len(successful) != len(grid) or chosen is None:
        raise ValueError("Incomplete sweep or no validation selection; no partial winner report")
    with (PUBLIC/(name+"-all-trials.json")).open("w") as handle:
        json.dump(all_rows,handle,allow_nan=False)
    flat = []
    for row in all_rows:
        for label in masks:
            flat.append({k:v for k,v in row.items() if k not in masks} | {"period":label} | row[label])
    with (PUBLIC/(name+"-all-trials.csv")).open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(flat[0]))
        writer.writeheader();writer.writerows(flat)
    selected_id,p = successful[chosen]
    selected = [row for row in all_rows if row["trial"]==selected_id]
    selected_r, selected_t, selected_x = simulate(levels,rf,start,p,averages)
    b = benchmarks[p["every"]][0]
    annual=[]
    for year in sorted(set(dates.year)):
        mask=dates.year==year
        annual.append({"year":int(year),**metrics(selected_r[mask,2],b[mask,2],selected_t[mask,2],selected_x[mask])})
    zero_r, zero_t, zero_x = simulate(levels,np.zeros(len(rf)),start,p,averages)
    zero_b = simulate(levels,np.zeros(len(rf)),start,dict(family="equal",every=p["every"]),averages)[0]
    active=np.column_stack(all_active)
    # Per-day matrices are local/temporary only; upload allowlist excludes private/.
    np.savez_compressed(PRIVATE/(name+"-active-primary.npz"),active=active)
    summary={"dataset":name,"start":str(dates[0].date()),"end":str(dates[-1].date()),
        "assets":list(panel.columns),"evaluation_days":len(dates),"signal_variants":len(grid),
        "strategy_cost_evaluations":len(all_rows),"selected_by":"2015-2019 information ratio at 10bp",
        "selected_trial":selected_id,"selected_parameters":p,"selected_all_costs":selected,
        "selected_annual_10bp":annual,
        "selected_zero_cash_yield_full":metrics(zero_r[:,2],zero_b[:,2],zero_t[:,2],zero_x),
        "benchmarks":{str(every):{label:metrics(v[0][mask,2],v[0][mask,2],v[1][mask,2],v[2][mask])
            for label,mask in masks.items()} for every,v in benchmarks.items()},
        "bootstrap":[block_diagnostic(active,chosen,block) for block in [21,63]]}
    write_json(PUBLIC/(name+"-summary.json"),summary)
    return summary

def report_text(manifest, failures, summaries, versions):
    lines=["# PDS01 public-data study","", "Exploratory results; no live trading or model promotion.",
        "2020–2025 was previously observed and is not an untouched holdout.",
        "ETF adjusted-close calculations are total-return proxies, not verified cash/share execution.",
        "Raw/vendor snapshots remain temporary in this CI run; only summaries are retained.","",
        "## Collection", "", f"- Retrieved sources: {len(manifest)}",
        f"- Valid reported nonmissing return/adjusted-close observations: {sum(v.get('observations',0) for v in manifest):,}",
        f"- Recorded failures: {len(failures)}", "", "## Validation-selected configurations", "",
        "| Panel | Days | Variants/cost runs | Configuration | Discovery CAGR | Validation CAGR | 2020–25 CAGR | 2020–25 benchmark CAGR | 2020–25 drawdown |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|"]
    for s in summaries:
        row=next(r for r in s["selected_all_costs"] if r["cost_bps"]==10)
        p=s["selected_parameters"];b=s["benchmarks"][str(p["every"])]["retrospective_2020_2025"]
        label=f'{p["family"]}; L={p["lookback"]}, skip={p["skip"]}, K={p["top_k"]}, rebalance={p["every"]}, SMA={p["trend"]}'
        lines.append(f'| {s["dataset"]} | {s["evaluation_days"]} | {s["signal_variants"]}/{s["strategy_cost_evaluations"]} | {label} | {row["discovery"]["cagr"]:.2%} | {row["validation"]["cagr"]:.2%} | {row["retrospective_2020_2025"]["cagr"]:.2%} | {b["cagr"]:.2%} | {row["retrospective_2020_2025"]["max_drawdown"]:.2%} |')
        for boot in s["bootstrap"]:
            lines.append(f'\n{s["dataset"]}, block {boot["block_days"]}: centered max-mean p={boot["centered_max_mean_p"]:.3f}; selected annual active mean {boot["selected_annual_active_mean"]:.2%}, interval {boot["selected_annual_mean_interval"]}. Exploratory, within-panel only.\n')
    lines += ["","## Limitations","", "Surviving, curated ETF sample; daily source/adjustment and corporate-action uncertainty; reconstructed French portfolios; model costs and cash yield; no spread, auction-size or intraday fill verification; correlated variants; historical selection contamination; stationarity-dependent bootstrap. No individual-stock, options, earnings or intraday strategy is validated by this batch.","",
        "All complete per-trial summaries, failures, source vintages and dependency versions accompany this report. Read PROTOCOL.md for the frozen grid and accounting."]
    return "\n".join(lines)+"\n"

def main():
    PRIVATE.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
    import yfinance
    manifest, failures, summaries = [], [], []
    versions={"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,
        "yfinance":yfinance.__version__,"commit":os.environ.get("GITHUB_SHA"),"started_at":stamp(),
        "code_sha256":sha(Path(__file__).read_bytes()),"protocol_sha256":sha(Path(__file__).with_name("PROTOCOL.md").read_bytes())}
    write_json(PUBLIC/"versions.json",versions)
    Path(PUBLIC/"PROTOCOL.md").write_text(Path(__file__).with_name("PROTOCOL.md").read_text())
    factors=industry=None
    try:
        factors=download_french("factors",4,manifest)
        if "RF" not in factors:raise ValueError("RF missing")
    except Exception as exc:
        failures.append({"stage":"factors","error":str(exc)})
    try:
        industry=download_french("industry49",49,manifest)
    except Exception as exc:
        failures.append({"stage":"industry49","error":str(exc)})
    etfs=download_etfs(manifest,failures)
    write_json(PUBLIC/"data-manifest.json",manifest)
    if factors is not None:
        rf=factors["RF"];calendar=factors.index
        candidates=[]
        if industry is not None:
            try:
                subset=industry.loc["1994-01-01":"2025-12-31"]
                if subset.isna().any().any() or (subset.to_numpy()<=-1).any():
                    raise ValueError("Missing/invalid industry daily returns in research period")
                levels=(1+subset).cumprod()
                panel,start=complete_panel(levels,calendar,"2000-01-01","1994-01-01")
                candidates.append(("industry49",panel,start))
            except Exception as exc:failures.append({"stage":"panel","id":"industry49","error":str(exc)})
        for name,tickers,first,warm in [("sectors9",SECTORS,"2000-03-01","1998-12-23"),("broad7",BROAD,"2005-01-01","2003-05-01")]:
            try:
                absent=[t for t in tickers if t not in etfs]
                if absent:raise ValueError("Missing required ETF(s): "+",".join(absent))
                # Union join preserves gaps; complete_panel tests against the factor calendar.
                prices=pd.concat({t:etfs[t]["Adj Close"] for t in tickers},axis=1)
                panel,start=complete_panel(prices,calendar,first,warm)
                candidates.append((name,panel,start))
            except Exception as exc:failures.append({"stage":"panel","id":name,"error":str(exc)})
        for name,panel,start in candidates:
            try:
                panel.to_csv(PRIVATE/(name+"-canonical-levels.csv"))
                manifest.append({"source":name+"-canonical","rows":len(panel),"series":len(panel.columns),
                    "canonical_sha256":sha((PRIVATE/(name+"-canonical-levels.csv")).read_bytes()),"not_additional_observations":True})
                summaries.append(run_panel(name,panel,rf,start,failures))
            except Exception as exc:
                failures.append({"stage":"sweep","id":name,"error":str(exc),"trace":traceback.format_exc()[-1200:]})
    write_json(PUBLIC/"data-manifest.json",manifest)
    write_json(PUBLIC/"failures.json",failures)
    write_json(PUBLIC/"study-summary.json",{"versions":versions,"datasets":summaries,"failures":failures,
        "source_observations":sum(v.get("observations",0) for v in manifest),
        "signal_variants_completed":sum(v["signal_variants"] for v in summaries),
        "strategy_cost_evaluations":sum(v["strategy_cost_evaluations"] for v in summaries)})
    report=report_text(manifest,failures,summaries,versions)
    (PUBLIC/"REPORT.md").write_text(report)
    summary_path=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path,"a") as handle:handle.write(report)
    print("REPORT_BEGIN\n"+report+"REPORT_END",flush=True)
    print("COMPACT_SUMMARY",json.dumps({"datasets":[{"name":s["dataset"],"days":s["evaluation_days"],
        "variants":s["signal_variants"],"runs":s["strategy_cost_evaluations"],"selected":s["selected_parameters"],
        "primary":next(r for r in s["selected_all_costs"] if r["cost_bps"]==10),
        "bootstrap":s["bootstrap"]} for s in summaries],"observations":sum(v.get("observations",0) for v in manifest),
        "failures":failures},allow_nan=False),flush=True)
    if len(summaries)!=3:
        raise SystemExit("Incomplete study: inspect explicit failures; complete panels retained")

if __name__ == "__main__":
    main()
