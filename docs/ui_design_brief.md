# UI design brief — Matchday IQ v2

> The data-grounded brief for the v2 visual design pass (#366, epic #361). Written to
> be handed to a design tool (Claude Design) or a human UI/UX expert as a
> self-contained package. **Everything a mockup shows must be backed by a field listed
> in §6 — the single most important rule in this document.** Structure/IA/URLs are
> fixed by `docs/site_architecture.md`; this brief governs the look, feel and layout.

## 1. Product context

**Matchday IQ** — a fun, sticky pre-match companion for football fans: the site you
open in the sports bar before kickoff, share with your group chat, and argue over.
Not a stats database, not a betting tool. Casual fans must feel smart in seconds;
hardcore fans must find depth on demand.

- Audience: casual + hardcore fans, mobile-first, multilingual (8+ languages).
- Scale ambition: media-grade platform (kicker/onefootball class), millions of users.
- v2 replaces a card-based mobile MVP; it is a full responsive website with
  programmatic pages for every competition, fixture, team and player.

## 2. Design principles (locked — Thread 3 + north star)

1. **Every page has one thing that makes you stop scrolling.**
2. **Data shown, not described** — charts over tables wherever possible.
3. **Max 2 clicks from home to anything interesting.**
4. **Data honesty**: a missing value renders as **"-"** — never a fabricated zero,
   never an invented stat. Empty states are designed, not hidden
   (e.g. "Player stats not available for this match" is a COMMON state, style it well).
5. Simple surface, depth on demand (progressive disclosure, not walls of numbers).

## 3. Reference sites (inspiration, not blueprint)

CPO note: none of these is to be copied; each contributes one thing.

| Site | Take | Avoid |
|---|---|---|
| last5games.com | The last-5-form-centric match preview — closest to our W1 momentum concept | Spartan look, no brand warmth |
| whoscored.com | Depth: ratings, dense stat tables, profile structure | Cluttered, dated, ad-heavy density |
| onefootball.com | Modern media UX: mobile-first cards, clean type, content hierarchy | News-first (we are data-first) |
| flashscore.com | Speed, fixtures-first navigation, information density done fast | Utilitarian, zero storytelling |

## 4. Hard design constraints

- **Responsive, mobile-first** — phone is the primary device (sports-bar use case);
  must scale to tablet/desktop multi-column gracefully.
- **Light + dark theme** from day one (tokens, not afterthought).
- **Multilingual**: text expands (DE ≈ +30% vs EN); layouts must tolerate it.
  Arabic (RTL) comes later — avoid direction-baked compositions.
- **Tabular numerals** for all stat columns (non-negotiable for a stats product).
- **Color semantics**: Win/Draw/Loss needs a consistent encoding (color + letter,
  never color alone); metrics have a "good direction" (the data carries
  `lower_is_better`) — the system must express better/worse consistently.
- **Accessibility WCAG AA**: contrast in both themes, touch targets, reduced motion.
- **Static site, fast**: no heavy JS; charts are lightweight islands. Core Web
  Vitals budget — design for instant first paint.
- **Images**: team crests + player photos come from the provider CDN (small PNGs,
  variable quality); design needs a graceful fallback (monogram/initials).
- Labels/wording are i18n keys — design with realistic longest-language strings.

## 5. Navigation & page inventory (fixed by site_architecture.md)

Nav: `Competitions · Matches · Teams · Players · Standings · Stats` + search + language.
Browse axes: competition groups (Leagues / Cups / Continental / National teams) AND
country hubs. Pages to design (priority order):

1. **Fixture page** ⭐ (the heart of the product)
2. **Team profile** ⭐
3. **Landing**
4. **Player profile**
5. Competition hub (incl. standings, fixtures, leaderboards tabs)
6. Head-to-head, metric glossary (system pages — derive from the established language)

## 6. Per-screen data contract (what a mockup MAY show)

Metric display names come from the metric catalogue (translated); listed here as
plain-English meaning. **If a stat is not listed below, we do not have it — do not
draw it** (no xG, no shot maps, no heat maps, no pass networks, no win probability).

### 6.1 Fixture page ⭐
Header: both teams (name, crest), kickoff datetime, competition, round, venue name.
Two complementary windows per team, always shown side by side:
- **W1 — last-5 form (cross-competition)**: games in window (≤5), points won,
  goals/match, goals against/match, shots/match, shot accuracy %, danger-zone ratio %
  (share of shots from inside the box), finishing efficiency %, passes/match,
  pass accuracy %, corners/match, corners conceded/match, save ratio %, key
  passes/match, tackles/match, interceptions/match, blocks/match, duels won %,
  dribbles success %, the list of contributing competitions, league rank (when a
  single round-robin table applies — else absent).
- **W2 — season to date (this competition)**: same metric set, cumulative; before a
  season starts it falls back to the previous season (labelled).
- **Form drill-down (per team)**: the actual last-5 matches — opponent (name, crest),
  date, competition, home/away, score, W/D/L — each clickable when a stat line exists
  (flags say whether team/player stats are available).
- **Match detail (a clicked past match)**: full team stat lines both sides
  (possession %, shots on/off/total/blocked/inside/outside box, fouls, corners,
  offsides, cards, saves, passes total/accurate/%) + per-player stat lines both sides
  (minutes, shirt, position, captain/sub, goals, assists, shots, passes, key
  passes, tackles, interceptions, blocks, duels, dribbles, fouls, cards, penalties).
- **Player insights (per team)**: top players over the form window — appearances,
  minutes, goals, assists, shots on target, key passes, pass accuracy %, duels won %,
  dribbles success %, cards; GK: saves, goals conceded, save %.
- Standings context: each team's rank + mini table slice (league/group phases only).
- Signature-moment candidates: the W1↔W2 contrast ("hot now vs season reality"),
  the form drill-down interaction.

### 6.2 Team profile ⭐
Identity: name, crest, country, founded, venue (name, city, capacity).
Per season (selector):
- Record: played, W/D/L, goals for/against, goal difference, points, clean sheets,
  rank, recent form string (e.g. WWDLW).
- Season metric rates: the same metric family as §6.1 (per-match values + ratios).
- **Deserved vs actual** (a differentiator): shot share % (share of all shots in the
  team's matches), points capture % (points won / points available), and the labelled
  gap between them — "dominates play more/less than results show". Two real numbers
  + their difference; NOT a composite score gauge.
- **Year-over-year** (domestic leagues): points / goals for / goals against through N
  games this season vs the same N games last season, with deltas. NULL for cups and
  where last season isn't ingested — design the absent state.
- **Streaks**: current unbeaten / win / winless / clean-sheet / scoring runs.
- Fixtures: next + recent matches list.
- Signature-moment candidates: deserved-vs-actual visual; YoY trend comparison.

### 6.3 Landing (home)
Agreed **hybrid** model (CPO, 2026-06-10): fixtures-first, with stats/storylines below.
The MVP's competition-card landing is **obsolete** for a website. Module order
(top → bottom), each tagged with its real data status:

1. **Fixtures hero — upcoming matches.** The product's core feature (the MVP's
   fixture list), elevated to the home across competitions: date-navigable, grouped
   by competition, each row carrying its form hook and linking to the fixture page.
   *Status:* the per-competition list + fixture page exist; ⚠ the cross-competition
   home aggregation is a feed to build.
2. **Hybrid browse:** competition groups (Leagues / Cups / Continental / National)
   + country hubs (crest/flag grid or list). *Status:* ✓ registry (#364).
3. **Storylines — "Trending":** biggest YoY risers/fallers, longest active streaks,
   biggest deserved-vs-actual gaps. *Status:* ✓ data in `mart_team_profile`; ⚠ needs
   the data-to-text narrative generator (build).
4. **Stats:** top-scorer leaderboard teasers + mini standings. *Status:*
   ✓ `mart_leaderboards`, `mart_standings`.

Persistent: search, language switcher.

The fixture page reached from the hero shows the **side-by-side form comparison**
(existing — the match preview) plus **past-meetings head-to-head**
(`mart_head_to_head`, #375). Note: an earlier draft of this section listed a landing
composition that had not been discussed; this is the reviewed, agreed version.

### 6.4 Player profile
Identity: name, photo, nationality, birth date, position badge (GK/DF/MF/FW), team.
Per season (selector): appearances, starts, sub appearances, minutes; goals, assists,
shots on target, passes (total, accurate, key), pass accuracy %, tackles,
interceptions, blocks, duels (won/total, %), dribbles (success/attempts, %, dribbled
past), offsides, cards (Y/R), penalties (won/committed); GK: saves, conceded, save %.
**Match log**: per match — date, competition, opponent (crest), home/away, score,
W/D/L, minutes, goals, assists, cards.
Note: per-90 rates and "smart composite scores" are deliberately NOT available yet —
do not draw them.

### 6.5 Competition hub
Standings table (rank, team+crest, P W D L GF GA GD Pts, form string; group tables
for tournaments incl. group letters), fixtures by round, top-scorer leaderboard
(rank, player, team, goals, assists, appearances), season selector.

## 7. Component inventory expected from the design

Fixture row/card · stat row (label + value + direction) · metric comparison bar
(team A vs B) · form string (W W D L W) · standings table (+compact variant) ·
player row · profile header (team/player) · radar or bar set for metric families ·
sparkline/trend (YoY, form over time) · big-number callout · tab/segment control ·
empty/absent-data state · nav (mobile bottom-bar or burger + desktop header) ·
search field · language switcher · footer (legal links).

## 8. Deliverables requested from the design pass

1. **2–3 distinct visual directions** (mood: e.g. "broadcast bold" vs "editorial
   clean" vs "data-zen") shown on ONE screen — the fixture page.
2. The chosen direction applied to: fixture page, team profile, landing (mobile +
   desktop for each), incl. dark mode for at least one.
3. Token sheet: color palette (incl. W/D/L + metric-direction semantics, both
   themes), type scale, spacing.
4. The empty/absent states styled (missing player stats; "-" values; no-YoY case).

Out of scope for the design pass: predictions UI (slot reserved, nothing rendered),
monetization slots (named placeholders), live-match states.
