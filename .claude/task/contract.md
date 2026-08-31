# Task contract — STEP 5: the English label "on target" → "on goal"

objective: >
  **STEP 5 of the metric catalogue naming programme, and the mirror image of step 4.** Step 4 moved
  `metric_id` and deliberately PROTECTED `label_en` in every one of its seven classifiers. This MR
  moves `label_en` and touches `metric_id` **nowhere**.

  Nine catalogue rows carry the English words "on target" while their internal ids have said
  `shots_on_goal_*` for months. RULING 2 closes that gap.

  ⭐⭐ **AND IT IS WIDER THAN THE RECORD'S SCOPE, BY A RULING TAKEN THIS SESSION.** RULING 2's scope
  was confirmed *"in the catalogue"*. I measured, before proposing anything, that **the catalogue is
  not where the website gets its labels** — the site reads its own `METRIC_LABELS_EN` map in
  `site_v2/src/i18n/strings.ts`, and **four of the nine labels render on the live site today**.
  Catalogue-only would therefore have left the visible mismatch untouched — the exact thing the
  ruling exists to fix. Asked in plain terms whether the website's four should move too, the CPO
  chose **catalogue + website**. Recorded in `escalations.log` under today's date.

  ⚠ **THE HANDOVER'S STEP-5 LIST WAS STALE AND WAS NOT USED.** It named nine metric_ids; **six were
  superseded** by step 3's team renames and step 4's player renames. The nine below are measured
  from the seed with `label_en` matched on "on target", not carried from any document.

refs: >
  **`.claude/task/escalations.log`, RULING 2**, verbatim: *"we have inconsistency between name and
  shown as / example: shots_on_goal_per_match vs Ø Shots on target -> should be Ø Shots on goal
  (apply everywhere where applicable)"*. Scope confirmed later, verbatim: *"in the catalogue"*.
  On languages, verbatim: *"i know, but here i explicitly want consistency between the metric name
  and what we show (in english). German and Finnish or any other language should not be affected."*
  Cited by CONTENT.

  ⭐ **THE NEW RULING, this session**, on whether the four rendered labels move with the catalogue:
  the CPO was shown that `strings.ts` and not the seed is what the site renders, and chose
  **catalogue + website**. Appended to `escalations.log` under 2026-08-31 before any file was
  touched.

  ⚠ The record's own measurement, re-confirmed here: **German already says `Torschüsse` and Finnish
  `Maalilaukaukset`**, both literally "goal shots". Only ENGLISH was out of step, which is why the
  ruling excludes the other languages rather than deferring them.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - dbt_project/seeds/metric_catalogue.csv
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/components/team/DeservedHero.astro
  - site_v2/scripts/check-metric-labels.test.mjs
  - docs/wireframes/metrics_display.md
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/10_home.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/14_team_stats.md

amendments: >
  **ROUND 2 — two files ADDED to `scope_paths`**, on no new CPO authority and needing none: this is
  not a widening of what the task does, it is the FIX for a MISS against a criterion the contract
  already declared ("every 'on target' occurrence classified once").
  `bi-analyst-reviewer` FAILed round 1 on `site_v2/src/components/team/DeservedHero.astro:43`, which
  carries a THIRD copy of the id-vs-label claim that `decisions_taken §2` identifies and rewrites in
  two other places. My census missed it, and the reason is worth more than the fix: **I matched
  "on target" and "on-target" and never matched `on_target`** — an enumeration of spellings, which
  loses by one variant every time. Re-swept with the PATTERN `on[\s_-]?target`: **136 occurrences,
  5 of them CLAIMS about the split.** Two were already rewritten, `check-page-specs.test.mjs:179` is
  still TRUE (it compares the id to the KEY, not to the user-facing term), and two were stale —
  `DeservedHero.astro` and `check-metric-labels.test.mjs`, hence these two paths.
  ⚠ Adding the test file routes `platform-reviewer` in from round 2.

protected_override: >
  **`metric_id` IS PROTECTED IN THIS MR, on every row and in every file.** Step 4 moved ids and
  protected labels; this moves labels and protects ids. Nothing in the seed changes except the
  `label_en` cell on nine rows.

  ⛔ **`label_i18n_key` IS PROTECTED TOO, including the one value that contains the words.**
  `shots_on_goal_per_match` declares `label_i18n_key = metrics.shots_on_target_per_match.label` —
  the ONLY key in the seed carrying "on_target", and it stays. It is a JOIN KEY across the seed,
  `strings.ts`, `metricRows.ts`, three hand-written parsers and the page specs; the catalogue
  declares no `metrics.shots_on_goal_per_match.label`, so "fixing" it would resolve the label to
  nothing. RULING 2 is about what is SHOWN, not about keys.

  ⛔ **The seed's `description` column is protected** — ~19 occurrences read "shots on target" as
  prose. Not labels, not ruled. See `decisions_reserved`.

  ⛔ **DE and FI are protected**, by the ruling's own words.
  ⛔ **`site/i18n/*.json` is protected** — the frozen retired-MVP corpus (2026-07-21).

impact_map: >
  `label_en` has exactly one live consumer: `fetch_glossary()` in `scripts/export_site_data.py`
  emits the whole seed row as `metrics.json`, so the nine new labels reach that payload. **No dbt
  model reads the metric catalogue's `label_en`** — verified by sweeping every reader of the token
  across the repo; the hits belong to `competition_types` and `confederations`, different seeds.

  `sync_metric_docs_blocks.py` has **zero** `label_en` references, so `metric_columns.md` does NOT
  regenerate from this change. Its "on target" text is descriptions, which are protected above.

  The four rendered labels reach the page as
  `strings.ts METRIC_LABELS_EN` → `metricLabel(lang, labelKey)` → the fixture comparison block.

acceptance_criteria:
  - The nine `label_en` values read "on goal", and the seed differs from base in `label_en` ONLY —
    `metric_id`, `label_i18n_key`, `description` and every other column byte-identical on every row.
  - The four rendered EN labels move, and the built `dist/` shows **"Ø Shots on goal"** with **zero**
    EN pages containing "on target". DE and FI pages byte-identical to base.
  - `npm test` stays 76/76, including all seven `check-metric-labels` tests, and the byte-identical
    gate is watched going RED on a deliberate break before being reverted.
  - Every "on target" occurrence in the repo is classified once with a printed decision, reported as
    a TWO-SIDED count (N move, M stay).

decisions_taken: >
  ⭐ **§1. THE DISCRIMINATOR IS "IS THIS A DISPLAYED LABEL?", AND IT IS APPLIED PER OCCURRENCE.**
  Step 4's closing lesson was that a scope coarser than the ROLE it must resolve is the one recurring
  defect, and it cost three rounds on `!132`. The same trap is here in a new dress: "on target"
  appears in display labels, in prose explaining the concept, in dated changelog rows, and in a
  comment that documents the id-vs-label split. Only the first moves. Each occurrence is classified
  once and the decision printed, and the result is reported as a two-sided count.

  ⭐ **§2. THE ONE COMMENT THIS CHANGE FALSIFIES, AND THE INSTRUCTION INSIDE IT THAT MUST SURVIVE.**
  `site_v2/src/lib/metricRows.ts:87-91` reads *"The internal id says 'on goal', the user-facing term
  is 'on target'. Do NOT 'fix' this to `metrics.shots_on_goal_per_match.label`."* After this MR both
  say "on goal", so the REASON is void — but the INSTRUCTION is not, and is now the only thing
  standing between a future reader and a label that resolves to nothing. The comment is rewritten to
  keep the instruction and replace the reason: the key name is legacy, not a term difference.

  ⭐ **§3. WHY THE BYTE-IDENTICAL GATE DOES NOT BLOCK THIS, SIMULATED BEFORE ANY EDIT.**
  `check-metric-labels.test.mjs`'s *"CPO-validated MVP labels are byte-identical to site/i18n"*
  compares only keys present in BOTH `strings.ts` and the frozen corpus. Simulated against the real
  files: **29 labels compared, of which ZERO contain "on target"** — three of our four are absent
  from the frozen corpus and `finishing_efficiency_pct` is skipped by name, a divergence the test
  already documents as a §10 pick reserved to the CPO. The gate is measured, not assumed, and is
  mutation-tested afterwards.

decisions_reserved:
  - ⛔ **THE SEED'S `description` COLUMN — flagged, not taken.** After this MR a row's label reads
    "on goal" while its description beside it still reads "shots on target", and `persist_docs`
    publishes those descriptions to BigQuery. My recommendation is a small follow-up applying the
    same wording to descriptions, but widening scope mid-MR is the failure this programme has been
    FAILed on, so it is the CPO's call and it is not taken here.
  - ⛔ **`label_i18n_key` renaming** — the one key containing "on_target" stays. A join-key rename
    across five surfaces and three parsers is its own job with its own contract.
  - ⚠ CARRIED from step 4, none of them touched here: the `__team`/`__player` split with no live
    instance; the resolver as a committed CI gate; **#99**; **#96**; **#87**; **#98**.

done_when: >
  - The nine `label_en` values read "on goal" and the seed differs from base in `label_en` only.
  - The four `METRIC_LABELS_EN` values move; DE and FI are byte-identical.
  - `metricRows.ts`'s comment keeps its instruction and loses its dead reason.
  - Every "on target" occurrence classified once, reported as N move / M stay.
  - All offline gates EXIT=0 unpiped; `npm test` 76/76; `pytest` at the `649b11c` baseline;
    the site built and `dist/` read for "on goal" with zero EN "on target".
  - The label gate watched going RED on a deliberate break, then reverted green.
  - Five blinded reviewers, `review.md` bound with `--staged-hash`. Round cap 3.
