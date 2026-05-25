# Product direction — open threads

Three topics surfaced in session 2026-05-24 that need dedicated discussion before any implementation starts.
Tackle one by one. Do not close a thread without explicit sign-off from Rami.

---

## Thread 1 — Cost at scale (CLOSED 2026-05-25)

**Resolution:**
- Raw tables partitioned by `DATE(ingested_at)` — PR #224 (249 tables migrated).
- Reference table staging reads latest partition only — `apif_latest_source_partition` macro, PR #222.
- Fanout facts (`fct_fixture_event`, `fct_fixture_team_stats`, `fct_fixture_player_stats`) converted to incremental — PR #232.
- Intermediate matchday models are correctly full-refresh: they read from stored fact tables (not raw), whose scan cost is proportional to fixture count, not raw table size. Making them incremental would not help — form metrics require full history by design.
- Daily costs acceptable at any realistic competition count. Architecture signed off.

---

## Thread 2 — Competition taxonomy (ACTIVE)

**Context:**
"One mart fits all" won't scale as the competition registry grows. Different competition types have fundamentally different data shapes. We need an explicit taxonomy in the registry to drive mart routing — otherwise every new competition type requires ad hoc logic scattered across models.

**Proposed taxonomy:**
- **domestic_league** — standings, form, promotion/relegation zones (BL1, BL2, PL, PD, SA, L1, VL, LMX, LP, MLS, SPL, ED)
- **domestic_cup** — bracket/knockout, no standings
- **international_club** — group stage + knockout, multi-nation squads (UCL, UEL)
- **international_tournament** — confederation groups, qualification paths (WC, Euros, qualifiers)

**Questions to answer:**
1. Agree the enum values above (or revise).
2. Add `competition_type` field to `docs/competition_registry.yml` for every active/in_progress competition.
3. Which existing marts and intermediates are affected — do any need to branch on `competition_type`?
4. Does `competition_type` drive mart file naming (`mart_matchday_insights_{type}.sql`) or is it metadata only?

**Status:** Open — needs discussion before any implementation.

---

## Thread 3 — Visual identity and UX (ACTIVE)

**Context:**
The site is evolving from a mobile MVP into a professional multi-device website. The card/color scheme is no longer the right direction. The product should be fun, visual, and low-click.

**Principles agreed:**
- Every page should have one thing that makes you stop scrolling
- Data shown, not described — charts over tables where possible
- Max 2 clicks from home to anything interesting

**Open questions:**
- Visual style: data-dense (heatmaps, radar charts) vs narrative (big numbers, sparklines, callout stats)?
- Tech stack: stay with static GitHub Pages + vanilla JS, or move to a framework that supports proper routing and SEO?

**Status:** Open — needs discussion before any new page is built.

---

## Related open items (not threads, but linked)

- ML/data science role brief — needs drafting before prediction mart design starts
- Prediction mart — deferred until role is defined and training data discussion happens
- `mart_league_standings`, `mart_team_season_stats`, `mart_team_squad`, `mart_player_season_stats` — scoped but not ticketed yet; wait until threads 2–3 are resolved
