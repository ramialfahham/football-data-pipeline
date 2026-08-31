# Acceptance evidence — STEP 5: the English label "on target" → "on goal"

Branch `refactor/metric-label-on-goal`, from main `649b11c`.

**Nine `label_en` values in the catalogue, plus the four `METRIC_LABELS_EN` values that actually
render.** The mirror image of step 4: that programme moved `metric_id` and PROTECTED `label_en` in
all seven of its classifiers; this moves `label_en` and protects `metric_id` everywhere.

⭐ **THE SCOPE IS WIDER THAN RULING 2's "in the catalogue", BY A RULING TAKEN THIS SESSION.** I
measured before proposing: the catalogue is **not** what the website renders — `strings.ts`'s
`METRIC_LABELS_EN` is — and four of the nine labels render today. Catalogue-only would have left
every page still reading "Shots on target". Shown both options, the CPO chose **catalogue + website**.

⚠ **The handover's step-5 list was STALE and was not used.** It named nine metric_ids; **six were
superseded** by step 3's and step 4's renames. The count was right and the names were wrong — the
nine below were re-derived by matching `label_en` against "on target" in the seed.

criteria_demonstrated:

  - **The seed differs from base in `label_en` ONLY** — 9 cells changed, **0** other cells, checked
    field-by-field across all 86 rows. `metric_id` and `label_i18n_key` columns are byte-identical.
    ⚠ This criterion FAILED on the first apply and caught a real defect — see §(a).
  - **The four rendered EN labels moved and DE/FI did not** — parsed out of `METRIC_LABELS_*` and
    compared to base: EN 4 of 19 changed, **DE 0 of 19, FI 0 of 19**. The ruling excludes the other
    languages because both already say "goal shots" (`Ø Torschüsse`, `Ø Maalilaukaukset`).
  - **The rendered pages prove it**: across 67 built pages, EN carries **0** occurrences of
    "on target" and **38** of "on goal"; DE and FI carry **0** of either, unchanged. The comparison
    block still renders **12/12/12 rows and 7/7/7 headings** in EN/DE/FI over 19 fixture pages —
    the structure is untouched and exactly one label string moved.
  - **Every occurrence of EVERY SPELLING is classified once and reported TWO-SIDED.** ⚠ The round-1
    census was **incomplete** and a reviewer proved it — see §(d). Re-swept with the PATTERN
    `on[\s_-]?target` rather than a list of spellings: **136 occurrences**, of which **5 are CLAIMS
    about the id/label split** (4 rewritten or already true, 1 still true as written), 14 are the
    protected `label_i18n_key`, and the rest are prose. The substitution itself is
    **10 move, 65 stay, 9 by hand**.
  - **`metric_id` moved nowhere.** No file in the diff changes an identifier.

## Gates — each run unpiped, exit code read bare

  - `check_copy_gate.py` — **EXIT=0**: 435 strings across 3 locales (378 chrome + 57 metric labels),
    390 corpus strings consulted. This is the gate that sees metric labels (its #370 parser).
  - `check_ui_i18n_metrics.py` — **EXIT=0**, 13 shown metrics resolve.
  - `sync_metric_docs_blocks.py --check` — **EXIT=0**, 163 blocks (unchanged: the generator has zero
    `label_en` references, so `metric_columns.md` does not regenerate from a label change).
  - `check_description_hygiene.py` — **EXIT=0**, 1604 descriptions, 225 blocks resolved.
  - `check_layer_contract.py` / `check_registry_var_sync.py` — **EXIT=0**.
  - `dbt parse` — **EXIT=0**.
  - `python -m pytest -q` — **1009 passed, 1 skipped, 14 subtests**, matching the `649b11c` baseline.
  - `npm test` — **76/76**, including all seven `check-metric-labels` tests.
  - `npm run build` — 66 pages, `audit-seo: 67 built page(s) checked. OK.`

## ⛔⛔ (a) THE DEFECT MY OWN CHECK CAUGHT, AND THE RULE THAT FIXED IT

The first apply changed **three seed `description` cells** the contract protects:
`'Shots on target.' → 'Shots on goal.'` and two others. Cause: my rule was "substitute an exact
rendered label", and a description **contains** its own label as a substring — `"Shots on target."`
contains `"Shots on target"`. Nothing about the rule was wrong; its SCOPE was, because it ran over
raw lines and so could reach any cell on the row.

⭐ **Fixed as `!131`/`!132`'s rule, not as three edits**: the seed is now parsed as CSV and only
`SEED_RENAMEABLE_FIELDS = {"label_en"}` may change, checked **before** any token rule can look at
the text. That is the same lesson those MRs ended on — *an allowlist that something is checked
before is not an allowlist* — arriving here in a new disguise. Verified after: **0 non-`label_en`
cells differ from base.**

## ⛔ (b) THE CONTRACT GATE CAUGHT A SCOPE VIOLATION, AND IT WAS RIGHT

The apply also touched `docs/wireframes/99_gaps_register.md`, which is **not** in `scope_paths`. The
gate refused the turn until it was reverted. It is now in the classifier's skip list so a re-run
cannot silently reintroduce it. On the merits the gate's answer is also the right one: the gap
register is a dated record of gaps as they were found, not a display spec.

## ⛔ (c) WHAT IS NOT GUARDED — measured by mutation, in BOTH directions

The label gate was mutated three ways, `npm test` run after each, then reverted green:

| mutation | result | what it proves |
|---|---|---|
| **EMPTY** one of the four labels | **RED** (exit 1) | the gate pins that a label EXISTS and is non-empty |
| **WRONG TEXT**, key intact (`"Ø Bananas per fortnight"`) | ⛔ **GREEN** | **nothing pins what these four labels SAY** |
| revert | green | the suite returns to 76/76 |

⛔ **So the wording of the four labels this MR changes is pinned by NO test** — they are absent from
the frozen `site/i18n` corpus (or, for `finishing_efficiency_pct`, skipped by name), which is exactly
why the byte-identical gate does not block the change. It also cannot catch a wrong one.
⛔ **And 3 of the 4 render on ZERO built pages.** Only `Ø Shots on goal` appears in the sample (38
times, 2 per fixture page × 19). `Ø Shots on goal against`, `Ø Shots on goal difference` and
`% Goals per shot on goal` live on the team Performance surface, which still renders "coming soon" —
the single built EN team page carries none of them.
**Those three were verified by reading `strings.ts` directly.** Stated as what it is — a manual
verification of an unguarded path — not dressed up as a passing check.

## ⛔⛔ (d) ROUND 1 FAILED 3–1, AND THE MISS IS MORE INSTRUCTIVE THAN THE FIX

`scope-auditor`, `analytics-engineer` and `football-analytics-expert` PASSed. **`bi-analyst` FAILed**,
and was right: `site_v2/src/components/team/DeservedHero.astro:43` carried a **third copy** of the
id-vs-label claim that §2 identifies and rewrites in two other places — live in the render path, and
absent from my census entirely.

⭐ **WHY IT ESCAPED, which is the part worth keeping.** My census matched `"on target"` and
`"on-target"`. `DeservedHero.astro` writes it `"on_target"`. **I enumerated spellings instead of
writing a pattern**, and an enumeration loses by one variant — the exact failure
`feedback_fix_the_class_not_the_instance` records holing a guard four rounds running.
Re-swept with `on[\s_-]?target`: **136 occurrences, 5 of them claims**. Two were already rewritten;
`check-page-specs.test.mjs:179` is still TRUE (it compares the id to the **KEY**, not to the
user-facing term, and that disagreement survives this MR); **two were stale and are now fixed** —
`DeservedHero.astro` and `check-metric-labels.test.mjs`. Both were added to `scope_paths` by a
recorded amendment, on no new authority: this completes a criterion the contract already declared.

**Two more round-1 findings, both accepted:**
  - **The ASCII mockups lost their box alignment** (`03_player_profile.md:48`,
    `12_player_stats.md:57`, `14_team_stats.md:65`) — "on goal" is two characters shorter than
    "on target", and a mockup's whole job is showing layout. Flagged by two reviewers independently.
    Measured rather than eyeballed: each closing border had moved LEFT by exactly 2 columns; all
    three are re-padded and now sit at their base columns (45, 52, 52), verified against the
    neighbouring rows.
  - **The new ruling was recorded as my narration, not his words.** `scope-auditor` called it "a
    weaker evidentiary form"; `football-analytics-expert` noted it departs from the file's
    convention. Corrected: the log now carries the question verbatim, the **exact title and text of
    the option he selected**, and the option he declined — and states plainly that it was a
    SELECTION rather than free text, instead of dressing it up as a quotation.

## The things rewritten BY HAND, because a substitution would have shipped a lie

Each of these asserted the old state as a FACT. A blind replace would have left a sentence that is
false in a new way, so the reason was rewritten while the instruction was kept verbatim.

  - **`site_v2/src/lib/metricRows.ts:87-91`** said *"the internal id says 'on goal', the user-facing
    term is 'on target'"* — no longer true. ⚠ Its INSTRUCTION is load-bearing and survives: do NOT
    "fix" `labelKey` to `metrics.shots_on_goal_per_match.label`, which the catalogue declares
    nowhere. Only the reason changed: what remains is a **legacy key name**, not a term split.
  - **`docs/wireframes/metrics_display.md:171-177`** carried the same claim, plus the #370 defect it
    caused. Rewritten the same way, keeping "resolve a label by reading `label_i18n_key`".
  - **`site_v2/src/i18n/strings.ts`'s header** asserted *"ENGLISH IS UNCHANGED BY THIS TASK … every
    EN string below is byte-identical to what shipped before"*. That was true of #370 and is false
    now; it names step 5 as the one change since, and records that DE/FI did not move.
  - **`site_v2/src/components/team/DeservedHero.astro:43`** and
    **`site_v2/scripts/check-metric-labels.test.mjs:66`** — added in round 2, same class, same
    treatment: the key really does read `on_target`, so the instruction stands; what died is the
    REASON, which is now a legacy key name rather than a term split.
  ⭐ **`site_v2/scripts/check-page-specs.test.mjs:179` was checked and deliberately NOT changed** —
  it says the metric_id says "on_goal" while the display KEY says "on_target", which is still exactly
  true. Naming it here so its absence from the diff reads as a decision, not an oversight.

## Deliberate non-changes, each with its reason

  - **`label_i18n_key`** stays, including `metrics.shots_on_target_per_match.label` — the only key
    containing "on_target". It is the JOIN KEY across the seed, `strings.ts`, `metricRows.ts`, three
    hand-written parsers and the page specs; the catalogue declares no `on_goal` variant, so
    "fixing" it resolves the label to nothing. RULING 2 governs what is SHOWN.
  - **The seed's `description` column** — see §(a). ⛔ **FLAGGED FOR THE CPO**: a row's label now
    reads "on goal" while its own description says "shots on target", and `persist_docs` publishes
    those to BigQuery. A small follow-up is recommended; not folded in.
  - ⛔ **FLAGGED, and the closest call in this MR — four CHROME strings in `strings.ts`'s `Dict`
    that name this same metric in rendered English**: `axPlay` ("Shots on target difference /
    match", the hero chart's x-axis) and the three `heroVerdict*`/`heroCaption` strings
    ("a shots-on-target difference of {sotd} per match"). They are copy, not `METRIC_LABELS`
    entries, and the approved scope named the four label values — so they are **flagged, not folded
    in**. ⚠ The consequence is concrete and should be decided: the team hero will say
    "shots-on-target difference" beside a metric row saying "Ø Shots on goal difference".
  - **DE and FI**, and **`site/i18n/*.json`** (the frozen retired-MVP corpus) — both excluded by
    ruling.
  - **71 hyphenated "on-target" occurrences** — measured; all are concept prose
    ("shots-on-target coverage", "the on-target pair"), none is a rendered label. All stay.
