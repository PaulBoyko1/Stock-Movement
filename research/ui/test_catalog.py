"""Provenance and safe offline embedding checks for the literature catalog."""
import copy
import json
from pathlib import Path
import unittest

from build_catalog import CATALOG, HTML, START, END, build, embedded_json, validate_catalog


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_sources_belong_to_the_corresponding_register_entries(self):
        register = (CATALOG.parent / "evidence-register.md").read_text(encoding="utf-8")
        for paper in validate_catalog(self.catalog)["papers"]:
            with self.subTest(paper=paper["id"]):
                entry = register.split("**" + paper["id"] + " — ", 1)[1].split("\n\n", 1)[0]
                self.assertIn(paper["source_url"], entry)

    def test_catalog_does_not_promote_or_lose_papers(self):
        for mutation in ("stage", "duplicate", "missing", "scheme", "horizon"):
            candidate = copy.deepcopy(self.catalog)
            if mutation == "stage":
                candidate["papers"][0]["evidence_stage"] = "validated"
            elif mutation == "duplicate":
                candidate["papers"][1]["id"] = "R01"
            elif mutation == "missing":
                candidate["papers"].pop()
            elif mutation == "scheme":
                candidate["papers"][0]["source_url"] = "javascript:alert(1)"
            else:
                candidate["papers"][0]["horizons"] = ["guaranteed"]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_catalog(candidate)

    def test_script_terminator_is_escaped_without_changing_text(self):
        candidate = copy.deepcopy(self.catalog)
        payload = '</script><img src=x onerror="alert(1)">'
        candidate["papers"][0]["finding"] = payload
        data = embedded_json(candidate)
        self.assertNotIn("<", data)
        self.assertEqual(json.loads(data)["papers"][0]["finding"], payload)

    def test_html_contains_exact_current_catalog(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertEqual(build(html, self.catalog), html)
        embedded = html.split(START)[1].split(END)[0]
        self.assertEqual(json.loads(embedded), self.catalog)


if __name__ == "__main__":
    unittest.main()
