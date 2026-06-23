# Review — fix/issue-526-team-event-attribution — 2026-06-23

diff_sha256: 6856870f0c67e4c19be98c2913f2132ece2ef9f159b21d0d433d4dcd4f9638ce

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + §10: all 7 staged paths are within `scope_paths`; the new override seed (a NEW mechanism)
  and its naming + the ERROR test severity are recorded as CPO-approved in `decisions_taken` ("do it"
  this session); the full-refresh fallback and the manual-seed-governance/automation are correctly
  left in `decisions_reserved`. No unrecorded §10 decision; not a coverage-cut (A6) — 38 event rows
  are corrected, none dropped.
- `impact_map` honesty: verified `fct_fixture_event` is a LEAF (no model ref()s it) so the corrected
  team_id reaches NO mart; the marts in the `base_apif__fixture_events+` closure sit downstream via
  `base_apif__players`/`dim_player` and `fct_fixture_player_stats` (player identity/stats), not the
  event team_id — the "no mart deltas" claim is truthful.
- Correctness of the `reattribute_if_cohabiting` gate + self-heal: the override only fires where the
  correct id IS a participant and the wrong id is NOT, so ASC Kara's own 6424 events (6424 IS a
  participant) are untouched; the incremental self-heal is self-limiting (once corrected the
  violation disappears and the fixture stops matching) and merges in place via `event_sk`.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Fan-out / grain: the seed carries `unique(wrong_team_api_id)`, so each event matches at most one
  `alias_override` and one `reattribute_override` row; `base_apif__fixtures_next` is unique on
  `fixture_id`; all three LEFT JOINs are 1:1, preserving the base grain
  (league_code, fixture_id, event_index).
- NULL-safety across all three `NOT IN` sites: the base `fixture_participants` CTE filters
  `home_team_id`/`away_team_id` IS NOT NULL (and a LEFT-JOIN miss yields the safe no-fire path); the
  self-heal guards `team_sk`/`home_team_id`/`away_team_id` IS NOT NULL before its `NOT IN`; the
  integrity test guards `team_sk`/`home_team_sk`/`away_team_sk` IS NOT NULL — no `NOT IN (…, NULL)`
  → UNKNOWN trap remains.
- Layer placement + blast radius: the entity-alignment correction belongs in `2_base` (staging is
  raw-cleanup-only; core cannot ref stg_* or alter source ids) — correct; `fct_fixture_event` leaf
  status confirmed by grep, so no mart numbers change. (Non-blocking: the `-- depends_on:` hint is
  the dbt-standard SQL-comment form and lineage is captured by the `ref()` in the conditional —
  confirmed by a clean compile.)

## escalations
(none)
