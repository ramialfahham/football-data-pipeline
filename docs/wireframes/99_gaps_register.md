# Gaps register (#391)

> Every data gap the blueprint surfaces: something a screen should show that the
> marts/export do not carry today. Each entry gets a proposed disposition; the CPO
> rules at the screen's PR review. Accepted gaps become their own issues — **gap
> fixes never ship inside blueprint PRs**. Types: `mart` (model change), `export`
> (export-script change), `catalogue` (metric-catalogue proposal), `feed` (new
> aggregate), `generator` (build-time content), `content` (i18n/copy strategy).

| ID | Screen(s) | Type | Gap | Proposed disposition | Ruling | Issue |
|----|-----------|------|-----|----------------------|--------|-------|
| GAP-01 | 02 team profile | mart + export | Identity fields promised by brief §6.2 — `team_founded_year`, `venue_name`, `venue_city`, `venue_capacity` — exist in `dim_team` but are not surfaced in `mart_team_profile` / the team export | Add the four columns to the mart + payload (small, additive) | pending | — |
| GAP-02 | 10 home | feed | Cross-competition upcoming-fixtures feed (the home hero) does not exist; only per-competition lists | Build as part of `landing.json` (#367), shape decided at 10_home review | pending | — |
| GAP-03 | 01 fixture, 10 home, SEO | generator | Data-to-text narrative generator (storylines, anti-thin-page text) not built | Export-layer generator, own issue; until then screens use templated factual sentences or omit the slot | pending | — |
| GAP-04 | 10 home | feed | Trending/storylines feed: which `mart_team_profile` signals surface (YoY swings, streaks, deserved-vs-actual gap) and how they rank | CPO selects signals + ranking at 10_home review; feed ships with `landing.json` | pending | — |
| GAP-05 | 05 leaderboards | export | Only goals / assists / shots_on_target boards are exported; `/stats/{metric-slug}/` implies more | CPO picks the metric set at 05 review; each added board is a one-line export change | pending | — |
| GAP-06 | 01 fixture, 06 h2h | export | `/h2h/{pair}/` is in the URL scheme and `mart_head_to_head` exists, but there is no standalone h2h export target (`ENTITY_TYPES` has none; fixture payloads embed only the summary) | Add an `h2h` export target (canonical pair = lower team id first) | pending | — |
| GAP-07 | 01 fixture | export (likely + mart) | Fixture pages exist only for upcoming fixtures (`status NS/TBD`); the URL promise is "preview → report" — a finished fixture has no payload (final score + stats on its own page). `matchstats/` covers drill-down stat lines but not the fixture page itself | Decide the report-state scope (which finished fixtures get pages, what they show — likely header + final score + `mart_fixture_stats__*`), then extend the export | pending | — |
| GAP-08 | 01 fixture, 04 hub | content | `round_name` (e.g. "Regular Season - 14", "Group Stage - 1") is a raw provider string rendered as-is — no localization strategy ("Spieltag 14") | i18n strategy decision in #370 (pattern-based round-label translation vs raw); blueprint renders the raw string until then | pending | — |
