# Rendered-page evidence — feat/370-metric-labels-from-catalogue

> Required by #827 for any `site_v2/src/**` diff. Read from the BUILT output (`site_v2/dist/`) or
> measured against the running dev server — never from source, never from `outerHTML`.

## 1. What renders differently

Metric names moved out of `metricRows.ts` and three hero chrome strings into one per-locale block keyed
by the catalogue's `label_i18n_key`. **Before this branch, every metric name on the German and Finnish
team and fixture pages was the English one.**

| surface | en | de | fi |
|---|---|---|---|
| hero tile 1 | `Ø Shots on target` | `Ø Torschüsse` | `Ø Maalilaukaukset` |
| hero tile 2 | `Ø Shots on target against` | `Ø Torschüsse gegen` | `Ø Maalilaukaukset vastaan` |
| hero tile 3 | `Ø Shots on target difference` | `Ø Torschussdifferenz` | `Ø Maalilaukauksien ero` |
| Performance row 1 | `Ø Goals` | `Ø Tore` | `Ø Maalit` |
| Performance row 3 | `Clean sheets` | `Zu-Null-Spiele` | `Nollapelit` |
| Performance row 8 | `Ø Duels` | `Ø Zweikämpfe` | `Ø Kaksinkamppailut` |

## 2. Overflow — the defect this branch caused, and its fix

Localised names are longer than English ones, so `overflow-wrap: normal` (inherited from the design
system) clipped them. Measured on the running dev server at **375 x 812** with a **Range-based** method,
after `scrollWidth` proved untrustworthy — it reported nothing wrong on the fixture page while a
22-character word sat in a 49px box. Numbers are `max(text rect width) − content box width`; negative
fits. Each container is measured **on the tab that renders it**: a hidden container yields no client
rects, which would read as a clean zero.

**Before**, with labels localised and no styling change:

| surface | locale | worst label | over |
|---|---|---|---|
| hero tile (71px box) | fi | `Ø Maalilaukauksien ero` | **+12.0** |
| Performance row (77px box) | fi | `% Viimeistelytehokkuus` | **+53.3** |
| Performance rows | fi | **9 of 16 overflowed** | |

`% Viimeistelytehokkuus` is a **CPO-validated corpus string**, so the gap was pre-existing in
`system.css` and localisation merely exposed it. Not a defect in his copy.

**After** `overflow-wrap: anywhere` on `.hero .hn .hl` and `.vs-name`, plus the hero stack:

| container | tab measured on | en | de | fi |
|---|---|---|---|---|
| hero tiles, worst of 3 | Overview | +0.5 | +0.4 | +0.3 |
| `.verdict` + `.cap2` prose | Overview | −2.8 | −5.6 | −1.3 |
| `.vs-row` labels, worst of 16 | Performance / vs-league | −0.3 | −0.3 | −0.3 |
| `.ss-row` labels, worst of 16 | Performance / vs-season | +0.5 | +0.4 | +0.5 |
| anything over **1px** | both | 0 | 0 | 0 |
| `unmeasured` (no client rects) | both | 0 | 0 | 0 |
| sideways page scroll | both | no (375 = 375) | no | no |

The sub-pixel figures are rounding between a fractional Range rect and an integer `clientWidth`: they
appear in **English**, where this branch changes no string. `.ss-row` also has no `overflow: hidden` and
its label box grows to 175px, so a real 0.5px excess would wrap rather than clip.

## 3. Zero overflow is not the same as reading like a word

`overflow-wrap: anywhere` prevents clipping by breaking at an arbitrary letter, with no hyphen.
Measured with the same Range method, walking character by character to recover each line's text:

| locale | hero tile 3, before the stack |
|---|---|
| de | `Ø` / `Torschussdiffe` / `renz` |
| fi | `Ø` / `Maalilaukauksi` / `en ero` — all THREE Finnish tiles broke this way |

`hyphens: auto` does not fix it: tested live, and this engine carries no de/fi hyphenation dictionary,
so the line breaks are byte-identical with it on. The tile label box is 71px at 375px while
`Torschussdifferenz` alone needs **89.1px**, so no wrap rule can save three tiles side by side.

**Fix, CPO-approved ("Stack them on phones") after being shown the rendered line breaks:** below 560px
the three tiles become three rows, name left and value right. Measured at 375px, per tile:

| | px |
|---|---|
| tile, outer | 301.0 |
| tile, content box | 277.0 |
| value box (`.hv`, widest) | 36.2 |
| flex gap | 10 |
| **label's available width** | **~231** |
| label's rendered width, longest German (`Ø Torschussdifferenz`) | 100.4 |
| what that word needs | 89.1 |

| | en | de | fi |
|---|---|---|---|
| hero tile mid-word breaks, before | 0 | 2 | 3 |
| hero tile mid-word breaks, after | **0** | **0** | **0** |
| `.heronums` block height | 96px → **149px** | same | same |
| `.ss-row` mid-word breaks | 0 | 0 | 0 |

A mid-word break is counted mechanically: a line that is not the last and does not end in whitespace or
a hyphen. English is unaffected either way — its names already fit.

**`.vs-row` still breaks mid-word: 3 rows in German, 9 in Finnish.** Its label column is 77px inside a
four-column grid, and widening it costs the comparison bar 115px → 80px, which is a visible change to a
block the CPO has not ruled on. Nothing clips or overflows there (max −0.3px). **#876**, with the
one-line fix and its measured trade-off; he ruled "leave it filed".

## 4. The fixture page, tabulated

16 of the 19 render slots this branch localises are on the fixture page, and its German row 6 changed
value (`Ø Schüsse aufs Tor` → `Ø Torschüsse`). Same instrument, same viewport, both windows forced via
`#seg-w1` / `#seg-w2`:

| `.mlabel`, 375x812 | en w1 | en w2 | de w1 | de w2 | fi w1 | fi w2 |
|---|---|---|---|---|---|---|
| labels measured | 16 | 16 | 16 | 16 | 16 | 16 |
| `unmeasured` | 0 | 0 | 0 | 0 | 0 | 0 |
| worst overflow | +0.3 | +0.3 | +0.4 | +0.4 | +0.4 | +0.4 |
| over **1px** | 0 | 0 | 0 | 0 | 0 | 0 |
| **mid-word breaks** | **0** | **0** | **0** | **0** | **0** | **0** |
| sideways page scroll | no (375 = 375) | | no | | no | |

`.mlabel` deliberately did NOT get `overflow-wrap: anywhere`, and the numbers say it does not need it:
`.mmid` is the centre track of the `1fr 1.5fr 1fr` grid at `system.css:126` and centres rather than
stretches, so a long compound wraps on whitespace inside a wide box. At 375px that track is ~137px,
nearly double the hero tile. It is the only container clean **without** the wrap rule.

## 5. No lookup code reaches a reader

```
grep -rE 'metrics\.[a-z_]+\.label' dist   ->  0 files   (all of dist, not only HTML)
find dist -name '*.html'                  ->  10 files
audit-seo: 10 built page(s) checked. OK.
check-page-specs: 3 page(s) validated against their specs. OK.
npm test: 59 pass, 0 fail   (runs via prebuild, so it gates the build)
```

## 6. No screenshot, and why that is not a gap

`computer{action:"screenshot"}` fails in this environment ("the Browser pane is not displayed, so the
page is not compositing frames"). For the questions at issue — does the block name one metric
consistently, and does any label clip or break — measured text and measured pixel overflow are stronger
evidence than an eyeball, and #862's rule points the same way: read the built output, not a rendering
of it.
