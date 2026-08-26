# Review — feat/catalogue-team-totals-and-counts — 2026-08-26

diff_sha256: 735de4656ab143501e31496f403ace835e214f745571a0f9dcc0b94984086f9a

rounds: 5

rounds_cap_override: CPO, 2026-08-26, verbatim: "commit it once they pass" — recorded in
`.claude/task/escalations.log` under the 2026-08-26 entry, which is the only place a CPO ruling
counts. Each round past the cap found a REAL defect and each fix changed the artifact under
review, so a reviewer that failed had not yet seen the version being shipped; that is a re-read,
not a fourth opinion on the same question.
⚠ THE OVERRIDE ITSELF WAS THE FOURTH INSTANCE OF THIS TASK'S ONE RECURRING DEFECT — it cited an
authority that existed only in prose. Caught by scope-auditor round 4. See the log entry.

⛔ ROUND 1 RETURNED THREE FAILS OUT OF FOUR, and the two that matter were both mistakes I had
already written down. The contract cited `escalations.log` for the CPO's rulings and the log was
empty. And four of the five new metric names are names the PREVIOUS merge deliberately left blank
as "one word, two quantities" — giving them a catalogue row silently re-armed the generator, and
a per-match sentence landed on 18 cumulative columns. Both fixed; see the amendments.

⚠ THIS IS A DIFFERENT CHANGE FROM THE ONE FOUR REVIEWERS SAW. That round ran against NINE seed
rows and returned two PASS and two FAIL, both FAILs on one field — the `direction` of a `draws`
row. Two CPO rulings then cut the MR to FIVE rows, and `draws` no longer exists. **Nothing from
that round carries over; every verdict below is fresh.**

WHAT CHANGED AND WHY IT SHRANK:
  · CPO, "win, draw, loss are not metrics. they are results of a match." Removing those three rows
    removed the whole cascade they caused — 3 docs-block name collisions, a hard `dbt parse`
    failure, the `standings_wins/draws/losses` rename and 6 repoints. `shared_columns.md` is now
    untouched and all 24 references to those blocks stay as they were. 16 files → 14.
  · CPO, "use clean_sheets (for the number of matches with clean sheets) and clean_sheets_share
    (for the percentage)." That renames a metric that already ships, so it is its own MR.

⚠ THE PART THAT REACHES THE WAREHOUSE AND NO TEST CAN CHECK: 20 `goals_against` references were
each classified `__team` or `__player` by reading the expression in that model's own SQL. Twelve
TEAM columns carry the PLAYER definition in BigQuery today — that is the defect this fixes, and a
misclassification would replace one wrong sentence with another.

⚠ THREE OF THE GUARDS THAT WOULD CATCH A BAD ROW CANNOT RUN HERE, and would not see these rows on
an MR even with a warehouse (`--defer --favor-state` resolves `ref('metric_catalogue')` to main's
seed). Every predicate was re-implemented offline instead; the evidence records it.

## analytics-engineer-reviewer
VERDICT: PASS (round 2)
risks_checked:
- ⛔ ROUND 1 FAIL, and the most serious finding of the task. The five new descriptions were phrased
  as single-match facts ("Present on every finished match") and `--wire-shared-docs` pointed them
  at 18 columns that are NOT per-match values: cumulative sums
  (`int_team_season_record.sql:100-101,129,132,136`), form-window sums
  (`int_team_momentum__metrics.sql:61-62,76,79,81`) and all-time sums
  (`mart_head_to_head.sql:82-83`).
- ⛔ IT FOUND THE PRECEDENT I HAD DELETED. Four of the five names — `goals_for`, `corner_kicks`,
  `shots_inside_box`, `goalkeeper_saves` — are among the thirteen the PREVIOUS merge left blank as
  "one word, two quantities", and it found that text in the patch's own deleted lines. This
  contract never mentioned, let alone overturned, that precedent. Giving a multi-grain name a
  catalogue row silently re-arms the generator against it; that is the lesson, not "check grain".
- ROUND 2 PASS. It re-derived the fix at all 30 sites and verified the claim the fix RESTS on
  rather than accepting it: that each model's own yml description states its grain, so the
  catalogue-says-what / model-says-span split actually holds in the warehouse. It quoted the grain
  sentence from `int_legs.yml:6-9`, `int_season_record.yml:6-9`, `mart_team_profile` and
  `mart_head_to_head` to prove it.
- It checked "understates rather than nulls" against the SQL rather than the contract's assertion:
  `int_team_season_record.sql:129,132,136` and `int_team_momentum__metrics.sql:76,79,81` are plain
  ungated `sum()`, so a NULL leg is dropped from the total.
- ⭐ AND IT CONFIRMED A DETAIL I HAD RIGHT WITHOUT SAYING WHY: `goals_for`/`goals_against` carry no
  missing-data caveat because `int_legs__team_match.sql:69-72,94-97` filters to a non-null
  scoreline — the caveat would be FALSE on those two.
- Re-counted the wiring site by site: `goals_for` x12, the other three x6 each, `goals_against`
  12 team / 8 player. Confirmed only `mart_head_to_head.sql` changed and it is comment-only.

## football-analytics-expert-reviewer
VERDICT: PASS (round 1)
risks_checked:
- `goals_against` (team): `int_legs__team_match.sql:61-62` and `:86-87` confirm the leg column is
  genuinely the OPPONENT's score on both branches, and `direction`/`lower_is_better` are in
  lockstep with it.
- The scoreline provenance claim traced the whole way: `goals_home`/`goals_away` through
  `fct_fixture.sql:26-27` to `stg_apif__fixtures_next.sql:41-42` (`$.goals.*`), which is the
  post-extra-time score and a distinct field from the shootout score. It added the football
  reasoning I had not stated: a `PEN` match uses the pre-shootout count, **which is correct
  because a shootout does not add goals.**
- `goalkeeper_saves` vs the player `saves`: different entities, different feeds, confirmed to
  `base_apif__fixture_statistics.sql:50-51` (`'Goalkeeper Saves'`) versus the player stats table.
  ⭐ It found corroboration I had missed — `save_ratio` ALREADY uses `sum(goalkeeper_saves)` as its
  numerator, so the new row is the first to expose that same numerator as a standalone total,
  which is the opposite of a duplicate.
- `shots_inside_box`: `danger_zone_ratio` at `metric_catalogue.csv:12` has exactly
  `sum(shots_inside_box)` as its numerator — the claim is an exact match, not an approximation.
- `corner_kicks` won-vs-conceded settled from the grain: `int_legs__team_match.sql:133-136` joins
  `own.corner_kicks` against `opp.corner_kicks as opponent_corner_kicks`, so "won by the team" is
  right and consistent with the existing per-match pair.
- `format: integer` with a blank denominator: checked against `schema.yml:283-284,309-312`, where
  `count_fraction` is documented as a count of games. All five totals routinely exceed games
  played, so `count_fraction` would be a real misrepresentation.
- `importance_tier` against the written rubric: `corner_kicks` at 2 sits one tier above its own
  `corner_kicks_per_match` at 3, exactly as the rubric requires; `shots_inside_box` at 3 is a
  breakdown. No mismatch.
- 8 of the 20 `goals_against` repoints re-derived by reading each model's SQL and grain rather
  than its name, including both counter-intuitive ones. All correct.
- `mart_head_to_head.sql`: both halves of the new comment verified against the SQL — `:79-81` is a
  categorical `countif(result = ...)` tally, `:82-83` is the catalogue's own numerator over the
  H2H window. Comment-only confirmed.
- ⛔ IT CHECKED THE CPO QUOTES AGAINST THE LOG, at `escalations.log:5170-5258`, and found them
  verbatim — the scope-auditor's FAIL is closed. ⚠ It noted the `clean_sheets` quote in
  `contract.md` is TRIMMED against the log's fuller wording. Not misleading, but a quote presented
  as verbatim should be verbatim; corrected.

## bi-analyst-reviewer
VERDICT: PASS (round 3)
risks_checked:
- ROUND 3 PASS, and it earned it by attacking the fix rather than accepting it. It re-derived the
  pattern from scratch over all 85 rows — 16 count-versus-rate pairs, not the seven the contract
  names — and confirmed the tie is gone with spacing of exactly 1 everywhere, zero ties.
- ⭐ IT RAISED THE INVERSION ITSELF, before finding the justification, and treated it as a live
  candidate finding: `goals_for`/`goals_against` at 2 are the only pairs where the RATE is more
  prominent than the total. It then established the constraint is structural rather than taste —
  `goals_per_match` / `goals_against_per_match` are genuinely LOCKED at tier 1 by the CPO-ruled
  team table (`docs/wireframes/metrics_display.md:8,133-134`), which is the ceiling, so "one
  above" does not exist. Of the three legal values: 1 is empirically refuted by its own round-2
  survey, 3 plainly does not fit a core scoreline count beside real breakdowns
  (`goals_penalty`/`goals_own`/`goals_open_play`), leaving 2 by ELIMINATION rather than choice.
  ⭐ And it noted `corner_kicks`(2)/`corner_kicks_per_match`(3) — added in this same commit —
  follows the ordinary direction precisely BECAUSE its rate is not locked at 1, which confirms the
  ceiling-lock is what drives the one exception rather than a new inconsistent rule.
- ⭐ IT FOUND A CONSISTENCY THE OLD VALUE DID NOT HAVE, which I had not seen: `goalkeeper_saves`(2),
  `goals_against`(2) and `save_ratio`(2) now sit together — and `save_ratio`'s denominator is
  literally `sum(goalkeeper_saves + goals_against)` (`metric_catalogue.csv:28`). A full
  percentage-of-attempts triple, matching the player-side `saves`/`shots_on_goal_against`/
  `save_pct` precedent one rung down.
- It ran the mechanical denominator test against EVERY percent-format row, not the named seven, and
  it reproduces every relationship — including the non-obvious `points_capture`, which is
  `format: percent` but has denominator `3 * count(*)` and is correctly bucketed as an exposure
  rate rather than a tie.
- ⚠ ONE PRE-EXISTING WRINKLE REPORTED HONESTLY AND LEFT ALONE: `finishing_efficiency`'s own
  numerator and denominator components (`goals_open_play` at 3, `shots_on_goal` at 1) do not share
  a tier with each other or with the ratio, on both team and player rows. It predates this branch
  and is out of scope for this delta. Worth an issue.
- Confirmed no `site_v2/src/**` or `site/i18n/**` file is touched and none of the five ids appears
  in the locked 16-row team table, so there is no rendering consequence today.
- ROUND 1 AND 2 FINDINGS, kept because the cause outlives the fix:
- ROUND 1 FAIL: the `importance_tier` of the new `goals_for`/`goals_against` rows was an
  undeclared judgement in a column the CPO's 2026-08-04 override made a product decision. It also
  closed the risk I was most worried about — `count_fraction` with a blank `denominator_expr` —
  by tracing `countFraction()` in `site_v2/src/lib/format.ts:41-60` and establishing the fraction
  is assembled from a component-level `denom` mapping, not from the CSV, with `points_won` as the
  exact precedent. No defect there.
- ⛔ ROUND 2 FAIL, and the argument was empirical rather than interpretive, which is why it stuck.
  It tabulated EVERY count-versus-rate pair in all 85 rows: 13 player total/per-90 pairs,
  `points_won`/`points_capture`, and `corner_kicks`/`corner_kicks_per_match` **in this same
  commit** — all one tier apart. My `goals_for`/`goals_against` tie at 1 was the SOLE exception in
  the file. It also showed exactly where my reading broke: the tying clause says "raw counts and
  their headline PERCENTAGE", every percentage-tie precedent is `format: percent` over a sum of
  attempts, and `goals_per_match` is `decimal_1` over `count(*)` — an exposure rate, the same
  shape as a per-90, which the rubric's own worked example puts one tier below its total.
- ⛔ THE LESSON IS ABOUT MY FIRST FIX, NOT THE DEFECT. Round 1 said "the tier is undeclared"; I
  declared it and left the value alone. Declaring a wrong value is not a fix, and the reviewer had
  to return with the survey I should have run myself.
  FIXED: both rows moved to tier 2, and BUILDER'S CALL 4 now states the mechanical test — the
  DENOMINATOR — that decides which clause applies, re-derived across all seven pairs.
- ⚠ THE FIX MAY TRADE ONE EXCEPTION FOR ANOTHER and round 3 is asked that directly: at tier 2 the
  goals pair is one apart but INVERTED, the rate sitting above the total, which no other pair
  does. It is forced — `goals_per_match` is locked at tier 1 by the display table so "one above"
  is not expressible — but forced is not the same as right.
- It also confirmed no frontend change is required: none of the five ids is in `metricRows.ts`,
  and `check-metric-labels.test.mjs` only asks for keys a component requests.

## scope-auditor
VERDICT: PASS (round 5)
risks_checked:
- ROUND 5 PASS. It verified both round-4 fixes landed: the CPO quote is verbatim at
  `escalations.log:5259` and `review.md:7-8` cites it rather than asserting it.
- ⭐ IT RE-DERIVED 229/24 BY A DIFFERENT METHOD THAN MINE and got the same answer. I used
  `git diff --numstat`; it had no shell this session, so it reconstructed from the patch's own
  `@@` hunk headers — total additions minus the two governance files — landing on exactly
  +229/-24 for the 14 code and doc files. It also confirmed 225 survives nowhere as a live claim,
  only in the log's note explaining why it was corrected.
- Every remaining integer re-derived from the tree by grep rather than accepted: 85 seed rows,
  181 blocks, 20 references at 12 team / 8 player, 30 wired columns broken down per file, and all
  five tier values against BUILDER'S CALL 4.
- `decisions_reserved` checked item by item against the shipped seed: no `clean_sheets_share` row,
  no W/D/L rows, no team totals for the four deferred names. The pre-existing `clean_sheets` row
  is untouched, `count_fraction` intact.
- Scope, comment-only `.sql`, credentials sweep, and both threshold declarations all clean.
- ⚠ ONE THING IT COULD NOT VERIFY AND SAID SO RATHER THAN GUESSING: the handover's
  16,000-character cap, because its session had no shell and grep cannot count characters. It
  flagged the tooling gap instead of manufacturing a verdict, and noted the cap is separately
  machine-enforced. Measured here with Python `len()`: **15,968**.
- ⛔ ROUND 4 FAIL, kept because the cause outlives the fix:
- ⛔ ROUND 4 FAIL, THE SAME CLASS A FOURTH TIME, and this time in the field whose entire job is to
  carry an authority: `rounds_cap_override` quoted the CPO's "commit it once they pass" while
  `escalations.log` contained no such line. It established that every prior cap override in this
  repo's history was logged (`escalations.log:376`, `:2173`, `:2199`, `:3915`) and that
  `ROUND_CAP = 3` is itself recorded at `:333`. FIXED: the instruction is now in the log with the
  three earlier instances named beside it, so the pattern is recorded where the next task reads.
- ⚠ IT ALSO CAUGHT A STALE FIGURE THE WAY STALE FIGURES SHOULD BE CAUGHT — by reconstructing the
  added-line count by hand, landing at ~218-220 against a claimed 225, and REPORTING THE GAP AS
  UNRESOLVED rather than asserting either number. Re-derived: the true figure is **229**; 225 was
  correct two revisions ago and went stale when the descriptions were rewritten grain-free.
  Corrected in the evidence and the log. Had it asserted its own number instead of flagging the
  discrepancy, the real one would still be wrong.
- Everything else clean and independently re-derived: 85 seed rows by line count, 181 blocks by
  grep, 30 wired sites counted per name, the 12/8 `goals_against` split, all five tier values
  against BUILDER'S CALL 4's stated rule, 24 deletions reconstructed hunk by hunk, 16 patch files
  inside `scope_paths`, `mart_head_to_head.sql` comment-only, and no `decisions_reserved` item
  shipping as a concrete value. It also confirmed `contract.md`'s amendments and `review.md`'s
  per-reviewer sections no longer contradict each other.
- ⛔ ROUND 3 FAIL, AND IT IS THE SAME CLASS FOR THE THIRD TIME IN ONE MR. `review.md` still carried
  round-1 state — two reviewers "pending", scope-auditor "FAIL (round 1)" — while `contract.md`'s
  amendments narrated round 2 in detail. So **the machine-parsed governance file did not
  corroborate the review history the contract claimed**, and a `rounds_cap_override` resting on
  "each round found a real defect" was unverifiable against the durable record.
  Its words: exactly the self-certification risk round 1 was failed for, applied to a different
  artifact. ⛔ THE PATTERN IS MINE AND IT IS NOW THREE FOR THREE — I narrate a verdict in prose and
  do not write it into the record that is actually parsed. Round 1 it was `escalations.log`;
  round 3 it is `review.md`. FIXED: every round for every reviewer is now written here.
- ROUND 2 FAIL: BUILDER'S CALL 4 declared tiers for four of the five rows and never mentioned
  `goalkeeper_saves` — the same defect it had just failed, 80% remediated. Its tier 2 is right (a
  percentage pair with `save_ratio`, so it ties) but nothing said so. Now stated.
- ⚠ IT ANSWERED THE HARDER QUESTION I PUT TO IT — whether a self-authored, after-the-fact
  `escalations.log` entry merely relocates the self-certification. Judged ACCEPTABLE: the entry
  discloses its own timing on its face rather than in a chat message, is append-only under the
  same mechanism as every other ruling, was independently cross-read by another reviewer against
  the file, and records the CPO CORRECTING me plus a claim of mine withdrawn — "not the shape of a
  fabricated self-serving record".
- Re-derived from the tree across rounds: 85 seed rows, all five tiers matching BUILDER'S CALL 4
  including `goalkeeper_saves`, no `label_i18n_key` or `(entity, label_en)` collision, the 12/8
  `goals_against` split, 30 wiring lines, the block delta as 1 split plus 19 new = +20, and 16
  patch files matching `scope_paths`. `mart_head_to_head.sql` comment-only, verified line by line.
- Every `decisions_reserved` item checked against the diff: none ships as a concrete value.
- ROUND 1 FINDINGS, kept because the cause outlives the fix:
- ⛔ ROUND 1 FAIL, and it is the sharpest finding of this task. `contract.md` cited
  `.claude/task/escalations.log` as recording the CPO's two rulings — the sole authority for
  removing §10 metric-definition decisions — and **the log held nothing**. It read the file end to
  end (5,168 lines, last entry 2026-08-25), confirmed neither ruling nor any 2026-08-26 entry
  existed, and confirmed `escalations.log` was in `scope_paths` yet carried zero changes in the
  patch while NOT being on the patch's declared exclusion list. Its words: a contract citing an
  authority record that does not corroborate it.
- ⛔ THIS IS THE SAME CLASS AS THE ERROR EARLIER THE SAME DAY, in a different form. Then I said
  "you ruled" about something from a seed description. Here I cited the right source and never
  populated it. Both make a claim about authority that cannot be checked.
  FIXED: the rulings are now in the log, verbatim, with the whole task's findings —
  and the entry states plainly that it was written the same day but AFTER the fact, so the
  disclosure travels with the record rather than sitting in a message. 89 lines, append-only.
- Scope: all 14 changed files match `scope_paths`; `mart_head_to_head.sql` confirmed comment-only,
  no executable line changed.
- Seed re-derived from the file itself: 86 lines = 1 header + 85 data rows, the 5 new rows all
  `entity=team`, "80 → 85" holds.
- ⛔ CHECKED FOR THE DEFECT THAT FAILED THE PREVIOUS ROUND and found none: the `clean_sheets` item
  is genuinely deferred — no `clean_sheets`/`clean_sheets_share` row among the 5, and no W/D/L row.
  Nothing sits in `decisions_reserved` while shipping as a concrete value.

## escalations
- none yet
