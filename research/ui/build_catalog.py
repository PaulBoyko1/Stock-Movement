"""Embed the canonical literature catalog so the prototype works as one offline file."""
import argparse
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parent
CATALOG = DIRECTORY.parent / "evidence-catalog.json"
HTML = DIRECTORY / "index.html"
START = '<script type="application/json" id="paper-catalog-data">'
END = '</script><!-- END PAPER CATALOG -->'


def validate_catalog(catalog):
    papers = catalog["papers"]
    if catalog["schema_version"] != 1 or len(papers) != 27:
        raise ValueError("Expected schema 1 and the 27-paper screened register")
    if {paper["id"] for paper in papers} != {f"R{i:02d}" for i in range(1, 28)}:
        raise ValueError("Paper IDs must uniquely preserve R01 through R27")
    for paper in papers:
        for field in ("title", "authors", "family", "finding", "limitation", "application",
                      "source_kind", "verification_scope", "source_url"):
            if not isinstance(paper[field], str) or not paper[field].strip():
                raise ValueError("Missing paper field: " + field)
        if not isinstance(paper["year"], int) or not 1900 <= paper["year"] <= 2026:
            raise ValueError("Invalid publication year")
        if paper["evidence_stage"] != "published":
            raise ValueError("This catalog contains screened literature, not local replications")
        if not paper["source_url"].startswith("https://"):
            raise ValueError("Sources must be HTTPS URLs")
        if not paper["horizons"] or not set(paper["horizons"]) <= {"intraday", "weeks", "months", "years"}:
            raise ValueError("Invalid proposed application tags")
    return catalog


def embedded_json(catalog):
    # A literal </script> in imported text must not terminate the data element.
    return json.dumps(validate_catalog(catalog), ensure_ascii=False, indent=2).replace("<", "\\u003c")


def build(html, catalog):
    if html.count(START) != 1 or html.count(END) != 1:
        raise ValueError("Expected exactly one catalog insertion point")
    before, tail = html.split(START)
    _, after = tail.split(END)
    return before + START + "\n" + embedded_json(catalog) + "\n" + END + after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the embedded copy is stale")
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    original = HTML.read_text(encoding="utf-8")
    generated = build(original, catalog)
    if args.check:
        if generated != original:
            raise SystemExit("Embedded catalog is stale; run python research/ui/build_catalog.py")
        print("27-paper embedded catalog matches its canonical source")
    else:
        HTML.write_text(generated, encoding="utf-8", newline="\n")
        print("Embedded 27 screened papers into the offline interface")


if __name__ == "__main__":
    main()
