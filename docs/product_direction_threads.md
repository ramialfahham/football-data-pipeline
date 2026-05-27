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

## Thread 2 — Competition taxonomy (COMPLETE)

**Context:**
"One mart fits all" won't scale as the competition registry grows. Different competition types have fundamentally different data shapes. We need an explicit taxonomy in the registry to drive mart routing — otherwise every new competition type requires ad hoc logic scattered across models.

---

### Agreed taxonomy (session 2026-05-25)

12 types in two groups. Enum values are final — do not change without explicit sign-off.

#### Club competitions

| `competition_type` | Description | Examples |
|--------------------|-------------|---------|
| `domestic_league` | Standings, form, promotion/relegation zones | BL1, BL2, PL, PD, SA, L1, VL, LMX, LP, MLS, SPL, ED |
| `domestic_cup` | Knockout bracket, multiple rounds, no standings | DFB-Pokal, FA Cup, Copa del Rey |
| `domestic_super_cup` | One-off match(es) between domestic titleholders | DFL-Supercup, FA Community Shield, Supercoppa Italiana, Supercopa de España |
| `club_qualifying` | Qualifying rounds feeding into a continental club competition | UCL qualifying, UEL qualifying |
| `continental_club` | Group stage + knockout, multi-nation club squads | UCL, UEL, UECL |
| `continental_super_cup` | One-off match between continental titleholders | UEFA Super Cup |
| `club_friendly_domestic` | Pre-season or mid-season friendly between club sides (domestic context) | — taxonomy only, not ingesting |
| `club_friendly_international` | Pre-season or mid-season friendly between club sides (cross-border) | — taxonomy only, not ingesting |

#### National team competitions

| `competition_type` | Description | Examples |
|--------------------|-------------|---------|
| `qualifying` | Qualification campaign for a major tournament | WCQ (all confederations), ECQ |
| `continental_championship` | Confederation tournament — groups + knockout; includes Nations League | Euros, Copa América, AFCON, Nations League |
| `world_championship` | Global confederation tournament | FIFA World Cup |
| `national_team_friendly` | International friendly between national teams | — taxonomy only, not ingesting |

#### Design decisions recorded

- **Play-offs are a phase attribute, not a type.** A play-off is a stage within a parent competition (e.g. WCQ intercontinental play-off round). It inherits the parent's `competition_type`. `WCQIP` is `qualifying`, not a separate type.
- **Gender is a competition attribute, not a mart split.** The 12 types apply equally to men's and women's competitions. Add a `gender` field to the registry (`men` / `women` / `mixed`) when the first women's competition is onboarded. Do not pre-empt this.
- **Supercups split at domestic/continental boundary.** The mart shape is identical but the competitive context differs (domestic: league champ vs cup winner; continental: UCL winner vs UEL winner). Separate types allow clean routing without conditional logic.
- **No national team supercup type.** The FIFA Confederations Cup (the closest equivalent) was sunset after 2017. No live competition exists. Add if needed when one appears.
- **Friendlies are in the taxonomy even though not currently ingested.** They will need separate mart treatment when onboarded (no meaningful standings, form context is weak). Domestic and international club friendlies are distinct types.

#### Registry state as of 2026-05-25

The registry already carries `competition_type` on most entries but the values **do not yet match this taxonomy**. Entries that need updating:

| `league_code` | Current value | Correct value |
|---------------|--------------|---------------|
| `WC` | `international_tournament` | `world_championship` |
| `WCQEU`, `WCQAF`, `WCQCA`, `WCQSA`, `WCQAS`, `WCQIP`, `WCQOC` | `wc_qualifier` | `qualifying` |

All `domestic_league` entries (BL1, PL, PD, BL2, SA, L1, VL, LMX, LP, MLS, SPL, ED) and `UCL` (`continental_club`) are already correct.

---

### Decisions

1. ✅ **Enum values agreed** — 12 types, final. See taxonomy table above.
2. ✅ **`competition_registry.yml` patched** — WC → `world_championship`; all 7 WCQ entries → `qualifying`. All other active entries already correct (2026-05-26).
3. ✅ **dbt folder organization by `competition_type`** — revised 2026-05-27 (Path B impact):
   - `1_staging`: **flat** — Path B replaces per-competition staging files with ~10 generic models (one per endpoint). Generic models are cross-type; type subfolders are obsolete here. Staging type subfolders from PR #237 are removed in issue #253.
   - `2_base`: flat — base models collapse the league dimension; type folders would fragment that (unchanged).
   - `3_core`: flat — core facts are type-agnostic; `league_code` column carries type through (unchanged).
   - `4_intermediate`: **type subfolders** — multiple intermediate models per type are expected (form windows, standings logic, bracket tracking, relegation zones all differ by type). Folder = what kind of football this model is about.
   - `5_marts`: **type subfolders** — multiple mart files per type are expected; types have genuinely different consumer shapes (standings + relegation for domestic leagues, cumulative form for tournaments, bracket progression for knockouts).

   **Architectural boundary:** staging and base are the generic infrastructure layer (flat). Intermediate and marts are the type-aware business logic layer (type subfolders). A new engineer can internalize this in one sentence: *below intermediate, type is a data column; at intermediate and above, type drives file organisation.*

4. ✅ **`competition_type` drives mart file organisation via type subfolders** — agreed 2026-05-27. Multiple mart files per type are expected as the competition catalog grows. `competition_type` is not metadata-only — it drives folder structure and file ownership at the intermediate and mart layers. Individual mart files are named by consumer purpose within their type folder (e.g. `5_marts/domestic_league/mart_matchday_insights.sql`, `5_marts/continental_club/mart_group_stage_standings.sql`). No per-type suffix in the file name itself — the folder provides the type context.

**Status:** All 4 questions resolved. Thread 2 COMPLETE.

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
