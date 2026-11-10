# Review — claude/250-team-window-data — 2026-11-10

diff_sha256: 0065188ca095ccda411d502f03751323c3f9d4b5ced74f1f05a1df5f2f261918

rounds: 7

rounds_cap_override: round 7 re-checks the two pin fixes the full test run found after round 6, one long sentence in layering.md and the decision-history pin lowered to 281; approved in chat, 2026-11-10

## scope-auditor
VERDICT: PASS
risks_checked:
- Every changed file is inside scope_paths; the four amendments each name their authority and date, and the fourth matches the pin moving down from 282 to 281.
- The national-team question stays reserved: only club windows are built, and the mart gives a national team no row.
- decisions_taken declares the new mart, the model names, the season rule, the tie-break and the recurring cost of four small tables; no new mechanism, no secrets, no workflow file.
- The impact map carries pasted lineage and a measured blast radius; approved_design none holds, as no site_v2 or export file is in the diff.
- Doc-sync: the layering.md mart table, the engineering_standards.md guard list and count, the regenerated metric_map.csv and the generator surfaces move together; the split layering.md row carries no rationale or history.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: intermediate reads only intermediate and core models; the mart only selects, unpivots and joins.
- Grain tests on all four new tables; share ranges and non-negative counts and rates on the window model, the phase model and the mart; the 37 metric_key values match the generated map.
- The answer key, the league-phase pool test and the rate guard are new; the catalogue formula recompute is extended to both new surfaces, not weakened.
- Same-window rule: numerator and denominator over the same legs under the generated R4 gate; the benchmarks union leaves domestic and knockout-only seasons unchanged.
- is_featured_season reads the same source, one row per team, with the Player page's tie-break.
- Coverage notes (the answer key's single club and window; its cases going inert once the featured season moves on) are recorded for the page MR's contract under the coordinating session's ruling of 2026-11-10.

## platform-reviewer
VERDICT: PASS
risks_checked:
- No guard path, workflow, CI file, dependency or permission in the diff; no credentials.
- PINNED_LINES moves down only, from 282 to 281, after the mart_team_profile comment lost its issue reference.
- generate_metric_sql.py: the two Surface entries match the generated blocks and the registry test; reruns are idempotent.
- The new singular tests fail closed: the rate guard raises below its floor, the answer key on a missing row, column or value, the pool test on an extra or missing team or a differing value.
- Build health: four small tables over the legs; the benchmarks long form is narrowed by the phase branch, never multiplied.
- Coverage notes (a pin test for the featured-season tie-break; the answer key going inert) are recorded for the page MR's contract under the coordinating session's ruling of 2026-11-10.

## escalations
(none)
