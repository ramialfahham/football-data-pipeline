# Chrome — global header, footer, search, theme toggle, mobile nav (#391 / #825)

## 1. Purpose

The chrome that wraps every screen: brand, primary navigation, search, locale/theme controls,
and the footer. Unlike the other screens in this folder, chrome has no "stop-scrolling moment" of
its own — its job is to be the same, predictable frame on every page so a reader always knows
where they are and how to get anywhere else. Built as the frontend-foundation task (#825), from
the CPO-approved mock (artifact `87d14109`, "looks good for now").

## 2. URL

N/A — chrome wraps every route in `site_architecture.md` §3. It renders once, inside
`Layout.astro`, around every page's content.

## 3. Data sources

None. Chrome is fixed product IA (`site_architecture.md` §4: "the nav exposes Competitions ·
Matches · Teams · Players · Standings · Statistics"), not registry- or mart-driven — it does not vary
by competition, team, or any exported payload. Labels are static i18n strings
(`site_v2/src/i18n/strings.ts`). This means the binding rule (00_overview.md — "may reference only
fields that exist in today's exported JSON") does not apply here; there is no payload to bind to.

## 4. Layout

```
┌────────────────────────────────────────────┐
│ MatchdayPilot         [search] [🌓] [☰]     │  (1) header, sticky
├────────────────────────────────────────────┤
│  ▾ drawer (phone only, hidden by default)  │  (2) drawer — opens on ☰
│    Competitions                            │
│    Matches                                 │
│    Teams / Players / Standings / Statistics│
├────────────────────────────────────────────┤
│              (page content)                │
├────────────────────────────────────────────┤
│ MatchdayPilot                              │  (3) footer
│ Competitions · Teams · Players ·           │
│ Statistics ·                               │
│ About · Imprint (pending)                  │
│ EN · DE · FI · Data: API-Football          │
└────────────────────────────────────────────┘
```

**Phone (< 700px)**: brand + search icon + theme toggle + hamburger in the header; the 6-item nav
lives in the drawer (`#menuBtn` toggles `.drawer.open`), closed by default.

**≥ 700px**: the 6-item nav (`.mainnav`) goes inline in the header; the hamburger and drawer are
hidden — there is no drawer state to open on a laptop-width screen.

**≥ 900px**: a generic two-column page grid (`.shell > .page-grid { main | aside.rail }`, max
content width ~1100px, rail border-left) becomes available for any page that needs a context rail
alongside its main content. **Not wired into any page this task** — home, competition hub, and
leaderboards are the candidates (per the home-content mock `1c35e7aa`'s rail: standings/
trending/top-scorers), but per-page rail contents is a reserved CPO call (`.claude/task/contract.md`).
The team and fixture pages keep their existing locked single column (`.inner`, 680px, unchanged) —
see §10 for the open gap this leaves.

**≥ 1010px**: the search box becomes a full field with placeholder text (`.searchbox`); the
icon-only mobile search button (`.search-m`) hides.

## 5. Module bindings

All chrome text is chrome-string i18n (`t(lang, key)`), not catalogue-bound (§3). Keys, all in
`site_v2/src/i18n/strings.ts`:

| Element | Key(s) |
|---|---|
| Brand | hardcoded "MatchdayPilot" (proper noun, not translated), links to `localeHref(lang)`. Rendered as SPLIT markup — `Matchday<span class="iq">Pilot</span>` — so no source file contains the joined string; verify any future rename against rendered text, never a grep (#862) |
| Main nav (6 items) | `navCompetitions`, `navMatches`, `navTeams`, `navPlayers`, `navStandings`, `navStatistics` |
| Main nav aria-label | `mainNavAria` |
| Search placeholder / icon-button aria | `searchPlaceholder`, `searchAria` |
| Theme toggle aria | `themeToggleAria` |
| Hamburger aria | `menuAria` |
| Footer link row (5 of 6 items reuse the nav keys) | `navCompetitions`, `navTeams`, `navPlayers`, `navStatistics`, `footerAbout` |
| Footer Imprint slot | `footerImprintPending` |
| Footer data-source line | `footerDataSource` (prefix only — "EN · DE · FI" itself is locale-invariant literal text, language codes are not translated) |

## 6. States

- **No dead links.** A nav or footer item is an inert `<span>` (not `<a>`) until the page behind
  it is built. Competitions became a real link when its index shipped; none of
  Matches/Teams/Players/Standings/Statistics/About has a built index page, so those are still
  spans — beyond Competitions, only detail pages exist today, reachable by direct entity URL and
  not by browsing from chrome. `.mainnav a, .mainnav span` (and the footer/drawer
  equivalents) apply identical styling to both, so an inert item looks no different from a real
  one until it's wired. This mirrors the existing convention on the fixture page's breadcrumb and
  the team page's Explore chips (both already ship this pattern, pre-dating this task). The brand
  links to `localeHref(lang)`, which resolves — the locale root is a real, if placeholder, route.
- **Imprint**: permanently labelled "(pending)" until the CPO settles the operator/address
  question (#799); not a data state, a publication gate.
- **Search**: visually present, functionally inert — no input element wired, no keystroke
  behaviour, no results. Search mechanism/style is a reserved CPO call.
- **Theme**: two states, `data-theme="dark"` (default) / `"light"`, toggled by `#themeBtn` and
  persisted to `localStorage` (`mdp-theme`) so the choice survives navigating to a different
  static page. A blocking inline script (`Layout.astro`, `<script is:inline>`, first thing inside
  `<body>`) applies a saved choice before the header renders, avoiding a flash of the hard-coded
  default for a returning light-theme reader. No-preference default is fixed dark; whether the
  site should ever read `prefers-color-scheme` instead is a separate, reserved question.
- **Drawer**: closed by default on every page load (no persisted open state).

## 7. Interactions

- Hamburger (`#menuBtn`) toggles `.drawer.open` and its own `aria-expanded`; no outside-click or
  Escape-key close (matches the approved mock exactly — nothing more was shown or asked for).
- Theme toggle (`#themeBtn`) flips `data-theme` on `<body>` and writes the choice to
  `localStorage`; both handlers live in `SiteHeader.astro`'s own `<script>` (module, not
  blocking — only the FOUC-prevention read in `Layout.astro` needs to block).
- Both are vanilla JS, not the site's existing JS-free radio-toggle CSS pattern (tabs, segments):
  that pattern only shows/hides a sibling panel within one component tree, but these two mutate
  an attribute across the whole shell (theme) or toggle a landmark nav's visibility (drawer).

## 8. SEO

N/A for this spec — chrome carries no schema.org markup of its own (`BreadcrumbList` is per-page,
already shipped on the fixture and team pages). `robots: noindex` stays on every page while v2 is
a build-phase preview (`Layout.astro`, pre-existing, unchanged by this task).

## 9. Component census

New this task, added to the aggregate census in `00_overview.md`:

| Component | File | Brief §7? |
|---|---|---|
| Site header (brand, nav, search, theme toggle, hamburger) | `components/chrome/SiteHeader.astro` | ✓ ("nav … desktop header") |
| Mobile nav drawer | `components/chrome/SiteHeader.astro` (same file — one component, two rendered regions) | ✓ ("nav … mobile bottom-bar or burger") |
| Site footer (brand, link row, locale/data-source meta) | `components/chrome/SiteFooter.astro` | ✓ ("footer (legal links)") |
| Generic page grid (`.shell`/`.page-grid`/`.rail`) | `styles/system.css` (no dedicated component — a layout primitive, not a visual component) | ➕ (system-level, not in the brief's component list) |

## 10. Gaps

Not a data gap (chrome has no export dependency, §3) — two open, non-data items, recorded here
rather than silently resolved:

- **Team/fixture desktop width.** The original wireframes (`01_fixture_page.md` §4,
  `02_team_profile.md` §4) call for those two pages themselves to widen to ~1100px on desktop with
  an internal two-column reflow. Today they still render at the locked 680px `.inner` single
  column (unchanged by this task — see §4 above). Closing this means changing an already-shipped,
  CPO-approved page's width, which is a design decision outside this task's contract.
- **Rail contents.** The `.page-grid`/`.rail` primitive exists but is wired into zero pages. The
  home-content mock (`1c35e7aa`, reference only) shows one candidate rail (standings/trending/
  top-scorers) for the eventual home page — CPO decides per page type when that page is built.
