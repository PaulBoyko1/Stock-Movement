"""Compare the baseline's mean uncertainty to an independent HAC implementation."""
from pathlib import Path
import sys
import unittest

import numpy as np
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import industry_baseline as model


def serially_correlated_fixture(count):
    rng = np.random.default_rng(65537)
    shocks = rng.normal(0, .018, count)
    values = np.zeros(count)
    for i in range(count):
        previous = values[i - 1] - .001 if i else 0
        values[i] = .001 + .65 * previous + shocks[i]
    return values


class MeanUncertaintyReferenceTests(unittest.TestCase):
    def test_nonconstant_serially_correlated_series_matches_statsmodels(self):
        # Unlike a constant series, this exercises every lagged covariance term.
        for count, requested_lag in ((72, 0), (120, 4), (312, 12), (8, 12)):
            with self.subTest(count=count, requested_lag=requested_lag):
                values = serially_correlated_fixture(count)
                observed = model.nw_mean_interval(values.tolist(), lag=requested_lag)
                effective_lag = min(requested_lag, count - 1)
                reference = sm.OLS(values, np.ones((count, 1))).fit(
                    cov_type="HAC",
                    cov_kwds={"maxlags": effective_lag, "use_correction": False},
                    use_t=False,
                )
                expected_mean = reference.params[0]
                expected_se = np.sqrt(reference.cov_params()[0, 0])
                self.assertEqual(observed["lag"], effective_lag)
                self.assertAlmostEqual(observed["monthly_mean"], expected_mean, places=13)
                self.assertAlmostEqual(observed["monthly_se"], expected_se, places=13)
                self.assertAlmostEqual(observed["annual_arithmetic_mean"],
                                       12 * expected_mean, places=13)
                expected_interval = 12 * np.array([
                    expected_mean - 1.96 * expected_se,
                    expected_mean + 1.96 * expected_se,
                ])
                np.testing.assert_allclose(observed["annual_arithmetic_95pct_interval"],
                                           expected_interval, rtol=1e-10, atol=1e-13)


if __name__ == "__main__":
    unittest.main()
