# Agent instructions

This file is the standard config picked up by Codex and other agents that
follow the AGENTS.md convention. The full briefing is in
[`CLAUDE.md`](./CLAUDE.md) — this file points there and adds
Codex-specific notes.

## Read first

1. [`CLAUDE.md`](./CLAUDE.md) — repo conventions, ownership, what to avoid
2. [`UNIFIED_DESIGN.md`](./UNIFIED_DESIGN.md) — architecture
3. [`TODO.md`](./TODO.md) — phase plan + role split
4. [`docs/limitations.md`](./docs/limitations.md) — explicit non-goals

## Tests

Backend uses stdlib `unittest`. Run from `backend/`:

```bash
python -m unittest discover -s tests -v
```

CI (`.github/workflows/ci.yml`) runs the same command on Python 3.11 + 3.12,
plus smoke-tests `eval/runner.py` and `eval/compare.py`.

## Style

- English for PR titles, commit messages, and code comments
- No AI attribution in commits or PRs
- Prefer editing existing files over creating new ones
- Keep diffs scoped — one concern per PR

## When in doubt

If a change touches files owned by another contributor (see CLAUDE.md
ownership table), call it out in the PR body so the owner can flag
interface concerns.
