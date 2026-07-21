# Review — feat/metric-direction-sweep — 2026-07-21

> Blinded review cycle for the catalogue-wide `direction` sweep. Three required reviewers per
> `.claude/review_routing.json`: scope-auditor (always) + analytics-engineer-reviewer and
> football-analytics-expert-reviewer (both routed by `dbt_project/seeds/metric_catalogue.csv`;
> analytics-engineer-reviewer also covers `dbt_project/**`). All three PASS, after 4 / 2 / 1 rounds.

diff_sha256: 73f349594b7775c4bd2a67076feaea299ab7589a1f5f24761018ac1b88c6d419

## scope-auditor
VERDICT: PASS
risks_checked:
- Seed column integrity — audited every changed hunk in `metric_catalogue.csv` and spot-checked 15+ rows across team and player metrics: all columns except `direction` (13) and `interpretation` (14) are byte-identical between the minus and plus lines, including `numerator_expr`, `denominator_expr` and `lower_is_better`. Zero column drift or creep.
- Final-tally arithmetic — independently reconciled the counts rather than trusting the contract: 35 pre-existing higher_better + 18 newly filled + 10 un-neutralled = 63; 5 + 8 = 13 lower_better; 12 − 10 = 2 neutral; 63 + 13 + 2 = 78 = total rows. Confirmed exactly 2 `neutral` rows survive (`sot_rank_gap`, `contribution_share`).
- Amendment legitimacy — verified AMENDMENT r1 is dated, attributed to the analytics-engineer-reviewer FAIL that drove it, and is not a silent scope grab; confirmed the two newly-in-scope files carry prose-only changes and that the test's `where entity in ('team', 'team and player')` predicate is byte-identical, so no enforcement behaviour changed under cover of a doc fix.
- Handover accuracy and verdict-overstatement guard — confirmed `.claude/active_work.md` satisfies the contract's `done_when` (a cold chat can resume from branch, counts, tally, do-NOTs, review state and the known follow-up), that no reviewer is described as "pending" after voting, and that the handover did not claim a final scope-auditor verdict while that verdict was still open.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Test predicate and logic byte-identity — read the full `assert_team_metric_meaning_complete.sql`; the diff touches only the Jinja comment block, and the query body (`select ... where entity in ('team','team and player') and (direction is null or trim(direction) = '' or interpretation is null or trim(interpretation) = '')`) is byte-identical, confirming rather than trusting the amendment's "prose only, no logic change" claim.
- Schema documentation accuracy — independently re-derived each new claim directly from the post-diff seed instead of accepting the contract's assertion: counted `neutral` = 2, `higher_better` = 63, `lower_better` = 13 (summing to all 78 rows), and verified the `interpretation` description's "populated on some player rows and still blank on others" is literally true.
- CSV structural integrity — one contiguous hunk with equal old and new line counts (no row added, removed or reordered); 36 changed rows matching the stated 26 blank-filled plus 10 un-neutralled; all 10 rewritten `interpretation` strings scanned for unquoted commas (none — they use `-` and `;`), so no CSV quoting corruption or column shift.
- Downstream blast radius — read both benchmark marts in full and confirmed neither selects nor joins `direction` (ranking is `rank() over (... order by metric_value desc)`), so zero number movement; confirmed `scripts/export_metric_definitions_json.py` reads only the untouched `lower_is_better`, leaving the live MVP byte-identical; confirmed `export_site_data.py` passes the seed through without computation; confirmed `site_v2/src/lib/metricRows.ts` needs no mirror edit because none of the 36 changed rows is one of its 16 locked fixture-comparison rows.
- Seed diff stability across patch regeneration — re-confirmed the `metric_catalogue.csv` hunk is byte-identical to the pre-amendment patch, ruling out drift introduced by the stash-and-amend cycle.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- `lower_is_better` versus `direction` divergence — checked all 26 blank-filled rows against their untouched boolean and confirmed the divergent set is exactly the four logged in `decisions_reserved` (`cards_yellow`, `cards_red`, `cards_total`, `shots_on_goal_against`), with no hidden fifth; verified the boolean column itself is untouched byte-for-byte, so no silent live-MVP behaviour change.
- The two surviving `neutral` rows — verified against their description text rather than accepting the claim: `sot_rank_gap` is a signed rank-space residual where neither sign is intrinsically good (a negative gap flatters today but foreshadows regression), and `contribution_share`'s low pole is structurally produced by playing position (a centre-back's low share is not a failing). Both correctly resist the all-else-equal test; grep-confirmed exactly 2 remain.
- Volume-treatment consistency on the edge cases — confirmed `offsides` and `dribbles_past` were correctly NOT swept into the "volume is higher_better" treatment applied to `shots_total` / `duels_total` / `dribbles_attempts`: a failed shot or lost duel still produced output, whereas an offside voids the phase of play entirely and being dribbled past is an unambiguous defensive failure. Distinct and correct football reads, not an inconsistency.
- Interpretation honesty on the 10 un-neutralled rows — read all ten; every one leads with the "more X is better all else equal" reading before its volume/role caveat, and none asserts an absolute ("always better", "proves quality"), matching the PR #676 precedent and the display contract's ban on a naked uncaveated verdict on a style number.
- Row-count and structural integrity of the changed rows — recounted the diff by hand (18 higher_better + 8 lower_better = 26 blank-filled; 3 team + 7 player = 10 un-neutralled) and spot-checked field counts on rows carrying punctuation in the new interpretation text, confirming no column shift into `interpretation`.

## escalations
(none)
