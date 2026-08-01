# Acceptance evidence — metric labels from the catalogue, per locale (#370 slice)

> Every claim here is read from `site_v2/dist/`, the BUILT output — never from source, never from
> `outerHTML`. Rendered-page measurements are in `.claude/task/rendered_page_evidence.md` and are not
> restated here.
>
> Build: `cd site_v2 && NODE_OPTIONS=--max-old-space-size=8192 npm run build` → **Complete**, 9 pages
> built, 10 audited. `npm test` **59 pass, 0 fail** (via `prebuild`, so it gates the build).
> `check-page-specs: 3 page(s) validated. OK.` `audit-seo: 10 built page(s) checked. OK.`
> `pytest tests/test_governance_hooks.py` **245 pass**.

criteria_demonstrated:
  - **Each stat name is written down once.** `metricRows.ts` declares no `label:` and the three
    `heroSot*` chrome strings are gone, both pinned by tests that fail on revert. The 18 names live
    only in `METRIC_LABELS_{EN,DE,FI}`, keyed by the catalogue's own `label_i18n_key`.

  - **A German reader sees German stat names.** Hero tiles, matched on the built markup
    `<span class="hl">…</span><span class="hv num">…</span>`:

    | locale | tile 1 | tile 2 | tile 3 |
    |---|---|---|---|
    | en | `Ø Shots on target` 5.7 | `Ø Shots on target against` 3.7 | `Ø Shots on target difference` +2.0 |
    | de | `Ø Torschüsse` 5,7 | `Ø Torschüsse gegen` 3,7 | `Ø Torschussdifferenz` +2,0 |
    | fi | `Ø Maalilaukaukset` 5,7 | `Ø Maalilaukaukset vastaan` 3,7 | `Ø Maalilaukauksien ero` +2,0 |

    Performance rows, first six from `<span class="vs-name">`:
    en `Ø Goals · Ø Goals against · Clean sheets · Ø Shots · % Shots from box · Ø Shots on target`;
    de `Ø Tore · Ø Gegentore · Zu-Null-Spiele · Ø Schüsse · % Schüsse aus dem Strafraum · Ø Torschüsse`;
    fi `Ø Maalit · Ø Päästetyt maalit · Nollapelit · Ø Laukaukset · % Laukaukset boksista · Ø Maalilaukaukset`.
    **Before this task all three columns were the English one.** All six German and Finnish hero values
    are the CPO's own words, supplied verbatim.

  - **No raw lookup code reaches a reader.** `metricLabel()` deliberately does not fall back to the key
    the way `t()` does, because a miss would print `metrics.duels_per_match.label` on a public page.
    **`grep -rE "metrics\.[a-z_]+\.label" dist` → 0 files**, across all of `dist`, not only HTML.
    Pinned forward by `every metric name the page asks for resolves in all three locales` and `no
    locale carries a label nothing renders, and none is empty`.

  - **Every name belongs to a stat that really exists.** `every labelKey is a label_i18n_key the
    catalogue actually declares` reads the **`label_i18n_key` column** of `metric_catalogue.csv` and
    requires every key used by `metricRows.ts` and `DeservedHero.astro` to appear verbatim, asserting
    it parsed at least 50 declared keys first. Proved non-vacuous: the catalogue's real key passes and
    a key derived from the `metric_id` column fails.

  - **The CPO's validated wording is unchanged.** `the CPO-validated MVP labels are byte-identical to
    site/i18n` compares against `site/i18n/{en,de,fi}.json` and asserts it compared at least 27, so it
    cannot pass by comparing none. Confirmed in the built pages: de `Ø Tore`, `Ø Gegentore`,
    `% Angekommene Pässe`, `Ø Ecken gegen`; fi `Ø Maalit`, `Ø Päästetyt maalit`, `% Syöttötarkkuus`,
    `Ø Päästetyt kulmapotkut`. The one deliberate exclusion is EN `finishing_efficiency`, where v2's
    locked `% Goals per shot on target` is kept over the corpus's `% Conversion rate`.

  - **The new names go through the same copy check as everything else.** `check_copy_gate.py` gained a
    second parser, because its entry regex requires a bare identifier and cannot see a quoted dotted
    key — 54 user-visible strings would otherwise have skipped the em dash, completeness and
    terminology checks. It parses **18 per locale, 54 total**, and its finding count is **16, unchanged,
    with 0 naming a metric label**. Exit 1 comes from those 16 pre-existing findings, which are the
    CPO's copy to fix (#872).

## One name per metric, on every surface that shows it

Four strings on the deserved-vs-actual block name the same number, and nothing binds them, so revising
one leaves three disagreeing. Read from `dist/` after all four were aligned:

| line | en | de | fi |
|---|---|---|---|
| verdict sentence | `a shots-on-target difference of +2.0 per match` | `eine Torschussdifferenz von +2,0 pro Spiel` | `maalilaukauksien ero +2,0 ottelua kohden` |
| tile 3 | `Ø Shots on target difference` | `Ø Torschussdifferenz` | `Ø Maalilaukauksien ero` |
| chart axis | `Shots on target difference / match` | `Torschussdifferenz / Spiel` | `Maalilaukauksien ero / ottelu` |
| chart caption | `shots-on-target difference per match` | `der Torschussdifferenz pro Spiel` | `maalilaukauksien eron ottelua kohden` |

Both prose changes are the CPO's, ruled on the rendered sentences. **The binding is still by hand** —
the tile reads `METRIC_LABELS`, the other three are chrome strings — which is why binding prose to the
layer is the next task rather than a promise in a comment.

**Retired forms are gone from `dist/`**, swept by stem and case-insensitively over all of it, with the
German rows word-anchored so the current `Torschussdifferenz` cannot false-positive them:
`aufs Tor` 0 · `\bDifferenz (von|der|Sch)` 0 · `laukaus.ro` 0 · `laukaisu` 0 · `maalia kohti` 0.
Positive controls, so an empty or stale `dist` cannot read as a pass: `Torsch` 2 files ·
`maalilaukau` 2 · `Torschussdifferenz` 1 · `Maalilaukauksien ero` 1.

## Beyond the criteria, stated because it is not covered

- **English is byte-identical.** All 18 EN values equal the `label:` and `heroSot*` strings they
  replace, including `% Goals per shot on target`. **No English text on any page changes**, which is
  what makes this diff safe on the side the CPO cannot proof-read.
- **The build gate found a defect I had missed:** `check-page-specs.mjs` refused the build because
  `team.spec.json` declared `heroSotDiff`, a key criterion 1 deletes. Fixing that exposed a second,
  pre-existing gap — the block renders three tile labels and declared one.
- **Residuals**, each with an owner: `sublabel` is still English in all three locales (a caption, not a
  name); `heroVerdictUnder`/`Over` hand-spell the name rather than reading it from `METRIC_LABELS`;
  `YearOverYear.astro` renders three stat names from chrome strings; metric GROUP headings render in
  English on DE/FI pages (**#875**, needs a ruling); every other place a stat is named or abbreviated
  (**#877**, needs only the words); `.vs-row` labels break mid-word in DE/FI (**#876**, CPO ruled
  "leave it filed"); EN `finishing_efficiency` has two approved names; and the `-n` of `eron` in the
  Finnish caption is my inference, approved on that basis and still unverified against a source.
