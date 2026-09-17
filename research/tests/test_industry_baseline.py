import copy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
import industry_baseline as model


def rows(count=14):
    result = []
    for i in range(count):
        absolute = 1999 * 12 + i
        year, month0 = divmod(absolute, 12)
        result.append((year * 100 + month0 + 1, [0.0] * 12))
    return result


def source(records):
    lines = ["Test fixture", "Average Value Weighted Returns -- Monthly",
             "," + ",".join(model.INDUSTRIES)]
    lines.extend(str(date) + "," + ",".join(str(100 * v) for v in values)
                 for date, values in records)
    lines += ["", "Average Equal Weighted Returns -- Monthly", "," + ",".join(model.INDUSTRIES),
              "199901," + ",".join(["999"] * 12)]
    return "\n".join(lines)


class ParserTests(unittest.TestCase):
    def test_converts_percent_and_stops_before_equal_weighted_section(self):
        data = rows(2)
        data[0][1][0] = .025
        names, parsed = model.parse_monthly(source(data))
        self.assertEqual(names, model.INDUSTRIES)
        self.assertEqual(len(parsed), 2)
        self.assertAlmostEqual(parsed[0][1][0], .025)

    def test_duplicate_missing_and_out_of_order_months_fail(self):
        for malformed in ([rows(3)[0], rows(3)[0]], [rows(3)[0], rows(3)[2]],
                          [rows(3)[1], rows(3)[0]]):
            with self.subTest(malformed=malformed):
                with self.assertRaises(ValueError):
                    model.parse_monthly(source(malformed))

    def test_missing_codes_and_nonfinite_fail(self):
        for value in (-99.99, -999, float("nan"), float("inf")):
            fixture = source(rows(1)).replace("199901,0.0,", "199901," + str(value) + ",", 1)
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    model.parse_monthly(fixture)

    def test_schema_changes_fail(self):
        with self.assertRaises(ValueError):
            model.parse_monthly(source(rows(2)).replace("NoDur", "Unexpected"))

    def test_invalid_calendar_month_fails(self):
        with self.assertRaises(ValueError):
            model.parse_monthly(source([(199913, [0.0] * 12)]))


class TimingTests(unittest.TestCase):
    def test_eleven_month_signal_excludes_recent_and_holding_month(self):
        data = rows()
        for i in range(11):
            data[i][1][0:3] = [.01, .02, .03]
        data[11][1][3] = .90
        data[12][1][4] = .90
        scores = model.momentum_scores(data, 12)
        self.assertAlmostEqual(scores[0], 1.01 ** 11 - 1)
        self.assertEqual(scores[3], 0)
        self.assertEqual(scores[4], 0)
        result = model.simulate(data, 0, start=200001, end=200001)[0]
        self.assertEqual(result["selected"], ["Manuf", "Durbl", "NoDur"])
        self.assertEqual(result["signal_start"], 199901)
        self.assertEqual(result["signal_end"], 199911)
        self.assertEqual(result["skipped_month"], 199912)

    def test_future_change_cannot_change_past_holdings_or_returns(self):
        data = rows(15)
        original = model.simulate(data, 10, start=200001, end=200002)
        future = copy.deepcopy(data)
        future[14][1][8] = 9.0
        self.assertEqual(original, model.simulate(future, 10, start=200001, end=200002))

    def test_fixed_tie_break_and_weights(self):
        result = model.simulate(rows(), 0, start=200001, end=200001)[0]
        self.assertEqual(result["selected"], list(model.INDUSTRIES[:3]))
        self.assertAlmostEqual(sum(result["weights"]), 1.0)
        self.assertTrue(all(w >= 0 for w in result["weights"]))

    def test_insufficient_history_or_missing_endpoint_fails(self):
        with self.assertRaises(ValueError):
            model.simulate(rows(), 10, start=199912, end=200001)
        with self.assertRaises(ValueError):
            model.simulate(rows(), 10, start=200001, end=200003)


class AccountingTests(unittest.TestCase):
    def test_entry_and_terminal_costs_on_flat_one_month_portfolio(self):
        point = model.simulate(rows(), 10, start=200001, end=200001)[0]
        self.assertAlmostEqual(point["rebalance_notional"], 1.0)
        self.assertEqual(point["terminal_liquidation_notional"], 1.0)
        self.assertAlmostEqual(point["net_return"], .999 ** 2 - 1)

    def test_drift_turnover_when_target_does_not_change(self):
        data = rows()
        data[12][1][0] = .12
        result = model.simulate(data, 10, top_k=12, start=200001, end=200002)
        expected = 2 * ((1.12 / 12) / 1.01 - 1 / 12)
        self.assertAlmostEqual(result[1]["rebalance_notional"], expected)
        self.assertAlmostEqual(result[0]["net_return"], .999 * 1.01 - 1)
        self.assertAlmostEqual(result[1]["net_return"], (1 - .001*expected)*.999 - 1)

    def test_full_replacement_trades_twice_portfolio_value(self):
        data = rows()
        for i in range(11):
            data[i][1][0:3] = [.01, .01, .01]
        data[11][1][3:6] = [.50, .50, .50]
        result = model.simulate(data, 10, start=200001, end=200002)
        self.assertEqual(result[0]["selected"], list(model.INDUSTRIES[:3]))
        self.assertEqual(result[1]["selected"], list(model.INDUSTRIES[3:6]))
        self.assertAlmostEqual(result[1]["rebalance_notional"], 2.0)
        self.assertAlmostEqual(result[1]["net_return"], .998 * .999 - 1)

    def test_higher_cost_cannot_improve_fixed_strategy(self):
        data = rows(24)
        for i, (_, values) in enumerate(data):
            values[i % 12] = .05
        wealth = []
        for cost in (0, 10, 25):
            points = model.simulate(data, cost, start=200001, end=200012)
            wealth.append(math.prod(1 + p["net_return"] for p in points))
        self.assertGreaterEqual(wealth[0], wealth[1])
        self.assertGreaterEqual(wealth[1], wealth[2])

    def test_drawdown_includes_initial_capital(self):
        self.assertAlmostEqual(model.max_drawdown([-.10, .05]), -.10)
        self.assertAlmostEqual(model.max_drawdown([.10, -.20]), -.20)

    def test_constant_active_series_has_zero_uncertainty(self):
        result = model.nw_mean_interval([.01] * 48)
        self.assertAlmostEqual(result["annual_arithmetic_mean"], .12)
        self.assertAlmostEqual(result["monthly_se"], 0, places=12)


if __name__ == "__main__":
    unittest.main()
