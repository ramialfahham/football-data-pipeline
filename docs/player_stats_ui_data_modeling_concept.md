# Player Stats in Match Preview — UI + Data Modeling Concept

## Purpose

Define how player statistics integrate into the existing Matchday IQ flow and what must change in the data model to support it cleanly, testably, and competition-agnostically.

## Scope (this concept)

- In scope: UX concept, metric concept, dbt modeling impact, role ownership, subticket/PR split.
- Out of scope: implementing production SQL/HTML/JS in this document.

## Current state (baseline)

- Navigation is `landing -> fixture-list -> match-preview` with mobile-first swipe cards.
- `site/match-preview/index.html` renders team-vs-team metric rows only.
- `mart_player_season` exists, but fixture-level player stats in `fct_fixture_player_stats` currently read from `base_apif__bl1_fixture_players` only.
- WC-first player stats in match preview therefore require core model expansion before any UI wiring.

## Product concept (UI)

### Flow

`landing -> fixture-list -> fixture-detail`

No new top-level pages. Player stats are added inside fixture detail to keep the current fast navigation.

### Fixture detail information architecture

1. Match header (teams, logos, kickoff, round) — unchanged.
2. Segment control under header:
   - `Team insights` (default)
   - `Player insights` (new)
3. `Player insights` content block (per fixture card):
   - `Top players - home` (top 3)
   - `Top players - away` (top 3)
   - `Why these players` explainer line (one-line plain-language summary).

### Player card concept (inside `Player insights`)

Each player row shows:

- player name
- role badge (`ATT`, `MID`, `DEF`, `GK` when available)
- 3 smart metrics (not raw-only counts), e.g.:
  - `Threat` = goals + assists + shots_on_target contribution rate
  - `Creation` = key passes + pass accuracy context
  - `Reliability` = minutes-weighted availability + card risk signal

Null/optional metrics show `Not provided` (never fake `0`).

### Low-fi wireframe

```text
[Team A] vs [Team B]
[Team insights] [Player insights]

Player insights
Home top players            Away top players
1) Musiala   Threat 0.62    1) Mbappe    Threat 0.71
   Creation 0.55               Creation 0.49
   Reliability 0.81            Reliability 0.76
2) ...
3) ...

Why these players:
"Highest recent attacking contribution and chance creation in this fixture context."
```

## Data modeling implications

## Metric policy (before SQL)

Football Analytics Expert + BI Analyst must approve:

- final metric list (max 3 per player card for v1),
- formulas,
- windows,
- nullability semantics,
- copy labels.

No metric reaches UI without this sign-off.

## Proposed dbt contract by layer

### `1_staging` (raw cleanup only)

- Ensure fixture-player staging exists and is consistent for active competitions (including WC surfaces): `stg_apif__{league}_fixture_players`.
- No business logic in staging.

### `2_base` (union + dedup)

- Add unified `base_apif__fixture_players` that `UNION ALL`s all active competition stagings.
- Keep dedup key at `(fixture_id, team_id, player_id)` with latest ingestion priority.

### `3_core` (system of record)

- Refactor `fct_fixture_player_stats` to read from unified `base_apif__fixture_players` (remove BL1-only dependency).
- Keep grain one row per `(fixture_sk, team_sk, player_sk)`.
- Maintain `league_code` partitioning and relationships to `fct_fixture`, `dim_team`, `dim_player`.

### `4_intermediate` (feature logic)

Add fixture-context player feature models:

- `int_matchday__player_form_window`  
  Applies the same competition form rules as match preview:
  - domestic: up to last 5 current-season finished matches (previous-season fallback before season start),
  - WC: qualifiers through Group Stage MD1, then cumulative finished WC tournament matches.

- `int_matchday__fixture_player_insights`  
  Computes derived smart metrics and ranks top players per fixture/team.

### `5_marts` (UI-ready)

Add `mart_matchday_player_insights`:

- grain: `(fixture_sk, team_sk, player_sk)`
- required keys: `league_code`, `fixture_sk`, `team_sk`, `player_sk`
- includes:
  - player identity columns
  - approved smart metric columns
  - `player_rank_for_fixture_side`
  - `selection_reason_code` (for deterministic copy mapping in UI)

UI export shape (new file per league):

- `data/<league>/matchday_player_insights.json`
- optional payload shape:
  - `fixtures[]`
    - fixture identity
    - `home_players[]` (top 3)
    - `away_players[]` (top 3)

## Data quality requirements (hard gate)

- Grain tests:
  - unique combination on `(fixture_sk, team_sk, player_sk)` for mart.
- Relationship tests:
  - player/team/fixture foreign key integrity.
- Formula consistency tests:
  - derived metric equals its numerator/denominator formula within tolerance.
- Range tests:
  - ratio metrics in `[0,1]` when non-null.
- Completeness tests:
  - if a fixture is shown in `matchday_insights`, player insight rows for both sides must exist unless explicitly flagged `Not provided`.

## UX requirements (hard gate)

- Mobile-first remains primary; no horizontal overflow in player blocks.
- Desktop/tablet parity: no swipe-only dead-ends (mouse/keyboard navigation must work).
- Clear copy; no internal data jargon in user-facing labels.

## Acceptance checks (for implementation PRs)

- Phone:
  - user can switch `Team insights <-> Player insights` in one tap,
  - top players visible without horizontal scrolling.
- Tablet:
  - two-column player layout remains readable.
- Desktop:
  - user can navigate fixtures and switch segments without touch gestures.
- Data honesty:
  - any missing optional stat renders `Not provided`, not `0`.

## Role-by-role delivery plan

1. Football Analytics Expert: shortlist meaningful player metrics + caveats.
2. BI Analyst: finalize metric catalogue, labels, ordering, and fallback copy.
3. Analytics Engineer: implement dbt models/tests and data contract.
4. Data Engineer: ensure fixture-player ingestion/completeness for target competition(s).
5. UI Expert: implement segment UI and player cards against approved contract.
6. Growth Expert: define share-surface for player cards (phase 2, not v1 blocker).
7. Product Analyst + Legal Counsel: tracking + GDPR/licensing review before player-level tracking events.
8. QA: cross-device and data-integrity validation.

## Suggested subtickets and separate PRs

1. **Metric spec ticket** (no code)  
   Owner: Football Analytics Expert + BI Analyst  
   Output: approved metric table in `docs/metrics_catalogue.md`.

2. **Core fixture-player unification**  
   Owner: Analytics Engineer  
   PR scope: `2_base` + `3_core` for competition-agnostic `fct_fixture_player_stats`.

3. **Intermediate player insight features + tests**  
   Owner: Analytics Engineer  
   PR scope: `4_intermediate` models + singular/schema tests.

4. **Player insights mart + export wiring**  
   Owner: Analytics Engineer  
   PR scope: `5_marts`, exporter script, JSON contract tests.

5. **UI integration in fixture detail**  
   Owner: UI Expert  
   PR scope: `site/match-preview/` segment control + player cards + i18n strings.

6. **Cross-device QA and regression**  
   Owner: QA  
   PR scope: test evidence artifacts + bugfixes only.

## Suggested branch naming (example)

- `cursor/player-metric-spec-deef`
- `cursor/core-fixture-player-union-deef`
- `cursor/int-player-insights-features-deef`
- `cursor/mart-player-insights-export-deef`
- `cursor/ui-player-insights-tab-deef`
- `cursor/qa-player-insights-regression-deef`

## Easy access to this concept / mock-up draft

- Repo path: `docs/player_stats_ui_data_modeling_concept.md`
- After merge: direct GitHub URL  
  `https://github.com/ramialfahham/football-data-pipeline/blob/main/docs/player_stats_ui_data_modeling_concept.md`

For visual iteration, keep this doc as the canonical product/data contract and link a Figma file from this same section in a follow-up PR.
