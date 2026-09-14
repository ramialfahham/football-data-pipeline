# Competitions index — `/{locale}/competitions/` (#62 step 5, GitLab #54)

> ⭐ **THE AUTHORITY FOR THIS PAGE IS GITLAB #128** ("The approved design", CPO 2026-09-14), which
> rechecked the filters, the groups, the order, the row, the competition set and the links. Where
> this file and #128 disagree, #128 wins; the passages that disagreed on 2026-09-14 are corrected
> in place and marked `#128`. What #128 changed against this file: **every row links to its
> competition's page**; the empty-group collapse decides from the **filter state**, never from
> on-screen visibility; every competition kind in the seed carries all three languages; the
> country under a row is shown in the reader's language (#69). No country-hub pages exist or are
> planned under this page. #144 builds the page-owned parts.

## 1. Purpose

Every competition we carry, grouped and browsable: the site's "everything we cover" page, and
the first item in the main nav to point somewhere real. Designed and CPO-reviewed 2026-08-10 on
GitLab #54, corrected several times through 2026-08-17 (grouping axis, ordering rule, region
resolution); built here from that record, not from a separate mock. Distinct from the competition
HUB (`/{locale}/{competition-slug}/`, #47) — this is the index above it, not a single competition's
own page.

## 2. URL

`/{locale}/competitions/` — one page per locale (`page_count_driver: count(locales)`), permanent.
Route: `site_v2/src/pages/[lang]/competitions/index.astro`.

## 3. Data sources

One mart, one export, one committed file — the whole point of #62. `mart_competition_index`
(`dbt_project/models/5_marts/shared/mart_competition_index.sql`, merged `!65`) → `scripts/
export_site_data.py`'s `fetch_competition_index()`/`shape_competition_index()` (`!67`) →
`site_v2/src/data/competition_index.json`, 48 rows, committed whole (small enough not to sample).
Before #62 this page would have read four things directly (the registry YAML, `competition_types.
csv`, `confederations.csv`, `dim_league`) — `docs/content_architecture.md` §1 forbids that, and
#62 is the fix. Binding rule (00_overview.md): every field below is verifiable against
`competition_index.json`'s actual keys; nothing here is invented ahead of the data.

## 4. Layout

```
┌────────────────────────────────────────────┐
│ Home › Competitions                        │  breadcrumb
│ Competitions                               │  H1 (reuses navCompetitions — #54)
│ [ All | Clubs | National teams ]           │  filter axis 1 (entity_type)
│ [ All | Europe | S.America | ... ]         │  filter axis 2 (confederation)
│                                             │
│ Domestic leagues                           │  category heading, ALWAYS shown
│  [crest] Premier League      England       │
│  [crest] La Liga             Spain         │  responsive grid, 280px min column
│  ...                                       │
│                                             │
│ Continental championships                  │
│  [crest] UEFA Nations League  Europe       │
│  ...                                       │
└────────────────────────────────────────────┘
```

Single column at the standard 680px `.inner` measure — the mock's 1080px override was flagged in
#54 as "a system-level decision, not a page one... flagged for a ruling" and never actually ruled
on, so this ships at the width every other page uses rather than carrying an unresolved system
change. Row grid is `repeat(auto-fill, minmax(280px, 1fr))` — "as many as fit" per #54's spec,
which naturally yields 2 columns at 680px rather than the mock's 3-at-1100px, since the container
itself is narrower here.

## 5. Module bindings

| Element | Source | i18n / notes |
|---|---|---|
| Category heading | `competition_type` (grouped) | `t(lang, category_label_i18n_key)` — the served key, no derivation |
| Row crest | `logo_url` | `Crest.astro` (shared with team/fixture rows), falls back to a monogram when null |
| Row name | `competition_name` | — |
| Row region sub-line | `region_label_en` / `region_label_i18n_key` | i18n key when set (a confederation); raw `region_label_en` when the key is null (a country name — not chrome, #62) |
| Filter — type | `entity_type` (club / national) | `filterAll` / `filterClubs` / `filterNational` |
| Filter — region | `confederation` (7 codes) | `filterAll` / `confedUefa` / `confedConmebol` / `confedConcacaf` / `confedCaf` / `confedAfc` / `confedOfc` / `confedFifa` |
| Row/category order | `region_rank`, `next_kickoff_datetime`, `last_kickoff_datetime` | computed by `lib/competitionOrder.mjs`, not served pre-sorted — see §7 |
| Breadcrumb + H1 | — | both `navCompetitions` (#54: "the H1 deliberately reuses the NAV item's key, so the menu and the page it leads to cannot drift apart") |
| `<title>` / meta description | — | `seoCompetitionsTitle` / `seoCompetitionsDesc` |

## 6. States

- **Every row is a link to its competition's page** (`/{locale}/{competition-slug}/`; #128,
  built by #144) with the same hover/active treatment as the Home boards' rows. ~~Rows are NOT
  links, on purpose. #54 describes each row as a "row target" linking to the competition's own
  page. That page (#47, the competition hub) is confirmed not built — only the fixture page exists
  under `[competition]/`. Linking today would be the exact "browse-chip 404" #47's own issue
  text names as a failure mode.~~ The page exists for every row: `[competition]/index.astro`
  builds one per `competition_index.json` row.
- **Every category always shows its heading**, including one with a single member — never hidden
  for looking sparse.
- **A category with zero visible rows under the active filter disappears entirely** — no
  "0 results" placeholder. Independent per filter combination (e.g. Clubs + Oceania can legitimately
  empty a category neither axis alone would).
- **Filters are single-select per axis**, not the mock's limitation but this round's own scope
  decision — #54 calls for client-side multi-select eventually; deferred to a follow-up (§10).

## 7. Interactions

- Two independent radio groups (`entity-filter`, `region-filter`), each defaulting to "All". Row
  show/hide is the zero-JS `.seg-in`/`:checked ~` sibling-selector pattern already used for the
  fixture page's W1/W2 toggle and the team page's tabs — nine simple CSS rules, no compound
  selectors, since each axis hides independently.
- Category collapse (zero visible rows → hide the whole category) is the one place this page uses
  real JS: doing it in pure CSS would need a hand-written rule per (entity × region) combination
  (up to ~24) to express "zero rows survive BOTH active filters at once", which `:checked` sibling
  selectors can express but not maintainably. A small inline script decides it on every filter
  `change` (and once on load) **from the filter state** — the two checked radios' values against
  each row's `data-entity-type` / `data-confederation` — and toggles `[hidden]` (#128). ~~re-evaluates
  each category's visible-row count~~: it used `offsetParent`, which is null for every row while
  the tab is not displayed, so a page loaded in a background tab hid all eight categories until a
  filter was touched. Progressive enhancement only: the unfiltered page is already correct without
  it (every rendered category has ≥1 row).
- Ordering (`lib/competitionOrder.mjs`, unit-tested) is applied once at render time, not stored:
  has-upcoming-fixture → days-to-next-kickoff bucketed by calendar day → `region_rank` → kickoff
  time → `league_code`; no-upcoming rows sort last, most-recently-played first. The SAME key
  orders the category headings, by their own earliest-sorting member (`escalations.log`,
  2026-08-16) — this is why a category can rank ahead of "Domestic leagues" during an
  international break, with no special case written for it.

## 8. SEO

Page-spec: `site_v2/src/specs/competitions/index.spec.json`. `schema_org: ItemList`
(`numberOfItems` only — no `itemListElement`, since rows carry no URL yet to list, per §6).
`inbound_hub: "none"` — honest rather than "home": the `SiteHeader` nav links here sitewide after
this change, but that's persistent chrome, not a dedicated content hub, the same distinction the
home page's own spec already makes (also `"none"` despite being nav-linked from everywhere).
`outbound: []` for the same reason rows aren't links yet. `url_permanence: "permanent"` — the
route survives; only the row content's linkedness is still catching up.

## 9. Component census

| Component | File | New? |
|---|---|---|
| Competitions index page | `pages/[lang]/competitions/index.astro` | ✓ new |
| Grouped/filtered grid | `components/competitions/CompetitionIndexGrid.astro` | ✓ new |
| Ordering logic | `lib/competitionOrder.mjs` (+ `competitionOrder.test.mjs`) | ✓ new |
| Crest | `components/ui/Crest.astro` | reused, unchanged |
| Nav anchor (Competitions item) | `components/chrome/SiteHeader.astro` | modified — one item, both desktop nav and mobile drawer |

## 10. Gaps

- **Row links** — reserved to the MR that ships #47 (§6).
- **Multi-select filtering** — #54's stated end state; single-select ships this round (§6), a
  follow-up adds the JS.
- **CI wiring** — `competition_index` is not yet in `.gitlab-ci.yml`/`deploy-site-v2.yml`'s
  `--entities` list; nothing outside this page reads the file's freshness guarantee yet, so
  wiring it in now would commit a refresh path nothing depends on. Revisit when a real deploy
  needs it kept current.
- **`minimum_data`** — none beyond the mart's own browsable filter (non-blank `display_group`,
  already applied upstream); every competition in the committed file renders.
