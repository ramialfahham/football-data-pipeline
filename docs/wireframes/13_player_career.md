# 13 — Player → Career (clubs · competitions · seasons)

> A sub-screen of the player page (03). Field-bound against `mart_player_career` — **built** (#630, #480 §8.3:
> the per-club player-season foundation `int_player_club_season__metrics` → the rebuilt career mart). The mart
> is **not yet exported** — every key in §5 is a **proposed** shape pending [GAP-22](99_gaps_register.md) (the
> wiring PR); this spec is written ahead of it, the same way Squad (11) preceded its wiring (#619) and Stats
> (12) preceded [GAP-21](99_gaps_register.md). **Counts only:** labels/formats for `goals`/`assists` come
> from `metric_catalogue.csv` (the 00 binding rule); **no per-90, no composite scores** — deliberately not
> offered yet ([`ui_design_brief.md`](../ui_design_brief.md) §6.4) — and a career-long rate across mixed
> clubs/seasons is not meaningful (the CPO counts-only ruling on `mart_player_career`).

## 1. Purpose

"Where has he played, and what did he do there?" A player's whole career on one screen: every **club** and the
**national team**, **season by season**, per **competition**, with the honest counts — appearances, goals,
assists. The **stop-scrolling moment** is the **career sweep**: the run of club-grouped season rows a fan
scrolls to trace a career (Bayern → Spurs; 2019/20 → today). Aggregates are **counts only** — no per-90, no
composite ratings: per-90 rates and composite scores are deliberately not offered yet
([`ui_design_brief.md`](../ui_design_brief.md) §6.4), and a career-long rate across mixed clubs/seasons is not
meaningful (the CPO counts-only ruling on `mart_player_career`).

**Honest limits (state them, do not hide):**
- **National rows are appearances in COVERED competitions, NOT true caps** — we ingest only a subset of
  national competitions, so this undercounts a player's full international history (the mart's own contract).
- **The log is thin until the history backfill runs.** Today the pipeline holds mostly current seasons; the
  career table is correct at its grain but shallow until the per-competition backfill (§10, a separate
  cost-gated task). The screen renders what exists and says so — it never fabricates depth.

## 2. URL

```
/{locale}/players/{kebab-name}-{player_id}/career/
```

- Sub-path of the canonical player URL (`/players/{slug}/`, 03 §2); same slug rule.
- Breadcrumb: Home → Players → {player} → Career.
- One Career URL per player (no selector — the whole career is one view).

## 3. Data sources

`data/players/{player_id}.json` — the existing player payload. **Proposed** addition (GAP-22): a
**`career[]`** set, one member per `(club, competition, season)`, sourced 1:1 from `mart_player_career`
(grain `(player_sk, team_sk, season_sk)`) + a top-level `national_appearances_total`. The export
**selects/reshapes only** — grouping into clubs and any subtotals are display concerns (§5, §10); no fact is
derived in the export (consumption-layer contract). The exact nesting (flat `career[]` vs pre-grouped by
club) is confirmed at the wiring PR. Until GAP-22 lands the payload carries no `career[]`; the surface is not
generated (§6).

## 4. Layout

```
┌───────────────────────────────────────────────────┐
│ ▸Home › ▸Players › ▸Harry Kane › Career           │  (1) breadcrumb
├───────────────────────────────────────────────────┤
│  [photo] Harry Kane — Career                      │  (2) identity header
│          England                                  │
├───────────────────────────────────────────────────┤
│  ▸FC Bayern München                        [crest]│  (3) club group header
│   Season   Competition      Apps  Goals  Assists  │      column head
│   2025/26  Bundesliga        29    24     8       │      season row
│   2024/25  Bundesliga        32    26     11      │
│   ─ Bayern total             61    50     19      │      (4) per-club subtotal
├────────────────── fold (~700px) ──────────────────┤
│  ▸Tottenham Hotspur                        [crest]│
│   2022/23  Premier League    38    30     3       │
│   … the rest of the clubs / seasons we hold …     │
│   ═ Career total            137   104     22      │      (5) career total
├───────────────────────────────────────────────────┤
│  NATIONAL TEAM                                    │  (6) national section
│   England · 12 appearances (covered competitions) │      caps line (honest)
├───────────────────────────────────────────────────┤
│  ▸Overview ▸Stats ▸Match log                      │  (7) internal links
└───────────────────────────────────────────────────┘
```

Rows are **grouped by club** (`entity_type = 'club'`), each club's seasons newest-first, clubs ordered by most
recent season descending; then a **National team** section (`entity_type = 'national'`). Each season row:
`season_api_year` · competition badge (`league_code`) · appearances · goals · assists. **Desktop (≥ ~900px)**:
the club groups sit in one column; identity header full-width. The per-club subtotal and career-total lines are
**display aggregations of the rows** (or a reserved precompute — §5, §10).

## 5. Module bindings

All keys **proposed** (GAP-22); each a real `mart_player_career` column.

### (2) Identity header

| Element | JSON key | ← mart column | Notes |
|---|---|---|---|
| Name / photo | top-level `name`, `photo` | (player payload) | photo fallback = monogram |
| Nationality | top-level `nationality` | (player payload) | — |

### (3)(4)(5) Club groups + season rows + subtotals

| Element | JSON key (proposed) | ← mart column | Display |
|---|---|---|---|
| Club group header | `career[].team_name`, `team_logo_url` | `team_name`, `team_logo_url` | crest + name; ▸ team profile via `team_sk` |
| Row — season | `career[].season_api_year` | `season_api_year` | e.g. "2025/26" (locale season format) |
| Row — competition | `career[].league_code` | `league_code` | competition badge; ▸ competition hub |
| Row — appearances | `career[].appearances` | `appearances` | integer (a playing-time fact, not a catalogue metric) |
| Row — goals | `career[].goals` | `goals` | integer; label/format from `metric_catalogue` (`goals`) |
| Row — assists | `career[].assists` | `assists` | integer; label/format from `metric_catalogue` (`assists`) |
| Per-club subtotal | (derived) | sum of the club's rows | **display-side grouping** of `career[]`, OR a reserved dbt precompute (§10) |
| Career total | (derived) | sum of all club rows | same — display grouping or reserved precompute |

### (6) National team section

| Element | JSON key | ← mart column | Display |
|---|---|---|---|
| Split club vs national | `career[].entity_type` | `entity_type` | `club` rows in the club groups; `national` rows in this section |
| Caps line | top-level `national_appearances_total` | `national_appearances_total` | "{national_team} · {n} appearances (covered competitions)" — **precomputed on the mart**; worded as covered-competition appearances, **never** "caps" |

`goals`/`assists` labels, formats, and better/worse direction come **only** from `metric_catalogue.csv` (never
invented); `appearances` is a playing-time fact rendered as an integer. No per-90, no ratios on this screen.

### (7) Internal links

Back to the player Overview (03), the player Stats (12), and the Match log. Club → its team profile
(`team_sk`); competition → its hub (`league_code`). No new player-level targets invented.

## 6. States

| State | Trigger | Render |
|---|---|---|
| Normal | — | club groups + national section above |
| No career rows | player has no `mart_player_career` rows | page not generated (thin-page rule) |
| Thin / shallow history | few seasons (pre-backfill) | render what exists + a one-line "career history deepens as more seasons are added" note; never fabricate seasons |
| No national rows | player has no `national` competition rows | omit the National team section entirely (no zero caps line) |
| Unmapped competition | `entity_type` null (competition not in `competition_types`) | group under an "Other" bucket; not counted as club or national |
| Unresolved identity | player OR club identity fields null (a `mart_player_career` row with no resolvable `dim_player`/`dim_team` — the mart LEFT-joins both, per its header) | guarded upstream by the `player_sk` → `dim_player` and `team_sk` → `dim_team` `relationships` DQ tests (`shared.yml`), so a name-less row surfaces as a **test failure, not a rendered blank** (mirrors 11 §6); the build omits any that slip through rather than fabricating a name |
| Zero denominator | n/a | this screen has no ratios — counts only |
| Not yet wired | GAP-22 open (today) | payload carries no `career[]`; the surface is not generated |

## 7. Interactions

- Static table — club grouping + season order + subtotals render server-side (crawlable); no selector, no
  fetch (the whole career is one view).
- Club → team profile; competition → competition hub; footer links to Overview / Stats / Match log.
- No charts required at v1.

## 8. SEO

- `schema.org/Person` (athlete): name, image = photo, nationality; `memberOf` from the most recent club row.
- Title: `{name} — Career | Matchday IQ` (localized).
- Meta description templated from the career total (e.g. "137 appearances, 104 goals across 3 clubs").
- `BreadcrumbList` (Home → Players → {player} → Career); canonical per locale + hreflang.

## 9. Component census

Breadcrumb · profile header (player, shared with 03) · **club group header (crest + name) ➕** ·
**career-log row (season · competition · apps · goals · assists) ➕** · **subtotal / career-total line ➕** ·
**national-caps block ➕** · empty/absent state · internal-links footer.

## 10. Gaps

- [GAP-22](99_gaps_register.md) — `mart_player_career` (the per-club career log; built #630) is not carried by
  the v2 player export; the Career surface has no payload. Disposition: add a `career[]` block (+ top-level
  `national_appearances_total`) to `shape_player_payload` (select/reshape only). Own follow-up PR.
- **Subtotals (per-club / career totals): precompute in dbt vs display-side grouping** — reserved (the #630
  `decisions_reserved` item). Summing a club's season rows for a subtotal is display grouping, but if a
  DQ-testable total is wanted it belongs in the mart. CPO ruling at the GAP-22 wiring PR; this spec renders
  subtotals as display grouping until then. `national_appearances_total` is already precomputed.
- **History depth** — the career log is thin until the per-competition backfill runs (a separate registry +
  cost-gated ingest task; content_architecture §8). Not a blocker for the spec; the screen is honest about it.
- Season-over-season / YoY and per-90 career rates are **out of scope** (counts only, locked); YoY depends on
  the player-season foundation (#480 continued, Phase C).
