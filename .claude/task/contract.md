# Task contract — the seed's PROSE follows the label, where English allows

objective: >
  **Make the catalogue's reader-facing prose say "on goal" wherever the label already does — in the
  cells where that can be done without rewriting a sentence.**

  Step 5 moved nine `label_en` values from "on target" to "on goal" and deliberately left the prose.
  The result is visible in BigQuery, because `persist_docs` publishes both: `shots_on_goal_player`
  is labelled **"Shots on goal"** and described as **"Shots on target."** — the label and its own
  definition using different words for one thing.

  ⭐ **THE CPO WIDENED THIS TO TWO COLUMNS.** Asked whether `interpretation` — the seed's second
  reader-facing column, which feeds the site's good/bad reading — should move with `description`, he
  chose **both**. Leaving it would have produced a THIRD spelling on one row.

refs: >
  **CPO, verbatim, this session:** *"start the seed description sweep"*, then — asked whether to
  include the `interpretation` column — he selected **"Both columns (recommended)"**, whose stated
  text was: *"Sweep `description` AND `interpretation` together. Otherwise one metric ends up saying
  'on goal' in its label, 'on goal' in its description, and 'on target' in its interpretation."*

  **RULING 2** (`escalations.log`): *"…should be Ø Shots on goal (apply everywhere where
  applicable)"*, scope confirmed *"in the catalogue"*. This MR is inside that scope; the phrase
  **"where applicable"** is what `decisions_taken §1` turns into a checkable rule.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md

protected_override: >
  ⛔ **`metric_id`, `label_en`, `label_i18n_key` AND EVERY OTHER COLUMN ARE PROTECTED.** Only
  `description` and `interpretation` may change — a field allowlist, checked before any text rule,
  which is the `!131`/`!132`/`!136` lesson. `label_i18n_key` in particular still carries
  `metrics.shots_on_target_per_match.label` and stays: it is a join key across five surfaces.

  ⛔ **NO SENTENCE IS REWRITTEN.** Only the exact phrase substitution below. Rewording reader-facing
  English is copy, and `scripts/check_copy_gate.py` states the standing position in its own
  docstring: *"Editorial and Localisation exists as a mechanical gate, not a copy approver. Wording
  stays yours… Judgement about whether a sentence reads naturally stays with the CPO, permanently."*

  ⛔ **NO MODEL, MACRO OR TEST CHANGES.** `metric_columns.md` is REGENERATED, never hand-edited —
  it renders these descriptions, so `sync_metric_docs_blocks.py` must run and `--check` must pass.

impact_map: >
  `description` and `interpretation` reach three places: `metric_columns.md` (generated, hence in
  scope), the BigQuery table/column comments via `+persist_docs`, and `metrics.json` via
  `fetch_glossary()`, which dumps the whole seed row. No model logic reads either column, so no
  value, grain or row count can move.
  ⚠ **Unlike step 5, `metric_columns.md` DOES regenerate here** — that generator renders
  descriptions, and it ignored step 5 only because it never reads `label_en`.

acceptance_criteria:
  - The seed differs from base in `description` and `interpretation` ONLY — every other column
    byte-identical on every row.
  - ⭐ **NO ROW IS MADE WORSE — the criterion round 1 lacked, and the one that matters.** Measured
    across `label_en` + `description` + `interpretation` on BOTH sides: rows split on main **9**, on
    head **7**; **2 fixed, 0 newly split**. Every row this MR writes ends fully self-consistent.
  - **The sweep INTRODUCES no internally-mixed cell** — no cell it writes contains both "on goal"
    and "on target". ⚠ Stated two-sided, because the absolute form ("no cell anywhere is mixed") is
    FALSE and measuring it is what proved it: **`finishing_efficiency_pct` [description] is ALREADY
    mixed on main** — it says *"per shot on goal"* and *"their own on-target shots"* in one
    sentence. §2 leaves it untouched, so this MR neither creates nor removes it. Measured both
    sides: mixed on base **1**, on head **1**, introduced **0**, removed **0**.
  - `metric_columns.md` regenerated, `sync_metric_docs_blocks --check` EXIT=0, and the description
    hygiene gate green (⚠ BigQuery hard-rejects a column description over 1,024 chars; "on goal" is
    shorter than "on target", so every cell shrinks).
  - Every occurrence classified once with a printed decision, reported as a TWO-SIDED count.

decisions_taken: >
  ⭐⭐ **§1. THE RULE, AND IT IS A GRAMMAR FACT, NOT A PREFERENCE.** "on target" serves two
  grammatical roles and only one has an English equivalent:
    · **NOUN PHRASE** — "shots on target", "shots-on-target data", "per shot on target". Substitutes
      cleanly to "shots on goal", "shots-on-goal data". **MOVES.**
    · **BARE MODIFIER** — "on-target threat", "on-target dominance", "the on-target process",
      "on-target shots". **"on-goal threat" is not English.** No substitution exists. **STAYS.**
  Checkable form: substitute only where `shot`/`shots` immediately precedes.

  ⭐⭐ **§1a. AND THE PHRASE HAS FOUR SPELLINGS IN ONE FILE — the census regex was widened THREE
  times and each widening found more.** This is `!134`'s miss, repeated, and worth stating as a
  rule rather than a war story:
    · `on target` · `on-target` · `on_target` (`label_i18n_key`) · `OnTarget` (camelCase, same column)
  Two traps behind it, both silent — a too-narrow census reports a confident **zero**, never an error:
    1. **`\b` does not delimit `on` in `shots_on_target`.** `_` is a WORD character, so there is no
       boundary there. The count read 0 until the boundary was respelled as `(?<![A-Za-z])`.
    2. **camelCase has NO separator at all**, so every bounded pattern misses it.
  Standing form: the regex that DECIDES may be strict; the regex that COUNTS must be permissive
  (`on[ _-]?target`, no anchors) — its only job is to miss nothing.

  ⚠ **AND THE SAME BLINDNESS HIT THE DETECTOR FOR THE *NEW* WORD.** The row-consistency check first
  asked `"on goal" in cell` — a literal SPACE — so a cell converted to *"shots-**on-goal** data"*
  read as still-unconverted and `deserved_points` was scored as a clean move while its row actually
  ended holding both spellings.

  ⛔⛔ **AND WIDENING *THAT* ONE BROKE IT THE OTHER WAY — the fifth error, and the first
  FALSE POSITIVE.** `on[ _-]?goal` matches the METRIC ID `shots_on_goal_difference_per_match`, which
  `deserved_points`' description quotes verbatim; a fully consistent row then read as split.
  ⭐ **THE RESOLUTION IS THE RULE STEP 4 ALREADY EARNED — ROLE, NOT PUNCTUATION.** Prose separates
  with a SPACE or a HYPHEN; an identifier separates with an UNDERSCORE. Row consistency is a claim
  about the ENGLISH A READER SEES, so an identifier must not count either way.

  ⭐⭐ **THEREFORE: THREE DETECTORS, THREE JOBS, AND COLLAPSING ANY TWO HAS BROKEN THIS SWEEP ONCE
  EACH.** (1) the one that DECIDES what changes — strict; (2) the one that COUNTS occurrences —
  maximally permissive, every separator, because its only job is to miss nothing; (3) the one that
  JUDGES reader-facing consistency — prose only, no identifiers. ⚠ Proof they are not
  interchangeable: narrowing (2) to prose dropped the protected count from **3 to 0**, and widening
  (3) past prose invented a split that was not there.

  Two-sided count, final: **5 move, 34 stay** — 16 premodifier (no English form), 15 held because
  the row would split, 3 protected — **39 total**.

  ⚠ **AND ADJACENCY WAS THE WRONG PROXY FOR THAT ROLE — round 1 FAILed on it.** The first checkable
  form was *"substitute only where `shot`/`shots` immediately precedes"*, which is a different
  claim: *"Share of shots **that were** on target"* is the identical role and is not adjacent, so it
  was frozen while its sibling column moved. The discriminator is **POSITION relative to the noun** —
  "on target" FOLLOWING a shot (directly, or across a copula) moves; "on-target" PREMODIFYING a noun
  stays.

  ⭐⭐ **§2. THE UNIT IS THE ROW, NOT THE CELL — and that is the whole correction of round 1.**
  A row's cells are written **only if the row ends fully consistent**: `label_en`, `description` and
  `interpretation` all spelling the phrase the same way, none holding both. Otherwise **nothing on
  that row is touched.**

  ⛔ **THE CELL-LEVEL RULE FAILED REVIEW, AND FOR THE RIGHT REASON.** It moved whichever column
  happened to hold a convertible phrase and froze its sibling, producing rows reading "on goal" in
  the label, "on goal" in the description and "on target" in the interpretation. **That is not an
  approximation of the CPO's ruling — it is the literal state he named as his reason for widening
  this sweep to two columns.** `scope-auditor` and `analytics-engineer` FAILed it independently; the
  second measured **7 rows** where two previously-agreeing columns were made to disagree, and traced
  it into `metrics.json` via `fetch_glossary()`, which serialises both fields of a row side by side.
  A partly-converted ROW is worse than an unconverted one, for the reason a partly-converted cell is.

  ⭐ **Measured under the row rule: 5 occurrences move across 4 rows; 34 stay.** Rows split on main
  **9**, on head **7** — **2 fixed, 0 newly split**, no row made worse in any respect.

  ⛔ **§3. WHAT BLOCKS THE REST IS A COPY DECISION, AND IT IS THE CPO'S.** Seven rows stay split:
  `shots_on_goal_per_match`, `finishing_efficiency_pct`, `finishing_efficiency_player_pct`,
  `shots_on_goal_player`, `shots_on_goal_against_player`, `shots_on_goal_difference_per_match`,
  `shots_on_goal_against_per_match`. Each holds a bare modifier for which no English "on-goal" form
  exists — **"on-goal threat" is not a football phrase, and there is no "off-goal" the way there is
  "off-target"**. So there is no substitution available, only a rewrite, and
  `scripts/check_copy_gate.py` reserves wording permanently: *"Judgement about whether a sentence
  reads naturally stays with the CPO, permanently."*

  ⚠⚠ **THE FIRST VERSION OF THIS PARAGRAPH WAS WRONG IN THREE WAYS, AND IT WAS WRONG BECAUSE I WROTE
  THE LIST FROM MEMORY INSTEAD OF DERIVING IT** — `scope-auditor` FAILed round 2 on it and
  `football-analytics-expert` flagged the same thing independently. It (a) claimed the named phrases
  make "all 7 rows convertible", (b) said every block sits in the `interpretation`, and (c) listed
  `deserved_points`, which **is not split at all** — its `label_en` never carried the phrase, so
  nothing in that row disagrees with anything. **A blocker inventory is a claim about the file and
  has to be extracted from it**, which is the same rule as the census itself.

  Derived, with site counts:

  | blocking phrase | sites | where |
  |---|---|---|
  | «on-target shots» | 4 | `finishing_efficiency_pct`.desc, `finishing_efficiency_player_pct`.desc, `shots_on_goal_against_player`.interp, `shots_on_goal_difference_per_match`.interp |
  | «on-target threat» | 3 | `shots_on_goal_per_match`.interp, `shots_on_goal_player`.interp, `shots_on_goal_against_per_match`.interp |
  | «on-target dominance» | 1 | `shots_on_goal_difference_per_match`.interp |
  | «on target for − against» | 1 | `shots_on_goal_difference_per_match`.desc |

  ⭐ **Deciding the first three frees 6 of the 7.** `shots_on_goal_difference_per_match` needs the
  fourth as well. ⚠ Note **two of the seven are blocked in their DESCRIPTION, not their
  interpretation** — "not finishing the team's/player's own on-target shots" — which is exactly what
  the memory-written version got wrong.
  ⚠ `finishing_efficiency_pct` is additionally the one **pre-existing** mixed cell (see the
  acceptance criteria); it is stuck for both reasons at once.
  ⚠ Three further rows — `saves_pct`, `deserved_points`, `deserved_points_gap` — are held by §2 but
  are **NOT split**: every field they have already agrees, and converting only the movable part is
  what would split them. They need no decision and are not debt.
  ⚠ **So this MR does NOT fix its own headline example.** `shots_on_goal_player` still reads label
  "Shots on goal" / description "Shots on target." — because its interpretation says "On-target
  threat", and moving the description alone is exactly the defect above. Stated plainly rather than
  buried: the objective is only partly reachable without that decision.

decisions_reserved:
  - ⛔ **THE DECISION THAT UNBLOCKS THE REMAINING 7 ROWS: what replaces the bare modifier.** Four
    phrases carry it, with the site counts derived in §3 — **«on-target shots»** (4),
    **«on-target threat»** (3), **«on-target dominance»** (1), **«on target for − against»** (1).
    Deciding the first three frees **6 of 7**; the fourth frees
    `shots_on_goal_difference_per_match`. Not answering leaves all seven exactly as main has them.
    ⚠ Do NOT restate this list from memory — it was wrong three ways when I did, and `scope-auditor`
    FAILed round 2 for it. Re-derive it from the seed.
  - ⚠ **Leaving them forever is defensible and this is NOT assumed to be debt.** "Shots on goal" is
    the product term for the metric; "on-target" as an ordinary adjective is normal football English
    and reads correctly. `football-analytics-expert` reviewed the STAY set on football grounds and
    agreed no natural "on-goal" phrasing was missed.
  - ⚠ CARRIED, untouched: step 5's four chrome strings (`axPlay`, the hero verdicts);
    `fdp-freshness`'s hourly cadence; the disabled GitLab schedule; the `__team`/`__player` split
    with no live instance; the resolver as a CI gate; **#99**, **#96**, **#87**, **#98**.

done_when: >
  - The 5 occurrences move across 4 rows, each ending fully consistent; every other row is
    byte-identical to base.
  - **0 rows newly split**, measured against base across all three reader-facing fields.
  - The MR introduces no mixed cell, measured against base on BOTH sides. The single pre-existing
    one (`finishing_efficiency_pct`) is reported, not silently inherited.
  - Seed differs in `description`/`interpretation` only; `metric_columns.md` regenerated.
  - Gates green, two-sided count reported, blinded review, `review.md` bound with `--staged-hash`.
    **Round cap 3.**
