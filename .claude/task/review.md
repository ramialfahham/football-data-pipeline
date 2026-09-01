# Review — chore/roll-forward-sample — 2026-09-01

> **The sample roll-forward.** The committed build sample under `site_v2/src/data/` moves from the
> 2026-08-28 matchday to 2026-09-01, so the fixture comparison renders its full sixteen locked rows
> again instead of twelve. Data and a `.gitignore` allowlist only — no code, no mart, no frontend
> file. Branched from main `7caaf21`.

diff_sha256: 3d938a277dfc4a4fc02372d0af906c9c14bb2f96657f5c382911e50dde6a3a3c

rounds: 2

⭐ **THE RESULT.** The old payloads pre-dated four mart columns and were missing those keys
**entirely** — absent from the key set, not null. The new set restores `% Shots from box`,
`% Goals per shot on goal`, `% Pass accuracy` and `Ø Key passes`. **Seven of eight rendered windows
now show the full 16 rows / 7 groups.**

⛔⛔ **ROUND 1 FAILED 1–1, AND BOTH REVIEWERS WERE RIGHT ABOUT SOMETHING I HAD WRITTEN CARELESSLY.**

**`scope-auditor` FAILed on an authority record that did not exist.** The contract cited a CPO steer
as the basis for accepting a materially thinner CI sample, and `escalations.log` carried **no entry
for this task at all**. That is `feedback_dont_attribute_repo_practice_to_cpo` recurring — *"'you
ruled' needs a quote from `escalations.log` … I narrate outcomes in prose and never write them into
the file the gate parses."* I appended the STEP 5 ruling correctly two MRs ago and skipped it here
because the input arrived as conversation rather than as a formal answer, which is not a distinction
the record recognises.

⭐ **Writing it forced a correction I had glossed over.** The contract said he "answered the
thinness question". **He did not — he DISMISSED it**, asked for a plain-language explanation, then
stated *"We're doing infrastructure work and don't show anything now."* **He never said "run it
today."** Proceeding was MY reading: my recommendation to wait rested entirely on the thinner sample
being visible, and his statement removed that premise. The log now records the sequence exactly and
labels the decision an INTERPRETATION, so it can be challenged rather than merely trusted.

**`bi-analyst` PASSed but caught a measurement error.** I reported the HEBC page as "15 rows / 6
groups" — measured per page and divided by two windows, averaging two different numbers.

## scope-auditor
VERDICT: PASS

**Round 1 FAIL** — the missing `escalations.log` entry, above. **Round 2 PASS.**

risks_checked:
- The new log entry verified as a **pure append** after the STEP 5 entry's separator: no prior dated
  entry's text touched.
- The account cross-checked against `contract.md`'s `refs` and `decisions_taken §1`: both cite the
  log, both repeat "he never said 'run it today'" verbatim, and both frame the call as mine.
  Explicitly checked for **overstating in the other direction** and found none.
- ⚠ Noted the `objective` section's terser phrasing reads less self-contained, but judged it fully
  qualified by the adjacent `refs`/`decisions_taken` text, so not a misattribution on its own.
  Left as-is rather than churned: the contract gate requires a clean tree, and re-opening a passed
  item for a phrase two reviewers have read in context is not worth the stash-dance.
- Round-1 items re-checked for drift: the `scope_paths` glob fix, `.gitignore` replace-not-append
  (19 ids out, 4 in, no leftovers), `protected_override`'s no-hand-edit / no-code rules.
- The unrelated `github-actions-dbt` finding confirmed present, marked "flagged and not acted on",
  and **not** absorbed into `decisions_taken` or `acceptance_criteria`.
- Swept for new §10 decision classes, new mechanisms and credential-shaped strings: none.

## bi-analyst-reviewer
VERDICT: PASS

**Round 1 PASS**, but with the finding that drove the round-2 correction. **Round 2 PASS**, verified
against the built output rather than the corrected prose.

risks_checked:
- ⭐ **The measurement error it caught.** Reading the built HTML directly, it found `win-w1` =
  15 rows / 6 groups and `win-w2` = 16 rows / 7 groups on the HEBC fixture — two different numbers
  my per-page division had averaged into one. Re-measured by splitting at the `win win-w2` marker
  and corrected in both evidence files.
- The mechanism traced to the payload: HEBC's `w1` is null in full; Dortmund's
  `w1.defensive_actions_per_match` is null (its `blocks_per_match` is null, breaking the sum), so in
  w1 the row has data on neither side. In `w2` Dortmund's value is 24.33 and HEBC renders "–".
  ⭐ **So one fixture exercises BOTH null-display paths** — a stronger coverage result than the
  original claim, not a weaker one.
- The row-hiding logic traced to `MetricComparison.astro` and confirmed **unmodified** by this
  branch — pre-existing behaviour, not a defect introduced by the data swap.
- ⚠ **A citation-precision note, acted on**: `01_fixture_page.md:235` covers only the one-side-null
  "–"; the both-null omission belongs to `00_overview.md:37-39` and the component's own header. Both
  evidence files now cite the right rule for the right case.
- 16-row claim verified on the built pages, all four fixtures, with no "on target" text left in
  `dist/en`. Set self-consistency re-confirmed across landing / allowlist / tracked / disk.
- No hand-edited payload: `landing.json` carries only `type`/`upcoming` and the fixture payloads
  keep the full nested export shape — consistent with genuine output, not a trimmed sample.
- The four restored fields traced to `select * from mart_team_momentum` in `fetch_fixture_payloads`,
  so they are forwarded from a real mart column rather than typed into the sample.

## escalations

**One, and it is recorded rather than resolved.** The thin-matchday decision is documented in
`escalations.log` (2026-09-01) as **my interpretation of a CPO statement**, not as a ruling — see the
round-1 account above. If the reading is wrong the cost is one more roll-forward, not a bad artefact.

⛔ **AN UNRELATED FINDING, FLAGGED AND NOT ACTED ON.** Attributing this MR's BigQuery spend surfaced
**1,488 query jobs / 37.23 GB at 04:02–05:27 UTC on 2026-09-01** under
`github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com` — ~$0.23/day, recurring.
That contradicts `CLAUDE.md` ("GitHub … Its Actions run nothing") and `active_work.md` ("no nightly
SCHEDULE exists … nothing refreshes the data on a timer"), and it explains why the warehouse was
fresh enough for this roll-forward to work at all. **Cost is the CPO's.** Not investigated further
and not folded in.

⚠ **CARRIED, untouched:** step 5's two follow-ups (the seed `description` column; the four chrome
strings including the hero x-axis); the `__team`/`__player` split with no live instance; the
resolver as a committed CI gate; **#99**, **#96**, **#87**, **#98**.
