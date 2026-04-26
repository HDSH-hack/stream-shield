"""Ed25519-signed receipt sidecar — UNIFIED_DESIGN §7 (stretch).

Append-only hash chain over Decision events. Each entry stores:
    seq, ts, prev_hash, decision_digest, sig

Verifier replays the chain by recomputing prev_hash and checking each sig.

Standalone — only runs when policy.receipt_enabled is True. The signing key is
loaded lazily; if `cryptography` is not installed the receipt log records
unsigned digests (still hash-chained) and emits a warning once.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

try:  # optional dep — receipts are stretch
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )

    _HAVE_CRYPTO = True
except Exception:  # pragma: no cover
    _HAVE_CRYPTO = False


@dataclass
class ReceiptEntry:
    seq: int
    ts: float
    prev_hash: str
    decision_digest: str
    sig: str            # hex; "" when unsigned

    def as_json_line(self) -> str:
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True)


def _digest(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


class ReceiptLog:
    """In-process append-only receipt log with optional Ed25519 signing.

    Real deployment splits this into a sidecar process holding the key (§7);
    the in-process variant is enough for hackathon demo + verifier.
    """

    def __init__(self, log_path: Path, signing_key_path: Path | None = None):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0
        self._prev_hash = "0" * 64
        self._sk: Ed25519PrivateKey | None = None
        if signing_key_path and _HAVE_CRYPTO:
            self._sk = self._load_or_create_key(Path(signing_key_path))
        elif signing_key_path and not _HAVE_CRYPTO:
            log.warning("cryptography not installed — receipts will be unsigned")
        # Replay existing log to recover seq + prev_hash on restart.
        if self.log_path.exists():
            for line in self.log_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                self._seq = max(self._seq, int(entry["seq"]))
                self._prev_hash = self._hash_entry(entry)

    @staticmethod
    def _load_or_create_key(path: Path) -> "Ed25519PrivateKey":
        if path.exists():
            data = path.read_bytes()
            return serialization.load_pem_private_key(data, password=None)  # type: ignore[return-value]
        path.parent.mkdir(parents=True, exist_ok=True)
        sk = Ed25519PrivateKey.generate()
        pem = sk.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        path.write_bytes(pem)
        path.chmod(0o600)
        return sk

    @staticmethod
    def _hash_entry(entry: dict[str, Any]) -> str:
        # Hash everything except sig — sig binds the hash, not vice versa.
        payload = {k: v for k, v in entry.items() if k != "sig"}
        return _digest(payload)

    def append(self, decision_payload: dict[str, Any]) -> ReceiptEntry:
        self._seq += 1
        entry_dict = {
            "seq": self._seq,
            "ts": time.time(),
            "prev_hash": self._prev_hash,
            "decision_digest": _digest(decision_payload),
        }
        h = self._hash_entry(entry_dict)
        sig_hex = ""
        if self._sk is not None:
            sig_hex = self._sk.sign(bytes.fromhex(h)).hex()
        entry = ReceiptEntry(sig=sig_hex, **entry_dict)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(entry.as_json_line() + "\n")
        self._prev_hash = h
        return entry

    def public_key_pem(self) -> bytes | None:
        if not self._sk:
            return None
        return self._sk.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )


def verify_log(log_path: Path, public_key_pem: bytes | None = None) -> tuple[bool, str]:
    """Replay the chain. Returns (ok, message)."""
    pk: Ed25519PublicKey | None = None
    if public_key_pem and _HAVE_CRYPTO:
        pk = serialization.load_pem_public_key(public_key_pem)  # type: ignore[assignment]

    prev = "0" * 64
    expected_seq = 0
    for lineno, line in enumerate(Path(log_path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        entry = json.loads(line)
        expected_seq += 1
        if entry["seq"] != expected_seq:
            return False, f"line {lineno}: seq mismatch (got {entry['seq']}, expected {expected_seq})"
        if entry["prev_hash"] != prev:
            return False, f"line {lineno}: prev_hash break"
        h = ReceiptLog._hash_entry(entry)
        if pk is not None and entry.get("sig"):
            try:
                pk.verify(bytes.fromhex(entry["sig"]), bytes.fromhex(h))
            except Exception as e:
                return False, f"line {lineno}: bad signature ({e})"
        prev = h
    return True, f"verified {expected_seq} entries"


def _cli(argv: list[str] | None = None) -> int:
    """`python -m stream_shield.receipt <verify|inspect> ...`"""
    import argparse

    ap = argparse.ArgumentParser(prog="stream_shield.receipt")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify", help="replay + verify a receipt log")
    v.add_argument("log", type=Path)
    v.add_argument("--pubkey", type=Path, default=None,
                   help="PEM public key path; omit to skip signature check")

    i = sub.add_parser("inspect", help="dump entries one per line")
    i.add_argument("log", type=Path)

    args = ap.parse_args(argv)

    if args.cmd == "verify":
        pem = args.pubkey.read_bytes() if args.pubkey and args.pubkey.exists() else None
        ok, msg = verify_log(args.log, pem)
        print(("OK   " if ok else "FAIL ") + msg)
        return 0 if ok else 1

    if args.cmd == "inspect":
        for line in args.log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entry = json.loads(line)
                print(f"#{entry['seq']:>4}  ts={entry['ts']:.3f}  "
                      f"digest={entry['decision_digest'][:12]}...  "
                      f"sig={'yes' if entry.get('sig') else 'no '}")
        return 0

    return 2


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
