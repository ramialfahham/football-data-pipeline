# Rendered page evidence — `feat/41-top-teams-block` (#41, the Top teams block)

Read from the RUNNING page (Astro dev server, `preview_start` name `v2`) and the built
`site_v2/dist`. Screenshots are unavailable in this pane, so geometry is `getBoundingClientRect()` /
`getComputedStyle()` and structure is the emitted HTML.

⛔ **THIS FILE HAS GONE STALE TWICE, AND THE SECOND TIME IS THE INSTRUCTIVE ONE.**

1. The first version of this branch was written without reading #41 and was wrong in three places —
   unlinked rows, raw board labels, invented intro copy. This file measured that build, and was
   replaced wholesale rather than amended.
2. ⚠ **The replacement then claimed "EVERY NUMBER HERE WAS RE-DERIVED", and that claim was itself
   false within two rounds.** The CPO re-ruled BOTH home intro sentences on 2026-09-10, after this
   file was rebuilt, and §3b went on quoting the superseded copy. `bi-analyst-reviewer` FAILed round
   4 for it. A blanket "everything was re-derived" banner is exactly the wrong instrument: it is
   written once, ages silently, and reads as an assurance while it decays.

So the standing rule for this file is **re-capture on every build whose output it quotes**, not
"re-derive once and declare it". Every rendered quote below carries the artefact it came from
(`dist/{lang}/index.html`, the audit line, or a measured geometry value) so a stale one can be
spotted by re-running the same read rather than by trusting a banner.

## 1. The composition is complete — three sections

`document.querySelectorAll('section')` returns **3**: next matches, Top players, Top teams. That is
10_home.md §0's composition, finished.

## 2. The board title spells the rate out, per locale — #41's rule

From `dist/{en,de,fi}/index.html`, comments stripped and whitespace collapsed:

| | team board titles |
|---|---|
| **EN** | Goals per match · Shots on goal per match · Passes per match · Duels per match |
| **DE** | Tore pro Spiel · Torschüsse pro Spiel · Pässe pro Spiel · Zweikämpfe pro Spiel |
| **FI** | Maalit ottelua kohden · Maalilaukaukset ottelua kohden · Syötöt ottelua kohden · Kaksinkamppailut ottelua kohden |

**Sigil left behind: 0 in every locale.** #41: "Ø Goals" reads badly as a heading and a bare "Goals"
wrongly reads as a season total, so the sigil is expanded into the words it stands for.

Each is derived from the LOCALISED label, which is the part #41 warns about by name — the DE and FI
labels carry the sigil too, so deriving from the English one would title a Finnish board in English.
The "per match" wording is not new copy: `heroVerdictUnder`/`heroCaption` already ship "per match",
"pro Spiel" and "ottelua kohden".

The player boards are untouched and still read Goals / Assists / Passes / Key passes — those are
metric ROW labels, which `metrics_display.md` locks, and #41's expansion is the heading case only.
That boundary is now RECORDED in `metrics_display.md` itself rather than only in #41 and a code
comment — `analytics-engineer-reviewer` FAILed the branch for the record gap, and the file's own
charter ("records the display rulings … until they are codified as catalogue columns") is where it
belonged.

⛔ **THE HEADINGS ABOVE ARE UNCHANGED, BUT THE CODE BEHIND THEM WAS REWRITTEN.** `boardTitle()` used
to read `metricId.endsWith("_per_match")` before expanding. That was a taxonomy judgement made in
the frontend — and unsound on this catalogue, where `shots_on_goal_per_match` declares the label key
`metrics.shots_on_target_per_match.label`. It now takes `(lang, labelKey)` only and branches on
nothing; the premise that the block's four boards are per-match rates is asserted against the
catalogue's `denominator_expr` in `test_the_team_board_set_is_all_per_match_rates`. Mutations:

| mutant | result |
|---|---|
| `duels_won_pct` (a team metric, `denominator_expr = sum(duels_total)`) joins `_HOME_TEAM_BOARDS` | RED |
| `boardTitle` stops stripping the sigil | RED, 2 JS tests |

## 3. Every row links out — #41: "That is why the block exists"

`npm run build`:

```
[seo-audit] page-count driver: /robots.txt -> 1, /[lang]/competitions -> 3,
  /[lang]/players/[player] -> 84, /[lang]/teams/[team] -> 60,
  /[lang]/[competition]/matches/[fixture] -> 12, /[lang]/[competition] -> 144, /[lang] -> 3, / -> 1
audit-seo: 307 built page(s) checked. OK.
```

- Team pages went **3 → 60**: the 20 distinct teams the boards link to, × 3 locales.
- On the running page, **28 team hrefs** and **7 anchors on every one of the four team boards** —
  against 0 anchors in the first version of this branch.
- Check 8 (dead internal link) passes, so all 20 payloads are committed and every href resolves.
  That is the procedure `site_v2/src/data/README.md` sets out for a sample that is a SET, and the
  same reason the four linked fixtures are committed.

## 3b. The competition name is the warehouse's, on every surface that shows one

The CPO read `1. Fußball-Bundesliga` in the Top players intro on the rendered page. The export was
building its competition dict from `docs/competition_registry.yml`, which is INPUT; the site
displays `mart_competition_index.competition_name`.

⛔ **THIS TABLE QUOTED THE PRE-RULING COPY FOR A FULL ROUND, and `bi-analyst-reviewer` FAILed round
4 for it.** It was captured after the competition-name fix but before the CPO re-ruled both intro
sentences on 2026-09-10, and never re-captured — so it showed "The top player from each league:"
with no window phrase and no "in the rankings", and the superseded DE/FI nouns (*beste Spieler*,
*paras pelaaja*). The file's own opening claim that every number was re-derived was therefore false
for exactly the one string on this branch with the longest history of being wrong. Worse, the Top
TEAMS intro — this MR's actual deliverable, and the string that FAILed rounds 1 and 2 — was not
quoted anywhere in this file at all, so the acceptance criterion "the intro sentence names exactly
the leagues that appear on the boards" had no built-page evidence behind it.

Re-captured below from `dist/{en,de,fi}/index.html`, comments stripped and whitespace collapsed,
**both blocks, all three locales** — the complete sentences, not excerpts:

| | Top players | Top teams |
|---|---|---|
| **EN** | Current season. The top player from each league in the rankings: La Liga, Serie A, Liga Portugal, Ligue 1, Eredivisie, **Bundesliga**, Premier League. | Current season. The top team from each league in the rankings: La Liga, Eredivisie, **Bundesliga**, Liga Portugal, Serie A, Premier League, Ligue 1. |
| **DE** | Aktuelle Saison. Der Top-Spieler jeder Liga in den Ranglisten: La Liga, Serie A, Liga Portugal, Ligue 1, Eredivisie, **Bundesliga**, Premier League. | Aktuelle Saison. Die Top-Mannschaft jeder Liga in den Ranglisten: La Liga, Eredivisie, **Bundesliga**, Liga Portugal, Serie A, Premier League, Ligue 1. |
| **FI** | Tämä kausi. Kunkin sarjan kärkipelaaja ranking-listoilla: La Liga, Serie A, Liga Portugal, Ligue 1, Eredivisie, **Bundesliga**, Premier League. | Tämä kausi. Kunkin sarjan kärkijoukkue ranking-listoilla: La Liga, Eredivisie, **Bundesliga**, Liga Portugal, Serie A, Premier League, Ligue 1. |

Two things this table now evidences that the old one could not:
- **`Bundesliga`, not `1. Fußball-Bundesliga`**, in six rendered sentences — the defect the CPO
  caught, in both blocks and all three locales.
- **Each block's league list is its OWN boards' members**, not a shared constant: the two orders
  differ (players open `La Liga, Serie A, Liga Portugal…`, teams `La Liga, Eredivisie, Bundesliga…`)
  because each is read from that block's payload rows. A hardcoded list would render identically.

Swept across the whole registry rather than the pool that made it visible — **37 names identical,
11 DIFFERENT**: BL1, BL2, UECL, all seven WCQ*, and WC (`FIFA World Cup 2026` → `FIFA World Cup`).
37 of 48 agreeing is why one wrong row hid; six of the seven elite leagues are among the 37.

**Both surfaces, not just the one that was looked at.** `competitions.json` is registry-derived too
and `TeamHeader.astro` renders it, so BL1 team pages carried the same string — and two of the twenty
team pages this branch builds are BL1 clubs. After the fix, `/en/teams/bayern-munchen/` renders
`Bundesliga` in its header. `competitions.json` gains 11 corrected names and **0 slug changes**: the
slug is an assigned identifier, not a display string.

Swept over the whole build: `Fußball-Bundesliga`, `FIFA World Cup 2026`,
`UEFA Europa Conference League` and `WC Qualification` appear in **0 of the 307 built pages**.

Mutation-tested, four mutants, all now caught:

| mutant | result |
|---|---|
| `_competitions_index` ignores the warehouse (the shipped defect) | RED |
| `_warehouse_competition_meta` widened to carry a slug | RED |
| the overlay prefers a served slug over the registry's | RED **only after the test was rewritten** |
| `fetch_landing_payload` drops the name overlay | `landing.json` reverts to `1. Fußball-Bundesliga` |

⚠ The third one SURVIVED at first. Asserting the slug beside the name was **vacuous**: the helper
selects only `league_code, competition_name, region_rank`, so no slug ever reached the overlay and
the assertion could not fail whatever the code did. It is now its own test with the helper patched
to hand a slug over — the only shape in which it means anything.

## 4. Geometry at 375×812 — all EIGHT boards

| | rows | min row height | `.ent` computed display | `.v` right edge | anchors |
|---|---|---|---|---|---|
| four player boards | 7 | 55.8–56.8px | `block` (one value) | 359 | 7 each |
| four team boards | 7 | 55.8px | `block` (one value) | 359 | 7 each |

- Tap target: smallest row 55.8px against the 44px floor.
- Per-board stacking: `.ent` collapses to a SINGLE computed display value per board, so a board
  stacks as a whole and never row-by-row — CPO 2026-08-10, "they all stack together or not".
- **The two blocks line up with each other**: the value column's right edge is 359 on all eight,
  not merely consistent within each block. This branch adds no CSS; that is the evidence the shared
  board pattern actually holds.

## 5. Geometry at 1280×900

| | min row height | `.ent` display | `.v` right edge | any name truncated |
|---|---|---|---|---|
| all eight boards | **44.0px** | `flex` (one value) | 945 | no |

## 6. The focus ring, re-measured on a TEAM board

The rows are anchors now, so `:focus-visible` applies to them and had to be checked rather than
carried over from the player block. Real keyboard focus (`Tab`, `:focus-visible` confirmed true),
row 3 of the "Shots on goal per match" board at 375px:

| outline-offset | reach beyond border box | ring top / bottom | dividers | crosses |
|---|---|---|---|---|
| **-2px** | **0px** | 377.5 / 434.3 | 377.5 and 434.3 | **no** |

The `a.brow:focus-visible { outline-offset: -2px }` rule shipped with #40 covers these rows too,
which is what "no new CSS" has to mean if it is true.

`read_console_messages` with `onlyErrors` returns nothing.

## 7. What is NOT evidenced here

- No screenshot: the pane's `screenshot` action fails in this environment, so every visual claim is
  a measured number or emitted text.
- No dark/light toggle. The block adds no colour token — it reuses the board classes Top players
  shipped, which the theme swaps. Reasoning, not a measurement, and labelled as one.
- The crest images are not fetched here. #41 records that the block inherits #36 (crests hotlinked
  from `media.api-sports.io`, a go-live blocker with a licence question attached). This block does
  not add to that problem and does not solve it.
