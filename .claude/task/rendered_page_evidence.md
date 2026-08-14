# Rendered-page evidence — feat/367-landing-page (#367)

> Required by #827 for any `site_v2/src/**` diff. Read from the BUILT output (`site_v2/dist/`) and
> from the running preview, never from source and never from `outerHTML`.
>
> RE-MEASURED 2026-08-08 against the TWO-module page, after the trending block was cut. This file
> has now been replaced twice for the same reason, which is the point worth carrying forward: an
> artifact describing a superseded build cannot discharge the evidence requirement for the diff
> under review, and a code read cannot show block order, geometry or chip counts. Replaced wholesale
> each time, per the corrections-replace rule.

Build: `npm run build` in `site_v2` -> 45 pages emitted, `audit-seo: 46 built page(s) checked. OK.`
Preview: `preview_start` name `v2` on port 4321, viewport 375x812.

⚠ Page count fell 63 -> 45. That is 18 pages, exactly the six team payloads removed with trending
times three locales, and it is expected rather than a regression: the trending row's team link was
the only link to a team page anywhere on the site, so those six pages had become orphans.

⚠ `preview_start` name `v2` is CORRECT this session and was NOT in the previous one. It resolves
`.claude/launch.json` from the harness root; that root was a different worktree on 2026-08-08 and
served its "under construction" scaffold. Confirm which tree is being served before trusting any
measurement here — the check is that `/en/` renders "Next matches", not a scaffold.

## 1. What renders, per locale, read out of `dist/`

| | de | en | fi |
|---|---|---|---|
| `<title>` | Fußballstatistiken und Spielvorschauen | Football stats and match previews | Jalkapallotilastot ja otteluennakot |
| canonical | `/de/` | `/en/` | `/fi/` |
| hreflang | de, en, fi, x-default | de, en, fi, x-default | de, en, fi, x-default |
| blocks, DOM order | Nächste Spiele → Entdecken | Next matches → Browse | Seuraavat ottelut → Selaa |
| match links | 12, all unique | 12, all unique | 12, all unique |
| team links | **0** | **0** | **0** |
| `.prow` rows | **0** | **0** | **0** |
| browse chips | 66 | 66 | 66 |
| of which anchors | 0 | 0 | 0 |
| country headings | 15 | 15 | 15 |
| bytes | 17,345 | 17,214 | 17,258 |

Distinct titles 3/3, distinct descriptions 3/3 — acceptance criterion 5, from built output.
`x-default` resolves to `https://matchdaypilot.com/en/`, not `/`.

Descriptions, all three rewritten AGAIN this round:

```
de  Kommende Spiele aus allen Wettbewerben, die wir abdecken, dazu Ligen, Pokale und Länder zum Entdecken.
en  Upcoming matches from every competition we cover, plus leagues, cups and countries to browse.
fi  Tulevat ottelut kaikista kattamistamme kilpailuista sekä sarjat, cupit ja maat selattavaksi.
```

⚠ **THE SAME DEFECT, TWICE, ONE MODULE APART.** The previous round rewrote these because they
promised "league tables, top scorers" after the stats teasers were removed. The replacement then
promised "teams on a run" / "Teams in Form" / "vireessä olevat joukkueet" — which is the trending
block, removed this round. Each time the block was deleted and the copy that advertised it was not.

The lesson is a check, not resolve-to-do-better: **after deleting a block, re-read the built
`<meta description>` in all three locales.** A source grep does not surface it, because the copy
describes the block without naming it — "teams on a run" contains neither "trending" nor any mart
name. That is the same "a deleted module leaves traces that do not carry its name" class recorded
in `10_home.md` §9, and it has now fired three times on this branch.

Wording is provisional: all copy is a §10 CPO call and is on the open list.

## 2. Block order and geometry, measured live at 375px

| block | top | height |
|---|---|---|
| Next matches | 95px | 1205px |
| Browse | 1336px | 2531px |

Page height 4126px, measured (`document.documentElement.scrollHeight`), NOT derived. A draft of the
matching table in `10_home.md` reached 4162px by subtracting the trending block from the old total
and was wrong; the number here is read from the running page.

**Browse is last**, the 2026-08-04 CPO ruling, and it is now block 2 of a decided 4 rather than of
3 — it holds the bottom slot so Top players and Top teams insert above it without rearranging
anything. Browse moved up 409px (1745 -> 1336), exactly the trending block plus its margin.

No horizontal overflow: `documentElement.scrollWidth` 375 equals `clientWidth` 375.

## 3. Both removed blocks are gone, verified three ways each

**The stats teasers** (CPO 2026-08-08: *"top scorers and table are useless, i already said it, why
is it in the pr???"*) — block, two export helpers, component, three type interfaces, four i18n keys
× 3 locales, page-spec entry, ten tests.

**Trending** (absent from the CPO's 2026-08-08 composition) — block, `TrendingList.astro`, the
`trending[]` key, `mart_landing_trending` and its `shared.yml` entry, `TrendingStory`, six i18n keys
× 3 locales, page-spec entry, seven tests, six team payloads and their `.gitignore` allowlist rows.

- **Rendered body, all three locales**, comments stripped and whitespace collapsed: zero occurrences
  of `Top scorers`/`Torjäger`/`Maalintekijät`, and zero of
  `Trending|Im Trend|Nousussa|unbeaten|ungeschlagen|winless|streak`. `.prow` count 0 — that was the
  row primitive trending composed, and no home component uses it now.
- **Whole tree, not just the diff**: `eligible_stats_competitions`, `pick_stats_competition`,
  `_STATS_ROWS`, `LandingStats`, `LandingScorer`, `LandingStandingRow`, `select_trending`,
  `TrendingStory`, `mart_landing_trending` return no hits outside explanatory comments.
- **Payload**: `landing.json` carries `{type, upcoming, browse}` — neither removed key;
  `index.spec.json` declares exactly two blocks and `outbound: ["fixture"]`, matching the measured
  0 team links.

⚠ Near-misses recorded, because each looked like a leak and was not. `Tabelle` and `Sarjataulukko`
are the site header's standings nav item, a different key. `pts` appears inside `opts` in a script
comment. `trend` appears in `system.css` as the deserved-vs-actual regression line (`.sc .trend`)
and in `types.ts` as "on the trend line" — both belong to the team page, not this one, and neither
was touched. Every one of these was a crude match on a value or substring rather than on the key;
the check that settles it matches exact phrases in visible text with scripts and comments stripped.

## 4. Chips are still inert, deliberately

66 browse chips per locale, `a.linkchip` count 0, `span.linkchip` count 66. The competition hub
does not exist, so linking them would emit a guaranteed 404 on the site's front door. The hover
affordance is scoped to `a.linkchip:hover`, so an inert chip does not invite a click; that fix from
round 1 survives this round's reorder, re-verified live rather than from CSS source.

This is why `index.spec.json` declares `"outbound": ["fixture"]` and nothing else — the page
genuinely has no competition edge yet, and since the trending cut it has no team edge either.

⚠ That declaration has now been wrong twice, both times because a removed module took its links with
it: it read `["fixture", "competition", "team"]`, then `["fixture", "team"]`, and is now
`["fixture"]`. Each correction followed a block deletion. **Re-derive it by counting anchors in the
built HTML, never by editing the previous value** — this round's 0 team links is a measurement, not
an inference.

## 5. Not covered here

No BigQuery was queried and no dbt test was executed against real data. The three new seed tests
are verified only to REGISTER (`dbt ls` shows them in the manifest) and to hold against the CSV as
it stands; `data:build:mr` is where they actually run.

The player page is not on this branch; its Overview lives in `stash@{1}`, held on #845.
