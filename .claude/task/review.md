# Review — docs/391-career-screen-spec — 2026-07-02

> G3 Lock artifact. NEW `docs/wireframes/13_player_career.md` — the Player → Career sub-screen — bound to the
> merged per-club `mart_player_career` (#630), + companion doc-syncs (00 inventory/census, 99 GAP-22, 03
> footer link + §10 ref). Doc-only; mirrors #625 (Stats 12) + #617 (Squad 11). No code/model/dbt/export change.
> Required set (routing `.claude/review_routing.json`): scope-auditor (always) + bi-analyst-reviewer
> (`docs/wireframes/**`). metrics_display.md deliberately NOT touched (counts-only screen, no new display idiom).
>
> Cycle history (re-run fresh on every hash change):
> - Round 1 (hash 7aa729b9): scope-auditor PASS; bi-analyst-reviewer FAIL — (a) §6 missing the "unresolved
>   identity" state sibling 11 carries; (b) the header/§1 mis-cited metrics_display.md for the "no per-90 /
>   counts-only" rule (that doc governs the season bundled-row display, not career). Fixes: added the §6
>   null-identity state (mirrors 11, grounded in the player_sk/team_sk relationships DQ tests); re-cited the
>   rule to ui_design_brief.md §6.4 + the CPO counts-only ruling on mart_player_career.
> - Round 2 (hash 841a96fc, THIS lock): scope-auditor PASS + bi-analyst-reviewer PASS. Only doc content
>   changed since round 1; both fixes verified genuinely resolved + a clean regression sweep.

diff_sha256: 841a96fc95d727a10a51a7fadb86ecfb9b1958a0385a1cb474e18617c58355c4

## scope-auditor
VERDICT: PASS
risks_checked:
- Metric binding integrity (§5 → mart_player_career): every §5 JSON key (player/club identity, season_api_year,
  league_code, appearances, goals, assists, entity_type, national_appearances_total) maps 1:1 to a real column
  on the merged per-club mart_player_career (#630) — no fabricated field, no schema drift. The 00 binding rule
  (the blueprint's structural foundation) holds.
- Consumption-layer contract (export derives no facts): national_appearances_total is precomputed on the mart,
  not the export; per-club/career subtotals are flagged "display grouping OR reserved dbt precompute" — not
  pre-decided (the #630 reserved item); GAP-22 is registered pending, not shipped. Scope: only docs/wireframes
  + .claude/task/** touched; content_architecture.md ("caps" wording) is out of scope and correctly left
  untouched (the spec uses honest wording). No §10 decision made silently; contract "amendments: (none)" is
  correct (the round-1 fixes were content corrections within scope, not scope extensions).

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- §6 "Unresolved identity" row: verified the cited DQ tests exist verbatim (shared.yml player_sk→dim_player
  :1294-1296, team_sk→dim_team :1301-1303); the "test failure, not a rendered blank" framing matches 11 §6;
  both FKs are also not_null so the real failure mode is an orphaned FK — the wireframe's "no resolvable
  dim_player/dim_team" describes it correctly.
- Citation fix: the "per-90 / composite scores deliberately not available yet" claim is now the exact
  ui_design_brief.md §6.4 quote (lines 156-157); metrics_display.md is cited ZERO times in the file; the
  distinct "career-long rate not meaningful" claim is honestly framed as the CPO judgment, no doc mis-cited.
- Regression sweep clean: every §5 key traces to a real mart column (none fabricated); goals/assists exist in
  metric_catalogue.csv, appearances treated as a fact; national wording honest ("covered competitions", never
  "caps") throughout; counts-only genuinely honored (zero %/percentile/tier in the file); the entity_type-null
  "Unmapped competition" state matches the mart's LEFT JOIN chain; 00 inventory row 13 + the 4 census
  components + 03 footer link/§10 ref + 99 GAP-22 all cross-reference consistently.

## escalations
(none) — both round-1 bi-analyst findings fixed in-cycle (§6 identity state; the ui_design_brief citation).
The subtotal precompute-vs-display question + the export wiring + the history backfill are reserved to the
GAP-22 wiring PR / separate follow-ups, not decided here.
