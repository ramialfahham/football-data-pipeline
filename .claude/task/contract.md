# Task contract — Handover refresh (2026-06-21 close-out)

objective: >
  Refresh .claude/active_work.md to hand the next session the true state after this
  session's deep-backfill DQ heal + Phase 2a depths landed: #527 (events recovery +
  self-heal, standings test relocation, player id-collision drop) and #524 (Phase 2a
  registry §8 depths) are BOTH MERGED; main is green and the nightly is unblocked.
  Record the locked process lesson (coverage-cut is never a DQ fix; count offending
  rows in RAW first — #518 updated) and set the FIRST next action: RESUME the stopped
  Phase 2a deep ingest for the leagues not yet at their §8 depth.

refs: >
  This conversation 2026-06-21 (CPO: "524 merged. Let's close for today.").
  PRs #527, #524, #520, #523 (all merged). Issue #518 (behaviour retrospective) updated.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation-only handover refresh. No code, no product decision. An active_work.md +
  .claude/task/** commit is review-exempt per the commit gate (artifact-only), but
  active_work.md still needs scope_paths to pass the task_contract_gate. No reviewers
  required by routing for these paths beyond the artifact exemption.

done_when:
  - active_work.md reflects: #527 + #524 merged (main green, nightly unblocked); PD/SA/L1
    at 2016-2025 parity (#523); Phase 2a registry depths set (#524) but the deep INGEST
    stopped partway → RESUME as FIRST next action; #518 lesson logged.
  - Tree matches the contract (only active_work.md + .claude/task/**).
