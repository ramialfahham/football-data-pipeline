# Product direction — open threads

Three topics surfaced in session 2026-05-24 that need dedicated discussion before any implementation starts.
Tackle one by one. Do not close a thread without explicit sign-off from Rami.

---

## Thread 1 — Cost at scale (ACTIVE)

**Context:**
BL1 has 10 seasons of historical data. If we apply the same history depth to every league in the growing competition registry, BigQuery processing costs could scale significantly. Storage is cheap; scans are not.

**Questions to answer:**
- Which dbt models are full-refresh vs incremental? Are raw tables date-partitioned?
- What is the per-run scan cost today vs projected cost with 20 competitions × 10 seasons?
- Do we need a cost audit before onboarding more historical data?

**Proposed next step:** Audit incremental/full-refresh split across dbt models before adding historical data to new leagues.

---

## Thread 2 — Competition taxonomy

**Context:**
"One mart fits all" won't scale as the competition registry grows. Different competition types have fundamentally different data shapes.

**Proposed taxonomy:**
- **Domestic leagues** — standings, form, promotion/relegation zones
- **Domestic cups** — bracket/knockout, no standings
- **International club** (CL, EL) — group stage + knockout, multi-nation squads
- **International national** (WC, Euros, qualifiers) — confederation groups, qualification paths

**Questions to answer:**
- Add `competition_type` field to `competition_registry.yml` to drive mart routing?
- Which existing marts need to be split or parameterised per type?

**Proposed next step:** Define `competition_type` enum, update registry, audit which marts are affected.

---

## Thread 3 — Visual identity and UX principles

**Context:**
The site is evolving from a mobile MVP into a professional multi-device website. The card/color scheme is no longer the right direction. The product should be fun, visual, and low-click.

**Principles agreed:**
- Every page should have one thing that makes you stop scrolling
- Data shown, not described — charts over tables where possible
- Max 2 clicks from home to anything interesting

**Open questions:**
- Visual style: data-dense (heatmaps, radar charts) vs narrative (big numbers, sparklines, callout stats)?
- Tech stack: stay with static GitHub Pages + vanilla JS, or move to a framework that supports proper routing and SEO?

**Proposed next step:** Decide visual direction and tech stack before any new page is built.

---

## Related open items (not threads, but linked)

- ML/data science role brief — needs drafting before prediction mart design starts
- Prediction mart — deferred until role is defined and training data discussion happens
- `mart_league_standings`, `mart_team_season_stats`, `mart_team_squad`, `mart_player_season_stats` — scoped but not ticketed yet; wait until threads 1–3 are resolved
