# Acceptance evidence — one shared competition-ordering rule + the matchday selection

criteria_demonstrated:
  - **One comparator, two callers — verified by grep, not by claim.**
    `grep -rn "compareCompetitions" site_v2/src` returns its single definition in
    `lib/competitionOrder.mjs` plus its two internal callers (`groupAndOrderCompetitions` for the
    competitions page, `orderUpcomingGroups` for the home page). No second implementation of the
    key exists: the Python export contains no ordering logic (it only sorts fixtures by kickoff for
    a deterministic payload diff, documented as NOT the display order), and no `.astro` file sorts
    competitions itself. `compareCompetitions` was NOT edited — the competitions page's 7 existing
    tests pass unchanged, pinning that its behaviour did not move.
  - **Same-day competitions render in REGION order on the built page.** Built `dist/{de,en,fi}/index.html`
    all render the group order `['UEFA Champions League', 'Copa Libertadores']` — UEFA
    (`region_rank` 1) before CONMEBOL (`region_rank` 3), both on 2026-08-18. Read from built HTML by
    regex over `<div class="gh">`, all three locales identical.
    ⚠ HONEST LIMIT: today's live data does not by itself DISCRIMINATE the two rules — UCL also
    kicks off earlier (19:00 vs 22:00), so pure chronology would produce the same order today. The
    discriminating proof is the unit test below, which was seen RED.
  - **The region rule was seen RED against the old behaviour.** Temporarily reverted
    `orderUpcomingGroups` to pure chronology (sort on `next_kickoff_datetime` only) and re-ran
    `node --test`: `tests 76 / pass 75 / fail 1`, the failure being
    "home groups on the SAME day order by region_rank, not by clock time". Reverted; 76/76 green.
    That test uses a 10:15 Eredivisie vs a 19:00 Premier League — the exact example the 2026-08-16
    ruling names as noise — so it can only pass if region breaks the same-day tie.
  - **Day still beats region — selection stays chronological.** `a UEFA group does NOT jump a
    better-region-ranked group playing an earlier day` asserts an OFC group (rank 7) kicking off
    2026-08-20 outranks a Premier League group (rank 1) on 2026-08-21. Green. This is why the CPO's
    sub-question about selection vs ordering resolved itself: the key answers it.
  - **`region_rank` is served, never derived.** Every group in the regenerated
    `site_v2/src/data/landing.json` carries it (`groups missing region_rank: none`, checked over the
    real export output). Its source is `mart_competition_index` — a `select league_code, region_rank`
    added to `fetch_landing_payload`, priced first at **644 bytes** (`bq query --dry_run`). The
    registry YAML's `confederation` is NOT mapped to a rank in Python; that would be a taxonomy
    mapping the consumption-layer contract forbids.
  - **The block is a matchday, with no fixed count anywhere.**
    `grep -rn "_HERO_FIXTURE_LIMIT" scripts/ tests/ site_v2/src` returns exactly ONE hit —
    `export_site_data.py:77`, the comment recording that the constant was removed and why. No
    definition, no reference, no default argument: the constant is gone as CODE and survives only as
    the explanation. (Stated precisely because "zero hits" would have been false.) The regenerated
    payload holds
    `distinct kickoff dates in payload: ['2026-08-18']` — one date, 2 groups, 4 fixtures. The
    previously committed sample held 12 fixtures spanning **two** dates (2026-08-03 and 2026-08-04),
    which is what the cap produced and is not a matchday.
  - **The matchday test was seen RED against the retired cap.** Temporarily restored
    `for f in fixtures[:12]` and re-ran: `FAILED test_hero_takes_the_whole_first_matchday_and_nothing_from_the_next_day`
    with `assert 12 == 13`. The fixture set deliberately puts THIRTEEN matches on day one — one more
    than the old cap — so the test cannot pass against the previous behaviour. Reverted; 46/46 pass.
  - **Gates green.** `python -m pytest tests/test_export_site_data.py` -> 46 passed.
    `node --test` (site_v2) -> 76 passed. `python scripts/check_copy_gate.py` ->
    "COPY GATE ok: 450 strings across 3 locales". `node scripts/check-page-specs.mjs` ->
    "4 page(s) validated against their specs. OK." `npm run build` ->
    "audit-seo: 61 built page(s) checked. OK.", 60 pages.
    `python -m ruff check --config .ruff-ci.toml` (the CI config) -> "All checks passed!".
  - **Rendered size MEASURED, not predicted.** Live at 440px viewport: 4 matches, 2 groups,
    `scrollHeight` 3301px, `horizontalOverflow: false`. ⚠ Today is a QUIET day — the honest range is
    wider: `10_home.md`'s measurement recorded a busiest day of 57 fixtures. The block will be
    materially longer then. Per the contract's decisions_reserved that is a CPO call on the block
    (#908 parks a "more matches" control), NOT a number to reintroduce here — reported, not acted on.
    ⚠ The SHORT direction is the one this build actually hit (4 matches, where the retired count
    showed 12 by borrowing the next day) and it was initially registered nowhere; now written into
    `10_home.md` §5(1) as an open product question alongside the long direction.
  - **The matchday decision lives in SQL, not Python (round-1 FAIL fix).** The first implementation
    took `min()` over the fetched rows and filtered in a Python loop; analytics-engineer-reviewer
    ruled that window selection in the consumption layer, citing this same file's `_featured_season_row`
    (#846), where an identical "pick from a set" was moved out of Python. Now a
    `where fixture_date = (select min(fixture_date) from upcoming)` clause beside the
    upcoming-window filter that always lived there. Verified two ways: the re-exported payload is
    **byte-identical** to the Python-filtered one (`a == b` -> True), so no semantic drift between
    `fixture_date` and the UTC kickoff date; and `bq query --dry_run` prices both forms at exactly
    **4,862,919 bytes** — the subquery costs nothing. `test_hero_matchday_selection_lives_in_the_query_not_in_python`
    pins the placement so it cannot drift back.
