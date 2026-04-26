# Claude / Codex agent guide

This file is read by Claude Code, Codex, and similar coding agents. Keep it
short — it loads into every session.

## What this repo is

Hackathon project (9-hour build, 4 contributors). A WebSocket proxy in front
of Gemini Live API that catches prompt injection in the streaming text path
*before* it reaches the model. See [`UNIFIED_DESIGN.md`](./UNIFIED_DESIGN.md)
for full architecture and [`TODO.md`](./TODO.md) for role splits and phase
plan.

## Contributors and ownership

| Owner | Area |
|---|---|
| Eunjin (@foura1201) | `server.py`, `gemini.py`, `protocol.py`, `session.py`, `buffer/manager.py`, `guard/classifier.py` |
| Gihwang (@hangole1999) | `frontend/**`, `buffer/response_buffer.py` |
| Dohoon (@DoHoonKim8) | `guard/rules.py`, `guard/normalizer.py`, `guard/llm_judge.py`, `guard/engine.py`, `eval/` (with Soowon), attackset |
| Soowon (@swjng) | `policy.py`, `config/policy.*.yaml`, `metrics.py`, `receipt.py`, `eval/runner.py`, `eval/compare.py`, `docs/eval-analysis.md`, `docs/limitations.md` |

When editing files outside your owner's area, prefer raising it in PR
description or asking before refactoring shared interfaces.

## Conventions

- **Branches**: `<owner>/<short-slug>` (e.g. `soowon/per-entity-comparison`,
  `dohoon/l1-classifier`). Stack PRs on each other when work depends on
  unmerged work; note the base branch in the PR body.
- **PRs**: every change goes through a PR. Don't push to `main` directly.
  Title in English. Body has Summary / Notes / Test plan sections.
- **Commits**: present-tense imperative. Group related changes; don't squash
  unrelated ones together. Don't add AI attribution lines.
- **Tests**: backend uses stdlib `unittest` (no pytest dependency). Add tests
  next to the module you change in `backend/tests/test_<module>.py`. CI runs
  `python -m unittest discover -s tests` on Python 3.11 + 3.12.
- **No secrets**: `.secrets/` and `*.key` are gitignored. Don't commit
  Gemini API keys, signing keys, or `.env` files.

## Commands

```bash
# from backend/
python -m unittest discover -s tests -v       # all tests
python -m stream_shield.eval.runner --policy default
python -m stream_shield.eval.compare --diff-only
uvicorn stream_shield.server:app --reload     # dev server
```

## Things to avoid

- **Don't replace lists in `policy.py` extends merge** — semantics is
  *union with order-preserving dedupe*. Child policies extend parent rules,
  not replace them. The merge tests will fail loudly.
- **Don't fold `eval/runner.py`'s stub classifier into the real cascade**.
  It exists as a fallback so eval and CI run before L1 lands. Inject the
  real classifier via `runner.run(classify=...)`.
- **Don't add deps that aren't strictly needed**. Backend `requirements.txt`
  is shared by all four contributors and CI installs only the lightweight
  subset (pyyaml + cryptography) for tests.
- **Don't commit large model weights or fixture audio**. Use `.gitignore`
  patterns under `backend/models/` and `backend/fixtures/audio/`.
- **Don't break the L0 → L1 → L2 cascade contract** without raising it. Each
  layer returns a `Verdict(score, label, layer, reason)`. Higher layers
  should only run on borderline scores from lower layers.

## When you're stuck

Read [`UNIFIED_DESIGN.md`](./UNIFIED_DESIGN.md) §2 (architecture) and
[`docs/limitations.md`](./docs/limitations.md) (what's *not* in scope) before
escalating scope. The hackathon constraint is real: 9 hours, demo-driven.
Prefer "ship the smallest working slice" over "design for v2."
