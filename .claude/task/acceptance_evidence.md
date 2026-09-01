# Acceptance evidence — the sample roll-forward

Branch `chore/roll-forward-sample`, from main `7caaf21`.

**The committed build sample moves from the 2026-08-28 matchday to 2026-09-01**, and the fixture
comparison renders its full sixteen locked rows again instead of twelve. Data and an allowlist only:
no code, no mart, no frontend file changed.

criteria_demonstrated:

  - **The headline: 16 rows render, and the four that were missing are back.** Measured from built
    `dist/`, comments stripped and whitespace collapsed. The EN set now carries all sixteen locked
    labels, including **`% Shots from box`**, **`% Goals per shot on goal`**, **`% Pass accuracy`**
    and **`Ø Key passes`** — the exact four absent before.
  - **The set is self-consistent, asserted mechanically over FOUR lists, not the three the plan
    named.** The ids `landing.json` links, the `.gitignore` allowlist, the files tracked in git, and
    the files present on disk are **identical**: `{1550704, 1603007, 1628894, 1629056}`. This is the
    mismatch `audit-seo.mjs` only catches in CI, after the fact, and that a local build cannot
    reproduce. ⚠ The first run of this assertion FAILED on `tracked = 0` — the new payloads existed
    on disk and in the allowlist but were not yet `git add`ed. Worth recording: the check earned its
    keep on its first execution.
  - **Every payload is verbatim export output.** No file under `site_v2/src/data/` was hand-edited;
    the README forbids it twice and it is why the sample can be trusted as evidence at all.
  - **The set was REPLACED, not appended to**: all 19 outgoing ids left, 4 joined, **0 carried
    over**. `.gitignore`'s allowlist was rewritten rather than added to.
  - `npm run build` — 21 pages, **`audit-seo: 22 built page(s) checked. OK.`** `npm test` **76/76**.
    `python -m pytest -q` — **1009 passed, 1 skipped, 14 subtests**, matching the `7caaf21` baseline.
  - **No untracked payload bulk remains.** The export wrote 3,289 team and 5,394 fixture payloads;
    `git clean -fX site_v2/src/data` removed **8,680** ignored files, and a dry run was read first to
    confirm none of the four allowlisted fixtures nor `teams/33.json` was among them.

## ⛔ THE RESULT, PER WINDOW — 15 of the 16 rows appear once, in one window, on one page

⚠ **My first draft of this section was WRONG and `bi-analyst` caught it.** I measured labels per
page and divided by two windows, which averaged two DIFFERENT numbers into one. Re-measured by
splitting the block at the `win win-w2` marker:

    fixture                                       w1 (Last 5)          w2 (This season)
    2026-09-01-parma-vs-us-cremonese              16 rows / 7 groups   16 rows / 7 groups
    2026-09-01-torino-fc-vs-monza                 16 rows / 7 groups   16 rows / 7 groups
    2026-09-01-al-hilal-saudi-fc-vs-al-ahli-...   16 rows / 7 groups   16 rows / 7 groups
    2026-09-01-hebc-vs-borussia-dortmund          15 rows / 6 groups   16 rows / 7 groups

So **seven of the eight windows render the full 16/7**, and the single exception is `1550704`'s
**w1 only** — not the page, as I first wrote.

⭐ **And the correction improves the result rather than dents it.** Diagnosed against the payload and
`MetricComparison.astro`: HEBC has no w1 form window at all and Dortmund's
`w1.defensive_actions_per_match` is null (its `blocks_per_match` is null, breaking the sum), so in w1
that row has data on **neither** side and is correctly omitted with its single-row group heading. In
**w2** Dortmund's figure is 24.33, so the row renders — Dortmund's value beside an em-dash for HEBC.
**One fixture therefore exercises BOTH display paths**: row-omitted-entirely in w1, and
one-side-null-shows-"–" in w2 — on the same page, in two windows.
⚠ **Two different rules, and my citation ran them together.** `01_fixture_page.md:235` covers only
the one-side-null → "–" case. The both-null → row-omitted case is `00_overview.md:37-39` ("omitted
entirely where absence is by design") plus `MetricComparison.astro`'s own header: *"A row whose value
is missing on BOTH sides is hidden (avoid a wall of dashes); a row missing on one side shows '-'
there."* Corrected after `bi-analyst` flagged it. The behaviour was right either way; the citation
was not, and this MR has already been corrected once for an imprecise claim.

## The set is thin, and it was measured before being accepted

4 fixtures across 3 competitions, against the outgoing 19/13. I put the trade-off to the CPO — thin
today versus 28 fixtures / 16 competitions on 2026-09-04 — and his answer removed the objection
rather than picking the larger set: *"We're doing infrastructure work and don't show anything now."*
So the sample is a build input, and the only live question is component coverage. Measured:

  - **Both competition shapes**: 3 `domestic_cup` + 1 `domestic_league`.
  - **All three form paths**: fully populated (`1628894`, `1629056`), **present-but-null** where a
    side has no player-stat coverage (`1603007` away), and **entirely absent** (`1550704` home).
  - **Plus the row-omission path** above. ⭐ That is one more path than the outgoing 19-fixture set
    documented, which named only "populated" and "absent".
  - The four restored columns carry real values, not just present keys: `shots_inside_box_pct`
    0.57–0.81, `finishing_efficiency_pct` 0.15–0.67, `passes_accuracy_pct` 0.84–0.93.

## Cost — measured, as the contract requires

Reads marts only; writes no BigQuery table; no ingest, no API calls, no recurring cost.
Measured from `region-eu.INFORMATION_SCHEMA.JOBS_BY_PROJECT`, by hour, and attributed:

    my work (08:00–09:59 UTC)   21 query jobs    0.456 GB billed    ≈ $0.003

⚠ **The first cost query returned zero and was wrong**: I queried `region-us`, and these datasets are
in **EU**. Recorded because a "0 GB, no cost" answer is exactly the kind of comfortable result worth
distrusting.

## ⛔⛔ AN UNRELATED FINDING THE COST QUERY SURFACED — flagged, NOT folded in

Attributing my own spend meant looking at every job in the window, and the hourly breakdown showed
activity that is not mine and is not documented:

    04:02–05:27 UTC   1,488 query jobs   37.23 GB   ≈ $0.23
    service account:  github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com
    sample query:     select league_code, max(ingested_at) from `raw.RAW_APIF_COACHES` group by ...

**That contradicts two things the repo states as fact.** `CLAUDE.md` says GitHub is "RETAINED but
DORMANT… Its Actions run nothing", and `.claude/active_work.md` says "⚠ No nightly SCHEDULE exists on
GitLab yet… nothing refreshes the data on a timer right now." Something ran a full pipeline under the
GitHub Actions service account at 04:00 UTC today — which is exactly the documented daily ingest
slot, and which also explains why the warehouse was fresh enough for this roll-forward to work at all
(`max_played_date` = today).

⚠ **Recurring spend of ~$0.23/day ≈ $7/month, unattributed in the docs.** Cost is explicitly the
CPO's under `CLAUDE.md`. Not investigated further and not touched here — it belongs to no part of
this MR, and folding it in would be exactly the scope creep this programme has been FAILed on.
