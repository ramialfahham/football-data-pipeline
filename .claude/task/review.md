# Review — chore/reconcile-content-arch-post-648 — 2026-07-07

> G3 Lock artifact. Doc-only status reconciliation (the #615/#620/#636 pattern): flip stale ✓/⚠/✗ markers in
> `docs/content_architecture.md` §3 (block↔mart board) + §7 (new-mart status) to match shipped reality — the
> legend predated #638/#645/#648. Flips: player Season (#630), player Season-over-season (#638+#648),
> Contribution-share (#645) → ✓; Opponent/schedule-context → ✗ SHELVED 2026-07-03; player Streaks → SKIPPED;
> Career backfill note → effectively done. Team benchmark stays ⚠ orphan; "17 marts" unchanged.
> Required set (routing): scope-auditor only.
>
> **REBIND (sibling-PR, #661 merged first):** rebased onto main@#661. The reviewed content is BYTE-IDENTICAL —
> the `docs/content_architecture.md` diff patch-id (`1569bd82…`) is unchanged from the pre-rebase reviewed commit
> (5f5229c), and contract.md content is this task's version verbatim. Only contract.md's diff BASE shifted
> (#655→#661), moving diff_sha256 40e03450 → 789f1f93. The scope-auditor PASS below verified the identical bytes;
> no content changed, so the verdict stands and only the hash is rebound ([[feedback-sibling-pr-rebase-rebind]]).

diff_sha256: 789f1f93f6603976ff6c9ec35cb135daeb8c56cbc2fc80fa367efffa95435b64

## scope-auditor
VERDICT: PASS
risks_checked:
- **Wiring verification (Season / Season-over-season / Contribution-share).** Confirmed all three intermediate
  models (`int_player_profile__yoy`, `int_player_profile__contribution`, `int_player_season__metrics`) are
  genuinely `ref()`-ed in `mart_player_profile`, and `mart_player_profile` is consumed end-to-end by the v2 export
  via `fetch_player_payloads` with `select *` — so "wired to the export" is honest (not merely existing in an
  internal layer); no silent filtering masks them. The ✓ flips do not overclaim.
- **Shelving-claim boundary (opponent/schedule context).** Verified the "✗ SHELVED 2026-07-03" flip rests on an
  explicit CPO ruling already recorded in active_work.md ("Phase D flagship opponent/schedule context is SHELVED
  … no display home"), not a retrospectively invented judgment; elevating "not built" → "SHELVED" (a decision NOT
  to build) is significant and correctly grounded in existing CPO authority. Also spot-checked: team benchmark
  stays ⚠ orphan (not falsely flipped), "17 marts" unchanged (new intermediates enrich mart_player_profile, add
  no new wired mart), scope = content_architecture.md + .claude/task/** only, §10 record-only.

## escalations
- None open. No ESCALATE. Record-only: every flip is bound to a merged PR (#630/#638/#645/#648) or an existing CPO
  ruling (opponent-context SHELVED / player streaks SKIPPED / backfill-effectively-done); no new status invented.
