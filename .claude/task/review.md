# Review — refactor/metric-rename-team-passing — 2026-08-28

> Step 3 of the metric catalogue naming programme, MR **D of six**:
> `pass_accuracy` → `passes_accuracy_pct`, `key_passes_per_match` → `passes_key_per_match`.
> Branched from main `62d3b18`, the main carrying `!119` (batch C).

diff_sha256: 0c13f5f308e851414a23bbab6238f990064d28d81037499189aafc8eeda9f1d7

rounds: 3

> ⛔ **THE CODE NEVER CHANGED ACROSS ANY OF THE THREE ROUNDS.** Every round turned on one thing: the
> naming-authority citation for `key_passes_per_match` → `passes_key_per_match` in `contract.md`.
> The rename itself passed every warehouse, platform and display check in round 1 and was
> re-confirmed in each later round.
>
> **Round 1 — 4 PASS, 1 FAIL.** `football-analytics-expert-reviewer` found the contract cited
> RULING 6. RULING 6 verbatim is `"key_passes_player"` → `passes_key_player` — the **PLAYER**
> metric throughout; it never names the team one. It further established the rename is not among
> "THE SIX, ENUMERATED", the list built specifically to cure builder-reconstruction-dressed-as-record.
> Correct on both counts.
>
> **Round 2 — 3 PASS, 2 FAIL.** My fix rested the authority on the CPO approving this MR's plan
> ("then go ahead"). `football-analytics-expert-reviewer` and `analytics-engineer-reviewer`
> independently FAILed it: the approval was recorded without reproducing the table it answered, so
> it is unverifiable from the record, and the identical phrase appears at `escalations.log:5618`
> answering an unrelated question. Also correct. I had broken the log's own 2026-08-26 rule —
> *record the thing the approval was given against, not only the approval* — for the second time in
> one MR.
>
> **Then I escalated the name to the CPO as an open §10 question.** His reply: *"we have defined it.
> you should be able to look it up, no?"*
>
> **Round 3 — 5 PASS.** The authority was in the record the whole time and is neither thing I cited:
> the ruled naming PATTERN at `escalations.log:5483-5485`, explicitly scoped "to be applied to any
> metric added later". Applied — noun `passes` + qualifier `key` + team form `_per_match` —
> it yields `passes_key_per_match` uniquely.
>
> ⭐ **THE RULE THIS LEAVES, and it matters for step 4's 35 player renames: when a ruling is a
> PATTERN, the pattern is the authority for every name it determines.** Hunting for a per-instance
> quote where a general rule already decides the name manufactures a gap. I manufactured one and
> then escalated it.

## scope-auditor
VERDICT: PASS
risks_checked:
- Delta scope confirmed: only `contract.md` and `escalations.log` changed since the round-2 PASS — no model/site/seed file moved, so the rename mechanics rest on the prior PASS rather than being re-derived.
- Verified the new authority against the primary source: `escalations.log:5483-5485` reads verbatim "THE PATTERN THIS PRODUCES, to be applied to any metric added later: noun [_qualifier] [_against] [_player] [_form]... `_form` is `_per_match` for a team", and applying it yields `passes_key_per_match` exactly — not a stretch.
- Cross-checked the pattern-derived name against an independently-dated entry: `escalations.log:5443` lists `key_passes_per_match → passes_key_per_match` verbatim, so the citation is corroborated by a second source rather than resting on the pattern alone.
- Checked the two prior wrong citations are characterised as wrong rather than papered over: RULING 6 at `:5387` is verbatim "key_passes_player" (player metric); the "then go ahead" at `:5618` demonstrably answers a different question (moving two locked acceptance criteria). Both `amendments:` entries describe real, checkable errors.
- Confirmed the "⛔ NO PLAN FILE IS CITED" line is no longer contradicted — the round-2 plan-approval citation is gone from `refs:`, replaced by the in-repo pattern ruling.
- Threshold declarations (no new mechanism, no recurring cost) consistent with a citation-only change plus already-reviewed rename mechanics.
- Secrets sweep over the diff region — none found.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Naming-authority citation tested for AMBIGUITY rather than accepted: the pattern's fixed slot order (noun before qualifier before form), with noun `passes` already fixed by `passes_total`/`passes_accurate`/`passes_key`/`passes_per_match`, yields `passes_key_per_match` and no other pattern-consistent string. Not ambiguous.
- Both prior wrong citations checked against the source they misquote — RULING 6 (`:5387`) never names the team column; the "then go ahead" (`:5618`) answers an unrelated question. The contract records both as wrong rather than re-asserting either.
- Formula byte-identity: `int_team_season__metrics_cumulative.sql:135,150` and `mart_team_momentum.sql:83,104` — `safe_divide(passes_accurate, passes_total)` and `safe_divide(key_passes, games_with_player_stats)` unchanged; only the alias moved.
- Player/team stem protection: `int_player_profile.yml` and `int_player_profile__yoy.sql` carry no `pass_accuracy`/`key_passes_per_match` tokens at all; the four `*_pass_accuracy_pct_in_range` player tests (`shared.yml:987,1270,1734`, `int_team_season.yml:432`) are untouched and absent from the diff.
- Bare `key_passes` exemption confirmed: 0 seed rows, not a declared column, so `assert_no_uncatalogued_season_metric` cannot reach it; consumed as `safe_divide(key_passes, games_with_player_stats) as passes_key_per_match`.
- Three 22-name `accepted_values` lists counted: 22 each, both new names once, old names absent from all three.
- Impact-map lineage sanity: `mart_team_competition_benchmarks` and `mart_team_season` correctly contain no literal reference to either renamed column — they pass the long-format `metric_key`/`metric_value` pair through generically.
- Residual sweep: every remaining hit sits in the generated sample, the frozen page, or task paperwork.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Pattern quote verified verbatim against `escalations.log:5483-5485` — matches the contract word for word. No misquote this time.
- Uniqueness of the derived name tested against the sibling columns sitting untouched in the same model (`passes_per_match`, `passes_accurate`, `passes_total`, all noun-first): given the pattern's fixed bracket order there is no alternative slot for "key" that stays pattern-consistent.
- ⭐ THE SCOPE QUESTION, tested specifically because it was the one reading that could sink the citation: does "to be applied to any metric added later" cover a RENAME or only genuinely new metrics? Read the surrounding context at `:5386-5391` — the instruction was given precisely because "passing was the only family with the qualifier on both sides", i.e. both the player form AND the team form. That framing already treats the team metric as part of the anomaly being fixed. The narrower new-metrics-only reading is not better supported by the record.
- Precedent checked: this reviewer role already accepted "a direct application of an approved general rule rather than an unapproved new naming decision" for items 4/5 of the enumerated six, on identical reasoning. Applying the same standard here is consistent, not convenient.
- No overstatement: the contract discloses both prior wrong citations plainly, quotes the reviewer findings against itself, and does not launder them into "the record was unclear".
- `pass_accuracy` → `passes_accuracy_pct` chain re-derived independently: RULING 1 (`:5351-5357`) plus item 6 of the enumerated six (`:5410-5411`). Holds without gaps.
- Both seed rows are pure renames — table, numerator, denominator, `is_lower_better` (false for both), format, group, tier, interpretation and description all byte-identical. No formula drift, no direction flip.
- Football validity unaffected: both remain real, honestly-caveated quantities with their null/coverage caveats intact.

## platform-reviewer
VERDICT: PASS
risks_checked:
- "No code changed" verified: no file in `scripts/`, `tests/`, or `.gitlab-ci.yml` appears anywhere in the patch (`.gitlab-ci.yml`, `requirements`, `package.json`, `astro.config`, `firebase.json` all zero hits). Batch C's script/test edits are correctly absent under this contract's narrower `scope_paths`.
- `escalations.log` diff is a pure append (`@@ -5816,3 +5816,115 @@`, every added line `+`) — no historical entry rewritten, consistent with the log's append-only discipline.
- Pattern citation at `escalations.log:5483-5485` checked character for character against the live file.
- Four renamed team `*_in_range` tests bind to live columns: `mmi_home_`/`mmi_away_passes_accuracy_pct_in_range` (`domestic_league.yml:181,184`) test `home_`/`away_passes_accuracy_pct_recent`, which `mart_matchday_insights.sql:153,165` aliases; `momentum_team_` and `std_team_passes_accuracy_pct_in_range` (`shared.yml:118,868`) test the renamed column directly.
- Four player `*_pass_accuracy_pct_in_range` tests intact and still referencing the unrenamed player column.
- Both regenerated artifacts show no hand-edit signature: `metric_columns.md` blocks land in sorted position; `metric_definitions.json`'s single changed entry mechanically mirrors the bindings row with `live_id` preserved.
- No CI gating change; credential sweep clean; no dependency or hosting config touched.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- "Code never changed" verified by reading the full patch: every hunk outside the two task files is a mechanical rename, single-purpose, no stray hunk. `escalations.log` diff is a pure append.
- `metricRows.ts` re-read: 16 rows, `Passing` still holds `passes_per_match` (tier 3), `passes_accuracy_pct` (tier 2), `passes_key_per_match` (tier 2) — same tiers, same order, same group. No reordering.
- `acceptance_evidence.md` and `rendered_page_evidence.md` agree with each other and with the tree: 13/13/13 rows, 7 headings, `Passing` keeps its heading with `Ø Passes` surviving, rows honestly omitted per `14_team_stats.md` §6, label wording byte-identical in EN/DE/FI (only JSON keys changed).
- `docs/wireframes/10_home.md`: lines 134 and 150 still read the PLAYER `pass_accuracy_pct`; only line 175 (the team pair) was renamed.
- `pass_accuracy_recent` unchanged in `metric_bindings.csv`, `metric_definitions.json` and `metric_manifest.json:12` — only the mapped columns repointed.
- Repo-wide sweep for both old bare tokens: remaining hits are exactly the declared exceptions — task artifacts, the generated sample, the frozen page. No orphan on any live surface.
- Both authority quotes verified verbatim; the pattern's inputs (`passes_total`, `passes_accurate`, `passes_key`) confirmed present and untouched in the seed, making the derived name unambiguous.
- Player-side `pass_accuracy_pct` confirmed untouched in the seed — no cross-entity corruption from the shared stem.
