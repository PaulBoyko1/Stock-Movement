"""Independent numerical and input-integrity checks for factor attribution."""
from pathlib import Path
import sys
import unittest

import numpy as np
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import factor_attribution as model

FF5_COLUMNS = ("Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF")
MOM_COLUMNS = ("Mom",)


def factor_source(columns, lines):
    return "\n".join([
        "Synthetic input fixture; returns are percentages.",
        "," + ",".join(columns),
        *lines,
        "",
        " Annual Factors: January-December ",
        "," + ",".join(columns),
        "2000," + ",".join(["99"] * len(columns)),
    ])


def regression_fixture():
    rng = np.random.default_rng(104729)
    factors = rng.normal(0.003, 0.04, size=(312, 6))
    innovations = rng.normal(0, 0.015, size=312)
    residual = np.zeros(312)
    for i in range(312):
        residual[i] = innovations[i] + (0.55 * residual[i - 1] if i else 0)
    coefficients = np.array([0.18, -0.12, 0.07, 0.21, -0.09, 0.31])
    y = 0.0014 + factors @ coefficients + residual
    return y, factors


def alignment_fixture():
    dates = [year * 100 + month for year in range(2000, 2026)
             for month in range(1, 13)]
    points, ff5, mom = [], {}, {}
    for i, month in enumerate(dates):
        benchmark = (i % 11 - 5) / 1000
        active = 0.002 + (i % 5) / 10000
        points.extend([
            {"cost_bps": 10, "portfolio": "strategy",
             "month": month, "net_return": benchmark + active},
            {"cost_bps": 10, "portfolio": "benchmark",
             "month": month, "net_return": benchmark},
            # Other cost scenarios must not contaminate the requested series.
            {"cost_bps": 0, "portfolio": "strategy",
             "month": month, "net_return": 0.80},
            {"cost_bps": 0, "portfolio": "benchmark",
             "month": month, "net_return": -0.20},
        ])
        # A deliberately large RF makes accidental subtraction detectable.
        ff5[month] = [0.01, 0.02, -0.01, 0.005, -0.003, 0.04]
        mom[month] = [0.007]
    return dates, points, ff5, mom


class FactorParserTests(unittest.TestCase):
    def test_percent_conversion_column_order_and_annual_stop(self):
        text = factor_source(FF5_COLUMNS, [
            "200001,1.50,-2.00,0.00,0.40,0.20,0.25",
            "200002,0.50,1.00,2.00,-0.10,0.30,0.20",
        ])
        parsed = model.parse_factors(text, FF5_COLUMNS)
        self.assertEqual(sorted(parsed), [200001, 200002])
        np.testing.assert_allclose(
            parsed[200001], [.015, -.02, 0, .004, .002, .0025],
            rtol=0, atol=1e-15,
        )

    def test_momentum_single_column(self):
        parsed = model.parse_factors(
            factor_source(MOM_COLUMNS, ["200001,2.30", "200002,-1.10"]),
            MOM_COLUMNS,
        )
        self.assertEqual(sorted(parsed), [200001, 200002])
        np.testing.assert_allclose(parsed[200001], [.023], rtol=0, atol=1e-15)

    def test_duplicate_month_fails(self):
        with self.assertRaises(ValueError):
            model.parse_factors(
                factor_source(MOM_COLUMNS, ["200001,1", "200001,2"]),
                MOM_COLUMNS,
            )

    def test_invalid_calendar_month_fails(self):
        with self.assertRaises(ValueError):
            model.parse_factors(factor_source(MOM_COLUMNS, ["200013,1"]), MOM_COLUMNS)

    def test_sentinels_and_nonfinite_values_fail(self):
        for value in ("-99.99", "-999", "nan", "inf", "-inf"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.parse_factors(
                    factor_source(MOM_COLUMNS, ["200001," + value]), MOM_COLUMNS,
                )

    def test_wrong_header_and_row_width_fail(self):
        for text in (
            factor_source(("SMB", "Mkt-RF", "HML", "RMW", "CMA", "RF"),
                          ["200001,1,2,3,4,5,6"]),
            factor_source(FF5_COLUMNS, ["200001,1,2,3,4,5"]),
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                model.parse_factors(text, FF5_COLUMNS)


class RegressionReferenceTests(unittest.TestCase):
    def test_coefficients_and_hac_match_independent_statsmodels(self):
        y, factors = regression_fixture()
        observed = model.fit_model(y, factors, lag=12)
        reference = sm.OLS(y, sm.add_constant(factors, has_constant="add")).fit(
            cov_type="HAC",
            cov_kwds={"maxlags": 12, "use_correction": True},
            use_t=False,
        )
        np.testing.assert_allclose(observed["params"], reference.params,
                                   rtol=1e-9, atol=1e-12)
        np.testing.assert_allclose(observed["covariance"], reference.cov_params(),
                                   rtol=1e-8, atol=1e-14)
        self.assertAlmostEqual(observed["annual_alpha"], 12 * reference.params[0], places=12)
        se = np.sqrt(reference.cov_params()[0, 0])
        interval = 12 * np.array([reference.params[0] - 1.959963984540054 * se,
                                  reference.params[0] + 1.959963984540054 * se])
        np.testing.assert_allclose(observed["annual_alpha_interval"], interval,
                                   rtol=1e-8, atol=1e-12)
        self.assertAlmostEqual(observed["r_squared"], reference.rsquared, places=11)
        self.assertIsInstance(observed["residual_diagnostics"], dict)

    def test_known_coefficients_are_recovered(self):
        _, factors = regression_fixture()
        coefficients = np.array([0.002, 0.5, -0.2, 0.1, 0.3, -0.1, 0.4])
        y = coefficients[0] + factors @ coefficients[1:]
        fitted = model.fit_model(y, factors)
        np.testing.assert_allclose(fitted["params"], coefficients, rtol=1e-9, atol=1e-12)
        self.assertAlmostEqual(fitted["r_squared"], 1.0, places=12)
        self.assertAlmostEqual(fitted["annual_alpha"], .024, places=12)

    def test_lag_zero_matches_hc1(self):
        y, factors = regression_fixture()
        fitted = model.fit_model(y, factors, lag=0)
        reference = sm.OLS(y, sm.add_constant(factors, has_constant="add")).fit(
            cov_type="HC1", use_t=False,
        )
        np.testing.assert_allclose(fitted["covariance"], reference.cov_params(),
                                   rtol=1e-8, atol=1e-14)

    def test_zero_active_series_has_zero_alpha_and_undefined_r_squared(self):
        _, factors = regression_fixture()
        fitted = model.fit_model(np.zeros(len(factors)), factors)
        np.testing.assert_allclose(fitted["params"], np.zeros(7), atol=1e-14)
        np.testing.assert_allclose(fitted["covariance"], np.zeros((7, 7)), atol=1e-14)
        np.testing.assert_allclose(fitted["annual_alpha_interval"], [0, 0], atol=1e-14)
        self.assertEqual(fitted["annual_alpha"], 0)
        self.assertIsNone(fitted["r_squared"])

    def test_rank_deficient_design_fails(self):
        y, factors = regression_fixture()
        factors[:, 5] = factors[:, 0]
        with self.assertRaises(ValueError):
            model.fit_model(y, factors)

    def test_rescaling_outcome_preserves_units(self):
        y, factors = regression_fixture()
        original = model.fit_model(y, factors)
        scaled = model.fit_model(2 * y, factors)
        np.testing.assert_allclose(scaled["params"], 2 * np.asarray(original["params"]),
                                   rtol=1e-8, atol=1e-12)
        np.testing.assert_allclose(scaled["covariance"],
                                   4 * np.asarray(original["covariance"]),
                                   rtol=1e-8, atol=1e-14)
        np.testing.assert_allclose(scaled["annual_alpha_interval"],
                                   2 * np.asarray(original["annual_alpha_interval"]),
                                   rtol=1e-8, atol=1e-12)
        self.assertAlmostEqual(scaled["r_squared"], original["r_squared"], places=12)

    def test_factor_column_permutation_preserves_alpha_and_fit(self):
        y, factors = regression_fixture()
        permutation = [5, 4, 0, 2, 1, 3]
        original = model.fit_model(y, factors)
        reordered = model.fit_model(y, factors[:, permutation])
        indices = [0] + [i + 1 for i in permutation]
        np.testing.assert_allclose(reordered["params"],
                                   np.asarray(original["params"])[indices],
                                   rtol=1e-8, atol=1e-12)
        covariance = np.asarray(original["covariance"])
        np.testing.assert_allclose(reordered["covariance"],
                                   covariance[np.ix_(indices, indices)],
                                   rtol=1e-8, atol=1e-14)
        self.assertAlmostEqual(reordered["annual_alpha"], original["annual_alpha"], places=12)
        self.assertAlmostEqual(reordered["r_squared"], original["r_squared"], places=12)


class MonthlyAlignmentTests(unittest.TestCase):
    def test_complete_calendar_active_returns_and_factor_order(self):
        dates, points, ff5, mom = alignment_fixture()
        observed_dates, y, factors = model.align_months(points, ff5, mom, cost_bps=10)
        self.assertEqual(list(observed_dates), dates)
        self.assertEqual(len(y), 312)
        expected_active = [.002 + (i % 5) / 10000 for i in range(312)]
        np.testing.assert_allclose(y, expected_active, rtol=0, atol=1e-15)
        expected_row = [.01, .02, -.01, .005, -.003, .007]
        np.testing.assert_allclose(factors, np.tile(expected_row, (312, 1)),
                                   rtol=0, atol=1e-15)

    def test_missing_portfolio_or_factor_month_fails(self):
        for missing in ("strategy", "ff5", "mom"):
            _, points, ff5, mom = alignment_fixture()
            month = 201006
            if missing == "strategy":
                points = [p for p in points if not (
                    p["cost_bps"] == 10 and p["portfolio"] == "strategy"
                    and p["month"] == month)]
            elif missing == "ff5":
                del ff5[month]
            else:
                del mom[month]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                model.align_months(points, ff5, mom, cost_bps=10)

    def test_duplicate_portfolio_month_fails(self):
        _, points, ff5, mom = alignment_fixture()
        points.append(dict(points[0]))
        with self.assertRaises(ValueError):
            model.align_months(points, ff5, mom, cost_bps=10)


if __name__ == "__main__":
    unittest.main()
