# Review — fix/freshness-guard-severity-by-cause — 2026-09-08

diff_sha256: 7487f15666a5a5e67f22a13e9b1a1797ba709f6d0f3874858351291364b83029

rounds: 4

rounds_cap_override: >
  ⛔ **THE CPO HAS NOT RULED ON THE CAP, AND THIS DOES NOT CLAIM HE HAS.** Recording that plainly,
  because inventing a ruling here is the failure `feedback_dont_attribute_repo_practice_to_cpo`
  exists to stop and this branch was already FAILed twice for weaker versions of it.
  What he DID do, verbatim and logged in `escalations.log`, is redirect the design twice mid-branch:
  *"yes, rebuild it that way"* (round 2 → 3, after he rejected the warn-severity split outright with
  *"Why and when should susp or int throw a warning at all??"*) and *"do it that way, warn severity
  for now"* (round 3 → 4, after the reconciliation turned out to be a tautology).
  **Two of the four rounds exist because the change under review became a materially different
  change.** A review of design A cannot carry forward to design C; re-reviewing after a CPO-directed
  rebuild is the cap working, not looping. Nothing was re-argued and no reviewer verdict was disputed
  — every FAIL was accepted in full and fixed.
  ⚠ He was asked to rule on this same cap question on `!156` earlier today and merged without
  answering, and has since told me twice, forcefully, to stop bringing him mechanics. I am treating
  the cap as unresolved rather than satisfied, and it is carried in the handover as an open
  precedent. If he wants these rounds counted against the cap, this branch is the one to say so on.

⚠ **THE DESIGN WAS REBUILT TWICE, so the round history is not a defect count on one design.**

    round 1  FAIL / PASS  severity classified against a §3 row that is about GRAIN violations
    round 2  FAIL / FAIL  CPO rulings quoted in the contract and logged nowhere; AND the widened
                          reconciliation was a TAUTOLOGY comparing a column to itself
    round 3  FAIL / FAIL  the fifth ruling still unlogged — the one authorising `warn`; AND stale
                          acceptance criteria describing a design two rewrites old
    round 4  PASS / PASS

⭐ Every FAIL was a claim I asserted without checking: which §3 row applied, that a column named
`played` came from the standings, that I had logged what I cited, that my acceptance criteria still
described the code. None was found by a gate.

## analytics-engineer-reviewer
VERDICT: PASS (round 4)
risks_checked:
- ⛔ **ROUND 2: it found that my reconciliation could not fail.** `mart_team_season.sql:34` is
  `m.season_games_played as played` — the mart's `played` is an ALIAS OF OUR OWN COUNT, so the test
  I widened from 1 league to 46 compared a column to itself through the `team_season_sk` join. My
  reported "0 mismatches over 1,826 rows" was 0 by construction, on any data. ⭐ And it found the
  genuine value being dropped: `fct_standings.sql:30` carries `cs.played_all as played`, which
  `int_team_season__standings_primary` reads and does not project. I had removed `SUSP`/`INT` from
  the freshness guard on the strength of that test, so the failure mode would have had NO detector.
- ⛔ **ROUND 3: it refused to accept the Al Wehda row as evidence without a check**, and it was
  right. `fct_standings` is grained on `(league_code, season, team_id, group_name)`; that team-season
  carries TWO rows with an identical `raw_ingested_at`, so my `qualify row_number()` tiebreak was
  unstable. Measured after the flag: 299 team-seasons have multiple rows and **204 disagree on
  `played`, spread up to 13 games**. Replaced with `max(played)`.
- **ROUND 3 also caught two acceptance criteria left over from the mart design** — "returns 0 rows
  across 46 leagues" and "every league in the mart has a non-null `played`" — both false against
  code that returns 3 rows and touches no mart.
- **ROUND 4** re-derived the join grain from `int_team_season__metrics`'s own docstring rather than
  my claim; confirmed the deleted file is gone from disk; checked `selectors.yml` directly to verify
  the new test's tags do not accidentally exclude it from CI; and checked the registry has a single
  `AFCCL` entry, removing the obvious way the "never ingested" inference about Al Wehda could be
  wrong.
- ⚠ It stated the limit of its own PASS on `max(played)`: if a later-stage standings table were
  ADDITIVE rather than cumulative, `max` would understate and could mask a shortfall. It judged that
  an acceptable, disclosed trade-off at `warn` severity rather than a hidden defect, and said it
  could not close the question without running BigQuery. Recorded as a limit, not a clearance.
- ⚠ It caught an arithmetic slip in the evidence — "982 tests, one fewer than before" when a delete
  plus an add nets to zero. Corrected to "UNCHANGED from main".

## scope-auditor
VERDICT: PASS (round 4)
risks_checked:
- ⛔ **ROUND 1: it FAILed the severity classification as a §10 rule extension.** §3's row 2 reads
  *"Grain violation from source data quality issue"* — a uniqueness rule, not a staleness one — and
  `!155` had already established that this class of call is the CPO's. Moot after the rebuild: there
  is no severity to classify, because those statuses are simply not in the test.
- ⛔ **ROUNDS 2 AND 3: it FAILed twice for the same thing, and the second time was worse.** The CPO's
  rulings were quoted in `contract.md` and recorded nowhere checkable; `escalations.log` had no entry
  for this branch, and its last word on the subject was two older entries saying the freshness guard
  was *unruled*. I then logged four of the five quotes and left out *"do it that way, warn severity
  for now"* — **the one authorising the highest-stakes call in the branch**, shipping a knowingly-red
  test at `warn`. It grepped, found zero hits, and failed it again.
- **ROUND 4** verified all five quotes resolve exactly once, and that the log is append-only past
  main — one hunk, `+` lines only, totals reconciling.
- ⭐ It then ruled on the deletion rather than deferring: removing a test that is provably incapable
  of failing is **"the opposite of a coverage-cut"**, because coverage went from a check that could
  never fire to one firing on confirmed defects.
- ⭐ And it ruled on shipping a red test at `warn`: not the A6 dodge pattern, because the test ships
  red and visible, the ruling is logged verbatim, GitLab #110 is named as the open rule its rows wait
  on, and `decisions_reserved` carries both the "does not license closing #110" caveat and the
  "nothing alerts on a dbt warning" gap forward.
- Scope, credentials, new-mechanism and recurring-cost checks all clean.

## escalations
- **`2026-09-08 — fix/freshness-guard-severity-by-cause — A VALID STATUS IS NOT AN ALARM`**, with
  five verbatim rulings: the instruction, the challenge that broke my first design
  (*"Why and when should susp or int throw a warning at all??"*), the classification
  (*"it's a valid status info and we should be able to handle it the right way"*), the rebuild
  approval, and the severity (*"do it that way, warn severity for now"*).
- ⚠ The entry states what *"for now"* does NOT license: it is not a decision that the three rows are
  acceptable, not authority to close **#110**, and not a general licence to downgrade a red test.

## ⛔ WHAT THIS BRANCH SHOULD BE REMEMBERED FOR

**1. I read a column NAME and asserted its provenance.** `played` sounded like the standings' count.
It was an alias of our own. Every number I reported from it was real, correctly computed, and
meaningless — which is the dangerous kind of wrong, because nothing looks broken.

**2. Two rewrites left claims behind both times.** Round 3 found acceptance criteria describing a
design two versions old. Fixing the design is not fixing the document that authorises it, and I only
ever updated the section I was thinking about.

**3. The CPO's question was better than my design.** *"Why and when should susp or int throw a
warning at all??"* had no good answer, and I had written several paragraphs defending the thing it
asked about. The fix that followed removes a concern from one test and an arbitrary restriction from
another — one fewer test than I started with.

**4. The detector found, unprompted, a defect I had spent the morning finding by hand** — and a
second one, from a completely different cause, that nobody knew about. That is the argument for
reconciling a symptom against an independent authority instead of enumerating provider statuses.
