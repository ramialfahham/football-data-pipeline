# Review — docs/391-player-stats-percentile-spec — 2026-07-02

> G3 Lock artifact. #391 Stats-percentile screen: rework the parked Player Stats percentile-vs-peers
> wireframe (docs/wireframes/12_player_stats.md, recovered from stash@{0}) + 4 companion doc edits, per the
> CPO-approved plan (ExitPlanMode this session). Doc-only (docs/wireframes/**). Median word = "median";
> label = distributional position (honest for the 7 neutral metrics); ratio metrics show the {num} of {den}
> · {pct}% triple; all 18 benchmark metrics bound to real mart columns; GAP-21 registered (export wiring, a
> later PR). Required set (routing): scope-auditor (always) + bi-analyst-reviewer (docs/wireframes/**).
>
> Round 1 (hash f72e750f) — scope-auditor PASS; bi-analyst-reviewer FAIL (two findings): (1) a silent,
> undisclosed footer label rename "Team profile" → "Team" in 03_player_profile.md (no i18n key / decision
> record); (2) the lower_better display rule mirrored only `percentile`, leaving the caption `rank`
> (mart-computed value-descending) un-mirrored — an incomplete "defined but dormant" path.
> Round 2 (hash f29f9f87, THIS lock) — both fixed: (1) 03 footer is now a two-line footer with full labels
> (▸Stats ▸Team profile / ▸Bundesliga ▸Top scorers), matching the established two-line footer in
> 01_fixture_page.md — no rename, no link dropped; (2) the lower_better rule now mirrors BOTH `percentile`
> (1 − percentile) AND the caption `rank` (peer_count + 1 − rank), stated identically in 12_player_stats.md
> §5 and metrics_display.md. Both reviewers PASS.

diff_sha256: f29f9f87f0147640db296442ad0782e454033232a22a28566ea67635ad4b37b0

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + §10: every staged change is inside contract scope_paths (the 5 wireframe docs + contract.md); no
  PROTECTED path touched; metric_catalogue.csv is NOT in the diff (no metric added/changed). decisions_taken
  are all pre-settled (median word CONFIRMED 2026-07-02; the 18-metric set + position eligibility CPO-locked
  2026-06-23; the ratio triple is the locked no-naked-% rule) or explicit factual corrections of the draft
  (the "all 18 higher_better" claim → the verified 11 higher_better + 7 neutral + 0 lower_better); no
  decisions_reserved item is taken. Appendix-A anti-patterns (A1 invented metrics, A2 unilateral product
  decisions, A5 frontend logic) all cleared — the spec states "export selects/reshapes only; label applied
  at render from the catalogue direction". Held.
- Grounded facts + forward risks: mart_player_competition_benchmarks exists; GAP-21 is the correct next
  register number (after GAP-20); no invented field. Two structural risks flagged for the GAP-21 wiring PR
  (correctly reserved, not blockers): (a) multi-position players must be exported once per position_group
  (the mart grain (player_sk, season_sk, position_group, metric_key) enforces this; the position selector +
  most-minutes default are specified); (b) the 5 ratio metrics must carry all 10 num/den atoms from
  int_player_season_position__metrics without derivation (consumption-layer contract) — atoms verified to
  exist. Held.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Round-1 findings both resolved: (1) 03_player_profile.md:63-64 is a two-line footer with all full labels
  (Team profile / Bundesliga / Top scorers) + the new Stats link, matching 01_fixture_page.md:90-91 — no
  rename, no drop; §10 "Linked from (7)" correctly references ASCII block (7). (2) rank mirror re-derived
  against the mart window functions (rank = value DESC, percentile = value ASC over the same
  (league,season,position,metric) partition that peer_count is counted over): peer_count + 1 − rank is the
  exact rank mirror, stated identically in 12_player_stats.md §5 and metrics_display.md, correctly marked
  dormant (0 lower_better). Held.
- Binding honesty re-verified against source (not prose): the "11 higher_better + 7 neutral + 0 lower_better"
  tally matches the player rows of metric_catalogue.csv metric-by-metric (the 7 neutral named exactly); all 5
  ratio num/den atoms match the safe_divide expressions in int_player_season_position__metrics.sql (incl.
  save_pct's saves/(saves+goals_against)); every mart column / GAP-21 payload key named appears verbatim in
  mart_player_competition_benchmarks.sql's select list — no fabricated field; the 18-metric set + GK/outfield
  eligibility match player_benchmark_metrics.sql. Cross-file consistency (00_overview inventory row 12 +
  census; no stray "middle" as a label; no player-"tier" conflation) all clean. Held.

## escalations
(none) — the reworked spec records only CPO-settled display rulings + factual corrections of the parked
draft; the benchmark→player-export wiring (GAP-21, carrying the num/den atoms), the exact benchmarks[] JSON
nesting, and the neutral-metric wording nuance are all reserved to the wiring PR / the CPO.
