# Rendered page evidence — `feat/40-top-players-block` (#40 MR B, the Top players block)

> ⚠ **EVERY NUMBER BELOW WAS RE-DERIVED ON 2026-09-09**, after the CPO's ranking rulings moved the
> tie-break into the warehouse and the payload was re-exported. `bi-analyst-reviewer` FAILed round 2
> because §5 still carried the pre-re-export counts while `acceptance_evidence.md` had been updated
> — a file describing a state that is not the one on disk, which is the same class it FAILed round 1
> for, one level down.
> The fix is not to correct the one number it caught. Every figure in this file was pulled out and
> re-checked against the running page and the committed payload; the ones that turned out unchanged
> are marked VERIFIED, not assumed. Two were wrong (§5), the rest held.
>
> Round 1's finding was that this file documented `feat/navigation-rules-competition-shell` (!151)
> entirely — a different branch. It was replaced wholesale then, and re-derived now.

> ⚠ **RE-CONFIRMED AFTER THE MR C SWITCH.** The export now orders by the served
> `board_leader_order` column instead of restating three keys. The payload it produces is
> byte-identical to the one every number below was measured against (line endings aside — see
> `acceptance_evidence.md`), so the rendered figures cannot have moved. `npm run build` was re-run
> anyway rather than reasoned about, and returned the same counts: `audit-seo: 250 built page(s)
> checked. OK.` and `/[lang]/players/[player] -> 84`.

Read from the RUNNING page (Astro dev server, `preview_start` name `v2`) and the built `site_v2/dist`.
Screenshots are unavailable in this pane, so geometry is `getBoundingClientRect()` /
`getComputedStyle()` and structure is the emitted HTML.

## 1. The block renders in all three locales, with no blank board title — VERIFIED

From `dist/{de,en,fi}/index.html`, HTML comments stripped and whitespace collapsed first — Astro
splits interpolated text with `<!-- -->`, so a naive line grep misses these.

| | section heads | board titles | blank titles | rows |
|---|---|---|---|---|
| **EN** | Next matches, Top players | Goals, Assists, Passes, Key passes | 0 | 28 |
| **DE** | Nächste Spiele, Top-Spieler | Tore, **Torvorlagen**, Pässe, Schlüsselpässe | 0 | 28 |
| **FI** | Seuraavat ottelut, Kärkipelaajat | Maalit, Maalisyötöt, Syötöt, Avainsyötöt | 0 | 28 |

`metricLabel()` falls back to English and then to `""`, so a missing Finnish label renders an empty
heading rather than an error — the blank count is the check that matters. DE assists is the CPO's
2026-09-08 ruling. The intro line names exactly seven leagues in each locale, which is the set every
board shows; it is derived from the rendered rows, so it cannot claim a league they lack.

## 2. Geometry at 375×812 — RE-MEASURED against the new payload

Row height is driven by whether a name wraps, and the ruling changed which players appear, so this
was re-run rather than carried over. It came out the same, which is a result and not an assumption.

| board | board width | row heights | min | `.ent` computed display | `.v` left / right |
|---|---|---|---|---|---|
| Goals | 343px | 57×6, 56 | **55.8px** | `block` (one value) | 303 / 359 |
| Assists | 343px | 57×6, 56 | **55.8px** | `block` (one value) | 303 / 359 |
| Passes | 343px | 57×6, 73 | **56.8px** | `block` (one value) | 303 / 359 |
| Key passes | 343px | 57×6, 56 | **55.8px** | `block` (one value) | 303 / 359 |

- **Tap target**: smallest row 55.8px against the 44px floor. !151 shipped a 21px target.
- **Per-board stacking**: `.ent`'s computed `display` collapses to a SINGLE value within each board,
  so a board stacks as a whole and never row-by-row — the CPO's 2026-08-10 rule ("they all stack
  together or not"). That is why the trigger is the board's own container width and not
  `flex-wrap`, which decides per row.
- **Value alignment**: one left edge and one right edge per board across all seven rows.
- The 73px row on Passes is a name wrapping to two lines — intended, since the name must never
  truncate on a block whose purpose is to reach the player's page.

## 3. Geometry at 1280×900 — RE-MEASURED

| board | board width | row heights | min | `.ent` display | `.v` right | any name truncated |
|---|---|---|---|---|---|---|
| all four | 624px | 44–45 | **44.0px** | `flex` (one value) | 945 | no |

Above the 480px container breakpoint every board switches to the one-line variant, again as a whole.
`scrollWidth > clientWidth` is false for every `.nm`.

## 4. The focus ring — a real defect, fixed, re-verified after the fix

Real keyboard focus (`Tab` from the previous row, `:focus-visible` confirmed true), row 3 of the
Goals board at 375px:

| | outline-width | outline-offset | reach beyond border box | ring top / bottom | dividers | verdict |
|---|---|---|---|---|---|---|
| **before** | 2px | 2px | **4px** | 373.5 / 438.3 | 377.5 and 434.3 | crosses BOTH |
| **after** | 2px | **-2px** | **0px** | 377.5 / 434.3 | 377.5 and 434.3 | clears both |

`crossesUpperDivider` and `crossesLowerDivider` are both `false` after the fix, re-confirmed on the
current payload.
⚠ The **before** row cannot be re-measured without reverting the CSS, so it is labelled as what it
is: measured on this branch before the fix, on the earlier payload. It remains the right comparison
because the row geometry is identical across the two payloads — §2 re-measured the same heights and
the same y-positions (divider above 377.5, below 434.3), so only the ring moved.

This is the same 4px overshoot `a.cnm` was fixed for earlier in `system.css`, and the defect !151
shipped. A row cannot spend the room outward the way `a.cnm` did — its neighbour is flush, and
padding would move the divider it is measured against — so the ring is drawn inward instead. At
`-2px` the outline sits entirely inside the border box at any row height.

## 5. The player links resolve — ⚠ THE NUMBERS ROUND 2 CAUGHT, CORRECTED

`npm run build`, run against the committed payload:

```
[seo-audit] page-count driver: /robots.txt -> 1, /[lang]/competitions -> 3,
  /[lang]/players/[player] -> 84, /[lang]/teams/[team] -> 3,
  /[lang]/[competition]/matches/[fixture] -> 12, /[lang]/[competition] -> 144, /[lang] -> 3, / -> 1
audit-seo: 250 built page(s) checked. OK.
```

The home page emits **28** `a.brow` hrefs over **28 distinct slugs** — counted from the running page
and independently from `landing.json` — and 28 × 3 locales = the **84** player pages the audit
counts. Check 8 (dead internal link) passes. Before this branch no page in `site_v2` emitted a
player href at all, which is the only reason that check was green without a player route.

⚠ **WHAT WAS WRONG HERE, AND WHY IT MATTERS.** This section said 28 hrefs over **27** distinct slugs
and **81** pages, from a build captured BEFORE the re-export. Under the old Python tie-break Dybala
led both the assists and key-passes boards, so one slug repeated; under the ruled tie-break he leads
neither and all 28 are distinct. The mechanism was never in doubt — `getStaticPaths` dedupes by slug
— but the count is DATA-DEPENDENT, which is exactly why it must be read from the build rather than
asserted, and why updating `acceptance_evidence.md` alone was not enough.

A stub renders correctly — `/fi/players/n-amiri-714/`:

- `<title>` → `N. Amiri (1. FSV Mainz 05): yleiskatsaus` (locale-distinct, club-disambiguated)
- breadcrumb → `Etusivu › N. Amiri`
- `<h1>` → `N. Amiri`

`read_console_messages` with `onlyErrors` returns nothing on the home page or a stub.

## 6. What is NOT evidenced here

- No screenshot: the Browser pane's `screenshot` action fails in this environment, so every visual
  claim above is a measured number or emitted text, never an image.
- Dark/light theme was not toggled. The block introduces no new colour token — it uses `--ink`,
  `--muted`, `--line`, `--div`, `--surface` and `--sunk`, all of which the theme already swaps — so
  there is no new theme surface to test. That is an argument, not a measurement, and is labelled as
  one.
- The player stub's own content, beyond its title, breadcrumb and h1 — because it has none. It is a
  `stub: true` page and #845 owns what it eventually shows.
