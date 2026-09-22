"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const { run, validateData } = require("./backtest-engine.js");

const SERIES = [
  { id: "A", label: "Alpha" },
  { id: "B", label: "Beta" },
  { id: "C", label: "Gamma" },
];

function monthAt(year, month, offset) {
  const absolute = year * 12 + (month - 1) + offset;
  const y = Math.floor(absolute / 12);
  const m = absolute % 12 + 1;
  return `${y}-${String(m).padStart(2, "0")}`;
}

function dataWith(rows, series = SERIES) {
  return {
    series: series.map((item) => ({ ...item })),
    rows: rows.map((row) => ({ month: row.month, returns: [...row.returns] })),
    meta: { source: "test fixture" },
  };
}

function flatData(count = 36) {
  return dataWith(Array.from({ length: count }, (_, i) => ({
    month: monthAt(2020, 1, i),
    returns: [0, 0, 0],
  })));
}

function params(overrides = {}) {
  return {
    start: "2021-01",
    end: "2021-12",
    lookback: 11,
    skip: 1,
    topK: 1,
    costBps: 0,
    initialCapital: 10000,
    rebalanceEvery: 1,
    ...overrides,
  };
}

function closeTo(actual, expected, tolerance = 1e-10) {
  assert.ok(Math.abs(actual - expected) <= tolerance,
    `expected ${actual} to be within ${tolerance} of ${expected}`);
}

function sampleStd(values) {
  const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
  return Math.sqrt(values.reduce((sum, value) => sum + (value - mean) ** 2, 0)
    / (values.length - 1));
}

test("formation uses only lookback observations before skipped and holding months", () => {
  const rows = Array.from({ length: 36 }, (_, i) => ({
    month: monthAt(2020, 1, i),
    returns: [0, 0, 0],
  }));
  for (let i = 0; i < 11; i += 1) rows[i].returns[0] = 0.05;
  // This return must be skipped. Including it would make B the leader.
  rows[11].returns[1] = 5;
  // This return belongs to the holding month. Including it would also make B the leader.
  rows[12].returns = [-0.1, 5, 0];

  const result = run(dataWith(rows), params());
  assert.deepEqual(result.points[0].selected, ["A"]);
  closeTo(result.points[0].strategyReturn, -0.1);
  closeTo(result.points[0].strategyWealth, 9000);
});

test("formation ties preserve original series order", () => {
  const result = run(flatData(), params({ topK: 2 }));
  assert.deepEqual(result.points[0].selected, ["A", "B"]);
});

test("entry and final liquidation costs are charged and turnover is annualized", () => {
  const result = run(flatData(), params({ topK: 2, costBps: 10 }));
  const c = 10 / 10000;

  closeTo(result.metrics.strategy.finalWealth, 10000 * (1 - c) ** 2);
  closeTo(result.points[0].turnover, 1);
  closeTo(result.points.at(-1).turnover, 1);
  closeTo(result.metrics.strategy.turnover, 2);
  closeTo(result.metrics.strategy.finalWealth, result.metrics.benchmark.finalWealth);
});

test("quarterly rebalancing carries drift between rebalance dates", () => {
  const rows = Array.from({ length: 36 }, (_, i) => ({
    month: monthAt(2020, 1, i),
    returns: [0, 0, 0],
  }));
  rows[12].returns[0] = 0.12;
  const result = run(dataWith(rows), params({ topK: 3, rebalanceEvery: 3 }));

  const driftedA = (1 / 3 * 1.12) / 1.04;
  const expectedTurnoverAtThirdMonth = 2 * (driftedA - 1 / 3);
  closeTo(result.points[0].turnover, 1);
  closeTo(result.points[1].turnover, 0);
  closeTo(result.points[2].turnover, 0);
  closeTo(result.points[1].weights[0], driftedA);
  closeTo(result.points[3].turnover, expectedTurnoverAtThirdMonth);
  closeTo(result.points[1].strategyReturn, 0);
});

test("higher proportional costs cannot improve the same strategy", () => {
  const fixture = flatData();
  const free = run(fixture, params({ topK: 2, costBps: 0 }));
  const ten = run(fixture, params({ topK: 2, costBps: 10 }));
  const expensive = run(fixture, params({ topK: 2, costBps: 25 }));
  assert.ok(free.metrics.strategy.finalWealth >= ten.metrics.strategy.finalWealth);
  assert.ok(ten.metrics.strategy.finalWealth >= expensive.metrics.strategy.finalWealth);
  assert.ok(free.metrics.strategy.finalWealth > expensive.metrics.strategy.finalWealth);
});

test("topK equal to the universe produces the equally weighted benchmark", () => {
  const rows = Array.from({ length: 36 }, (_, i) => ({
    month: monthAt(2020, 1, i),
    returns: [0.01 * ((i % 3) - 1), 0.005, -0.002],
  }));
  const result = run(dataWith(rows), params({ topK: SERIES.length, costBps: 10, rebalanceEvery: 3 }));

  for (const point of result.points) {
    assert.deepEqual([...point.selected].sort(), ["A", "B", "C"]);
    closeTo(point.strategyWealth, point.benchmarkWealth);
    closeTo(point.strategyReturn, point.benchmarkReturn);
    closeTo(point.strategyDrawdown, point.benchmarkDrawdown);
  }
  assert.deepEqual(result.metrics.strategy, result.metrics.benchmark);
});

test("metrics use initial capital for wealth, monthly sample volatility, and drawdown", () => {
  const rows = Array.from({ length: 36 }, (_, i) => ({
    month: monthAt(2020, 1, i),
    returns: [0, 0, 0],
  }));
  rows[12].returns = [0.1, 0.1, 0.1];
  rows[13].returns = [-0.2, -0.2, -0.2];
  const result = run(dataWith(rows), params({ topK: 3 }));
  const returns = [0.1, -0.2, ...Array(10).fill(0)];

  closeTo(result.metrics.strategy.finalWealth, 10000 * 1.1 * 0.8);
  closeTo(result.metrics.strategy.maxDrawdown, -0.2);
  closeTo(result.metrics.strategy.volatility, sampleStd(returns) * Math.sqrt(12));
  closeTo(result.points[1].strategyDrawdown, -0.2);
});

test("run and validateData do not mutate caller-owned input", () => {
  const data = flatData();
  const before = structuredClone(data);
  validateData(data);
  run(data, params({ topK: 2, costBps: 10 }));
  assert.deepEqual(data, before);
});

test("calendar and row validation reject malformed data", () => {
  const duplicate = flatData();
  duplicate.rows[1].month = duplicate.rows[0].month;
  assert.throws(() => validateData(duplicate));

  const gap = flatData();
  gap.rows[1].month = "2020-03";
  assert.throws(() => validateData(gap));

  const invalidMonth = flatData();
  invalidMonth.rows[1].month = "2020-13";
  assert.throws(() => validateData(invalidMonth));

  const unequal = flatData();
  unequal.rows[1].returns.pop();
  assert.throws(() => validateData(unequal));

  for (const value of [NaN, Infinity, -1]) {
    const invalidReturn = flatData();
    invalidReturn.rows[1].returns[0] = value;
    assert.throws(() => validateData(invalidReturn));
  }
});

test("parameter validation rejects unsupported values and insufficient warmup/evaluation", () => {
  const data = flatData();
  const invalid = [
    { lookback: 0 }, { lookback: 61 }, { lookback: 1.5 },
    { skip: -1 }, { skip: 13 }, { skip: 0.5 },
    { topK: 0 }, { topK: 4 }, { topK: 1.5 },
    { costBps: -1 }, { costBps: 101 },
    { initialCapital: 0 }, { initialCapital: -1 },
    { rebalanceEvery: 2 }, { rebalanceEvery: 1.5 },
  ];
  for (const override of invalid) assert.throws(() => run(data, params(override)));

  assert.throws(() => run(data, params({ start: "2020-01" })));
  assert.throws(() => run(data, params({ start: "2021-01", end: "2021-11" })));
});
