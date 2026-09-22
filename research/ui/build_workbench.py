"""Embed the canonical workbench assets into the single-file offline interface."""
import argparse
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
HTML = DIRECTORY / "index.html"
ASSETS = (
    ("/* BEGIN BACKTEST CSS */", "/* END BACKTEST CSS */", "workbench.css"),
    ("<!-- BEGIN BACKTEST VIEW -->", "<!-- END BACKTEST VIEW -->", "workbench-view.html"),
    ('<script type="application/json" id="backtest-data">', '</script><!-- END BACKTEST DATA -->', "backtest-data.json"),
    ('<script id="backtest-engine">', '</script><!-- END BACKTEST ENGINE -->', "backtest-engine.js"),
    ('<script id="backtest-ui">', '</script><!-- END BACKTEST UI -->', "workbench-ui.js"),
)


def build(original):
    for start, end, name in ASSETS:
        if original.count(start) != 1 or original.count(end) != 1:
            raise ValueError("Expected exactly one insertion point for " + name)
        asset = (DIRECTORY / name).read_text(encoding="utf-8").strip()
        if name.endswith(".json"):
            asset = json.dumps(json.loads(asset), ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        if name.endswith(".js") and "</script" in asset.lower():
            raise ValueError("Script closing tag cannot be embedded: " + name)
        before, tail = original.split(start)
        _, after = tail.split(end)
        original = before + start + "\n" + asset + "\n" + end + after
    return original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    original = HTML.read_text(encoding="utf-8")
    generated = build(original)
    if args.check:
        if generated != original:
            raise SystemExit("Workbench assets are stale; run python research/ui/build_workbench.py")
        print("Embedded workbench matches all five canonical assets")
    else:
        HTML.write_text(generated, encoding="utf-8", newline="\n")
        print("Embedded workbench assets into the offline interface")


if __name__ == "__main__":
    main()
