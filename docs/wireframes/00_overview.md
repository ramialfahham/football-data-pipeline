# Website blueprint — overview & format contract (#391)

> The wireframe-level spec for every screen of Matchday Pilot v2. This folder is the
> **primary input** to the design pass (#366) and the template build (#368), and a
> direct input to SEO (#369). The brief (`docs/ui_design_brief.md`) sets look-and-feel
> principles; `docs/site_architecture.md` fixes IA/URLs; these wireframes bind every
> block of every screen to a real exported field. Conflicts escalate to the CPO.

## The binding rule (the whole point)

A wireframe block may reference **only** fields that exist in today's exported JSON —
verifiable against the `shape_*` functions in `scripts/export_site_data.py` (and the
mart columns they `select *` from). Anything a screen *should* show but the export
does not carry goes to [`99_gaps_register.md`](99_gaps_register.md) with a proposed
disposition — it is **never silently drawn**. Metric labels, formats and
better/worse direction come only from `dbt_project/seeds/metric_catalogue.csv`
(catalogue governance — new metrics need a CPO-approved catalogue addition first).

## Per-screen spec template

Every screen file follows this structure:

| § | Section | Contents |
|---|---------|----------|
| 1 | Purpose | The screen's job + its **stop-scrolling moment** (north-star principle 1) |
| 2 | URL | Route pattern, params, locale notes (from `site_architecture.md` §3) |
| 3 | Data sources | Export file(s) + the exact payload keys consumed |
| 4 | Layout | Mobile-first ASCII wireframe with an explicit `——— fold ———` marker; desktop adaptation notes |
| 5 | Module bindings | Per block: JSON keys → format → direction → label source → link targets |
| 6 | States | Null/absent rules, partial-data cases, the thin-page rule |
| 7 | Interactions | Tabs, selectors, drill-downs; static-site constraints |
| 8 | SEO | Title/meta templates, schema.org type, breadcrumb, internal links |
| 9 | Component census | Which brief-§7 components the screen uses; NEW components flagged |
| 10 | Gaps | Links to gaps-register entries |

## Display conventions (apply to every screen)

- **Null → "-"** — never a fabricated zero. A null *block* (vs a null value) renders
  its designed empty state, or is omitted entirely where absence is by design
  (each spec says which).
- **Formats** from the catalogue `format` column: `integer` (no decimals),
  `decimal_0` / `decimal_1` (fixed decimals, locale separators), `percent`
  (0–100 with %, 0 decimals), `points_fraction` (e.g. `10/15` — won of available).
- **Direction**: catalogue `lower_is_better` decides which side of a comparison is
  "better"; the encoding (color + shape, never color alone) is a design-pass token.
- **W/D/L**: letter + color, never color alone (brief §4).
- **Tabular numerals** on every stat column.
- **Text expansion**: design with DE (~+30% vs EN); labels are i18n keys.
- **Timezones**: kickoff datetimes export as UTC ISO strings; render server-side in
  a competition-neutral format and progressively enhance to the visitor's local
  timezone with a tiny script (static site cannot know the timezone at build time).

## Layout system

The responsive chrome + grid contract, built as the frontend-foundation task (#825; full spec:
[09_chrome.md](09_chrome.md)). `system.css`'s only breakpoints before this were `@container`
queries scoped to a single component (e.g. `.split`, `.yoygrid`) — these three are the first
viewport-level `@media` rules beyond `prefers-reduced-motion`, and they govern the shared shell,
not any one screen:

| Breakpoint | What changes |
|---|---|
| **≥ 700px** | `.mainnav` goes inline in the header; the hamburger (`.hamburger`) and mobile drawer (`.drawer`) hide. |
| **≥ 900px** | The generic page grid (`.shell > .page-grid { main + aside.rail }`) goes two columns (`minmax(0,1.9fr) minmax(0,1fr)`), rail gets a left border. Max content width **~1100px** (`.shell`/`.header-in`/`.footer-in`). |
| **≥ 1010px** | The header search box (`.searchbox`) becomes a full field; the icon-only mobile search button (`.search-m`) hides. |

`.shell`/`.page-grid`/`.rail` is a **generic primitive**, not wired into any page yet — which
pages get a rail and what fills it is reserved (per-page rail contents, `.claude/task/contract.md`).
It is distinct from the team/fixture pages' own `.inner` (680px, single column, locked from the
CPO-approved mocks `d70aae67`/`f6348775`) — those two pages are unchanged by the foundation shell
and do not use `.page-grid`. **Open gap**: the original wireframes (01, 02) call for those two
pages themselves to widen to ~1100px on desktop with an internal two-column reflow; that has not
been built, and closing it means changing an already-shipped page's width — a separate decision,
not made here. See 09_chrome.md §10 for the full note.

## Screen inventory

| # | File | Screen | Spec status | PR |
|---|------|--------|-------------|----|
| 01 | [01_fixture_page.md](01_fixture_page.md) | Fixture page ⭐ | **spec'd** | 1 |
| — | [metrics_display.md](metrics_display.md) | Metric display contract (team + player, LOCKED) | **ruled** | 1 |
| 02 | [02_team_profile.md](02_team_profile.md) | Team profile ⭐ | **spec'd** | 2 |
| 03 | [03_player_profile.md](03_player_profile.md) | Player profile ⭐ | **spec'd** | 2 |
| 04 | 04_competition_hub.md | Competition hub + season + table + fixtures + top scorers | pending | 3 |
| 05 | 05_leaderboards.md | Leaderboards + per-metric stats pages | pending | 3 |
| 06 | 06_head_to_head.md | Head-to-head page | pending | 3 |
| 07 | 07_metric_glossary.md | Metric glossary | pending | 3 |
| 08 | [08_browse.md](08_browse.md) | Competitions index + country hubs | **competitions index built** 2026-08-18 (#62 step 5); country hubs (`/football/{country-slug}/`) still pending | 4 |
| 09 | [09_chrome.md](09_chrome.md) | Nav/header/footer/search/locale/404 | **spec'd + built** 2026-07-26 (header/footer/nav/search-chrome/theme-toggle; locale-switch mechanism + 404 page deferred) | 4 |
| 10 | 10_home.md | Home (pins the homepage spec → unblocks `landing.json`) | pending | 5 |
| 11 | [11_team_squad.md](11_team_squad.md) | Team → Squad (roster + per-player apps/mins-per-app/goals/assists) | **built** 2026-07-24 | #391 ⁑ |
| 12 | [12_player_stats.md](12_player_stats.md) | Player → Stats (percentile vs peers) | **spec'd** | #391 ⁑ |
| 13 | [13_player_career.md](13_player_career.md) | Player → Career (clubs · competitions · seasons) | **spec'd** | #391 ⁑ |
| 14 | [14_team_stats.md](14_team_stats.md) | Team → Stats (rank vs league) | **spec'd** | #391 ⁑ |
| 99 | [99_gaps_register.md](99_gaps_register.md) | Data-gap register | live | 1+ |

Order rationale: the fixture page first — the product's heart and the most
field-dense screen; it calibrates the vocabulary (stat rows, comparison bars, form
strings) every other screen reuses. Home last — it is mostly teasers of the other
screens and the only screen needing new feeds.

The **PR** column is the original blueprint batch (1–5) that first spec'd each
screen. **⁑** marks a screen added later, outside the original batches, under
epic **#391**'s data-first un-pause (gap-closure track) rather than a numbered
batch.

## Component census (aggregated — grows as screens land)

Components used so far, reconciled against brief §7. ➕ = not in the brief's §7
inventory, flagged as new for the design system (#366).

| Component | Used by | Brief §7? |
|---|---|---|
| Breadcrumb | 01 | ➕ (implied by SEO section) |
| Fixture header (crests, kickoff, venue, round) | 01 | profile header family |
| Standing chip (rank + points) | 01 | ➕ |
| Segment control (W1/W2) | 01 | tab/segment control ✓ |
| Metric comparison row (label + two values + paired bar) | 01 | metric comparison bar ✓ |
| Window caption (window meta line) | 01 | ➕ |
| Form string (W W D L W chips) | 01 | form string ✓ |
| Fixture row (past match, clickable) | 01 | fixture row/card ✓ |
| Result chip (W/D/L) | 01 | part of form string family |
| Player row (photo, name, stat columns) | 01 | player row ✓ |
| H2H record block (aggregate W-D-L bar + counts) | 01 | ➕ |
| Empty/absent state | 01, 02, 03, 11, 12, 13, 14 | ✓ |
| Narrative block (data-to-text slot) | 01 | ➕ (slot only — GAP-03) |
| Internal-links footer | 01, 02, 03, 11, 12, 13, 14 | ➕ (SEO-driven) |
| Profile header (team/player) | 02, 03, 11, 12, 13, 14 | ✓ |
| Competition-/season selector | 02, 03, 11, 12, 14 | ➕ |
| Position selector | 12 | ➕ |
| Percentile rank bar (single fill + track + dashed median) | 12 | ➕ |
| Rank + spread bar (value · k-of-N · vs-median · p25/median/p75 track) | 14 | ➕ |
| Sample caption (peers · minutes · apps) | 12 | ➕ |
| Big-number record block | 02 | big-number callout ✓ |
| Single-bar ratio row + gap callout (deserved vs actual) | 02 | ➕ |
| Aligned-comparison row (YoY) | 02 | sparkline/trend family ✓ |
| Streak chip | 02 | ➕ |
| Stat row (label + value + direction) | 02 | ✓ |
| Group subhead | 01, 02, 03, 12, 14 | ➕ |
| Position badge | 03 | ➕ |
| Fact summary line | 03 | ➕ |
| Bundled stat row (player contract) | 03 | player row ✓ |
| Match-log row | 03 | ➕ |
| Position-group header | 11 | ➕ |
| Squad player row (monogram · name · nationality · age · apps · mins/app · goals · assists) | 11 | player row ✓ |
| Club group header (crest + name) | 13 | ➕ |
| Career-log row (season · comp · apps · goals · assists) | 13 | player row ✓ |
| Subtotal / career-total line | 13 | ➕ |
| National-caps block | 13 | ➕ |
| Site header (brand, nav, search, theme toggle) | 09 | ✓ (nav … desktop header) |
| Mobile nav drawer | 09 | ✓ (nav … mobile bottom-bar or burger) |
| Site footer (link row + locale/data-source meta) | 09 | ✓ (footer (legal links)) |
| Generic page grid (main + rail) | 09 | ➕ (system-level layout primitive, not a visual component) |

## Verification (per screen, before its PR merges)

1. Every JSON key named in §5 exists in the export payload (cross-check against the
   `shape_*` functions / mart column lists — keys are written exactly to stay
   greppable).
2. Every metric label/format/direction references a real `metric_catalogue` row.
3. §6 covers the known partial-data cases for that screen's marts.
4. New components are flagged in the census, none silently invented.
