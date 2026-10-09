# 01 — Fixture page ⭐ (#391)

> The heart of the product (brief §5 priority 1). Every field below is verified
> against the export (`scripts/export_site_data.py`, `fetch_fixture_payloads`) and
> the mart columns as of 2026-06-11.

## 1. Purpose

Pre-match: within seconds, give the fan **five things worth saying about this match**
(north star). The **stop-scrolling moment** is the side-by-side form comparison, one
window per team.
Secondary hook: the past-meetings record ("they've never beaten them at home" energy).

## 2. URL

```
/{locale}/{competition-slug}/matches/{yyyy-mm-dd}-{home-name}-vs-{away-name}/
```

- Slug from `slug` in the payload (built by `fixture_slug()`: kickoff date + kebab
  team names; falls back to `fixture-{id}`).
- `fixture_id` in the payload is the provider fixture id (verified:
  `fixture_sk == fixture_api_id` for all 20,149 fixtures).
- Breadcrumb: Home → Competitions → {competition} → Matchdays (Rounds for a cup) → {this match}.

## 3. Data sources

| File | Used for |
|---|---|
| `data/fixtures/{fixture_id}.json` | Everything on this page |
| `data/matchstats/{played_fixture_sk}.json` | The drill-down target when a past-match row is clicked (§7) — exists exactly for fixtures referenced by a form window |

Payload top level: `fixture_id, slug, kickoff, status, league_code, league_name,
season, round, round_order, venue, home, away, head_to_head`.
Each side (`home`/`away`): `team_id, name, slug, crest, country, form, standing,
form_window[], top_players[], next_match`.

## 4. Layout

The page draws render `match-page_2026-10-07_75`. Its blocks, in order:

1. Breadcrumb: Home › Competitions › {competition} › Matchdays (Rounds for a cup) › the match.
2. Header: the competition's group head, then round · date · time UTC · venue, then the two teams.
3. Form comparison: one window per team, the W/D/L pills, the catalogue's rows.
4. Recent matches: up to 5 result rows per team.
5. Players to watch: up to 5 player rows per team.
6. Head to head: the intro, then up to 5 meetings.

The page has no sentence under the header, no window switch, no internal-link chips and no
sample-data line. Under 700px the teams stack and the trail slides on one line. From 560px the
two teams' lists sit side by side, their rows level.

## 5. Module bindings

Labels: `chrome` = UI string from the locale files; `cat:{metric_id}` = catalogue
i18n key. Formats/direction from the catalogue row named.

### (1) Breadcrumb + (2) Match header

| Element | JSON key(s) | Notes / links |
|---|---|---|
| Competition crumb, group head | `league_code` → `competitions.json` name and slug; `competition_index.json` `logo_url` | a link when the competition's page is built |
| Matchdays crumb | `league_code` → `competition_index.json` `competition_type` | "Matchdays" for a domestic league, "Rounds" otherwise; a link when the Matchdays tab is built |
| Kickoff | `kickoff` (UTC ISO) | locale date, then the time with "UTC" |
| Round | `round_order`, `round` | "Matchday N" for a domestic league round with a number; the provider's round name otherwise |
| Venue | `venue` | closes the kick-off line; left out when null |
| Status | `status` (`NS`/`TBD`) | `TBD` → "time TBD" in place of the time |
| Team names/crests | `home.name`, `home.crest`, `home.slug`, and the same for `away` | each team one link to its team page when that page is built; crest fallback = monogram |
| Page heading | the page title | one H1, visually hidden: the two teams and the date |

### (2a) Standing chips — per side `standing`

| Element | JSON key | Format |
|---|---|---|
| Rank | `standing.league_rank` | cat:league_rank (integer, lower better) |
| Points | `standing.standing_points` | integer |
| Played | `standing.standing_played` | integer (chip tooltip/secondary) |
| Goal diff | `standing.standing_goals_diff` | signed integer (secondary) |
| Group | `standing.group_name` | shown for group-stage comps ("Group A") |

`standing` is **null by design** for knockout rounds (`is_knockout`) and
overlapping-table leagues → omit the chip entirely, no empty state.
`standing.standing_form` is NOT rendered here (the comparison's form strings come
from `form_window`, §3b) — it belongs to the competition-hub table (04).

### (3) Form comparison — per side `form`

The window: each side's `form` is the block the warehouse flags with `is_form_window`.
That is the last 5 across all the club's competitions while a league runs. Before a team's
first match in a domestic league it is last season's record there. The export picks the
flagged block and decides nothing.

The head row: each team's name over its W/D/L pills, from `form_window[].result` in
`recency_rank` order, the letters in the page's language. A side showing last season's
record shows no pills.

The intro: `formIntro`, or `formIntroPrev` when a side shows last season's record. No
points, no caption, no switch.

Metric rows: the catalogue's team metrics with a `metric_order`, served as
`src/data/metric_rows.json`, under the Rankings tab's group headings in the catalogue's order.
A row shows when either side carries a value. A row is number · name · number, the bar the
full width beneath. Bars are normalized to the larger of the two values.

### (4) Recent matches — per side `form_window[]` (≤5 result rows, `recency_rank` asc)

| Element | JSON key | Notes |
|---|---|---|
| Result chip | `result` | the letter in the page's language, on the result colour |
| Score | `goals_for`, `goals_against` | always from this team's side |
| Home/away | `home_away` | `haHome` / `haAway` |
| Opponent | `opponent_name`, `opponent_logo_url` | crest before the name, the name wrapping |
| Competition | `played_league_code` → `competitions.json` name | the name, never the code |
| Date | `played_kickoff_datetime` | locale short date |
| Link | — | none until played-match pages exist |

### (5) Players to watch — per side `top_players[]` (≤5)

The players: `mart_player_season_record` by `top_player_rank`, the season record of the
match's competition. The rank orders by goals plus assists, then goals, then fewer minutes.

The player row: `player_photo_url`, `player_name` over `position_code`, then
`goals_total` and `goals_assists`; a goalkeeper shows `saves_player`.
The intro is `playersIntro`, or `playersIntroPrev` when a row's `window_type` is `prev_season`.
No link until the players' pages exist.

### (6) Head-to-head — `head_to_head` (perspective = **home team**)

| Element | JSON key(s) | Notes |
|---|---|---|
| Intro | `intro` (EN/DE/FI) | the export's sentence from the last-5 split; `h2hNone` when the warehouse holds no meeting |
| Meetings (≤5) | `recent_meetings[]`: `kickoff_datetime`, `league_code`, `home_away`, `goals_for`, `goals_against` | the meeting row: the score in the match's order, the side at home first with crests, competition · date with year |

The block shows no totals and no bar. No link until played-match pages exist.

## 6. States

| State | Trigger | Render |
|---|---|---|
| Preview (normal) | `status` = `NS` | everything above |
| Time TBD | `status` = `TBD` | date without time + "time TBD" |
| No form window (side) | `form` = null | that side's values show "–"; both null: the block is absent |
| No standings context | `standing` = null or no `league_rank` | no chip, no empty state |
| Last season's window | `form.window_type` = `prev_season` | `formIntroPrev`; that side shows no pills |
| Never met | `head_to_head` = null | "No meetings on record." |
| Null metric value | either side null | "–" on that side; both null: the row is hidden |
| **Report (finished match)** | `status` = FT | **no payload today — GAP-07.** URL stays (preview → report is the promise); until then the page is not regenerated after kickoff |
| Thin page | fixture not in export | page not generated (export covers upcoming NS/TBD fixtures only) |

## 7. Interactions

- Breadcrumb levels, the competition's group head and the two teams link to their pages when
  those pages are built.
- Rows of Recent matches, Players to watch and Head to head are not links until their pages exist.
  Every row of a block links, or none.
- Under 700px the breadcrumb slides sideways on one line; a small script opens it at its end.
- No swipe-carousel between fixtures (that is the MVP's pattern, retired in v2);
  prev/next-match navigation belongs to the competition fixtures list (04).

## 8. SEO

- `schema.org/SportsEvent`: `startDate` = `kickoff`, `competitor` = both teams
  (SportsTeam: name + crest), `location` = `venue` (when present), part of
  `league_name`.
- Title: `{home.name} <connector> {away.name}, {date}` (localized template).
  **The competition is NOT in the title** (CPO, 2026-08-03), and neither is the brand.
  - *Why not the competition.* Measured over every competition's worst real upcoming fixture,
    ending the title with the competition name failed 4 of 26 against the 660px hard cap, worst
    886px, and Google then truncates or rewrites it. Sofascore and FBref both omit the competition
    from a match title for the same reason; kicker uses an editorial headline with the teams only
    in the URL. It is not lost: it stays in the breadcrumb, the URL and the JSON-LD `superEvent`.
  - *Why not the brand.* Same ruling as the team title (2026-07-28): a suffix is earned by equity,
    and an identical one on every match page reads as boilerplate.
  - *The date closes the title* (`{date}`, the short day and month of the UTC kick-off, the day the
    match's address carries), in place of a descriptor word: two meetings of the same clubs, a cup
    tie and a league match or two league meetings in a season, otherwise share a title, and the
    audit fails the build on it. The date alone tells every meeting apart; the competition would
    not fit (see above). With no descriptor, the title stays true once a match is played.
  - *Per locale*, each measured at its worst real fixture over every upcoming match: EN
    `{home} vs {away}, {date}` 534px · DE `{home} - {away}, {date}` 535px · FI
    `{home}–{away}, {date}` 505px. All inside the 600px budget. The German dash replaces "gegen" (also the convention in
    German football writing); the Finnish tight en dash follows Yle/MTV's "KuPS–HJK".
- Meta description: templated from real fields (round, kickoff date, h2h record)
  until GAP-03 narratives.
- `BreadcrumbList` mirroring the visible trail of §4; canonical per locale + hreflang set + OG/Twitter
  card (both crests, kickoff).

## 9. Component census

Breadcrumb · competition group head · match header · standing chip · form head row · metric
comparison row · result chip · result row · meeting row · player row · block explainer ·
empty states. Each is a row of `block_standard.md` or of the comparison's own rules.

## 10. Gaps

- [GAP-06](99_gaps_register.md) — `/h2h/{pair}/` page has no export target.
- [GAP-07](99_gaps_register.md) — no report-state payload for finished fixtures (§6).
- [GAP-08](99_gaps_register.md) — `round_name` is a raw provider string; a cup's round shows it untranslated.
- [GAP-18](99_gaps_register.md) — the Form comparison's intro names only the last 5 and last season, not a tournament window — needed before WC 2026.
- Goalkeeper's save percentage on the player row: no mart serves the shots faced it needs.
