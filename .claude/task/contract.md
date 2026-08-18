# Task contract — one shared competition-ordering rule, and the matchday selection

objective: >
  Two live surfaces order competitions against each other with DIFFERENT rules. The competitions
  page uses the CPO's 2026-08-16 key (has-upcoming → calendar day → region_rank → kickoff →
  league_code). The home page's "Next matches" predates that ruling and uses raw chronology, so it
  still carries the exact noise the ruling was written to remove. Make the 08-16 key the single
  site-wide rule, implemented ONCE and called by both. Separately, and by the same CPO decision
  this session, drop the hardcoded 12-fixture cap on the home block in favour of the natural unit:
  every match on the next day that has football.
refs: `escalations.log` 2026-08-16 (the ordering key, Rulings 1-4) · GitLab #367 (the home page as
  built) · `10_home.md` §5(1) (GAP-02, the retired count) · #908 (a "more matches" control, parked)

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_export_landing.py
  - site_v2/src/lib/competitionOrder.mjs
  - site_v2/src/lib/competitionOrder.test.mjs
  - site_v2/src/lib/types.ts
  - site_v2/src/components/home/HeroFixtures.astro
  - site_v2/src/data/landing.json
  - site_v2/src/data/fixtures/*.json
  - .gitignore
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md
  - .claude/task/escalations.log
  - .claude/active_work.md

acceptance_criteria:
  - The home page and the competitions page order competitions with the SAME comparator function,
    called from two places — verified by grep showing exactly one implementation of the key and no
    second copy of its logic in Python or Astro.
  - On the rendered home page, competitions kicking off on the same day appear in region order
    (UEFA before CONMEBOL before AFC …), NOT in raw clock-time order. Demonstrated by hand-
    computing the expected order from the committed `landing.json` and matching it against the
    built page, all three locales.
  - A competition playing an earlier day still outranks one playing a later day regardless of
    region — the day bucket precedes region_rank, exactly as on the competitions page.
  - `landing.json` carries `region_rank` on every upcoming group, sourced from
    `mart_competition_index`, and NOT computed anywhere in Python or in the frontend.
  - The home block shows EVERY match on the earliest upcoming kickoff date and none from the day
    after — no fixed count anywhere in the path. `_HERO_FIXTURE_LIMIT` is gone from the codebase.
  - `node --test` (site_v2/) green including new ordering tests; `pytest tests/test_export_site_data.py`
    green including a matchday-selection test whose fixture set exceeds twelve on day one, so it
    would FAIL against the old capped behaviour.
  - Each new test seen RED before green (comparator broken / cap re-added), recorded in the
    evidence file — a passing test that was never seen fail is decoration (#904).
  - `python scripts/check_copy_gate.py` and `node scripts/check-page-specs.mjs` pass.
  - The rendered match count and page height under the new rule are MEASURED and reported at
    desktop and mobile, not predicted.

impact_map: >
  writers: `scripts/export_site_data.py` gains one small read of `mart_competition_index`
    (already live, shipped !65; the same mart `fetch_competition_index` queries). Priced with
    `bq query --dry_run` BEFORE running. `landing.json` is regenerated from a real prod run.

  downstream: `landing.json`'s shape changes additively (`region_rank` per group) and its CONTENT
    changes materially — the group list is now a matchday, not a 12-slice. Only `HeroFixtures.astro`
    consumes it. `competitionOrder.mjs` gains one exported function; `compareCompetitions` itself is
    UNCHANGED, so the competitions page's behaviour must not move — pinned by its existing 7 tests
    staying green without edit.

  layer_rules: ordering stays in the PAGE layer, per 08-16 Ruling 4 ("the mart carries facts, the
    spec declares the ORDER BY") and the CPO's correction "I don't agree that sorting has to be
    decided in the mart". The export selects and groups only. `region_rank` MUST come from the mart
    — deriving it in Python from `confederation` would be a taxonomy mapping, which
    `layering.md`'s consumption-layer contract forbids outright.

  blast_radius: the home page's first block changes visibly (order AND how many matches). The
    competitions page must not change at all. No dbt model, seed or mart is touched.

decisions_taken: >
  Both from the CPO, in conversation this session, and recorded in `escalations.log` in the same
  commit rather than left in chat:

  1. ONE SHARED RULE. The 2026-08-16 key becomes the single site-wide rule for ordering
     competitions against each other. Its own stated reasoning already covered the home page
     ("even matches from national teams can rank occasionally before club league matches"), and the
     home page simply predated it. Because DAY precedes REGION in the key, match selection stays
     chronological and only group order changes — so this is not a re-decision of the key, it is
     the key applied where it always reached.

  2. THE HARDCODED 12 GOES. CPO: "we will show what we have, more matches will come, because we
     ingest more competitions." The cap was reasoned (it filled the first screenful) but does not
     scale: as competitions are onboarded, twelve slots hold fewer and fewer competitions, so the
     block narrows exactly as the site broadens. Replaced by the next matchday — every match on the
     next day that has football. This does NOT reopen the calendar-window question GAP-02 settled:
     "today" was rejected for rendering 1 row on some days, and "the next day that HAS matches" is
     never empty by construction.

  NEW MECHANISM: none — one existing comparator gains a second caller. RECURRING COST: one extra
  small mart read per export run, priced before use.

decisions_reserved:
  - What to do if a busy matchday reads too long (57 fixtures was the measured worst day). The
    answer is a CPO call on the block — #908 already parks a "more matches" control — and NOT a
    new invented cap slipped back in here. The measurement gets reported; the decision is not made.
  - Flattening browse / deleting the "By country" axis (#44) — untouched here.
  - Top players and Top teams (GAP-27..GAP-31 warehouse work) — untouched here.
  - The hero reading `core.fct_fixture`/`core.dim_team` directly instead of a mart — a real layer
    defect, flagged, deliberately NOT folded into this change.
  - The league group heading's missing badge/arrow/link — needs the league page to exist.

amendments:
  - 2026-08-18: + `site_v2/src/data/fixtures/*.json` and `.gitignore` — authority: mechanical
    consequence, caught by the `audit-seo` build gate, not a new decision. Regenerating
    `landing.json` changes WHICH fixtures the home page links to, and the committed fixture sample
    was still the 2026-08-03 set, so the build failed with 8 dead internal links (4 fixtures x
    2 locales shown). `site_v2/src/data/README.md` documents exactly this — "⚠ Refresh as a set…
    regenerate `landing.json`, then update the `.gitignore` allowlist and the committed files to
    match it, in the same commit" — and names `audit-seo` as the only thing that catches a
    mismatch. It did. Adding the four payloads the new landing references plus their allowlist
    rows IS that documented procedure, so no CPO judgment is involved. Recorded on a clean tree.

  - 2026-08-18: + `tests/test_export_landing.py` — authority: MY BREAKAGE, not a scope choice.
    Removing `group_upcoming_fixtures`'s `limit` parameter broke two tests in this file
    (`TypeError: unexpected keyword argument 'limit'`). I did not catch it because I ran only
    `tests/test_export_site_data.py`, never the suite — analytics-engineer-reviewer found it in
    round 3 while tracing the signature, outside its own judging scope. Fixing a test my own change
    broke is not new scope; leaving it red would ship a broken suite. Recorded on a clean tree.

done_when:
  - Every item in `acceptance_criteria` demonstrated and recorded in
    `.claude/task/acceptance_evidence.md` under a `criteria_demonstrated:` marker (2-space indented
    bullets — the gate's `_block()` parser stops at column 0), read from BUILT output.
  - `.claude/task/rendered_page_evidence.md` replaced wholesale for THIS diff.
  - `escalations.log` carries both rulings, dated, at the time they were made.
  - `10_home.md` and `99_gaps_register.md` no longer state the retired count as current.
  - `.claude/active_work.md` updated in the same commit, under 16,000 characters.
