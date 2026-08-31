# Review — refactor/metric-rename-player-goals — 2026-08-31

> **STEP 4 of the metric catalogue naming programme, MR 7 of seven — THE LAST BATCH.** The seven
> player `goals` metrics: `goals` → `goals_player`, `assists` → `assists_player`, `goals_penalty` →
> `goals_penalty_player`, `scorer_points` → `scorer_points_player`, `goals_open_play` →
> `goals_open_play_player`, `penalty_won` → `penalty_won_player`, `contribution_share` →
> `contribution_player_pct`. PLAYER entity only. Branched from main `6f0ee07`.

diff_sha256: 0e995d62a43bac0f497c202c2bd4119d79ba614ef7457920dab314d6d835df32

rounds: 4

rounds_cap_override: The CPO authorised the fourth round explicitly. I brought the round-3 findings
to him rather than looping, recommended committing without a further pass, and offered the
alternative in these words: "The alternative is authorising one more scope-auditor pass on the
corrected log. That is the conservative call and I will run it if you want it." He replied, verbatim
and in full: **"do it"**. Round 4 is therefore a NARROW DELTA pass by `scope-auditor` alone, scoped
to one question — whether its own round-3 FAIL is properly fixed. No code, model, seed, doc or test
file changed between round 3 and round 4; the delta is `escalations.log`, `acceptance_evidence.md`,
`review.md` and `active_work.md` only.

⚠ **Round 4 was a NARROW DELTA pass by `scope-auditor` alone, authorised by the CPO past the cap of
3**, to check one thing: that its round-3 FAIL was properly fixed. It was asked for explicitly after
I recommended committing without it. **All five reviewers now PASS.**

⛔⛔ **ONE RULE SET THREE TIMES. ROUND 1 FAILED 5–0, ROUND 2 FAILED 4–1, ROUND 3 FAILED 4–1, ROUND 4
PASSED — AND EVERY GATE WAS GREEN AT ALL THREE FAILING STAGES.** `dbt parse`, both doc gates, the
resolver, the projection check, `pytest`, `npm test` and the site build passed with each defect in
the tree. **The blinded round was the only thing that found any of them**, which is now four MRs
running.

⭐⭐ **THE DEFECTS WERE ONE HABIT, NOT SIX BUGS: A SCOPE COARSER THAN THE ROLE IT HAD TO RESOLVE.**
`goals` and `assists` are ordinary English words as well as metric ids, and I mis-set the boundary
three times in a row:

1. **Too wide (round 1).** The sweep rewrote running prose — *"the club's WHOLE-SEASON
   goals_player"*, *"own goals_player"*, *"Involved in 45% of Bayern's goals_player"*. Because
   `+persist_docs` is on for every model, `int_player_profile.yml`'s model description would have
   shipped to BigQuery telling a stranger the club's season goal total is called `goals_player`.
   `int_player_profile__contribution`'s docstring said it BOTH ways in one paragraph — prose wrong,
   formula line beneath it right.
2. **Too narrow (round 1, same round).** My fix required the token to BE a whole backticked span,
   which left `` `mart_player_career.goals` ``, `` `goals − goals_penalty_player` `` and the
   `Atomics` column's `goals, assists` stale — the last two rows above ids `!130` had renamed.
3. **Right in tables, blind outside them (round 2).** Two SQL comments quoted the
   finishing-efficiency formula as `(goals − goals_penalty_player)` directly above code computing
   `(goals_player - goals_penalty_player)`.

⭐ **THE RULE THAT HOLDS IS ROLE, NOT PUNCTUATION**, in two reaches, each set from a census of the
whole tree rather than the sites a reviewer named:
  - **Inside a markdown table the COLUMN decides.** 16 distinct column headers, three roles —
    `Source column`/`Atomics`/`numerator`/`denominator` move; `Payload key`/`JSON key` stay (the
    CPO's ruling); everything else is prose. **51 in-table occurrences: exactly 6 move, 45 stay.**
  - **Outside one, an OPERAND is an identifier**: a token inside parentheses holding both an
    arithmetic operator and another underscored identifier. **26 comment occurrences: exactly 2
    move, 24 stay** — "own goals", "Penalty goals", `group=goals`, and an ORDER BY description over
    the PROVIDER columns `goals_total`/`goals_assists` all correctly left alone.
  - `{goals}` is excluded as a template slot, proved by its sibling row: `{won} of {total} · {pct}%`
    sits against atomics `duels_won_player, duels_player, duels_won_player_pct`. The slots were
    never the ids.
⭐ `11_team_squad.md:120` carries both rulings in one line and is right in both halves:
`` `squad[].goals` `` stays, `` `mart_player_career.goals_player` `` moves.

⛔ **A MACHINERY DEFECT COST A WHOLE ROUND, AND IT IS DISCLOSED RATHER THAN QUIETLY REPAIRED.** The
first round-2 attempt served all five reviewers a **STALE `review_input.patch`** — the round-1 diff.
`git_discipline.py --review-patch` PRINTS to stdout and builds from `git diff --staged <base>`, so
run bare with nothing staged it exits 0 and leaves the previous round's file on disk. Two reviewers
FAILed on defects fixed hours earlier, citing offsets that no longer existed; that attempt is void
and is not counted as a round. **The free tell is `--staged-hash` printing `e3b0c442…`, which is
`sha256("")`.** What resolved it in one step: `analytics-engineer`, reading the FILES, reported the
prose clean while `platform`, reading the PATCH, reported it corrupted — **two reviewers
contradicting each other on the same tokens means the artifact is wrong, not the code.**

⭐ **ONE PREDICTION WAS DISPROVED, AND THE CORRECTION IS THE INTERESTING HALF.** I predicted `goals`,
`goals_open_play` and `goals_penalty` would all leave the hygiene gate's ambiguous-name list, leaving
`league_code` alone. Measured base-vs-branch it goes **4 → 3**, not 4 → 1: `goals_open_play` leaves,
**`goals_penalty` does not, because it is also a PROVIDER leg column.** That is `!131`'s ruling
reproduced independently — **a rename frees a name from #87 only when no provider column shares it.**

## analytics-engineer-reviewer
VERDICT: PASS

**Round 1 FAIL** — prose corruption at `metrics_display.md:303` ("goals_player against", splitting the
team construct "goals against"), `:37-40`, `03_player_profile.md:118` and `mart_player_profile.sql:85,197`.
**Round 2 FAIL** — the two half-renamed formula comments at `int_player_season__metrics.sql:112` and
`int_player_season_position__metrics.sql:155`, each directly above code that got it right. Accepted in
full; fixed as `in_operand_position()` and censused across every comment line in the repo.
**Round 3 PASS.** Verified both findings fixed at the flagged lines with no collateral change, spot-checked
the 24 protected English comments, and re-checked catalogue governance and the consumption layer:
*"every changed row differs from base in `metric_id` only … payload keys stay, only warehouse-facing reads
and fixtures move; no derivation added."*

risks_checked:
- Both round-2 comment defects fixed exactly at the flagged lines, with no collateral change in the
  surrounding hunks; the code beneath each was already correct and is untouched by the delta.
- The `in_operand_position()` rule checked for OVER-reach: "own goals", "Penalty goals",
  `group=goals` and `mart_player_momentum.sql`'s ORDER BY comment all still read as English.
- Catalogue governance on `metric_catalogue.csv` — every changed row differs from base in `metric_id`
  only; the TEAM `goals`/`goals_against` rows untouched, consistent with the scoreline rule.
- Consumption layer: payload keys stay, only warehouse-facing reads and fixtures move; no new math,
  ranking or derivation introduced — still pure selection and rename.
- `mart_player_career.sql`'s `group=goals` correctly left unrenamed, confirming §9(b)'s fix held.

## bi-analyst-reviewer
VERDICT: PASS

**Round 1 FAIL** — the over-correction: `metrics_display.md:257`'s Atomics column unrenamed,
`11_team_squad.md:120-121` stale, `12_player_stats.md:142` half-renamed. This is the finding that
proved the backtick alone cannot decide, and it drove the column-role rule.
**Round 2 PASS. Round 3 PASS**, re-verified after the whole sweep was re-applied from base:
*"the payload keys `squad[].goals`/`squad[].assists` are still byte-identical (stay), while the
identifier column moved … both halves correct together on the same line."* Confirmed zero
`site_v2/` and `site/i18n/` hunks, and traced `_LEADERBOARD_METRICS` as the distinct already-ruled
§7 case rather than a contradiction of the payload rule.

risks_checked:
- All three round-2 identifier sites re-verified after the full re-apply from base, in BOTH
  directions: `11_team_squad.md:120-121` (payload key stays, source column moves — both halves right
  on one line), `metrics_display.md:257` (Atomics moves, `{goals}` template slot stays),
  `12_player_stats.md:142` (numerator operands both moved).
- Every wireframe touched by the MR swept for the reverse defect — an English-prose occurrence
  wrongly renamed: none found.
- The team scoreline family byte-identical everywhere it sits adjacent to a renamed player token.
- Zero `site_v2/src/**` and `site/i18n/` hunks, traced by reading each swept-but-protected frontend
  file's actual field reads against the mart and export diffs rather than trusting the contract.
- `rendered_page_evidence.md` read as evidence, not paperwork: built from `dist/`, states its method,
  and honestly scopes what the comparison can and cannot prove.

## football-analytics-expert-reviewer
VERDICT: PASS

**Round 1 FAIL**, two findings. The second is the one that mattered and it was about the record, not
the code: **the `contribution_player_pct` caveat I was carrying had already been DISCHARGED.**
`escalations.log`, 2026-08-29, records *"RULING, verbatim: 'contribution_player_pct is fine, go with
it'"* and states the older *"flag it rather than quote it as his"* warning "does not need to travel
further". I had repeated it in the contract, the evidence and the log entry. Corrected in all three.
**Round 2 PASS. Round 3 PASS**, re-verifying the seed is `metric_id`-only after the re-apply and
judging the corrected formula football-correct: *"All three operands are player-grain columns — no
team or provider-leg column is mixed in."*

risks_checked:
- The two corrected comments re-read against the code three lines beneath each — no half-renamed
  operand remains in either.
- Football correctness of the corrected formula: `goals_player` (own goals already excluded) minus
  `goals_penalty_player`, over that same player's `shots_on_goal_player`, is a standard open-play
  conversion rate at player grain; the `< 0` / `> shots_on_goal_player` guards preserve the
  never-above-100% honesty the catalogue enforces elsewhere.
- The seed re-checked after the full re-apply: all seven rows differ in `metric_id` only — label,
  description, base_relation, numerator/denominator, direction and interpretation byte-identical.
- The `contribution_player_pct` authority re-verified directly in `escalations.log`: the 2026-08-29
  verbatim ruling and its explicit discharge, now cited correctly in both contract and log.
- Surrounding hunks in both changed SQL files swept to confirm the fixes are isolated single-line
  changes with no new token, no new formula and no scope creep.

## platform-reviewer
VERDICT: PASS

**Round 1 FAIL** — the persisted-documentation instance of the prose defect across
`int_player_profile.yml`, `int_player_profile__contribution.sql` and `mart_player_profile.sql`.
**Round 2 PASS**, with the observation that pins §9(c): *"reverting `career.get("goals_player")` back
to `career.get("goals")` would make these assertions fail (fixtures no longer carry a `"goals"` key),
so the changed behaviour is exercised, not just renamed in lockstep."*
**Round 3 PASS.** Confirmed no hook, CI file, dependency manifest or build/hosting config is touched;
grepped the LIVE tree (not the patch) for any remaining half-renamed formula comment — zero hits.
⚠ It flagged, correctly, that two gate results were left as "see below" placeholders in the evidence.
Filled in: `pytest` **1009 passed / 1 skipped / 14 subtests**, `sqlfluff` **byte-identical** to base.

risks_checked:
- No file under `.claude/hooks/`, `.github/workflows/`, `.gitlab-ci.yml`, any `*requirements*.txt`,
  `package*.json`, or the site build/hosting config appears in the changed-file list at all.
- Both corrected comment lines read in the cumulative diff and confirmed to match the code beneath.
- Line length: `.sqlfluff` sets `max_line_length = 120`; the lengthened comment measures ~106 with
  indent, and the byte-identical lint result confirms no rule newly trips.
- The LIVE `dbt_project/` tree grepped — not just the patch — for any remaining half-renamed formula
  comment: zero hits, so the fix landed in the actual files.
- `tests/test_export_site_data.py` read directly: fixture inputs renamed, output assertions kept on
  the payload key, so reverting the export would make the assertions FAIL — the behaviour is
  exercised, not renamed in lockstep.
- `_LEADERBOARD_METRICS`/`_LB_KEEP` still pinned by no test — carried as the disclosed #99 gap, not a
  new defect.
- ⚠ Its one process note, recorded rather than waved away: it could not itself execute `sqlfluff`, so
  its line-length check was a manual character count against the stated rule, not an executed run.
  The executed run is mine, reported in `acceptance_evidence.md`.

## scope-auditor
VERDICT: PASS

**Round 1 FAIL** — the prose corruption in `int_player_profile.yml`'s model description and
`int_player_profile__contribution.sql`, i.e. the `persist_docs` hazard.
**Round 2 (void attempt) FAIL** — and it was RIGHT for a reason I had not considered: it refused to
certify a diff whose authority record it could prove stale from the same artifact set. That is what
exposed the stale-patch defect above.
**Round 2 PASS** on the correct patch, having verified both round-1 defect classes and all four §9
fixes directly against the artifacts rather than the narration.
**Round 3 FAIL — accepted in full, and it is the most uncomfortable finding of the three rounds.**
My `escalations.log` entry still carried the ROUND-1 counts ("442 renamed, 1,077 protected", "70
`doc()` re-points, 20 TEAM-side") while the contract carried the corrected ones — in the append-only
record other work cites as ground truth. **This is `feedback_corrections_replace` again: I fixed the
numbers where I remembered changing them and left them standing where I did not.** The fix applied is
the one that memory prescribes — extract EVERY number in the document and ask of each whether it is
still true — which caught a third stale figure the reviewer never named ("nine" → **eleven**
round-1 defect strings verified absent). A cross-document sweep over all five artifacts now returns
**zero** unexplained stale figures; the four remaining hits are labelled historical citations.

**Round 4 PASS** — the CPO-authorised delta pass on the corrected log. It confirmed the nine headline
figures agree across contract, evidence and log; that the third stale figure is gone with no orphan
left anywhere in the five artifacts; that the two placeholder gate lines are filled with real
results; and that `active_work.md` no longer claims step 4 complete. It also checked the thing worth
checking most: *"the correction is honestly recorded, not quietly made — the log entry names the
stale figures verbatim, states they are the round-1 numbers superseded by §9(d)/(e), states they were
corrected in contract/evidence but left standing in the log, and names me as the reviewer who FAILed
it in round 3."*

risks_checked:
- The nine headline figures cross-checked across `contract.md`, the `escalations.log` MR-7 entry and
  `acceptance_evidence.md` — all three agree on the shipped round-3 counts.
- The correction verified as honestly recorded rather than quietly made: the log names the stale
  figures verbatim, says which rules superseded them, admits they were fixed elsewhere and left
  standing there, and names the reviewer who caught it.
- The third stale figure hunted specifically: only the corrected "eleven round-1 defect strings"
  remains, matching the evidence; no orphaned "nine" anywhere in the five artifacts.
- Every remaining occurrence of "442 renamed", "1,077 protected", "70 re-points", "20 TEAM-side"
  checked and found to be a labelled historical citation, not a live claim.
- The two previously-placeholder gate lines confirmed filled with real results matching what
  `platform-reviewer` flagged.
- `active_work.md` confirmed no longer claiming step 4 complete — it states the MR is built and
  reviewed but NOT committed, and defers the commit decision to the CPO.
- Earlier rounds: `scope_paths` reconciled exactly against the changed file set; both round-1 defect
  classes verified fixed directly in the artifacts rather than the narration; all four §9 fixes
  confirmed present in the files, not merely asserted.

## escalations

**None raised.** The one §10-adjacent question — whether the published payload key follows the
warehouse column — was ruled by the CPO in this session: *"Naming conventions in the warehouse are
one thing. What we show on the website is another."* Implemented asymmetrically on all four lines,
and that asymmetry is what let `pytest` catch a real rule inversion (§9(c)).

⛔ **CARRIED, NOT CLOSED, AND THE CPO'S:** the `__team`/`__player` doc-block split has **no live
instance** after this MR — all six dual-entity ids are renamed. Nothing was removed or weakened;
`_derived()` still suffixes unconditionally, `_blocks()` still splits and still aborts, and the
synthetic fixtures stay. One new seed row recreates the collision. Whether a guard with no live
instance should remain is his call. Also carried: the resolver as a committed CI gate; **#99**
(the export's literal board keys moved here and remain pinned by no test); **#96**; **#87**; **#98**.
