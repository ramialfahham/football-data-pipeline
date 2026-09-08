# Acceptance evidence — restructure docs/metric_layer.md and correct what is false in it

Branch `docs/incomplete-data-rule-in-the-metric-doc`, from main `2708dff`.

criteria_demonstrated:

  - **The lookup table is first, and every row resolves.** No prose above it. Rows point at a file or
    an in-document anchor; the backward-pointing *"the section above"* row is gone. Checked by
    parsing the file: 4 anchors used, 4 resolve to real `##` headings, **0 broken**.

  - **Section order now follows the reader, not the author.** Where each thing lives → the NULL rule
    → how the layer works → adding a metric → what the guards enforce → what this is NOT.
    `## Adding or changing a metric` was 6th of 7 and is now 4th of 6, directly after the mechanism
    it depends on — it is the reader's primary action.

  - **The NULL rule keeps its prominence without opening the document.** It sits second, above every
    mechanism section, and is now reachable by a router row that names it (*"why a metric column is
    NULL"*). That is strictly more discoverable than before, when the only pointer to it read "the
    section above".

  - **Eight factual errors corrected. Each verified against the tree or prod by me, not taken from
    the structural review:**

        claim in the old doc                          | verified against                        | was
        ----------------------------------------------|-----------------------------------------|-----
        2 canonical models                            | drift guard scans 3                     | WRONG
        seed columns (listed twice, lists disagreed)   | the CSV header, 15 columns              | WRONG
        `group_display_order` is a seed column         | absent from the header                  | WRONG
        "no `metric_kind` taxonomy"                    | `computation_kind`, 4 values            | WRONG
        "no binding-map"                               | `base_relation` + expr cols + a guard    | WRONG
        1 guard named                                  | 5 catalogue guards exist                | WRONG
        finishing efficiency "uncapped"                | `int_team_season.yml:53` asserts 0-1     | WRONG
        `points_won` "not in the canonical models"     | `..._cumulative.sql:47` — it is          | WRONG

  - **⛔ AND I REINTRODUCED THE SAME DEFECT ONE LINE BELOW THE FIX.** Having corrected the
    canonical-model table, I wrote *"a player metric is added to the atoms model"* — which is false
    for most of the player catalogue. `int_player_club_season__metrics`'s own docstring says atoms
    are the SUMMABLE counts only, and that *"ratios / per-90 / count composites are NOT here: they
    are non-summable, so they are derived where consumed"*. Verified: every `_pct`, `_per90` and
    composite player metric is computed in `int_player_season__metrics`, the composing model. So the
    sentence meant to stop an engineer editing the wrong model sent them to the wrong model for the
    majority of cases. Caught by `analytics-engineer-reviewer`; corrected to split summable counts
    (atoms) from non-summable ratios and per-90s (composed where consumed).
    ⚠ The lesson is narrow and worth keeping: I fixed the TABLE from the review's finding and then
    wrote fresh guidance underneath it from memory, without opening the atoms model. Same root cause
    as the errors being corrected.

    ⭐ The canonical-model error is the one that mattered: `int_player_club_season__metrics` is the
    ATOMS source that `int_player_season__metrics` and `mart_player_career` both compose. The old
    text named only the composing model, so an engineer following *"add the computation to the
    canonical model (one place)"* for a player metric would have edited the wrong one and started
    the divergent rollup the sentence exists to prevent.

  - **`## Scope / follow-ups` is cut** — issue status in an authoritative doc, and already rotted:
    it listed `#500` as outstanding while the drift guard's own docstring says #500 Stage 2 shipped.

  - **`CLAUDE.md` gains a row.** Verified absent before the change (`grep -c metric_layer CLAUDE.md`
    = 0), so the document whose job is to be the map could not be reached from the front door.

  - **No provenance in the document.** No dates, no CPO quotes, no history, no lecture to future
    readers. That is what the first attempt got wrong, and the correction is the whole point of the
    ledger/lookup split: `escalations.log` records when and why, the doc says only what is true.

## The finishing-efficiency caveat, corrected on instruction

`metrics_display.md` said finishing efficiency *"can exceed 100% (penalties/own goals counted as
goals but not always as shots); the true value is always shown, never capped"*. Both halves are
false as shipped:

  - **The cause named is gone from the formula.** Since `!156` the numerator is open-play goals —
    `goals_for - goals_penalty - goals_own` — so penalties and own goals are already excluded.
  - **A value above 1 is never shown.** `int_team_season__metrics_cumulative.sql:147` NULLs it when
    `goals_open_play_in_sot_games > shots_on_goal`, and `int_team_season.yml:53` asserts
    `between 0 and 1`. Measured on prod: **0 of 4,999 non-null rows above 1, maximum exactly 1.0.**

⭐ The seed already says it correctly — *"In [0, 1] - penalties and own goals are excluded because
they are not finishing the team's own on-target shots"* — and the seed is the SSoT for glossary text.
So the display doc's rationale paragraph was simply left behind when the formula changed. It now
matches the seed and the test.

⚠ **Only the factual sentence changed.** The section is CPO-LOCKED, and what is locked is the DESIGN
— the shooting funnel and its row order — which is untouched.

⭐ **Swept for the same stale claim elsewhere:** `grep -rn "exceed 100%\|never capped"` across `docs/`
and `site_v2/src` returns nothing else. One instance, one fix.

## What this does NOT do

- **No computed number moves.** Documentation only — no model, seed, test, script or site file.
- **`metrics_context_model.md` §8.1** still restates the player half of the NULL rule in its own
  words and should defer here instead. Outside `scope_paths`; recorded, not touched.
