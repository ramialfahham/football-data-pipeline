# Task contract — the sample roll-forward

objective: >
  **Replace the committed build sample so the fixture comparison renders all sixteen locked rows
  again instead of twelve.**

  `site_v2/src/data/` holds a snapshot of one matchday so CI can build the site without BigQuery.
  It pins **2026-08-28**; today is **2026-09-01**, so it is four days past. Two consequences, both
  measured rather than assumed:

  1. **Four of the sixteen locked display rows do not render.** Probed a committed payload: the
     fields are **ABSENT FROM THE KEY SET**, not null — the snapshot predates those mart columns.
     `shots_inside_box_pct`, `finishing_efficiency_pct`, `passes_accuracy_pct`,
     `passes_key_per_match`. All four are emitted by `mart_team_momentum` today (`:63`, `:77`,
     `:86`, `:107`), so the roll-forward genuinely restores them.
  2. **It cannot be refreshed in place, and that is the whole trap.**
     `fetch_fixture_payloads` selects `status_short in ('NS','TBD') and fixture_date >=
     current_date()`; once a fixture kicks off its pre-match form rows leave `mart_team_momentum`
     entirely. A rerun writes thousands of NEW payloads and silently leaves every committed one
     untouched — exactly what happened on 2026-08-28, where the export exited 0, reported 5,066
     payloads written, and not one tracked file changed. **The set is REPLACED, never appended.**

  ⭐ **CPO steer this session**, on whether the thin next matchday is acceptable: *"We're doing
  infrastructure work and don't show anything now."* So the snapshot is a BUILD INPUT, not a shop
  window, and the only live question is whether it still exercises the components. It does — see
  `decisions_taken §2`.

refs: >
  **`site_v2/src/data/README.md`** documents the procedure and the trap in full, including the
  measured 2026-08-28 failure. This MR follows it verbatim rather than inventing one; the
  `--entities teams,fixtures` list is copied from **`.gitlab-ci.yml:941`**, where a comment marks it
  load-bearing.

  **`.claude/active_work.md`** carried this as the last owed item of the "after step 4" pair, and
  the standing instruction was that the CPO decides when it runs. He said, verbatim: **"start the
  sample roll-forward"**. That is the authority for doing the task.

  ⛔ **THE THIN-MATCHDAY DECISION IS AN INTERPRETATION, NOT A RULING, AND THE RECORD NOW SAYS SO.**
  `.claude/task/escalations.log`, dated 2026-09-01, sets out exactly what happened: I asked whether
  to run today or wait for 2026-09-04, **he DISMISSED the question**, asked for a plain-language
  explanation, and then said — verbatim and in full — *"We're doing infrastructure work and don't
  show anything now."* **He never said "run it today".** I read that statement as removing the sole
  premise of my own recommendation (that the thinner sample is visible) and proceeded.
  ⚠ `scope-auditor` FAILed round 1 because this contract cited that steer as authority while the log
  carried no entry at all — the recurrence of `feedback_dont_attribute_repo_practice_to_cpo`. The
  entry is now written, in the form above, so the interpretation can be challenged rather than
  merely trusted.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .gitignore
  - site_v2/src/data/README.md
  - site_v2/src/data/landing.json
  - site_v2/src/data/competitions.json
  - site_v2/src/data/competition_index.json
  # ⚠ GLOBS, not bare directory names. `scope_paths` entries are fnmatch patterns and `*` does not
  # cross `/`, so `site_v2/src/data/teams` matches the DIRECTORY and nothing inside it. The contract
  # gate caught that on the first export — correctly — and this is the fix, not an exemption.
  - site_v2/src/data/fixtures/*.json
  - site_v2/src/data/teams/*.json

protected_override: >
  ⛔ **NO PAYLOAD IS EVER HAND-EDITED.** Every committed JSON is verbatim export output. If a value
  looks wrong the fix is upstream in a mart, never in the file. `site_v2/src/data/README.md` states
  this twice and it is the reason the sample can be trusted as evidence at all.

  ⛔ **NO CODE CHANGES.** `scripts/export_site_data.py`, the marts and the frontend are untouched.
  This MR replaces DATA and the allowlist that pins it. If the export turns out to need a fix, that
  is a separate MR with its own contract — flag it, do not fold it in.

  ⛔ **THE `.gitignore` FIXTURE ALLOWLIST IS REPLACED, NEVER APPENDED TO** (block at `:262-289`).
  A stale id pins a payload no rerun can ever update, which is how the previous set came to serve
  column names renamed two MRs earlier.

impact_map: >
  Data-only. The committed sample is read at build time by `site_v2` and by nothing else; no dbt
  model, no export code path and no test imports it as a module. Its blast radius is the built
  pages plus `audit-seo.mjs`, which fails the build on an internal link resolving to no emitted
  page — the one check that catches a landing↔fixtures mismatch, and only in CI.

  ⚠ **A local build cannot reproduce that check.** A full export leaves thousands of untracked
  payloads on disk, so every link resolves locally while CI sees only the tracked set. `git clean
  -fX site_v2/src/data` before building is what makes the local build honest.

acceptance_criteria:
  - The fixture comparison renders **16** rows per window, not 12, measured from built `dist/` with
    comments stripped, and the four restored labels named explicitly.
  - **The set is self-consistent**: the fixture ids `landing.json` links, the ids in the `.gitignore`
    allowlist, and the files tracked under `fixtures/` are the SAME set, asserted mechanically.
  - Every committed payload is verbatim export output — no hand edits.
  - `npm run build` green with `audit-seo … OK.`; `npm test` 76/76; `pytest` at the `7caaf21`
    baseline; no untracked payload bulk left in the tree.

decisions_taken: >
  ⭐ **§1. RUN IT TODAY, ON A DELIBERATELY THIN MATCHDAY — and this is MY call on HIS statement, not
  a ruling of his.** The next matchday is **2026-09-01: 4 fixtures across 3 competitions**
  (`CIT` ×2, `DFBP`, `SPL`), against the outgoing set's 19/13. I put the trade-off to him — thin now
  versus 28/16 on 2026-09-04, recommending the wait — **he dismissed the question**, and then said
  *"We're doing infrastructure work and don't show anything now."* My recommendation to wait rested
  entirely on the thinner sample being VISIBLE; his statement removes that premise, leaving no
  argument for delay. So I proceeded today. Full account, including that he never said "run it
  today", in `escalations.log` 2026-09-01. **If the reading is wrong the cost is one more
  roll-forward, not a wrong artefact** — but it is his to overturn, which is why it is written down
  as an interpretation.

  ⭐ **§2. THE THIN SET STILL EXERCISES THE COMPONENTS, MEASURED BEFORE COMMITTING TO IT.**
    · **Both competition shapes**: 3 `domestic_cup` + 1 `domestic_league`, so the standings block is
      exercised on the league fixture and the no-table path on the cups.
    · **Both form paths**: the matchday has **7** `mart_team_momentum` rows for 8 team-slots, so one
      side has an absent W1 — the same deliberate absent-path coverage the outgoing set documented
      for `1575140`, arrived at by measurement rather than luck.
    · **The four restored columns are populated**: 6–7 of the 7 rows non-null.

  ⚠ **§3. THE CLOCK IS PART OF THE TASK.** First kickoff is **16:00 UTC**; it was 08:24 UTC when
  the target set was measured. A fixture that kicks off leaves the selector, so the set can shrink
  between measuring and exporting. **The committed set is verified against what the export actually
  returned, never against this contract** — and if it comes back smaller, that is reported, not
  papered over.

  ⭐ **§4. COST IS MEASURED, NOT ESTIMATED AFTER THE FACT.** Reads marts only, writes no BigQuery
  table, no ingest and no recurring cost. Read-only probing to build this plan billed ~84 MB; the
  export's own scan is reported in the evidence.

decisions_reserved:
  - ⛔ **Nothing enforces the landing↔allowlist match except `audit-seo.mjs` in CI, after the fact.**
    `site_v2/src/data/README.md` names the real fix — CI building from a live export instead of
    stored samples — as infrastructure work outside #367. Not proposed here; this MR asserts the
    match mechanically in its own evidence instead, which is a check, not a guard.
  - ⚠ CARRIED, untouched: step 5's two follow-ups (the seed `description` column; the four chrome
    strings including the hero x-axis); the `__team`/`__player` split with no live instance; the
    resolver as a committed CI gate; **#99**, **#96**, **#87**, **#98**.

done_when: >
  - 16 rows render per window, the four restored labels named, measured from `dist/`.
  - The three id lists (landing, allowlist, tracked files) are identical, asserted mechanically.
  - `.gitignore`'s allowlist and `site_v2/src/data/README.md` both describe the NEW set — date,
    counts, and the form-window coverage sentence.
  - Departed payloads `git rm`'d; no untracked bulk left; every committed payload verbatim output.
  - Gates green, the site built, `pytest` at baseline, and the export's BigQuery cost reported.
  - Blinded review with `review.md` bound by `--staged-hash`. **Round cap 3.**
