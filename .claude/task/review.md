# Review — docs/391-doc-sync-wired-screens — 2026-07-02

> G3 Lock artifact. Doc-only post-wiring reconciliation (chip task_4c709bd9): flips wireframes 11/12/13 +
> the gaps register (GAP-21/GAP-22) + content_architecture.md from proposed/pending/orphan → wired/shipped
> for the now-wired Squad (#619) / Stats-percentile (#627) / Career (#634) screens, AND corrects 12/13's §5
> JSON keys to the exact shipped export payload (CPO "full reconciliation" ruling, AskUserQuestion 2026-07-02;
> durably recorded in escalations.log lines 184-186). Required set (routing): scope-auditor (always) +
> bi-analyst-reviewer (docs/wireframes/**). No code/model/export/site path touched → no
> analytics-engineer / cto / data-engineer reviewer required.
>
> Round 1 (hash 20882a2b) — bi-analyst PASS; scope-auditor FAIL (single finding: the cited CPO "full
> reconciliation" ruling was not recorded in escalations.log — working_agreement §11). Fix: appended the
> ruling to escalations.log (hash-excluded → diff_sha256 unchanged). Round 2 (same hash) — scope-auditor
> PASS. Both required reviewers now PASS on the SAME hash; no diff line changed between rounds.

diff_sha256: 20882a2b0284cd507e99c999f17d342c98fa75da2ae7b20ffe3430cdaa59bc3a

## scope-auditor
VERDICT: PASS  (round 2; the round-1 finding is resolved)
risks_checked:
- Escalation authority durably logged: the round-1 finding was the contract citing "CPO ruling 2026-07-02:
  full reconciliation" with no escalations.log entry (§11). Verified escalations.log now carries the
  2026-07-02 entry (lines 184-186) recording the two-path escalation + the CPO AskUserQuestion answer
  "(A) full reconciliation", in the same format as prior AskUserQuestion rulings; the contract's
  decisions_taken (2) is now auditable. The entry is hash-excluded, so diff_sha256 (20882a2b) is unchanged —
  round-1's clean findings still bind.
- Structural scope isolation: all 6 changed paths are docs/markdown + contract.md (within scope_paths);
  scripts/export_site_data.py is READ FROM (to verify keys), not edited; nothing under ingestion/**,
  dbt_project/models/**, or site*/ is touched → the "doc-only, no impact_map" claim holds. The deliberate
  exclusions (GAP-20 "id+name only" register note, metrics_display.md:91, 00_overview, team rank-based
  benchmark stays orphan, backfill/thin-until-backfill notes) are all left untouched — no scope creep.

## bi-analyst-reviewer
VERDICT: PASS  (round 1)
risks_checked:
- §5 key greppability vs the shipped export: verified each flipped screen's §5 keys exist EXACTLY in the
  payload — 13 career[] (season / competition / entity_type / team block {team_id,name,crest,country} /
  appearances / goals / assists + top-level national_appearances_total) vs _shape_career_row /
  _player_team_block; 12 benchmarks[] nested under seasons[] per position_group with a metrics[] list, and
  the ratio atoms as numerator/denominator (the JSON key vs the mart column metric_numerator/
  metric_denominator are kept correctly distinct) vs _shape_benchmarks / _shape_benchmark_member; 11 squad[]
  six identity fields vs _shape_squad_member. Grepped the OLD flat keys (career[].season_api_year /
  league_code / team_name / team_logo_url, benchmarks[].season_api_year) → zero matches (fully removed).
- No invention / claim accuracy: the flips invent no field and do not contradict metrics_display.md (the
  percentile ladder, the ratio volume-triple, and Career counts-only are all consistent); PR/date claims are
  correct (#619 07-01; #627 & #634 07-02); content_architecture "17 marts" independently recounted (18
  distinct mart refs − the live-MVP mart_matchday_insights); "team benchmark stays orphan" corroborated
  (mart_team_competition_benchmarks absent from the export); §6 state tables read coherently after removing
  the "Not yet wired … open (today)" rows.

## escalations
- (scope, AskUserQuestion 2026-07-02 — RULED) Tracing the shipped export revealed 12/13's §5 JSON keys
  diverge from the payload; an honest "wired" flip must correct them (00 binding rule + §Verification),
  widening the diff beyond the approved "flip the markers" plan. Two paths presented with a recommendation.
  CPO ANSWER: **(A) full reconciliation** — flip the banners AND correct 12/13's §5 keys to the shipped
  payload; doc-only, no display-semantics/metric/layout change. Durable record: escalations.log 2026-07-02
  (lines 184-186). No open escalations remain.
