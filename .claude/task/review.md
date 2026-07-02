# Review — feat/391-gap22-career-wiring — 2026-07-02

> G3 Lock artifact. GAP-22: wire `mart_player_career` (per-club career log, #630) into the v2 player export
> as a TOP-LEVEL `career[]` block + `national_appearances_total`, so the Career screen (13, #632) has a
> payload. Consumption-layer: select/reshape only. The fix grew a small mart-column add (an ordering signal)
> — see the cycle + escalations. Required set (routing): scope-auditor (always) + analytics-engineer-reviewer
> (`scripts/export_*.py` + `dbt_project/**`) + cto-reviewer (`scripts/export_*.py` + `tests/**`).
>
> Cycle history (re-run ALL required reviewers on every hash change):
> - R1 (47e5ffb3→…): AE + cto FAIL — the career sort led on `team_sk` (opaque surrogate), not recency;
>   impact_map format + stale review_input.patch. Fixed: season-desc sort, labeled impact_map, patch regen.
> - R2: scope-auditor FAIL (doc-sync: wireframe 13 + gaps register go stale post-merge). **CPO ANSWER:
>   reconcile SEPARATELY** (matches #627/#619 wiring-PR precedent + the content_architecture ruling) — this PR
>   stays code-only; the wireframe/register flips fold into the reconciliation task (task_4c709bd9). AE + cto
>   FAIL: season-desc alone can't order a mid-season transfer / return spell (no temporal disambiguator).
> - R3: **CPO ANSWER: fix properly — add the mart column.** Added `last_kickoff_at` to the mart + a
>   club-contiguous sort. AE FAIL: the per-club recency MAX was computed in the EXPORT (client-side
>   aggregation = banned "ordering that encodes a business rule").
> - R4 (hash b3cc297d, THIS lock): moved the club-recency into the mart as a window column
>   `club_latest_kickoff_at`; the export is now a PURE sort over two mart columns (zero aggregation) +
>   multi-national test coverage. **scope-auditor + analytics-engineer-reviewer + cto-reviewer all PASS.**

diff_sha256: b3cc297d3845c6a64e15278cfb8a5225481f206bc12aaa673b3281625906ed39

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + §10: all changed files (`scripts/export_site_data.py`, `tests/test_export_site_data.py`,
  `mart_player_career.sql`, `shared.yml`, `.claude/task/**`) are in scope_paths; the mart-column widening is
  recorded in amendments 3+4 with CPO authority. `last_kickoff_at` + `club_latest_kickoff_at` are ordering
  SIGNALS (window max of an existing recency column), not new metrics/labels/mechanisms — dropped from the
  shipped career member, no catalogue change, mart grain (player_sk, team_sk, season_sk) unchanged.
- Structural mart dependency: the ordering signal is precomputed + materialized in the mart (the
  mart_leaderboards.rank pattern) and consumed by select+sort — correct consumption-layer design; the doc-sync
  (wireframe/register) stays CPO-ruled out of scope (amendment 2).

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Client-side aggregation eliminated: no max/group/dict-build over career_rows remains in the export — only a
  `sorted(...)` + filter + a constant `[0].get(...)`; the MAX genuinely moved into `mart_player_career`'s
  with_caps CTE as `max(last_kickoff_at) over (partition by player_sk, team_sk)` (dbt-layer pre-aggregation,
  matching the mart_leaderboards.rank / mart_team_fixtures.recency_rank precedent).
- Window correctness + no regression: partition (player_sk, team_sk) collapses the season axis so a club's
  rows share one ordering value → contiguous blocks, clubs most-recent-first (transfer + return-spell handled,
  data-driven test); grain test unchanged, no fan-out; both sort keys correctly excluded from the shipped
  member; national rows handled by the same window (no Python branch) + multi-national test added.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Sort trace + None-safety: traced all 6 test rows through the 3-tuple key (club_latest_kickoff_at,
  last_kickoff_at, team_sk) reverse=True → exactly `[(47,2024),(47,2020),(500,2023),(500,2021),(157,2022)]`
  (Spurs + England blocks contiguous); the `or datetime.min` fallbacks are sound by construction
  (appearances>=1 + inner-join-on-finished → non-null kickoffs); `cr["team_sk"]` is grain not_null.
- Mechanics: `_shape_career_row` returns a hardcoded 7-key literal (structurally cannot leak the sort keys);
  no dead `club_latest` loop; `datetime` still used elsewhere; mart change is a pure window column on with_caps
  + final select (no new join, no group by, grain test unchanged); 27 tests pass; no guard-path file touched.

## acknowledged (non-blocking; all three reviewers noted)
- `last_kickoff_at` + `club_latest_kickoff_at` carry no `not_null` dbt test — the non-null invariant the sort
  rests on is guaranteed by construction (mart's `appearances >= 1` test + the inner-join-on-finished chain)
  but is asserted only by inference, not a DQ test. Worth a trivial future hardening (a `not_null` on at least
  `club_latest_kickoff_at`, the primary ordering signal); the export's `or datetime.min` fallback means a
  hypothetical null would mis-sort silently rather than crash. Deferred, not a merge blocker.

## escalations
- Doc-sync (R2): wireframe 13 + gaps register go stale post-merge. **CPO ANSWER: reconcile SEPARATELY**
  (code-only PR, per the #627/#619 precedent); folded into reconciliation task task_4c709bd9. Resolved.
- Transfer/return-spell ordering (R2/R3): the sort needs a temporal disambiguator the mart didn't ship.
  **CPO ANSWER: fix properly — add the mart column.** Done (last_kickoff_at + club_latest_kickoff_at window).
  Resolved. No open escalation.
