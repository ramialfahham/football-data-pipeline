# Task contract — every domestic league gets a competition group

objective: >
  **Encode the CPO's league grouping as a registry field, so the home page's blocks have a set of
  leagues to select from.** Home's Top players and Top teams each show *one per league* drawn from a
  chosen set; nothing in the warehouse says which leagues form which set. That is **GAP-28**, and it
  blocks both blocks.

refs: >
  **CPO, verbatim, this session**, in order:
  · *"Drop the pools, let's rethink this properly"* — the existing pool table is retired, not amended.
  · *"However, the 3 new clubs would be in pool 2"* — Belgium/Turkey/Poland are NOT elite.
  · *"Should not be a blocker here. Basically all of it is judgement"* — settles the design question:
    **authored, not derived.**
  · The grouping itself, restated by him: *"we have one set of top 7 clubs (which all happen to be
    european), split calendar / we have a set of another european clubs (not part of the top group),
    split calendar / we have non-european groups, split calendar / we have leagues with calendar year
    (non-europena and 1 eurpean) / all of them are in the first league of their countries / then
    there is the 'rest'"*.
  · *"names are good, build it"* — on `elite` · `europe` · `international` · `summer` · `secondary`.
  · Then, correcting one: *"They play through summer, yes but not only in summer. actually for
    example in argetina season starts in january"* — so **`summer` became `calendar`**.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - docs/competition_registry.yml
  - dbt_project/seeds/competition_registry.csv
  - dbt_project/seeds/schema.yml
  - scripts/sync_dbt_vars.py
  - tests/test_registry_seed_projection.py
  - .claude/skills/onboard-competition/SKILL.md
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md

amendments: >
  ⭐ **2026-09-02 — `docs/wireframes/10_home.md` ADDED to scope_paths. CPO: "yes, widen it".**
  It was RESERVED in the first draft of this contract on the grounds that the file is the subject
  of **#100** and cost `!142` five review rounds. `bi-analyst-reviewer` FAILed that reservation and
  was right: the retired pool table is **not** in the file's disclaimed historical part, it is in
  **§0, which the file's own header calls "the current authority"** — so a builder following the
  document's stated authority chain reads a design this MR has retired. Worse, it contradicts the
  CPO directly (*"Belgium and Turkey belong in pool 1"* against his *"the 3 new clubs would be in
  pool 2"*), and its four-pool algorithm has no bucket for the three leagues now in `europe`.
  ⚠ Put to him as an explicit scope question rather than inferred, because inferring a ruling is
  what FAILed the previous round of this same MR.

  ⭐ **2026-09-02 — `.claude/skills/onboard-competition/SKILL.md` ADDED**, on
  `data-engineer-reviewer`'s FAIL. The skill is the procedure someone actually follows to onboard a
  league; it listed every other registry field and not this one, so following it exactly produced a
  league that fails CI with no explanation. A registry field onboarding does not know about is a
  defect in the field, not in onboarding.

protected_override: >
  ⛔ **NO DERIVATION IS ADDED TO `sync_dbt_vars.py`.** Its docstring calls the seed "the registry's
  own fields, PROJECTED into the warehouse", and `_registry_seed_rows()` is a pure copy —
  `_normalise(row.get(c))` per column, nothing computed. The only change there is one string in
  `SEED_COLUMNS`. Computing the group in that script would put business logic into a build step
  that is deliberately a projection, and `check_registry_var_sync.py` would then have to
  reimplement or import the rule to validate it.

  ⛔ **THE SEED IS GENERATED, NEVER HAND-EDITED.** `python scripts/sync_dbt_vars.py` writes it;
  commit the output.

  ⛔ **NO NEW SCRIPT, NO NEW SEED, NO NEW MECHANISM.** Drift protection already exists and extends
  itself — `check_registry_var_sync.py`: *"Both sides now iterate SEED_COLUMNS, so a new column is
  covered the moment it is [added]."*

  ⚠⚠ **THIS BULLET ORIGINALLY ENDED "Validation of the VALUES goes in dbt as tests on the seed,
  which is the existing pattern, not a new Python gate." THAT WAS FACTUALLY WRONG** and contradicted
  §6 in this same file. I wrote it before finding the `tier` precedent, and never reconciled it once
  §6 came to say the opposite. **The real existing pattern is Python-only**: `tier` has the identical
  non-empty-iff-domestic_league shape and carries **zero** dbt tests, for the stated reason that a
  blank is legitimate off a league. `competition_group` follows it — no `not_null`, no
  `accepted_values`, both directions plus the vocabulary pinned by
  `tests/test_registry_seed_projection.py` in `test:python`. Caught by `analytics-engineer` at
  round 3, which verified `schema.yml`'s `tier` entry has no `tests:` key at all.
  ⚠ **Third self-contradiction in this contract** (after `impact_map`'s dbt-test claim and
  `protected_override`'s stale `10_home.md` ban). All three are the same habit: a constraint written
  early, left standing after the reasoning behind it moved.

  ⛔ **NO DISPLAY LABELS, NO i18n.** A group has no user-facing name yet. That arrives with the
  blocks, and inventing one now is designing off the cuff.

  ⚠⚠ **THIS BAN IS LIFTED — see `amendments:` above.** It originally read *"`10_home.md` IS NOT
  TOUCHED… the register row is the authority and is updated instead"*, on the grounds that the file
  is the subject of **#100**. `bi-analyst-reviewer` FAILed that reservation and the CPO lifted it
  (*"yes, widen it"*): the stale content is in **§0, which the file calls its current authority**,
  and it contradicted his own ruling. **The ban is struck rather than deleted** because leaving a
  live prohibition next to an amendment that overrides it is itself the contradiction this section
  exists to prevent — `bi-analyst` caught exactly that at round 2.
  ⛔ What still holds: `10_home.md` is edited ONLY to supersede what this change falsifies. No
  design is rewritten there, and nothing is restated that `docs/competition_registry.yml` owns.

impact_map: >
  A new column on a seed nothing reads yet. `competition_registry.csv` is consumed by models that
  look up competition metadata; adding a column is additive and changes no existing value, no grain
  and no row count. `dbt ls --select competition_registry+` names what could read it.
  ⚠ The one live effect is CI: the two new tests are PYTHON and run in **`test:python`**, not
  `data:build:mr`. **No dbt test is added** — see §6. An earlier draft of this line said "the new
  dbt tests run in `data:build:mr`", contradicting §6 in the same file; `platform-reviewer` caught
  it. `data:build:mr` re-seeds and so carries the wider seed, but exercises nothing new for this
  column.

acceptance_criteria:
  - The seed gains **exactly one column** and **no other cell moves** — asserted by parsing both
    sides, not by reading the diff.
  - **All 19 `domestic_league` rows carry a group; all 29 other competitions are empty.** Counted.
  - **The documented assignment rule reproduces the authored values exactly**, on all 19 — so the
    rule and the data cannot silently disagree.
  - `check_registry_var_sync.py` EXIT=0 **and mutation-tested RED**: corrupt one group value in the
    seed by hand, confirm it fails, restore. A guard that passes either way proves nothing.
  - `dbt parse` EXIT=0; offline gates green, exit codes read bare.

decisions_taken: >
  ⭐⭐ **§1. AUTHORED, NOT DERIVED — and that is the CPO's ruling, not a convenience.** *"Basically
  all of it is judgement."* Only `elite` is genuinely underivable (Belgium, Turkey and Poland match
  every column-based rule for it and are deliberately excluded), but the whole grouping is authored
  so that one file states the answer plainly instead of a script inferring four fifths of it.

  ⭐ **§2. THE RULE IS DOCUMENTATION FOR AN ONBOARDER, AND IT IS VERIFIED, NOT ASSERTED.**

      if in the authored elite list -> elite      (never touched when a league is added)
      elif tier != 1                -> secondary
      elif season_type = calendar   -> calendar
      elif confederation = UEFA     -> europe
      else                          -> international

  Checked against all 19 leagues before it was written down: it reproduces the authored grouping
  exactly. It lives in the registry header, where every other projected field already documents what
  enforces it — an acceptance criterion re-runs it, so the prose cannot drift from the data.

  ⭐ **§3. `calendar` — HE REJECTED `summer`, THEN SEPARATELY APPROVED `calendar`. TWO RULINGS, NOT
  ONE.** His rejection was a fact, not a preference: those leagues do not merely play "in summer",
  and the label is hemisphere-nonsense for Argentina, whose season starts in January. `calendar`
  mirrors the registry's own `season_type: calendar_year`.

  ⛔⛔ **AND THE FIRST VERSION OF THIS SECTION MISATTRIBUTED IT — `scope-auditor` FAILed round 1.**
  It read *"the CPO corrected my name"*, which claims he supplied `calendar`. He did not: he
  rejected `summer` and said nothing about a replacement. **I chose `calendar` and wrote it up as
  his ruling.** The auditor's point was not pedantry — this name lands as a permanent enum in the
  seed, a CI-enforced vocabulary test, `schema.yml`, the registry header and the gaps register, and
  naming is §10 CPO-class precisely because it is expensive to undo. Put to him as an open
  question, he answered **"calendar / this"**. That answer is what authorises the name; the
  paragraph above only became true afterwards.
  ⚠ **FIFTH instance of `feedback_dont_attribute_repo_practice_to_cpo` this session, and the second
  in two consecutive MRs.** The tell is identical each time: I narrate a decision in prose without
  a quote behind it, and the narration reads as authority.

  ⭐ **§4. NON-LEAGUE COMPETITIONS GET NOTHING, not a placeholder.** Cups, continental competitions
  and qualifiers are not league-ranking candidates. Absent is the convention `parent_competition`
  already uses for "not applicable", and `_normalise` renders it `""`.

  ⭐ **§5. A COMPLETENESS TEST, BECAUSE THE FAILURE IS SILENT.** Without one, a newly onboarded
  league syncs with an empty group and simply falls out of every board — visible nowhere. That is
  GAP-27's lesson restated: *"A silently omitted board is invisible to the visitor by design — and
  therefore invisible to us too. A DQ check has to catch a board that vanished, because the page
  deliberately will not."*

  ⭐⭐ **§6. AND IT GOES IN PYTHON, NOT dbt — because `tier` IS THE SAME SHAPE AND ALREADY SOLVED.**
  `competition_group` is non-empty exactly when `competition_type` is `domestic_league`, which is
  `tier`'s rule verbatim. The registry header spells out how that is handled, and it is deliberate:
  *"⚠ NO dbt TEST, precisely because a blank is legitimate here. The rule that makes it safe —
  non-empty iff domestic_league — is a PYTHON test (`tests/test_registry_seed_projection.py`), which
  runs in the `test:python` CI job."* So this mirrors
  `test_tier_is_declared_exactly_for_domestic_leagues` — **both directions** (a league that loses
  its group, and a non-league that gains one), plus the value enum, in one offline test. No dbt test
  and no `accepted_values`: a second mechanism for a rule this file already has one for.
  ⚠ `tests/test_registry_seed_projection.py` is therefore in `scope_paths`.

decisions_reserved:
  - ⛔ **Which group the home page shows, and how it rotates.** CPO: *"I would like to have a
    mechanism for showing the others as well, by rotation or randomly, no idea, especially when a
    league group is not active but another is -> file it, should not block us here."* Filed as its
    own issue. Recorded there: the page uses `elite`, or `europe`+`international` **merged into one
    board**, or `calendar`.
  - ⛔ **Display labels / i18n for the group names** — with the blocks.
  - ⛔ **GAP-29** (the team boards mart) — the next step, unblocked by this one.
  - ⚠ CARRIED, untouched: step 5's four chrome strings; `fdp-freshness`'s hourly cadence; the
    disabled GitLab schedule; the resolver as a CI gate; **#99**, **#96**, **#87**, **#98**, **#100**.

done_when: >
  - 19 leagues grouped, 29 empty, one new seed column, nothing else moved.
  - The documented rule re-derives the authored values exactly.
  - The sync guard mutation-tested RED; gates green; `dbt parse` EXIT=0.
  - ⭐ **Reviewer set taken from `python scripts/check_task_artifacts.py --base main`, NOT
    hand-derived from `review_routing.json`** — that is exactly how `!142` failed CI.
  - Blinded review. **Round cap 3.**
