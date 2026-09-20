"""Prepare a compact, provenance-linked monthly panel from the frozen P1 source."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/code"))
from industry_baseline import parse_monthly, read_source

EXPECTED = "c7316c6ae07bc2028632b57ad757dfef8303a62a6956946d7aabe926aadfdeb4"
LABELS = ["Consumer nondurables", "Consumer durables", "Manufacturing", "Energy",
          "Chemicals", "Business equipment", "Telecommunications", "Utilities",
          "Shops", "Healthcare", "Finance", "Other"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-zip")
    args = parser.parse_args()
    raw, text, source = read_source(args.input_zip, EXPECTED)
    names, rows = parse_monthly(text)
    archive = ROOT / "work/backtest-source"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "source.zip").write_bytes(raw)
    panel = {"meta": {"id": "french-12-industry-202607-1994-2025",
        "title": "12 historical industry research portfolios",
        "frequency": "monthly", "returnUnits": "decimal total returns",
        "sourceUrl": source["source_url"], "sourceSha256": EXPECTED,
        "retrievedAtUtc": source["retrieved_or_replayed_at_utc"], "sourceHeader": source["source_header"],
        "defaultStart": "2000-01", "defaultEnd": "2025-12", "dataStart": "1994-01", "dataEnd": "2025-12",
        "warmupNote": "1994–1999 retained for formation history; default evaluation is 2000–2025.",
        "limitations": "Reconstructed value-weighted industry portfolios, not stock/ETF prices or modern fixed sectors. No live or intraday data. Historical data can be revised."},
        "series": [{"id": name, "label": label} for name,label in zip(names,LABELS)],
        "rows": [{"month":f"{month//100:04d}-{month%100:02d}","returns":returns}
                 for month,returns in rows if 199401<=month<=202512]}
    target = ROOT / "research/ui/backtest-data.json"
    target.write_text(json.dumps(panel,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8",newline="\n")
    print(f"Prepared {len(panel['rows'])} observed months; raw source hash verified")


if __name__ == "__main__":
    main()
