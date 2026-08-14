# Acceptance evidence — #367 landing page

Each criterion below is the CPO's own wording from `contract.md`'s LOCKED `acceptance_criteria`,
then how it was shown. Read from BUILT output (`site_v2/dist/`) or from a command's real output,
never from source and never from intention.

Build under test: `npm run build`, 2026-08-08 after the trending cut. Closing lines:
`audit-seo: 46 built page(s) checked. OK.` and `[build] 45 page(s) built in 5.95s`.

⚠ 63 -> 45 pages. Eighteen fewer, being the six team payloads deleted with trending × 3 locales.
Those pages were orphans the moment the block went: the trending row's team link was the only link
to a team page anywhere on the site.

criteria_demonstrated:

  - **1. Upcoming matches grouped by competition, each linking to its match page, a competition
    with nothing coming up absent.** Rendered `/en/` carries 12 matches under 4 competition
    headings in kickoff order: Veikkausliiga 1, Liga Profesional 5, Champions League 5, Conference
    League 1. Four headings out of 45 registry competitions, so absence is real and no row is
    zero-filled. The links are proven by the audit rather than by inspection: `audit-seo.mjs`
    check 8 fails the build on any internal href that does not resolve to an emitted page, and the
    build passed. Its page-count line confirms the targets exist:
    `/[lang]/[competition]/matches/[fixture] -> 39`, being 13 fixtures across 3 locales.

  - **2. Every competition browsable two ways, from the registry, no competition named in the
    template.** Rendered `/en/` shows 4 groups (Leagues 16, Cups 5, European club 9, National
    teams 15) and 15 country hubs, matching `build_nav`'s two axes over the registry. Verified by
    command, not assertion: grepping the four home components and the page for any of 21 league
    codes returns nothing. PARTIAL — the country axis renders country NAMES only and never
    `browse.countries[].competitions[]`, which the payload carries and the spec declares. Caught
    by bi-analyst-reviewer, open as finding 5.

  - **3.** ⛔ **STRUCK 2026-08-08 — the criterion no longer exists, so there is nothing to
    demonstrate.** It read "Trending: longest runs first, both directions, at most two per
    competition, six stories". The CPO's composition for this page is next matches → Top players →
    Top teams → browse, with no trending block, so the block and everything behind it were deleted
    from this PR; `contract.md` records the strike and the reasoning.

    Two things are worth keeping from what stood here. First, the evidence I had written passed:
    six rows, descending 19/19/19/18/15/14, cap held. It demonstrated the criterion faithfully and
    the criterion was still wrong — **a green acceptance check is not evidence that a block belongs
    on the page.** Second, four of those six rows were `winless` runs, a signal the CPO had
    explicitly dropped on 2026-08-04. The criterion's own "both directions" wording contradicted the
    later ruling, and I demonstrated against the criterion instead of noticing the conflict.

    The measurements behind the signal selection are kept in `10_home.md` §5(3); they are warehouse
    facts and survive the block.

  - **4.** ⛔ **STRUCK 2026-08-08 — the criterion no longer exists, so there is nothing to
    demonstrate.** The CPO ruled the stats-teasers block useless and it was deleted from this PR;
    `contract.md` records the strike and the reasoning. The evidence that stood here described a
    block that no longer ships, which made this file assert a rendered fact that was no longer
    true — the same defect `rendered_page_evidence.md` was rewritten for in the same round.
    The three eligibility rules the deleted code encoded are NOT lost: they are carried into
    GAP-24…GAP-29 and recorded in `10_home.md` §5(4) so the replacement mart inherits them rather
    than rediscovering the Premier League pre-season table, the zero-player-stats competition and
    Copa Libertadores' five joint-first group winners.

  - **5. Three locales, no shared title or description.** Read from `dist/{locale}/index.html`:
    de "Fussballstatistiken und Spielvorschauen", en "Football stats and match previews", fi
    "Jalkapallotilastot ja otteluennakot". All three differ and so do the descriptions. The audit
    enforces this independently and passed. The fixture page's rebuilt titles are also distinct per
    locale, read from `dist`: "Palmeiras - Atletico-MG: Vorschau", "Palmeiras vs Atletico-MG:
    Preview", "Palmeiras-Atletico-MG: Ennakko".

  - **6. Every number comes from the pipeline, a dash where there is none, no arithmetic in the
    template.** `landing.json` is real export output from the production path
    `fetch_landing_payload` against BigQuery, reduced by hand to the keys the writer still emits.
    Exactly ONE arithmetic-shaped hit remains in the landing templates: `w.slice(1)` in
    `BrowseGrid.astro:26`, camel-casing an i18n LOOKUP KEY and not touching a displayed value.
    (The second, `TrendingList.astro:25`, went with the component.) Stated precisely rather than
    claiming "no arithmetic", which the grep would not support. Nulls:
    `test_group_upcoming_fixtures_keeps_a_null_crest_null`.

  - **7. No longer a stub, which is what unblocks go-live.**
    `grep -n "export const STUB_PAGES" site_v2/src/config/indexability.mjs` returns
    `43: export const STUB_PAGES = [];`. `index.spec.json` no longer carries `"stub": true` and
    declares two real blocks. `INDEXABLE` is UNCHANGED at false on line 27, and the BUILT output
    proves it rather than the source: `dist/en/index.html` contains one `noindex` and
    `dist/robots.txt` line 2 is `Disallow: /`.

  - **8. Nothing else broke.** `npm test` in `site_v2` gives **65 passed, 0 failed**. The SEO audit
    against `dist/` gives `audit-seo: 46 built page(s) checked. OK.` `dbt parse` is clean after the
    mart deletion (BigQuery adapter registered, no compilation error; the one warning, an unused
    `snapshots.football_data_pipeline` config path, is pre-existing on main).

  - **3b. The full python suite passes.** `python -m pytest tests/ -q` gives
    **672 passed, 1 skipped, 15 subtests passed, 0 failed** — the WHOLE suite, quoted, not a
    filtered subset. This criterion exists because that distinction is exactly what went wrong.

    ⚠ **THE SUITE WAS RED ON THIS BRANCH FOR SIX REVIEW ROUNDS AND NOBODY SAW IT.** The evidence
    line here claimed "608 passed" and the handover claimed "15 python tests" — the latter being
    only `test_export_landing.py`. Five PASS verdicts and six rounds of adversarial review read the
    diff and never ran the suite. `[[feedback-verify-by-running]]` names this exactly: review checks
    the diff, not the runtime. The new criterion 3b is the fix, because it forces the whole-suite
    output into the evidence rather than a subset that happens to be green.

    Cause, traced not guessed. This branch splits `finishing_efficiency`'s two catalogue rows so the
    player row takes `playerMetrics.finishingEfficiency.label` while the team row keeps
    `metrics.finishing_efficiency.label`. `load_catalogue()` in
    `scripts/export_metric_definitions_json.py` keyed the catalogue by `metric_id` ALONE, but the
    catalogue's grain is (metric_id, entity) — so for any metric carrying both rows the LAST one in
    file order silently won. Invisible while both rows shared a key; after the split the generated
    legacy JSON took the PLAYER key, while `site/team-season/index.html:349` calls
    `t("metrics.finishing_efficiency.label", …)`, the TEAM key. `format` and `lower_is_better` rode
    the same entity-blind lookup and were exposed to the same defect.

    **THE FIRST FIX WAS WRONG AND WAS REPLACED.** It resolved the ambiguity with a hardcoded
    "prefer the team row" default in `load_catalogue`. I flagged the layering question to
    `analytics-engineer-reviewer` rather than hoping it would pass, and it FAILED it: entity
    alignment is business logic, `layering.md` §Consumption layer forbids entity derivation
    downstream of the marts and names `site/` scripts as inside the contract (so "it is legacy" is
    not an exemption), and — the part worth carrying — **byte-identical output does not cure a rule
    living in the wrong layer. The mandate for the default IS the violation.**

    The shipped fix is the one that reviewer named, which my own docstring had already named and
    skipped for scope convenience:

    - `site/match-preview/metric_bindings.csv` gains a `catalogue_entity` column, 13 rows, all
      `team` (every live binding compares two teams — it has `home_column`/`away_column`).
    - `load_catalogue` is keyed on `(metric_id, entity)`, the catalogue's real grain, with **no
      default and no preference rule**.
    - `build_defs` looks up that pair and raises `SystemExit` on a miss, so an unmatched binding
      fails loudly instead of falling back to another entity's row — a silent fallback being the
      exact defect the column was added to remove.

    The test that the logic actually left the file: adding a player-entity binding is now a CSV
    edit and needs no code change here.

    Verified four ways. (1) The test was RED before the fix and GREEN after. (2) It is still red
    when the DATA is wrong — flipping the `finishing_efficiency` binding to `player` reproduces the
    failure, so the guard is not vacuous under the new design either. (3) An unknown pair raises:
    `metric_bindings: 'finishing_efficiency_recent' references unknown catalogue metric
    'finishing_efficiency' for entity 'goalkeeper'`. (4) `site/match-preview/metric_definitions.json`
    is **byte-identical** — `git status site/` shows the bindings CSV and nothing else, so no
    generated artifact and no MVP behaviour moved.

    Scope was amended twice on CPO authority: the script (2026-08-09), then the bindings CSV after
    the FAIL. The CSV lives under the frozen `site/`; the CPO authorised that edit explicitly.

## Found in review round 7 and NOT fixed here, by CPO ruling: crests are hotlinked

`platform-reviewer` FAILED round 7 on it, and it is real. Measured from `dist/`, not read from
source: the home page emits **24** literal `<img src="https://media.api-sports.io/...">` tags per
locale, 72 across de/en/fi. `Crest.astro:23` renders the served URL verbatim; there is no
`astro:assets` integration, no Firebase rewrite, no fallback. Its role brief calls this
non-negotiable — *"Hotlinking someone else's origin is the defect that took the previous site
offline"*.

Not introduced here: `TeamHeader.astro` and the fixture `Masthead.astro` already do it (4 images on
the team page), and a prior `platform-reviewer` PASS on this same branch never surfaced it. #367 is
simply the first PR to put it on the home page.

**CPO ruling 2026-08-09: file it, do not fix it inside #367.** `INDEXABLE` stays `false`, the site
is unlisted, and self-hosting or proxying crests is new infrastructure (storage, refresh cadence,
cache headers, licensing) that deserves its own issue. Filed as **GitLab #36**, a stated blocker on
**#377**. Three options and the licence precondition are written up there.

⚠ Recorded here rather than only in the issue, because this file is the acceptance record and a
reader must not conclude from criterion 8's "nothing else broke" that the page has no known defect.

## Recurring cost, measured not asserted

⚠ **REVISED TWICE on 2026-08-08. The figure fell, then fell again**, because both removed blocks
took their queries with them. The first revision was reported by `analytics-engineer-reviewer` in
round 4, outside its own mandate — it judged task paperwork not its to police, flagged the staleness
factually and did not hold its verdict on it. Recorded that way because the catch would otherwise be
invisible.

`bq query --dry_run`, per export run, as the code now stands:

| query | bytes |
|---|---|
| `fct_fixture` upcoming | 706,573 |
| `dim_team` | 283,449 |
| **TOTAL** | **990,022 B (~1.0 MB)** |

TWO queries, both for the hero. Browse is registry-driven and reads nothing, so the landing export
no longer touches the marts dataset at all.

~~`mart_team_profile` streak columns 1,789,571 B.~~ ⛔ Deleted with the trending block — that query
read `mart_landing_trending`, which no longer exists.

~~mart_standings aggregate 146,303 B, mart_leaderboards distinct seasons 6,004,796 B,
mart_leaderboards narrowed 9,681,539 B, mart_standings narrowed 552,412 B. TOTAL 19,164,643 B
(~19.2 MB) per run.~~ ⛔ Those four backed `eligible_stats_competitions`, `scorer_seasons` and the
stats block's own scorers/table selects.

Net across both cuts: **19.2 MB → ~1.0 MB per run, about 18.2 MB/day cheaper** than the figure this
section originally carried. ⚠ That saving is temporary and should not be banked: Top players and Top
teams will each add reads when they are built.

~~`select *` on mart_leaderboards measured 51,858,116 B for the same rows, so narrowing it is a
5.4x reduction.~~ ⛔ Entirely about a query that no longer exists.

⚠ The two surviving figures are the ORIGINAL 2026-08-04 dry runs, not re-measured today. They are
unchanged code reading unchanged marts, so the numbers should hold, but they are carried forward
rather than freshly verified and should not be quoted as a same-day measurement. Nothing on this
branch has been run against BigQuery at any point.

Verified by cto-reviewer and still true: `deploy-site-v2.yml` passes `--entities teams,fixtures`,
so the landing export is not yet wired into any scheduled job and no version of this cost is
actually being incurred yet.

## Repo cost, and a correction to criterion 1

An earlier version of this file reported the audit green without qualification. That was true
locally and FALSE for CI, and I had not checked: `.gitignore` allowlisted exactly two sample files,
so the 18 generated payloads existed on disk and would not have been committed, and CI would have
failed on 18 dead links. Fixed by extending the allowlist (contract amendment 2026-08-04,
CPO-approved).

The allowlist then had to SHRINK again on 2026-08-08: the six team payloads it had gained were
there only because trending rows linked to them, so they went with the block.
`site_v2/src/data/teams/` holds one file again (`33.json`, the team page's own sample). Verified
both directions —
`git check-ignore` returns nothing for every remaining allowlisted path, and the build emits 45
pages with `audit-seo OK`, so nothing links to a payload that is no longer tracked.

## Metric catalogue (no acceptance criteria — the gate triggers on site_v2/src only)

80 of 80 rows now carry `importance_tier` (16 before), `metric_group` (73 before) and the new
`computation_kind`. `group_display_order` removed — verified nothing still reads it (one hit
repo-wide, a comment in `schema.yml` recording the removal).

⛔ **THE TIGHTENED GUARD IS NOT IN THIS PR.** `assert_metric_catalogue_expr_resolvable.sql` is
REVERTED to main's version. It had been tightened here to assert against `computation_kind`, and
`data:build:mr` failed on it: `Unrecognized name: computation_kind`. The deferred singular-test step
resolves `ref('metric_catalogue')` to MAIN's seed, which does not carry the column this PR adds.

The repo had already ruled on this and the ruling sits next to the code — the CI notes in
`assert_metric_meaning_complete.sql` and `assert_metric_direction_lower_is_better_agree.sql`:
*"the values merge first, then the guard. Do not try to solve this with a CI workflow change."*
Both of those guards shipped that way; this is the third instance.

**What still covers the column here**: its `accepted_values` schema test
(`computation_kind__expression__model__sourced__cross_grain`), which runs inside
`dbt build --select state:modified+` against `ci_analytics` — it passed there in the failing
pipeline, at `4 of 41`.

**What is deferred**: the three injected-defect classes the tightened guard catches — an
`expression` row stripped of its formula, a `model` row given one, and an `expression` row stripped
of its base relation. They were demonstrated locally and are NOT claimed as shipped here. The guard
follows in its own MR once the column is in prod.

⚠ Recorded rather than quietly dropped: an earlier version of this section claimed the tightened
guard as delivered. It is not, and a reader must not infer coverage this PR does not have.
