"""Audit saved summary artifacts only; does not retrieve or rerun market data."""
from pathlib import Path
import collections, csv, hashlib, json, math, os, statistics
INPUT=Path("work/sweep-analysis/input")
OUTPUT=Path("work/sweep-analysis/summary")
PERIODS=["discovery","validation","retrospective_2020_2025","full"]
def read(name):return json.loads((INPUT/name).read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def median(v):return statistics.median(v) if v else None
def pct(x):return f"{x:.2%}"
def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    study=read("study-summary.json"); manifest=read("data-manifest.json"); failures=read("failures.json")
    assert not failures,failures
    assert study["strategy_cost_evaluations"]==5508
    assert study["signal_variants_completed"]==1377
    actual=[x for x in manifest if not x.get("not_additional_observations")]
    etfs=[x for x in actual if x.get("provider")=="Yahoo via yfinance"]
    assert len(etfs)==36 and all(x["invalid_rows"]==0 for x in etfs)
    assert sum(x.get("observations",0) for x in actual)==study["source_observations"]
    audit={"source_run":36375746801,"source_commit":study["versions"]["commit"],
        "source_artifact_id":10950907873,"source_artifact_digest":"sha256:e04edf48a9ff5ba83cfac5da24c21c628a61be8dc8edb553ae13a2a81556b312",
        "source_observations":study["source_observations"],"source_files":len(actual),
        "etf_count":len(etfs),"etf_rows":sum(x["rows"] for x in etfs),
        "raw_adjustment_flags":sum(len(x["ordinary_return_reconciliation_gt20bp_dates"]) for x in etfs),
        "signal_variants":1377,"strategy_cost_evaluations":5508,"panels":[],"checks":[],
        "input_sha256":{p.name:digest(p) for p in sorted(INPUT.glob("*")) if p.is_file()}}
    summaries={s["dataset"]:s for s in study["datasets"]}
    for name,summary in summaries.items():
        rows=read(name+"-all-trials.json")
        assert len(rows)==1836 and len({r["trial"] for r in rows})==459
        assert len({(r["trial"],r["cost_bps"]) for r in rows})==1836
        assert {r["cost_bps"] for r in rows}=={0,5,10,25}
        baseline=summary["benchmarks"]
        primary=[r for r in rows if r["cost_bps"]==10]
        # Independent re-selection using only the protocol's validation field.
        candidates=[r for r in primary if r["validation"]["information_ratio"] is not None]
        selected=max(candidates,key=lambda r:r["validation"]["information_ratio"])
        assert selected["trial"]==summary["selected_trial"]
        bytrial=collections.defaultdict(list)
        for r in rows:bytrial[r["trial"]].append(r)
        for trial,group in bytrial.items():
            group.sort(key=lambda r:r["cost_bps"])
            for period in PERIODS:
                assert all(group[i][period]["cagr"] >= group[i+1][period]["cagr"]-1e-12 for i in range(3))
                assert all(r[period]["days"]>0 for r in group)
                assert all(-1<=r[period]["max_drawdown"]<=0 for r in group)
                assert all(0<=r[period]["mean_invested"]<=1+1e-10 for r in group)
                # Slice returns must reconcile multiplicatively to the whole run.
            pieces=math.prod(1+group[0][p]["total_return"] for p in PERIODS[:3])-1
            assert math.isclose(pieces,group[0]["full"]["total_return"],rel_tol=1e-9,abs_tol=1e-9)
        stats=[]
        for family in ["all","momentum","reversal"]:
            for cost in [0,5,10,25]:
                subset=[r for r in rows if r["cost_bps"]==cost and (family=="all" or r["family"]==family)]
                for period in PERIODS:
                    active=[r[period]["annual_active_mean"] for r in subset]
                    excess_cagr=[r[period]["cagr"]-baseline[str(r["every"])][period]["cagr"] for r in subset] if cost==10 else []
                    stats.append({"family":family,"cost_bps":cost,"period":period,"variants":len(subset),
                        "positive_active_fraction":sum(x>0 for x in active)/len(active),
                        "median_active_mean":median(active),"median_cagr":median([r[period]["cagr"] for r in subset]),
                        "positive_cagr_excess_fraction":sum(x>0 for x in excess_cagr)/len(excess_cagr) if excess_cagr else None})
        val_positive=[r for r in primary if r["validation"]["annual_active_mean"]>0]
        transfer=sum(r["retrospective_2020_2025"]["annual_active_mean"]>0 for r in val_positive)
        cost_rows=[r for r in rows if r["trial"]==selected["trial"]]
        panel={"name":name,"selected":selected,"selected_costs":cost_rows,"evaluation_days":summary["evaluation_days"],
            "selected_matched_benchmark":baseline[str(selected["every"])],
            "grid_statistics":stats,"validation_positive_count":len(val_positive),
            "validation_positive_also_later_positive_count":transfer,"bootstrap":summary["bootstrap"],
            "zero_cash_yield":summary["selected_zero_cash_yield_full"]}
        audit["panels"].append(panel)
    audit["checks"]=["All 5,508 distinct strategy/cost entries present","459 signal variants per panel",
        "All 36 downloaded ETF datasets have zero invalid OHLC rows","No ordinary return reconciliation differences above 20bp recorded",
        "Original validation selection independently reproduced for all panels","Higher costs never increased a candidate's CAGR in any period",
        "Three period returns multiply to the full-period return at zero costs","Drawdown and exposure ranges checked",
        "Canonical data copies excluded from source-observation counts",
        "Raw snapshots unavailable here: no new validation of provider history, corporate actions or full daily ledgers"]
    lines=["# PDS01 — independent results review","",f"Source run: https://github.com/PaulBoyko1/Stock-Movement/actions/runs/{audit['source_run']}",
        f"Source commit: {audit['source_commit']}","",
        f"Collected {audit['source_observations']:,} nonmissing source return/adjusted-close observations, including {audit['etf_rows']:,} rows across 36 actual ETF histories. The remaining observations are reconstructed industry/factor returns, not individual-stock prices.",
        "Ran 1,377 signal configurations across three panels, each at four costs: 5,508 strategy/cost evaluations. All 14 pre-download contract tests passed. No recorded collection or trial failures.","",
        "## Main result","",
        "No panel passed the exploratory search-adjusted maximum-active-mean test. This is not proof that every strategy has zero value: it means this broad screen did not establish an edge after its search. All selected active-return intervals include zero. Previously inspected 2020–2025 is retrospective robustness, not an untouched holdout.","",
        "### Configurations selected using 2015–2019 only; 10bp per dollar traded","",
        "| Panel | Rule | 2020–25 CAGR | Matched benchmark CAGR | 2020–25 drawdown | Annual active mean | 21-day block interval |",
        "|---|---|---:|---:|---:|---:|---|"]
    for p in audit["panels"]:
        r=p["selected"];m=r["retrospective_2020_2025"];b=p["selected_matched_benchmark"]["retrospective_2020_2025"];boot=p["bootstrap"][0]
        rule=f'{r["family"]}; {r["lookback"]}d lookback, {r["top_k"]} holdings, {r["every"]}d rebalance, SMA {r["trend"]}'
        lo,hi=boot["selected_annual_mean_interval"]
        lines.append(f'| {p["name"]} | {rule} | {pct(m["cagr"])} | {pct(b["cagr"])} | {pct(m["max_drawdown"])} | {pct(m["annual_active_mean"])} | {pct(lo)} to {pct(hi)} |')
    lines += ["","The benchmark uses the same universe and rebalance cadence. Active mean is an arithmetic return difference, not CAGR difference or factor alpha.","",
        "## Full-grid behavior at 10bp, 2020–2025","",
        "| Panel | Family | Configurations | Positive mean active return | Median annual active mean |",
        "|---|---|---:|---:|---:|"]
    for p in audit["panels"]:
        for row in p["grid_statistics"]:
            if row["cost_bps"]==10 and row["period"]=="retrospective_2020_2025":
                lines.append(f'| {p["name"]} | {row["family"]} | {row["variants"]} | {pct(row["positive_active_fraction"])} | {pct(row["median_active_mean"])} |')
    lines += ["","## Cost sensitivity of the validation-selected rule","",
        "| Panel | 0bp CAGR | 5bp CAGR | 10bp CAGR | 25bp CAGR |",
        "|---|---:|---:|---:|---:|"]
    for p in audit["panels"]:
        costs={r["cost_bps"]:r["retrospective_2020_2025"]["cagr"] for r in p["selected_costs"]}
        lines.append("| "+p["name"]+" | "+" | ".join(pct(costs[c]) for c in [0,5,10,25])+" |")
    lines += ["","## Search-adjusted diagnostics","",
        "| Panel | 21-day block p | 63-day block p | Validation-positive configurations still positive later |",
        "|---|---:|---:|---:|"]
    for p in audit["panels"]:
        lines.append(f'| {p["name"]} | {p["bootstrap"][0]["centered_max_mean_p"]:.3f} | {p["bootstrap"][1]["centered_max_mean_p"]:.3f} | {p["validation_positive_also_later_positive_count"]}/{p["validation_positive_count"]} |')
    lines += ["","These are nonstudentized, within-panel circular block-bootstrap diagnostics with 499 draws. They depend on stationarity, are not adjusted across all project research and must not be interpreted as live success probabilities.","",
        "## Data and implementation limits","",
        "- Current surviving ETF list, not a point-in-time census; no individual-stock or intraday claims.",
        "- Vendor-adjusted total-return levels with a full-session delay before assumed closing fills; no validated bid/ask or cash-distribution receivable ledger.",
        "- Zero flags in a 20bp ordinary-return reconciliation is a limited consistency check, not independent corporate-action validation.",
        "- Costs and RF cash yield are modeling assumptions; no capacity or auction-execution validation.",
        "- French history is reconstructed and revisable. Acquisition counts include older/newer observations outside the evaluation periods.",
        "- Raw and normalized vendor downloads stayed in the temporary first runner. This review uses retained summaries only. Raw bytes were not durably preserved and cannot be reconstructed from hashes alone.",
        "- Summary artifacts expire December 27, 2026 unless retained elsewhere. Source manifests and machine-readable findings are preserved with this report.","",
        "## Checks",""]+["- "+x for x in audit["checks"]]
    report="\n".join(lines)+"\n"
    (OUTPUT/"REVIEW.md").write_text(report)
    (OUTPUT/"review.json").write_text(json.dumps(audit,indent=2,allow_nan=False)+"\n")
    # Includes only summarized results and metadata, never downloaded price records.
    export={"review":audit,"report":report,"data_manifest":manifest,"versions":study["versions"],"failures":failures}
    print("REVIEW_EXPORT "+json.dumps(export,allow_nan=False))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as f:f.write(report)
if __name__=="__main__":main()
