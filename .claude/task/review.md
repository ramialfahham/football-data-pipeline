# Review — feat/player-mins-per-appearance — 2026-07-24

diff_sha256: d416908623cd5c1982e2f16d5c2750781d887668cd4b23a02f64126032ee8496

rounds: 2

> PR-A: adds `minutes_per_appearance` = safe_divide(minutes, appearances) to mart_player_career + a
> metric_catalogue row + a null-safe DQ test, on the appearances denominator corrected in #813. Round 1
> full: analytics-engineer PASS, football-analytics-expert FAIL (format=integer should be decimal_0;
> CPO authority not cited), scope-auditor FAIL (same authority gap). Round 2 delta: both fixes made
> (format -> decimal_0; contract now cites the AskUserQuestion authority), football + scope re-confirmed
> PASS. analytics-engineer's PASS carries — the only changes since its review are the format field and
> the contract's authority text, both outside its risk set (mechanics, formula equivalence, the four
> resolvability/uniqueness/meaning/direction guards, blast radius); format is not validated by any guard.

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 metric-catalogue authority: the contract now cites the CPO authority (AskUserQuestion 2026-07-23,
  "Catalogue it now" + "Ship minutes only, fix apps next") in refs and decisions_taken (1), dated and
  quoted, cross-referable to the escalations log — this executes a recorded, deferred decision now that
  #813 met its precondition, not a new or reversed one.
- Scope bounded: the diff touches only the four scope_paths (mart_player_career.sql, shared.yml,
  metric_catalogue.csv, active_work.md); no export/frontend/build leakage (that is PR-B);
  `amendments: (none)` is correct for a fresh contract on a fresh branch.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Corrected-denominator + formula equivalence: `appearances`/`minutes` in int_player_club_season__metrics
  are the #813-corrected atoms; proved `countif(minutes_played > 0)` (catalogue) is identical to the
  mart's `countif(coalesce(minutes_played,0) > 0)` under BigQuery null-comparison semantics, so the
  catalogue formula and the mart column agree; the bare countif (no coalesce) honors the no-null-gate
  rule, matching the clean_sheets precedent.
- Catalogue guards hand-traced against the real row and int_legs__player_match columns: resolvable
  (sum/countif allow-listed, minutes_played real), unique (metric_id, entity), meaning-complete, and
  direction/lower_is_better agree (neutral + false). Same-window (numerator/denominator share one
  per_fixture CTE). Leaf mart (zero ref() hits); export _shape_career_row does not surface the column,
  so nothing breaks on merge. Table materialization, no incremental-rename trap. No hardcoded league_code.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- direction=neutral RATIFIED: mins/app normalises minutes by appearance count (no output in the
  numerator), so it is a squad-role descriptor with no better/worse pole — a valued super-sub on short
  cameos is not "worse" than a starter — matching the existing neutral rows (contribution_share,
  sot_points_gap); lower_is_better=false agrees.
- format corrected to decimal_0: a divided value like every other ratio row (safe_divide returns
  FLOAT64), renders identically to integer per site_v2 format.ts; the rest of the row is unregressed
  (numerator sum(minutes_played), denominator countif(minutes_played > 0), interpretation unchanged).

## escalations
- question: is minutes_per_appearance a display-support column or a catalogue-governed metric?
  CPO ANSWER: catalogue it — "Catalogue it now" (AskUserQuestion 2026-07-23).
- question: ship the ratio now, or fix the appearances denominator first?
  CPO ANSWER: "Ship minutes only, fix apps next" (AskUserQuestion 2026-07-23). #813 did the fix; this
  PR ships the ratio on the corrected denominator.
- question: direction of minutes_per_appearance — neutral or higher_better?
  Ratified neutral by the football-analytics-expert reviewer (a reviewer-adjudicated domain call, not a
  §10 CPO decision).
