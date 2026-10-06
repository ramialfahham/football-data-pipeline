# UI design brief — Matchday Pilot v2

> This brief states how Matchday Pilot v2 pages look, feel and lay out, and which data fields each
> page may show. A design tool or a user interface and user experience (UI/UX) designer can use it
> as a self-contained package. **Everything a mockup shows comes from a field that §6 lists — the
> single most important rule in this document**. Where §6 points to another document, that
> document lists the fields.
> `docs/site_architecture.md` fixes the structure, the information architecture (IA) and the URLs.
> `docs/wireframes/00_overview.md` owns the reading order of the design documents.

## 1. Product context

**Matchday Pilot** is a fun, sticky pre-match companion for football fans. It is the site you open
in the sports bar before kickoff, share with your group chat, and argue over. It is not a stats
database and not a betting tool. Casual fans must feel smart in seconds. Hardcore fans must find
depth on demand.

| Aspect | Statement |
|---|---|
| Audience | Casual and hardcore fans |
| Primary device | The phone (mobile-first) |
| Languages | Multilingual; the product targets 8 or more languages |
| Scale ambition | A media-grade platform (kicker or onefootball class) with millions of users |
| Site | A full responsive website with programmatic pages for every competition, fixture, team and player |

## 2. Design principles (locked — north star)

1. **Every page has one thing that makes you stop scrolling.**
2. **Data shown, not described**: charts over tables wherever possible.
3. **Max 2 clicks from home to anything interesting.**
4. **Data honesty**: a missing value renders as **"–"**, never as a fabricated zero. A page never
   shows an invented stat. Design empty states instead of hiding them. For example, "Player stats
   not available for this match" is a COMMON state, so style it well.
5. **Simple surface, depth on demand**: progressive disclosure, not walls of numbers.

## 3. Reference sites

The reference sites are inspiration, not a blueprint. Do not copy any of them; each contributes one
thing.

| Site | Take | Avoid |
|---|---|---|
| last5games.com | The match preview built around last-5 form, closest to our W1 momentum concept | A spartan look with no brand warmth |
| whoscored.com | Depth: ratings, dense stat tables, profile structure | Clutter, a dated look, ad-heavy density |
| onefootball.com | Modern media UX: mobile-first cards, clean type, content hierarchy | News first (we are data first) |
| flashscore.com | Speed, fixtures-first navigation, information density done fast | A utilitarian look with zero storytelling |

## 4. Hard design constraints

| Constraint | Rule |
|---|---|
| Responsive, mobile-first | The phone is the primary device, for the sports-bar use case. Layouts scale gracefully to tablet and desktop multi-column. |
| Themes | The site has a light and a dark theme, both built from design tokens. |
| Text expansion | Text expands in translation, for example German by about 30% against English. Layouts tolerate it. |
| Writing direction | Arabic (right to left, RTL) comes later. Avoid compositions with a fixed writing direction. |
| Numerals | Every stat column uses tabular numerals. |
| Color semantics | Win, draw and loss (W/D/L) use one consistent encoding: color plus letter, never color alone. Each metric has a good direction, which the data carries in `direction`. The design expresses better and worse consistently. |
| Accessibility | WCAG AA (Web Content Accessibility Guidelines, level AA): contrast in both themes, touch targets, reduced motion. |
| Performance | The site is static and fast: no heavy JavaScript, and charts are lightweight islands. Design for instant first paint, within a Core Web Vitals budget. |
| Images | Team crests and player photos come from the provider's content delivery network (CDN) as small PNGs of variable quality. The design needs a graceful fallback: a monogram or initials. |
| Labels | Labels and wording are i18n (internationalisation) keys. Design with realistic strings from the longest language. |
| Row links | A row that leads somewhere is ONE link: the whole row. Hover tints its background, a press sinks it, and the focus ring sits inside the row. An underline marks a word inside running text, such as a breadcrumb or a sentence. A name inside a row never has an underline. One shared rule in `system.css` carries this for every row link on the site. |
| Nothing renders empty | A block with no served data is absent: no heading over nothing, no placeholder rows, no dashes in place of a block. A single missing value inside a rendered row shows "–". |
| Names hold together | A team name, a "Matchday N" or a date never breaks inside itself; a wrap falls between them. |

## 5. Navigation and page inventory

`docs/site_architecture.md` owns the navigation, the URLs and the competitions index.

Pages to design, in priority order:

1. **Fixture page** ⭐ (the heart of the product)
2. **Team profile** ⭐
3. **Landing** (home)
4. **Player profile**
5. Competition page, with its tabs (§6.5)
6. Head-to-head and metric glossary: system pages that derive from the established design language

## 6. Per-screen data contract (what a mockup MAY show)

Metric display names come from the metric catalogue, `dbt_project/seeds/metric_catalogue.csv`, in
translation. This section lists each metric by its plain-English meaning. **If a stat is not listed
below, we do not have it — do not draw it**. So a mockup shows no xG (expected goals), no shot maps,
no heat maps, no pass networks and no win probability.

### 6.1 Fixture page ⭐

- **Header**: both teams (name, crest), kickoff date and time, competition, round, venue name.
- **Two windows per team**: W1 and W2 complement each other and always show side by side.
- **W1 — form**: `docs/metrics_context_model.md` §4 names the matches in the window. For a club,
  they are the last 5 matches across all its competitions. Fields:
  - games in window, points won
  - goals per match, goals against per match
  - shots per match, shot accuracy %, danger-zone ratio % (share of shots from inside the box),
    finishing efficiency %
  - passes per match, pass accuracy %
  - corners per match, corners conceded per match
  - save ratio %, key passes per match
  - tackles per match, interceptions per match, blocks per match
  - duels won %, dribbles success %
  - the list of contributing competitions
  - league rank, only when a single round-robin table applies; otherwise absent
- **W2 — season to date (this competition)**: the same metric set, cumulative. Before a season
  starts, W2 falls back to the previous season, with a label that says so.
- **Form drill-down (per team)**: the actual matches in the W1 window. Per match: opponent (name,
  crest), date, competition, home or away, score, W/D/L. A match is clickable when a stat line
  exists. Flags say whether team stats and player stats are available.
- **Match detail (a clicked past match)**: full stat lines for both sides.
  - Team stat line: possession %, shots (on target, off target, total, blocked, inside box,
    outside box), fouls, corners, offsides, cards, saves, passes (total, accurate, %).
  - Player stat line: minutes, shirt, position, captain or substitute, goals, assists, shots,
    passes, key passes, tackles, interceptions, blocks, duels, dribbles, fouls, cards, penalties.
- **Player insights (per team)**: the top players over the form window. Fields: appearances,
  minutes, goals, assists, shots on target, key passes, pass accuracy %, duels won %, dribbles
  success %, cards. Goalkeepers: saves, goals conceded, save %.
- **Standings context**: each team's rank and a mini table slice, for league and group phases only.
- **Head-to-head**: the past meetings of the two teams (`mart_head_to_head`).
- **Signature-moment candidates**: the W1↔W2 contrast ("hot now vs season reality"), and the form
  drill-down interaction.

### 6.2 Team profile ⭐

**Identity**: name, crest, country, founded, venue (name, city, capacity).

**Per season** (selector):

- **Record**: played, W/D/L, goals for and against, goal difference, points, clean sheets, rank,
  recent form string (for example WWDLW).
- **Season metric rates**: the same metric family as §6.1, as per-match values and ratios.
- **Deserved vs actual** (a differentiator): shot share %, points capture %, and the labelled gap
  between them. Shot share % is the share of all shots in the team's matches. Points capture % is
  points won / points available. The gap label reads "dominates play more/less than results show".
  The block shows two real numbers and their difference, NOT a composite score gauge.
- **Year-over-year (YoY)** (domestic leagues): points, goals for and goals against through N games
  this season, against the same N games last season, with deltas. The values are NULL for cups and
  where the warehouse holds no last season. Design the absent state.
- **Streaks**: the current unbeaten, win, winless, clean-sheet and scoring runs.
- **Fixtures**: a list of the next and recent matches.
- **Squad**: per player, for the competition-season: appearances (matches played), minutes per
  appearance, goals, assists. Players group by position (GK, DEF, MID, FWD), with monogram avatars
  and no photos. The data is `mart_player_career` joined onto the roster. The list holds the members
  with at least one appearance, under an "N of M shown" caption.
- **Signature-moment candidates**: the deserved-vs-actual visual, and the YoY trend comparison.

### 6.3 Landing (home)

The home page's GitLab issue and `docs/wireframes/10_home.md` §0 own this screen's fields.

### 6.4 Player profile

**Identity**: name, photo, nationality, birth date, position badge (GK/DF/MF/FW), team.

**Per season** (selector):

- appearances, starts, substitute appearances, minutes
- goals, assists, shots on target
- passes (total, accurate, key), pass accuracy %
- tackles, interceptions, blocks
- duels (won/total, %)
- dribbles (success/attempts, %, dribbled past)
- offsides, cards (yellow/red), penalties (won/committed)
- goalkeepers: saves, conceded, save %

**Match log**: per match: date, competition, opponent (crest), home or away, score, W/D/L, minutes,
goals, assists, cards.

Do not draw per-90 rates or "smart composite scores".

### 6.5 Competition page

The competition page's GitLab issue owns this screen's fields; `docs/wireframes/00_overview.md`
names the issue.

## 7. Component inventory expected from the design

`docs/wireframes/block_standard.md` owns each built element's selector, rule and measurements.

- Fixture row or card
- Stat row (label, value, direction)
- Metric comparison bar (team A vs team B)
- Form string (W W D L W)
- Standings table, with a compact variant
- Player row
- Profile header (team, player)
- Radar or bar set for metric families
- Sparkline or trend (YoY, form over time)
- Big-number callout
- Tab or segment control
- Empty or absent-data state
- Navigation: a mobile bottom bar or burger menu, and a desktop header
- Search field
- Language switcher
- Footer with legal links

## 8. Deliverables requested from the design pass

1. **2–3 distinct visual directions**, shown on ONE screen: the fixture page. Example moods:
   "broadcast bold", "editorial clean", "data-zen".
2. The chosen direction applied to the fixture page, team profile and landing, each for mobile and
   desktop. At least one of them also in dark mode.
3. A token sheet: color palette (with W/D/L and metric-direction semantics, both themes), type
   scale, spacing.
4. The empty and absent states, styled: missing player stats, "–" values, the no-YoY case.

Out of scope for the design pass:

- the predictions UI (slot reserved, nothing rendered)
- monetization slots (named placeholders)
- live-match states
