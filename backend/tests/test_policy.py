"""Tests for policy loader + extends merge semantics."""

from __future__ import annotations

import unittest

from stream_shield.policy import _merge, load_policy


class MergeTest(unittest.TestCase):
    def test_dict_recursive(self):
        parent = {"a": 1, "b": {"x": 1, "y": 2}}
        child = {"b": {"y": 99, "z": 3}, "c": 4}
        out = _merge(parent, child)
        self.assertEqual(out, {"a": 1, "b": {"x": 1, "y": 99, "z": 3}, "c": 4})

    def test_list_union_dedup_order_preserving(self):
        parent = {"phrases": ["a", "b", "c"]}
        child = {"phrases": ["b", "d"]}
        self.assertEqual(_merge(parent, child)["phrases"], ["a", "b", "c", "d"])

    def test_scalar_override(self):
        self.assertEqual(_merge({"k": 1}, {"k": 2}), {"k": 2})

    def test_child_only_keys_pass_through(self):
        self.assertEqual(_merge({}, {"k": [1]}), {"k": [1]})


class LoadPolicyTest(unittest.TestCase):
    def test_default_loads(self):
        p = load_policy("default")
        self.assertEqual(p.policy_id, "default")
        self.assertGreater(len(p.block_phrases), 0)

    def test_hospital_inherits_default_phrases(self):
        default = load_policy("default")
        hospital = load_policy("hospital")
        # Union semantics: hospital should contain every default phrase.
        for phrase in default.block_phrases:
            self.assertIn(phrase, hospital.block_phrases, f"missing inherited phrase: {phrase}")

    def test_hospital_thresholds_tighter(self):
        d = load_policy("default")
        h = load_policy("hospital")
        self.assertLess(h.thresholds.safe, d.thresholds.safe + 1e-9)
        self.assertLess(h.thresholds.block, d.thresholds.block)

    def test_fintech_enables_receipt(self):
        self.assertTrue(load_policy("fintech").receipt_enabled)
        self.assertFalse(load_policy("default").receipt_enabled)

    def test_unknown_policy_falls_back(self):
        p = load_policy("does-not-exist")
        # falls back to default file but keeps requested id only if config sets it; else default
        self.assertEqual(p.policy_id, "default")


if __name__ == "__main__":
    unittest.main()
