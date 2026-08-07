# Task contract — clear the copy gate's 16 findings on `main`

> Branch `fix/i18n-copy-gate-defects` from `main` (`c701ecc`). Touches `site_v2/src/`, so
> `acceptance_criteria` is present and LOCKED by CPO approval of 2026-08-06. No protected path
> is in scope, so no `protected_override`.

objective: >
  Remove every defect `scripts/check_copy_gate.py` reports on `main`, so the gate can be wired
  into CI in the following MR without turning the default branch red.

  THE PROBLEM. `scripts/check_copy_gate.py` exits 1 on `main` with 16 findings: 14 em dashes
  across all three locales, `fi.secForm` using `muoto` where football Finnish uses `kunto`, and
  `fi.footerDataSource` byte-identical to English. Every one is a defect against a standing rule
  — `.claude/active_work.md`'s DO-NOT list says "no em dashes", and the `muoto`/`kunto` error is
  a recorded CPO correction (#867). The gate has existed and been correct this whole time; it is
  invoked by no CI job and no skill, so nothing ever surfaced them.

  THIS IS PR 1 OF 2. PR 2 wires the gate (`.gitlab-ci.yml`, a protected path) together with the
  other unwired guards. Fixing first and wiring second is what keeps `main` green: the reverse
  order lands a gate that fails on the branch it guards.

  MEASUREMENT DISCIPLINE, recorded because it already bit once here. The GitLab issue was first
  filed claiming 10 findings and 8 em dashes, confined to `de`/`fi`. That was wrong: the count
  came from output truncated by `tail -12`. The real figure is 16 and 14, and `en` is affected
  too. `LOCALES = ("en", "de", "fi")` and the module docstring stated 16 all along. The
  correction is recorded on the issue rather than silently edited. A6, again.

refs: >
  GitLab issue #7 ("check_copy_gate.py is wired into nothing, and main ships 16 defects"),
  including the correction note. CPO correction #867 (`muoto` -> `kunto`), cited in
  `site_v2/src/i18n/strings.ts:415-418`, which flags `secForm` as carrying the same error and
  explicitly defers it as "shipped copy he has not ruled on". This contract carries that ruling.

scope_paths:
  - site_v2/src/i18n/strings.ts
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/escalations.log

impact_map: >
  writers: none. `site_v2/src/i18n/strings.ts` is a leaf source module — it is authored by hand
    and written by no loader, no dbt model and no export script. `grep -rn "strings.ts"
    scripts/ ingestion/ dbt_project/` returns nothing.

  downstream: 23 files import it. Evidence — `grep -rlE "i18n/strings" site_v2/src` returns 23
    paths, including every consumer of the six changed keys:
      aboutWithH2h      -> components/fixture/NarrativeSlot.astro, Masthead.astro
      comingPerformance -> components/team/TeamPerformance.astro
      comingSquad       -> components/team/TeamSquad.astro
      heroVerdict*      -> components/team/DeservedHero.astro
      secForm           -> components/fixture/FormSegment.astro
      footerDataSource  -> components/chrome/SiteFooter.astro
    All consumption is through `t(lang, key, params)` (strings.ts:450). No component reads a
    dictionary directly, so no call site changes.

  layer_rules: none apply. `check_layer_contract.py` governs `dbt_project/models/**`; this diff
    touches no dbt model, no seed and no raw table. Verified: `python
    scripts/check_layer_contract.py` -> "Layer contract checks passed." both before and after.

  deploy_order: none. No warehouse object changes, so nothing is sequenced around the 04:00
    nightly and nothing breaks between merge and deploy. `deploy:site-v2` is manual-only and
    read-only against the warehouse.

  blast_radius: display text only, in three locales, on the fixture and team pages. No number,
    no metric, no query and no URL changes. Placeholder tokens are preserved exactly, which
    acceptance criterion 3 checks mechanically — a dropped `{sotd}` would render a literal brace
    to a user, and that is the only way a pure copy edit can break a page.

# The four criteria below were CPO-approved 2026-08-06 and are LOCKED — only the CPO may move
# them. This line is a NOTE and deliberately NOT a list item: the acceptance gate counts the
# bullets under `acceptance_criteria:` and demands one evidence entry each, so a note formatted
# as a bullet reads as a fifth, undemonstrated criterion. It was, and the gate caught it —
# "5 acceptance criteria declared, 4 demonstrated". Correcting the FORMAT, not the criteria.
acceptance_criteria:
  - "1. `python scripts/check_copy_gate.py` exits 0 and prints no findings."
  - "2. AMENDED 2026-08-06 — see `amendments:`. Zero U+2014 EM DASH characters in shipped string
    VALUES, which is the gate's own scope. Code comments are not shipped copy and are out of
    scope."
  - "3. Every changed string keeps its placeholder tokens exactly — the multiset of `{...}`
    tokens per key is identical before and after, shown by a diff of extracted tokens."
  - "4. `fi.secForm` uses the `kunto` root, matching the validated corpus (`kuntojakso` in
    site/i18n/fi.json)."

decisions_taken: >
  CPO approval of 2026-08-06, in this session, for all 16 fixes and for the four acceptance
  criteria above, given after the pattern and both judgement calls were put to him with their
  corpus evidence. Quoting the approved proposal:

  - The 14 em dashes are RESTRUCTURED, never swapped for an en dash: a trailing clause becomes a
    full stop, a parenthetical becomes appositive commas, and `aboutWithH2h` takes a colon. The
    shape is copied from `fi.aboutWithH2h`, which already uses a colon and is the one clean
    string of the set. An en-dash substitution would read identically and merely evade the
    check, which is the "never loosen a guard" failure in a different costume.
  - `fi.secForm: "Muotovertailu"` -> `"Kuntovertailu"`. This closes the deferral recorded at
    strings.ts:417-418.
  - `fi.footerDataSource` KEEPS the value `"Data: API-Football"` and gains a comment recording
    why identical-to-English is correct here. Evidence: the validated corpus uses `Data` as a
    Finnish word (`"Data julkaistaan kauden paatyttya."`, `"Datan lataaminen epaonnistui:"` in
    site/i18n/fi.json). The gate asks for exactly this — a comment when sameness is deliberate.

  NO THRESHOLD IS CROSSED. No new mechanism: this adds no hook, no script, no dependency and no
  CI job — the gate it satisfies already exists and stays unwired until PR 2. No recurring cost:
  no warehouse read or write, no scheduled job, no API call. No new external surface. Declared
  here because `scope-auditor` FAILs an undeclared crossing and no gate parses this field.

amendments: >
  A THIRD entry, recorded for completeness but NOT an amendment to any criterion: the
  `acceptance_criteria:` list originally carried a leading bullet reading "CPO-approved
  2026-08-06 and LOCKED", which was a NOTE, not a criterion. The acceptance gate counts bullets
  and correctly refused the commit — "5 acceptance criteria declared, 4 demonstrated". The note
  moved above the key as a comment. No criterion was added, removed, reworded or softened; the
  four are byte-identical. Recorded here rather than fixed silently because a change to the
  acceptance block is exactly what a reviewer must be able to audit.

  TWO amendments, both on 2026-08-06, both with the CPO ruling in the same conversation, both
  made on a clean tree as §2 requires.

  1. ACCEPTANCE CRITERION 2, reworded. Was: "`site_v2/src/i18n/strings.ts` contains zero U+2014
     EM DASH characters." Now scoped to shipped string VALUES.

     WHY, stated plainly because a loosened criterion is the thing reviewers must hunt: the
     original wording was MY drafting error, not a bar that turned out to be too high. It
     counted em dashes in CODE COMMENTS — 23 of them, in prose explaining past CPO rulings —
     which are not user-visible copy and which `check_copy_gate.py` correctly ignores (it reads
     dictionary values only, via `_ENTRY_RE`). Honouring the literal wording would have meant
     rewriting ~20 unrelated comment lines for no guard benefit and real diff noise.

     THE BAR DID NOT MOVE: the measured result is 0 em dashes in shipped values both before and
     after this amendment. Nothing that was failing now passes.

  2. `fi.footerDataSource`, reversing the ruling recorded under `decisions_taken`. The CPO first
     approved KEEPING "Data: API-Football" with an explanatory comment, on my recommendation.
     That recommendation was wrong on a checkable fact: `check_copy_gate.py`'s message promises
     that "the value needs a comment saying so", but its code (check 4, `untranslated values`)
     implements NO comment exemption, so the approved option could never pass. I also
     under-researched the corpus — it carries `Tietolähde` for exactly "data source"
     ("Tietolähde ei toimittanut tätä arvoa", site/i18n/fi.json).

     The CPO ruled on the corrected options: translate it to "Tietolähde: API-Football". This
     needs no change to the gate, which was the alternative and would have meant editing a guard
     so my own change could pass.

     NOTE FOR A FOLLOW-UP, deliberately NOT fixed here: the gate advertises an exemption it does
     not implement. That is a defect in `scripts/check_copy_gate.py` and belongs in the MR that
     wires it, not in this one.

decisions_reserved:
  - none for this task. Copy wording is a §10 CPO class and every string changed here was put to
    the CPO with its evidence and approved before any edit; the two genuine judgement calls
    (`secForm`, `footerDataSource`) were named as such and ruled on individually. If a reviewer
    finds a string whose new wording changes MEANING rather than punctuation, that is a §10
    question and goes back to the CPO rather than being re-worded in review.
