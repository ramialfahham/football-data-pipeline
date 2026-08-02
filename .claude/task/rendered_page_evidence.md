# Rendered-page evidence — feat/846-featured-season-from-mart

> Required by #827 for any `site_v2/src/**` diff. Read from the BUILT output (`site_v2/dist/`),
> never from source and never from `outerHTML`.

## 1. What renders differently: nothing, and that is the acceptance criterion

CPO acceptance criterion 2, approved 2026-08-02 and locked: *"Nothing a visitor sees on a team page
changes. Every sample team opens on the same season as it does today. This is plumbing, not a
redesign."*

`site_v2/src/pages/[lang]/teams/[team].astro:56` stopped applying the opening-season rule and
started reading a served flag:

```
- team.seasons.find((s) => s.competition_type === "domestic_league") ?? team.seasons[0]
+ team.seasons.find((s) => s.is_featured_season)!
```

Every block on the page is fed from that one `season` object (`TeamHeader`, `RecordStrip`,
`DeservedHero`, `YearOverYear`, `TeamFixtures`, `TeamPerformance`, `TeamSquad`), so if the selected
row had moved, the whole page would have moved with it.

## 2. The measurement: byte-identical output, all three locales

Method, because a code read cannot settle this. Built `main`'s version with the branch stashed,
copied the three built team pages out of `dist/`, restored the branch, rebuilt, and diffed:

```
diff before_<lang>.html dist/<lang>/teams/manchester-united/index.html
  de: IDENTICAL
  en: IDENTICAL
  fi: IDENTICAL
```

Not "no visible difference" and not a spot check of selected strings. The rendered HTML is
byte-for-byte the same file in every locale, which also settles geometry, ordering and every string
on the page at once, since none of them can differ if the bytes do not.

Corroborating counts in the built `en` page, before and after: `Premier League` x10, `2025/26` x3.
The page opens on Premier League 2025/26 in both, which is the season the old rule selected.

Why it is identical rather than merely close: the flag in the committed sample was set on the row
the old `.find()` would have returned (`PL 2025`), and the warehouse rule that produces the flag is
the same rule the page used to apply — most recent domestic-league season.

Build: `npm run build` -> 9 pages, 3 team pages x 3 locales,
`audit-seo: 10 built page(s) checked. OK.`

## 3. The missing-flag path, measured rather than argued

The new code carries a non-null assertion, which removes the `?? team.seasons[0]` fallback. What
that does was tested, not assumed: the one flagged season in the committed sample was flipped to
`false` and the site rebuilt.

```
/de/teams/manchester-united/index.html  Cannot read properties of undefined (reading 'league_code')
[build exit 127]
```

**The BUILD fails. A visitor never sees it.** These are statically generated pages, so there is no
runtime path to a browser: the failure happens while producing the HTML, the deploy has nothing to
publish, and the previously deployed page stays up. That is fail-closed in the correct direction
for a data-validity problem, and it is deliberate — a fallback to "some other season" is precisely
the defect this branch removes, so restoring one to make the build survive would reintroduce it.

The sample was restored immediately afterwards and the byte-identical diff in section 2 was re-run
against the restored build to prove the experiment left nothing behind:
`de: IDENTICAL · en: IDENTICAL · fi: IDENTICAL`, `flagged: [('PL', 2025)] | exactly one: True`.

Upstream of that, two things have to fail before a build can reach this state: the `not_null` test on
the column in `shared.yml` for both marts, and the export's own `_featured_season_row`, which raises
rather than writing a payload with no flagged season. A third guard, the singular test asserting
exactly one flagged season per entity, is split out to #886 on the CPO's ruling — it passed against
the real marts in this branch's CI run but cannot ship until prod carries the column (#887).

## 4. Not covered here

The player page is not built on this branch. Its Overview lives in `stash@{0}` and is held on #845,
so there is no rendered player page to measure. The mart half it needs is included, and its own
`.find()` is removed when that branch resumes.
