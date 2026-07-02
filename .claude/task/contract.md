# Task contract — doc-sync reconciliation: flip the 3 wired screens to "shipped" (chip task_4c709bd9)

> Written on a CLEAN tree (branch docs/391-doc-sync-wired-screens off main @ d48ff4c).
> Doc-only cleanup — no code/model/metric change. Flips the wireframe/register/architecture status
> markers for the now-wired Squad (#619), Stats-percentile (#627), and Career (#634) screens from
> proposed/pending/orphan → wired/shipped, AND reconciles 12/13's §5 JSON keys to the exact shipped
> payload (CPO ruling 2026-07-02: "full reconciliation" — a wired screen's §5 keys must be greppable
> against the export, per the 00 binding rule + §Verification). See docs/working_agreement.md §2, §10.

objective: >
  The Career chain is wired end-to-end (#630 model -> #632 spec -> #634 export); Squad (#619) and
  Stats-percentile (#627) are likewise built AND wired. Their status docs still read
  proposed/pending/orphan/not-yet-wired, and 12/13's §5 keys predate the export renames/nesting. Flip
  the markers to wired/shipped AND correct 12/13's §5 JSON keys so the docs match the shipped export.
  Chip task_4c709bd9. Doc-only; invents no field, changes no display semantics/metric/layout —
  it flips lifecycle status and fixes stale key NAMES/paths to the greppable shipped shape.
refs: #391 (GAP-20 #619 / GAP-21 #627 / GAP-22 #634); chip task_4c709bd9

scope_paths:
  - docs/wireframes/11_team_squad.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/13_player_career.md
  - docs/wireframes/99_gaps_register.md
  - docs/content_architecture.md
  - .claude/task/**

# No impact_map: nothing under ingestion/**, dbt_project/models/**, scripts/export_*.py, or site*/ is
# touched. Doc-only reconciliation of already-shipped status + §5 key accuracy; the structural surface
# is unchanged. §5 keys are read FROM the shipped export (scripts/export_site_data.py) — that file is
# not edited.

decisions_taken: >
  (1) Flip lifecycle status — each wireframe (11/12/13): header banner + §3 data-source + §5 "all keys
  proposed" + the "JSON key (proposed)" table header + §10 gap bullet -> wired (#619 / #627 / #634);
  remove the now-impossible "Not yet wired ... open (today)" §6 state row.
  (2) Correct 12/13 §5 JSON keys to the exact shipped payload (CPO "full reconciliation" 2026-07-02),
  verified against scripts/export_site_data.py: 13 career[] renamed season_api_year->season,
  league_code->competition, and team_name/team_logo_url -> a nested team block {team_id,name,crest,country}
  (_shape_career_row L285-300 / _player_team_block L227-240); 12 benchmarks[] nest under seasons[] (per
  position_group, with a metrics[] list) and the ratio atoms shipped as numerator/denominator
  (_shape_benchmarks / _shape_benchmark_member L243-282). 11 §5 keys already match _shape_squad_member
  (six identity fields) — no key change there. No display-semantics/metric/layout change.
  (3) 13 also resolves the reserved subtotal decision to DISPLAY-SIDE grouping (the export ships a flat
  career[] with no subtotal fields, computes nothing; national_appearances_total precomputed).
  (4) 99_gaps_register: GAP-21 -> shipped #627, GAP-22 -> shipped #634 (GAP-20 already shipped by #620).
  (5) content_architecture: §3 legend (reconciled post-#634 2026-07-02; 15->17 marts = 18 distinct mart
  refs minus the live-MVP mart_matchday_insights; reword the orphan clause to team-benchmark-only) +
  §3/§7 benchmark rows (player wired #627 / team still orphan) + §3/§7 career rows (wired #634, still
  thin-until-backfill) + §7 date 2026-06-30 -> 2026-07-02 (roster rows already flipped by #620).

decisions_reserved:
  - not_null hardening on mart_player_career.last_kickoff_at / club_latest_kickoff_at (thrice-flagged,
    non-blocking, transitively guaranteed) — a dbt model/yml change, held OUT to keep this PR doc-only;
    recommended as a separate tiny dbt PR. CPO may fold in (would widen scope to analytics-engineer +
    ci-data-build); NOT decided here.
  - Deliberately NOT flipped (still genuinely open): backfill / thin-until-backfill (13 §10; content_arch
    §8-§10), the team rank-based benchmark (screen unspec'd -> stays orphan), player deserved-vs-actual /
    player YoY (content_arch §6 flagship, Phase C/D). 00_overview untouched (spec-status only, already correct).
  - GAP-20 register note "id+name only" is loose (the shipped squad[] carries six identity fields) — left
    as-is (already-shipped row, out of the flip scope); flagged to the CPO, not folded in.
  - All §10 unchanged; no product/UX/metric/naming decision.

done_when:
  - The 5 docs carry no stale marker for the 3 wired screens: grep finds no "proposed" / "not yet
    exported" / "GAP-2[012] open" / "15 marts" / "2026-06-30" survivor beyond the intended (team orphan +
    backfill notes).
  - Every §5 key on 11/12/13 is greppable in scripts/export_site_data.py's shipped payload; every flipped
    GAP/PR/date matches the merge facts (#619 2026-07-01; #627 & #634 2026-07-02).
  - python scripts/check_layer_contract.py passes (doc-only, no-op). No dbt/export/site change ->
    ci-data-build + ui-checks skip; python-ci green.
  - scope-auditor + bi-analyst-reviewer PASS (>=2 named risks each); review.md diff_sha256 binds; CPO merges.

amendments: (none)
