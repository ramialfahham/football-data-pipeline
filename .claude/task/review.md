# Review — fix/metrics-display-percentile-direction — 2026-07-21

> Blinded review cycle for the percentile-display de-stale following the merged direction sweep (#677).
> Two required reviewers per `.claude/review_routing.json`: scope-auditor (always) + bi-analyst-reviewer
> (routed by `docs/wireframes/**`). Both PASS after 3 and 4 rounds. Doc prose only; no seed, model, test,
> export or `site_v2` change.

diff_sha256: 940396aa50f9252fba69e5c4e30b61ad2dc73c87e2d9422d375cbfcb791b7abd

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope containment across two amendments — confirmed every changed file sits inside the amended `scope_paths` and that NO seed, dbt model, test, export script or `site_v2` file moved. Verified both expansions (r1 pulling in `12_player_stats.md`, r2 pulling in `14_team_stats.md`) are the same defect class rather than unrelated creep, and that each amendment is dated and attributed to the review finding that drove it instead of being a silent grab.
- Superseded rules preserved, not deleted — checked all three wireframes and confirmed each retired rule is retained as an explicit "(Superseded: ...)" note carrying its original rationale and why it is void, so a future reader sees why the rule changed rather than assuming it was ignored.
- Contract self-consistency after the fabricated-precedent fix — the retired "team Performance tab" phrase no longer appears in any live section (`objective`, `decisions_taken` #2, `done_when`); `decisions_taken` #2 now carries an explicit instruction never to express the rule as parity with a pre-existing screen, and `done_when` requires that no document claims parity with a screen or rule that does not exist. The only surviving occurrences are deliberate historical quotes inside the amendment records.
- ASCII annotation factual consistency — the Duels row carries a `±0` delta, so the corrected annotation ("level with the median (±0) → plain ink") agrees with its own row data and correctly illustrates the colour rule, replacing an annotation that contradicted it.
- Handover accuracy without verdict overstatement — `.claude/active_work.md` satisfies `done_when`, reflects the expanded scope and all six findings across the two review FAILs, and never claims a final bi-analyst verdict while that verdict was still open.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Direction tally verified row-by-row against the merged seed, not the contract's claim — for the player screen, all 18 keys of `player_benchmark_metrics()` carry `direction=higher_better` (0 neutral, 0 lower_better); for the team screen, the 16 rendered rows are 14 `higher_better` / 2 `lower_better` (`goals_against_per_match`, `corners_against_per_match`) / 0 `neutral`. Both docs match exactly.
- Fabricated-precedent elimination — grepped the contract, the handover and all of `docs/wireframes/` for the retired screen name; the only hits are inside the amendment records quoting it as history. The three wireframes now cross-reference each other by number rather than by a phantom spec name, and the parity between the player and team screens is constructed in this PR rather than asserted.
- Cross-document consistency on both the tally and the colour rule — all three files state the identical direction-aware rule (green when the metric beats the median in its better direction, plain ink otherwise) and the identical "bar LENGTH = distributional position, bar COLOUR = whether that end is good" framing, resolving the earlier contradiction with the still-live "not a verdict" wording the same way everywhere.
- ASCII annotations agree with their own row data — the team Duels row (`±0` → level with the median → plain ink) and the player Duels-won row (`bottom 40%` → below the median peer) are each internally consistent with the new rules.
- Nothing still-accurate was damaged — the plain-language ladder ("top X%" / "median" / "bottom X%", never "Nth percentile"), median-anchored framing, position-group peers, the eligibility floors, the sample line, the ratio volume-triple rule, and the `lower_better` mirroring rule all survive intact and are still correctly described as dormant or as N=2 where applicable.
- Inline annotation consistency in the benchmarked-set table — the `(lower_better)` tag is now applied to `corners_against_per_match` as well as `goals_against_per_match`, matching the prose above it and the merged seed (confirmed in a final round).

## escalations
(none)
