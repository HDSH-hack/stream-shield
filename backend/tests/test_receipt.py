"""Tests for Ed25519 receipt log: round-trip + tamper detection."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from stream_shield.receipt import ReceiptLog, verify_log


class ReceiptTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _build(self, n: int = 3) -> tuple[ReceiptLog, bytes | None]:
        rl = ReceiptLog(self.dir / "r.log", signing_key_path=self.dir / "k.pem")
        for i in range(n):
            rl.append({"action": "BLOCK", "score": 0.9, "i": i})
        return rl, rl.public_key_pem()

    def test_round_trip(self):
        _, pem = self._build(3)
        ok, msg = verify_log(self.dir / "r.log", pem)
        self.assertTrue(ok, msg)
        self.assertIn("3", msg)

    def test_prev_hash_tamper_detected(self):
        _, pem = self._build(3)
        path = self.dir / "r.log"
        lines = path.read_text(encoding="utf-8").splitlines()
        # break the chain: replace the prev_hash field on line 2 with all-f
        lines[1] = lines[1].replace(
            '"prev_hash":"' + lines[1].split('"prev_hash":"')[1][:64] + '"',
            '"prev_hash":"' + "f" * 64 + '"',
        )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        ok, msg = verify_log(path, pem)
        self.assertFalse(ok)
        self.assertIn("prev_hash", msg)

    def test_seq_monotonic_after_restart(self):
        # First session: write 2.
        rl1 = ReceiptLog(self.dir / "r.log", signing_key_path=self.dir / "k.pem")
        rl1.append({"a": 1})
        rl1.append({"a": 2})
        # Second session: should pick up seq=3.
        rl2 = ReceiptLog(self.dir / "r.log", signing_key_path=self.dir / "k.pem")
        entry = rl2.append({"a": 3})
        self.assertEqual(entry.seq, 3)
        ok, msg = verify_log(self.dir / "r.log", rl2.public_key_pem())
        self.assertTrue(ok, msg)


if __name__ == "__main__":
    unittest.main()
