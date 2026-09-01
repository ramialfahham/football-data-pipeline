# Acceptance evidence — the seed's prose follows the label, where the whole ROW can follow

Branch `refactor/seed-prose-on-goal`, from main `89b8c01`. **Round 2** — round 1 FAILed and the rule
was rebuilt, not patched.

Step 5 (`!134`) moved nine `label_en` values to "on goal" and left the prose, so BigQuery shows a
column **labelled** "Shots on goal" and **described** as "Shots on target." — one thing, two
vocabularies, both published by `+persist_docs`. This closes that gap on the rows where it can be
closed completely.

**Seed prose only. No model, macro, test or label changed.** `metric_columns.md` is REGENERATED.

criteria_demonstrated:

  - ⭐⭐ **NO ROW IS MADE WORSE — this is the criterion round 1 did not have, and it is the one that
    matters.** Measured on the ACTUAL files, base vs head, across `label_en` + `description` +
    `interpretation`: **rows split on main 9, on head 7 — 2 FIXED, 0 NEWLY SPLIT.** Every row this
    MR writes ends fully self-consistent. The measurement is deliberately not a simulation of the
    sweep rule: the rule is what is being judged, so it must not also be the judge.
  - ⛔⛔ **ROUND 1 FAILED, TWICE, INDEPENDENTLY, AND BOTH REVIEWERS WERE RIGHT.** The rule was
    per-CELL: convert a cell if every occurrence in it is movable. That moved whichever column
    happened to hold a convertible phrase and froze its sibling — producing rows that read "on goal"
    in the label, "on goal" in the description and "on target" in the interpretation.
    **That is not an approximation of the CPO's ruling; it is the literal state he named as his
    reason for widening this sweep to two columns.** `scope-auditor` found it on `shots_on_goal_pct`;
    `analytics-engineer` independently measured **7 rows** where two previously-agreeing columns
    were made to disagree, and traced it to a live artifact — `fetch_glossary()`
    (`scripts/export_site_data.py:1296`) serialises `description` and `interpretation` side by side
    into `metrics.json`, so the disagreement would have shipped verbatim.
  - **The fix was to change the UNIT, not to add an exception.** A row's cells are now written only
    if the row ends fully consistent; otherwise nothing on that row is touched. A partly-converted
    ROW is worse than an unconverted one, for the same reason a partly-converted cell is — which is
    the rule the contract already had one level down.
  - **The cost of that fix is stated, not hidden: the sweep shrank from 12 substitutions to 5.**
    `shots_on_goal_pct`, `saves_player`, `saves_player_pct`, `shots_on_goal_per90` — 4 rows, 5 cells.
    ⚠ **And it means this MR does NOT fix its own headline example.** `shots_on_goal_player` still
    reads label "Shots on goal" / description "Shots on target.", because its interpretation says
    "On-target threat" and moving the description alone is precisely the defect above.
  - ⛔ **ONE CPO COPY DECISION UNBLOCKS THE OTHER 7 ROWS — with the inventory DERIVED, after the
    memory-written one FAILed round 2.** `scope-auditor` FAILed it and `football-analytics-expert`
    flagged the same thing independently: my list claimed the named phrases made "all 7 rows
    convertible", said every block sat in the `interpretation`, and included `deserved_points`,
    which **is not split at all** (its `label_en` never carried the phrase). Extracted from the seed
    instead: **«on-target shots» 4 sites · «on-target threat» 3 · «on-target dominance» 1 ·
    «on target for − against» 1.** Deciding the first three frees **6 of 7**; the fourth frees
    `shots_on_goal_difference_per_match`. ⚠ **Two of the seven are blocked in their DESCRIPTION**
    ("not finishing the team's/player's own on-target shots"), not their interpretation — the exact
    detail the memory-written version got wrong. **"On-goal threat" is not a football phrase, and
    there is no "off-goal" the way there is "off-target".** Rewording is writing, not renaming, and
    `scripts/check_copy_gate.py` reserves it permanently.
  - ⚠ **Three further rows are held but are NOT split and are not debt**: `saves_pct`,
    `deserved_points`, `deserved_points_gap` already have every field agreeing — converting only
    their movable part is what would split them.
  - ⭐⭐ **A FIFTH REGEX ERROR, AND THE FIRST FALSE POSITIVE — found by chasing that FAIL.** Widening
    the "on goal" detector to `on[ _-]?goal` made it match the METRIC ID
    `shots_on_goal_difference_per_match`, quoted verbatim inside `deserved_points`' description, so
    a fully consistent row read as split. **Resolution is step 4's rule: ROLE, NOT PUNCTUATION** —
    prose separates with a space or hyphen, an identifier with an underscore, and row consistency is
    a claim about the English a reader sees. **Verified the bug never reached the seed**: `git diff`
    shows the file byte-identical to what both round-2 reviewers read; only the reported prose was
    wrong. ⚠ Proof the three detectors are not interchangeable — narrowing the COUNTING one to prose
    dropped the protected count from **3 to 0**, while widening the JUDGING one past prose invented
    a split that was not there.
  - **The seed differs in `description` and `interpretation` ONLY** — asserted by column, not by
    eyeballing the diff. Parsed both sides as CSV: **86 rows base, 86 head**, row order identical by
    `metric_id`, and the set of columns holding any difference is exactly
    `['description', 'interpretation']`. **5 cells changed across 4 rows.**
  - **The protected join key is untouched on all three rows carrying it.** `label_i18n_key` still
    reads `metrics.shots_on_target_per_match.label`, `playerMetrics.shotsOnTarget.label` and
    `playerMetrics.shotsOnTargetPer90.label` — a join key across five surfaces, whose "fix" would
    resolve the label to nothing.
  - ⭐⭐ **THE CENSUS REGEX WAS WRONG FOUR TIMES ON ONE FILE, AND EVERY TIME IT REPORTED A CONFIDENT
    ZERO RATHER THAN AN ERROR.** Written up as a rule in `contract.md §1a`, because this is `!134`'s
    miss recurring. The phrase has **four spellings here**: `on target`, `on-target`, `on_target`,
    `OnTarget`. Three traps, all silent:
      1. **`\b` does not delimit `on` in `shots_on_target`** — `_` is a word character, so there is
         no boundary there. `\bon[ _-]target\b` matched nothing and printed "protected: 0".
      2. **camelCase carries no separator at all**, so every bounded pattern misses `shotsOnTarget`.
      3. ⭐ **The detector for the NEW word had the same blindness** — the row check first asked
         `"on goal" in cell`, a literal space, so a cell converted to *"shots-on-goal data"* read as
         unconverted and `deserved_points` scored as a clean move while its row ended holding both
         spellings. **The detector for what you write needs the permissiveness of the detector for
         what you replace.**
    Corrected protected count went **0 → 1 → 3**.
  - **Two-sided count, all 39 occurrences classified once with a printed reason**: **5 MOVE** ·
    **16 STAY** (premodifier, no English form) · **15 STAY** (row would split) · **3 STAY**
    (protected field) — **39 total**, reconciled against the file.
  - **The grammar rule is a fact, not a preference — and adjacency was the wrong proxy for it.**
    "on target" fills two roles: FOLLOWING a shot it substitutes cleanly ("shots on target" → "shots
    on goal"); PREMODIFYING a noun it does not — "on-goal threat" is not English. Round 1's checkable
    form was *"`shot`/`shots` immediately precedes"*, which is a different claim and is what broke
    `shots_on_goal_pct`: *"Share of shots **that were** on target"* is the same role, not adjacent.
    The rule is now **position relative to the noun**, matching across a copula.
  - ⚠ **The absolute claim "no cell is mixed" is FALSE, and measuring both sides caught it.**
    `finishing_efficiency_pct` [description] is **already mixed on main** — *"per shot on goal"* and
    *"their own on-target shots"* in one sentence. Measured: mixed on base **1**, head **1**,
    **introduced 0**, **removed 0**, and none of the 5 written cells is mixed.
  - **`metric_columns.md` regenerated, and proved changed by nothing but the substitution.** The
    generator hard-wraps, so a 2-char-shorter phrase reflows paragraphs and a raw line diff
    overstates the change. Compared as a **word sequence with whitespace collapsed** — the only
    comparison surviving a rewrap — **base 7,147 words, head 7,147, delta 0**, with **2 changed
    ranges, both `target`→`goal` inside an `on` phrase** (verified via the preceding word, since the
    differ splits "on target" and the bare token cannot distinguish "shots on target" from "hit the
    target"). The generator never reads `interpretation`, so only the 2 changed descriptions appear.
  - **All seven offline gates EXIT=0**: `sync_metric_docs_blocks --check`,
    `check_description_hygiene`, `check_copy_gate`, `check_layer_contract`,
    `check_registry_var_sync`, `check_competition_type_seed`, `check_ui_i18n_metrics`.
  - **Full Python suite green on the round-1 tree**: `1009 passed, 1 skipped, 14 subtests` (464s).
    ⚠ Reported for what it is worth, which is little: no test reads these columns, so green here
    proves the sweep broke nothing, never that it did anything.
  - **The BigQuery description limit moves the safe way.** "on goal" is shorter than "on target", so
    every changed cell shrank or held — asserted per cell. Longest rendered cell: **936 chars**
    against the hard 1,024 column cap that fails the prod build.
  - **No value, grain or row count can move.** `description`/`interpretation` reach exactly three
    consumers, and `analytics-engineer` independently confirmed the inventory is complete:
    `metric_columns.md` (generated), BigQuery comments via `+persist_docs`, and `metrics.json` via
    `fetch_glossary()`. `export_metric_definitions_json.py` reads `format`/`lower_is_better`/
    `label_i18n_key` only; `metricRows.ts` reads only `label_i18n_key`.
  - **Football-domain review PASSED on round 1 and its subject did not change.**
    `football-analytics-expert` verified every substitution is pure vocabulary — formulas,
    denominators, null conditions and `direction` all byte-identical — that "shots on goal" and
    "shots on target" name the same event given the explicit `saves + goals_against` derivation, and
    that no natural "on-goal" phrasing was missed on the STAY set. Round 2 is a strict subset of the
    substitutions it reviewed.

reserved:

  - ⛔ **The bare-modifier wording — the one decision that unblocks the remaining 7 rows.** See §3.
  - ⚠ **Leaving it forever is defensible and is NOT assumed to be debt.** "Shots on goal" is the
    product term for the metric; "on-target" as an ordinary adjective is normal football English and
    reads correctly — the football reviewer agreed explicitly.
