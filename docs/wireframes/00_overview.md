# Website blueprint — overview & format contract (#391)

> The wireframe-level spec for every screen of Matchday Pilot v2. This folder is the
> **primary input** to the design pass (#366) and the template build (#368), and a
> direct input to SEO (#369).

## Which document owns what — READ THIS BEFORE DESIGNING OR BUILDING A SCREEN

Six documents govern what a screen shows. Each owns a different question, and they are listed here
once so nobody has to guess. `CLAUDE.md`'s authority table points here rather than restating it.

| Question | Owner |
|---|---|
| What does the product look and feel like? | [`docs/ui_design_brief.md`](../ui_design_brief.md) §§1–5, 7 — principles, constraints, component inventory. ⚠ Its **§6 is NOT look-and-feel** — see below |
| What is the URL, and where does the page sit? | [`docs/site_architecture.md`](../site_architecture.md) — IA and URL scheme |
| Which blocks compose the page, and which mart backs each? | [`docs/content_architecture.md`](../content_architecture.md) — the block library and tabbed compositions |
| **What does this specific screen show, and is every field real?** | **these wireframes** where one exists for the screen — otherwise [`ui_design_brief.md`](../ui_design_brief.md) **§6**, which is a per-screen field contract in its own right ("what a mockup MAY show"; "if a stat is not listed below, we do not have it — do not draw it") |
| How is a METRIC displayed — label, format, grouping, order, direction? | [`metrics_display.md`](metrics_display.md) — **LOCKED**; the catalogue seed owns what a metric IS, this owns how it renders |
| What did the CPO approve it to LOOK like? | the **GitLab issue** for that surface, with `design-mocks/` as its rendering — see [`design-mocks/README.md`](../../design-mocks/README.md) |

**On conflict: escalate to the CPO.** That rule is unchanged and deliberately absolute — no
"the more recent one wins", no "the more specific one wins". Whoever is reading does not get to
decide which document is right.

A decision he has already made on a screen is not a conflict — it is the answer. Where it lives:
the screen's **GitLab issue** (its `What exactly` checklist and its edits), then the wireframe the
issue's MR edited. Look there before escalating something he has already settled. A ruling from
before 2026-09-11 may sit in the frozen `.claude/task/escalations.log`; cite it, never add to it.

### `ui_design_brief.md` §6 and these wireframes both bind fields — here is the relationship

§6 is titled "Per-screen data contract (what a mockup MAY show)" and the brief calls it *"the single
most important rule in this document"*. It is the same kind of gate as [the binding
rule](#the-binding-rule-the-whole-point) below, not a look-and-feel principle.

The pattern the documents already demonstrate: **once a screen's wireframe is written, it supersedes
that screen's §6 subsection.** §6.3 (Landing) carries exactly that marker and points at
[`10_home.md`](10_home.md) §0.

⛔ **SO §6 IS STILL LIVE FOR ANY SCREEN WITH NO WIREFRAME AND NO APPROVED ISSUE.** The competition
page was that screen until 2026-09-15: `04_competition_hub.md` does not exist, and
`ui_design_brief.md` §6.5 was its only field list. **GitLab #129 ("The approved design") now
supersedes §6.5 for the competition page's Overview tab** — four tabs, and the Overview's four
blocks with their marts, ruled block by block; the three other tabs are shaped there and their
content is reviewed on the same issue. A reader who took row 1 to mean "the brief is look-and-feel"
would have skipped the only field contract that screen had; that was the defect
`bi-analyst-reviewer` FAILed an earlier branch for.

⏳ **OPEN, AND NOT DECIDED HERE:** §6.1 (Fixture), §6.2 (Team profile) and §6.4 (Player profile) have
wireframes and carry NO supersession marker, unlike §6.3. Whether they should is a question for the
CPO — retroactively marking three sections superseded is a decision about which document binds, not
a formatting fix.

⚠ **THE MOCK/ISSUE LAYER IS NOT ABOVE OR BELOW THE WIREFRAMES — IT IS A DIFFERENT AXIS.** The issue
settles what the screen looks like and which boards it carries; the wireframe settles whether every
value on it is a real exported field. A design can be approved and still be unbuildable, and that is
a gap ([`99_gaps_register.md`](99_gaps_register.md)), not a contradiction.

⛔ Until 2026-09-10 this reading order named only three of the six and omitted the mock/issue layer,
which is how #41 came to be rebuilt against a design its issue had already approved.

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
| 04 | 04_competition_hub.md | Competition page: Overview · Matchdays · Teams · Players | **Overview approved on GitLab #129** (2026-09-15, "The approved design") — the authority for the page; #149 builds the Overview tab. No wireframe file: the issue's block list and its data-model table are the field contract. The three other tabs are reviewed on #129 before they are built | 3 |
| 05 | 05_leaderboards.md | Leaderboards + per-metric stats pages | pending | 3 |
| 06 | 06_head_to_head.md | Head-to-head page | pending | 3 |
| 07 | 07_metric_glossary.md | Metric glossary | pending | 3 |
| 08 | [08_browse.md](08_browse.md) | Competitions index | **built** 2026-08-18 (#62 step 5); **approved on GitLab #128** (2026-09-14, "The approved design") — the authority for the page; #144 builds the row links, the collapse fix and the missing labels. ~~Country hubs (`/football/{country-slug}/`) still pending~~ — in no menu and no issue; struck by #128 | 4 |
| 09 | [09_chrome.md](09_chrome.md) | Nav/header/footer/search/locale/404 | **spec'd + built** 2026-07-26 (header/footer/nav/search-chrome/theme-toggle; locale-switch mechanism + 404 page deferred) | 4 |
| 10 | [10_home.md](10_home.md) | Home (pins the homepage spec → unblocks `landing.json`) | **built**, three blocks; **approved on GitLab #127** (2026-09-13, "The approved design") — the authority for Home; the wireframe is corrected to it and #143 builds the Home-owned changes | 5 |
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
