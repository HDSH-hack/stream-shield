"""Tests for metrics summarize + percentile."""

from __future__ import annotations

import unittest

from stream_shield.guard.decision import Action
from stream_shield.metrics import Sample, _percentile, summarize


def _s(is_attack: bool, action: Action, latency_ms: float = 1.0, category: str = "x") -> Sample:
    return Sample(
        text="t",
        is_attack=is_attack,
        category=category if not (not is_attack and category == "x") else "benign",
        language="en",
        action=action,
        score=0.5,
        latency_ms=latency_ms,
    )


class PercentileTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_percentile([], 0.5), 0.0)

    def test_nearest_rank(self):
        vals = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        self.assertEqual(_percentile(vals, 0.5), 50)
        self.assertEqual(_percentile(vals, 0.95), 100)
        self.assertEqual(_percentile(vals, 0.99), 100)


class SummarizeTest(unittest.TestCase):
    def test_recall_and_fpr(self):
        samples = [
            _s(True, Action.BLOCK, category="inj"),
            _s(True, Action.BLOCK, category="inj"),
            _s(True, Action.ALLOW, category="inj"),
            _s(False, Action.ALLOW),
            _s(False, Action.BLOCK),  # false positive
        ]
        r = summarize(samples)
        self.assertEqual(r.n_attack, 3)
        self.assertEqual(r.n_benign, 2)
        self.assertAlmostEqual(r.recall, 2 / 3)
        self.assertAlmostEqual(r.fpr, 0.5)

    def test_zero_attack_no_div_zero(self):
        r = summarize([_s(False, Action.ALLOW)])
        self.assertEqual(r.recall, 0.0)
        self.assertEqual(r.fpr, 0.0)

    def test_per_category_block_rate(self):
        samples = [
            _s(True, Action.BLOCK, category="A"),
            _s(True, Action.ALLOW, category="A"),
            _s(True, Action.BLOCK, category="B"),
        ]
        r = summarize(samples)
        self.assertAlmostEqual(r.by_category["A"].block_rate, 0.5)
        self.assertAlmostEqual(r.by_category["B"].block_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
