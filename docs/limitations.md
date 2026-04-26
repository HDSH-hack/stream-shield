# Limitations & non-goals

We made deliberate scope cuts. This document is the contract for what Stream
Shield is *not* trying to do — useful for reviewers, future contributors, and
the limitations slide.

## Scope: cascaded text path only

Gemini Live can run in two modes:

1. **Cascaded** (STT → text → LLM → TTS) — the path Stream Shield protects.
   Audio enters Gemini, is transcribed, and the prompt the model sees is text.
   That text is what we intercept via `inputTranscription` side-channel and
   classify before it reaches the model.
2. **Native audio** (audio → audio model directly, no transcription). The model
   processes raw audio features. Our text classifier has nothing to read.

Stream Shield is **cascaded-only**. Native-audio attacks (acoustic
adversarials, ultrasonic injection, voice spoofing) are explicitly out of
scope. If a deployment uses native-audio Gemini, this proxy is the wrong tool.

## Non-goals (won't be in v1)

- **Audio-channel attacks**: ultrasonic / inaudible commands, room acoustics,
  device-level attacks. These need a different defense layer (signal
  processing, not text classification).
- **Output-side moderation**: we focus on input-side PI. Gemini's response is
  forwarded as-is. Detecting model-side leakage of the system prompt or PII
  in the *output* is a future stretch (`output_guard.py`, Dohoon ⭐ priority).
- **Generic content moderation**: Stream Shield does not replace Gemini's
  4-category safety filter (hate, harassment, sexually explicit, dangerous
  content). It complements it by adding the *prompt-injection* category that
  Gemini doesn't ship.
- **Tool-use / function-calling defense**: agent-level threats (tool
  parameter injection, indirect injection via retrieved docs) are a different
  problem space. Adjacent — not this project.
- **Adversarial robustness against white-box attacks**: a determined attacker
  with access to the classifier weights can craft GCG / AutoDAN suffixes that
  evade L1. Our defense-in-depth is policy diversity (per-entity O(N)
  attacker cost), not weight-level robustness.
- **Confidentiality of the proxy itself**: an attacker on the same machine
  with read access to the policy YAML knows exactly what we block.
  Per-entity policies should not be considered secrets — they're a friction
  layer, not a cryptographic one.

## Known weaknesses of the current MVP

- **L0-only stub classifier in eval**: the runner currently uses regex only;
  recall numbers will jump when `guard/classifier.py` (Prompt Guard 2) lands.
  See [`eval-analysis.md`](./eval-analysis.md).
- **`block_external_dest` not enforced by the stub**: the YAML rule exists and
  is loaded, but the L0-only stub classifier only checks `block_phrases` and
  `role_spoof_regex`. Dohoon's full L0 (`guard/rules.py`) will close this.
- **Receipt log is in-process**: per UNIFIED_DESIGN §7 the production design
  is a sidecar with the signing key, but for the hackathon the chain runs in
  the proxy itself. Verifier is already standalone and works either way.
- **Korean coverage is thin**: attackset has more English than Korean
  samples; multilingual_codeswitch only catches ko-en mixed strings, not
  Japanese or French. Expanding the dataset is high-leverage and cheap.
- **No multi-turn drip detection in MVP**: a sliding context window across
  turns is a Phase 4 stretch; today each utterance is judged in isolation
  (with same-utterance overlap for split_stream).

## What protects against scope creep

The four-contributor split in [`TODO.md`](../TODO.md) puts each non-goal under
a named owner ("Stretch" column). If something slides from non-goal to MVP,
it should be a deliberate trade — not drift.
