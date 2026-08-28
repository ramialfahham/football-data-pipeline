# Metric display contract — groups, tiers, order (#391)

> The CPO-ruled display contract for metric lists everywhere they render (fixture
> comparison, team profile, player profile, leaderboards). The
> `metric_catalogue.csv` seed stays the single source of metric definitions (the
> SSoT); this document records the **display**
> rulings (grouping, importance tier, order) until they are codified as catalogue
> columns (GAP-09). **Team table: LOCKED (CPO, 2026-06-11). Player rows: LOCKED
> (CPO, 2026-06-11).**

## Tier semantics (ruled)

> **Tiers now live in `metric_catalogue.csv`, and they cover players (CPO, 2026-08-04).**
> The seed carries a tier on all 85 rows. This section keeps the SEMANTICS; the values are in
> the seed. What this document still owns exclusively is **order**, which was deliberately
> removed from the catalogue: where a metric sits on a page is a frontend decision that changes
> with a design, so the seed holds what a metric IS, not where it appears.

1. **Tier never orders.** Display order is fixed by this document (block sequence +
   row position within block) and is identical everywhere the list renders.
2. **Tier = visibility under constraint.** Surfaces that cannot show the full list
   (home fixture hooks, teaser cards) show only tier-1 rows, in the same order.
   Full pages show all rows.
3. Optional in-place progressive disclosure: tier-3 rows may collapse behind a
   "show all stats" expander, reappearing exactly where they sit in the order.
   Design call (#366), not a data rule.

**Tier applies to players too.** This supersedes the 2026-06-11 ruling below that tiers are a
team-only concept because player importance is position-dependent. CPO override, 2026-08-04: a
tier states what a FAN wants to see, which is a product judgement rather than a statistical claim,
and that judgement is as available for a player metric as for a team one.

The rubric, as his rulings established it:

- **Tier 1 is the core stat line** — the raw counts AND their headline percentage. Passes,
  accurate passes and pass accuracy are all 1; so are duels, duels won and duels won %.
- **A per-90 sits one tier below its own total.** Goals is 1, goals per 90 is 2.
- **Tier 3 is breakdowns and rare events** — penalties won, penalties committed, own goals,
  open-play/penalty goal splits.
- **Redundancy at tier 1 is deliberate.** Goals, assists and scorer points are all 1. Tier means
  importance, not deduplication.

Tier-1 selection principle for TEAM metrics, unchanged from 2026-06-11: outcomes + the
highest-signal quality metrics, and only rows with near-universal data coverage
(scoreline/team-stat derived). The "never player-stat derived" half of that principle governed
which TEAM rows qualify on a compact surface; it never barred player metrics from having tiers of
their own, and does not now.

## Composite-row patterns (ruled)

- **No naked percentage** — every % must have its volume visible nearby. Two
  mechanisms by surface: team comparisons use an **adjacent count row** in the
  same block (Ø Duels before % Duels won); player bundles use the **inline full
  triple** `{num} of {den} · {pct}%`.
- **Context pairs travel together**: a count that contextualizes a percentage
  (Ø Duels before % Duels won) shares the percentage's tier — never separated.
- **Aggregates with breakdown**: defensive actions render as one number with the
  atomic breakdown as sub-display — `26.4` + `15 T · 9 I · 3 B` (the player
  defensive-actions bundle pattern).
- **Window form display**: W1 shows the last-5 W/D/L pills (from `form_window[]`,
  recency order). W2 shows aggregate counts `10W · 3D · 1L` — pills would
  misrepresent a 14+-game window (needs GAP-10).

## Window & scope display contract (ruled 2026-06-11)

The windows themselves are settled in `docs/metrics_context_model.md` (the
context→window matrix, §1/§4). This section binds them to DISPLAY:

1. **One cross-competition number exists in the product**: W1 live form. Every
   cumulative number (W2, season rollups, profiles) is **within one
   competition**. No surface may aggregate a season across competitions.
2. **W2's user-facing name is "through matchday N"** — "season-to-date" is the
   internal mart name only. At the final matchday it equals the full season;
   aligned by matchday it powers YoY.
3. **The W1/W2 switch must declare scope per state** (the toggle changes BOTH
   window and competition scope — the labels carry that, always):
   - W1: "Last 5 · all club competitions" / national: "all national-team
     matches" + the `contributing_competitions` caption.
   - W2: "{competition} · through matchday {N}"; `prev_season` fallback →
     "{competition} · last season ({year})"; finished season → "final".
4. **Tournament exception** (matrix §4): world/continental championships use
   cumulative-within-the-tournament while running ("This tournament so far"),
   with qualifier matches as the pre-MD2 preview — never a bare "last 5"
   label. ⚠ Not yet implemented in the new window marts — **GAP-18**.
5. Sample size is always displayable (`games_in_window` / `games_played`);
   the window meta line is part of the component, not optional copy.

## Percentile display (vs-peers) — ruled 2026-07-01; median word + distributional framing confirmed 2026-07-02

How a percentile-vs-peers benchmark renders (the Player Stats screen, [12](12_player_stats.md), fed by
`mart_player_competition_benchmarks`). Distinct from the team vs-benchmark, which is **rank-based** ("k of
N" + vs-median, honest at N≈18) — never a percentile.

1. **Plain-language ladder, not "Nth percentile."** A stat reads **"top X%"** (above the median),
   **"median"** (exactly the median peer — the dashed reference line), or **"bottom X%"** (below it). Fans
   grok "top 5%"; "95th percentile" is analyst-speak. ("middle" / "more than X%" were rejected — CPO.)
2. **Median-anchored.** The reference is the **median** peer (the middle-ranked one), shown as a dashed line —
   never called "average" ("average" = mean, a different statistic, reserved for the team bars-vs-average mode).
3. **Distributional position, read with direction.** The bar's LENGTH says WHERE the value sits among
   positional peers; its COLOUR (rule 5) says whether that end is the good one. The mart `percentile` is
   direction-agnostic (by value ascending); read position = `percentile`
   for `higher_better`/`neutral`, `1 − percentile` for `lower_better` (which also mirrors the caption rank to
   `peer_count + 1 − rank`, since the mart's `rank` is value-descending; so "top"/"1st" mark the better end —
   dormant, 0 such metrics today); then `>50 → top X%`, `<50 → bottom X%`, `=50 → median` (strong extreme =
   "top 1%", never "top 0%"). Since the catalogue-wide direction sweep (2026-07-21) **all 18 benchmark metrics
   are `higher_better`** — 0 neutral and 0 lower_better remain in this set — so "top" reads as quality on every
   row. (Superseded: this rule used to split the set "11 higher_better / 7 neutral" and warn that for the
   neutral volume/style metrics "top" meant *most*, not better. Those 7 per-90 volume metrics now carry a
   direction, so the caveat no longer applies here.)
4. **Peers = position group** (GK / DEF / MID / ATT) — position-aware, set at the mart (CPO 2026-06-23).
5. **One bar, direction-aware colour** (CPO 2026-07-21, v2 design review). ONE bar language across every
   vs-population screen, player and team alike — no bespoke percentile treatment; the team benchmark screen
   ([14](14_team_stats.md)) carries the identical rule. A single-fill rank bar on a track + the median
   reference mark; the fill goes **green when the metric beats the median in its better direction**
   and stays **plain ink** otherwise. Sample (`peer_count`, `minutes`, `appearances`) is always shown.
   (Superseded: the rule used to be "no traffic lights, no colour at all", on the grounds that colour would
   wrongly imply a verdict on the neutral metrics. That rationale is VOID — after the direction sweep there
   are no neutral metrics in this set, and dropping colour entirely made the player screen inconsistent with
   the team one for no remaining reason. Were a neutral metric ever added back to this set, it renders
   uncoloured, exactly as the team rule already prescribes.)
6. **Ratio metrics keep their volume (no naked %).** The five ratio metrics (`save_pct`, `pass_accuracy_pct`,
   `finishing_efficiency`, `dribbles_success_pct`, `duels_won_pct`) render the triple `{num} of {den} ·
   {pct}%` — consistent with the player-row contract below; the wiring PR (GAP-21) carries the num/den atoms.

## Team metrics — LOCKED (CPO, 2026-06-11)

Display order top to bottom. MVP rows keep their relative order; new blocks slot
into the spine. Block order: Goals → Shooting → Duels → Defending → Passing →
Set pieces → Goalkeeping.

| # | Display label | metric_id | Group | Tier | Status |
|---|---|---|---|---|---|
| 1 | Ø Goals | `goals_per_match` | Goals | 1 | live |
| 2 | Ø Goals against | `goals_against_per_match` | Goals | 1 | live |
| 3 | Clean sheets (x/y) · % Clean sheets | `clean_sheets` (fixture windows) · `clean_sheets_pct` (team page) | Goals | 2 | **new** (GAP-11) |
| 4 | Ø Shots | `shots_per_match` | Shooting | 2 | live |
| 5 | % Shots from box | `shots_inside_box_pct` | Shooting | 2 | live |
| 6 | Ø Shots on target | `shots_on_target_per_match` | Shooting | 1 | **new** (GAP-11) |
| 7 | % Goals per shot on target | `finishing_efficiency` | Shooting | 1 | live — **relabeled** (was "% Conversion rate", GAP-11) |
| 8 | Ø Duels | `duels_per_match` | Duels | 2 | **new** (GAP-11) |
| 9 | % Duels won | `duels_won_pct` | Duels | 2 | live |
| 10 | Ø Defensive actions (`T · I · B`) | `defensive_actions_per_match` | Defending | 2 | **new aggregate** (GAP-11) |
| 11 | Ø Passes | `passes_per_match` | Passing | 3 | live |
| 12 | % Pass accuracy | `passes_accuracy_pct` | Passing | 2 | live |
| 13 | Ø Key passes | `passes_key_per_match` | Passing | 2 | live |
| 14 | Ø Corners | `corners_per_match` | Set pieces | 3 | live |
| 15 | Ø Corners against | `corners_against_per_match` | Set pieces | 3 | live |
| 16 | % Save percentage | `saves_pct` | Goalkeeping | 2 | live |

Tier shape: 4 × tier 1 (rows 1, 2, 6, 7) · 9 × tier 2 · 3 × tier 3.

### Where these strings live, and what the `metric_id` column above really holds (#370, 2026-07-31)

**The Display label column above is still the locked ENGLISH contract and is unchanged.** What moved
is where the string is stored. Until #370 the English label was hard-coded in
`site_v2/src/lib/metricRows.ts`, three more were hard-coded as `heroSot*` chrome strings, and the
German and Finnish pages showed English because the catalogue's i18n keys resolved to nothing.

Now every metric name lives once per locale in `METRIC_LABELS_{EN,DE,FI}` in
`site_v2/src/i18n/strings.ts`, keyed by the catalogue's own `label_i18n_key`, and is rendered with
`metricLabel(lang, row.labelKey)`. `metricRows.ts` keeps the order, group, tier, format and direction
contract from this document and holds no metric NAME. One string does remain there: row 10's
`sublabel`, `tackles + interceptions + blocks`, which is this table's own row-10 parenthetical. It is a
caption rather than a name, it is still English in all three locales, and that is recorded in #370's
`acceptance_evidence.md` residuals and in a comment beside the row itself. (This sentence said "in the
task contract"; `contract.md` never mentioned `sublabel` at all. `scope-auditor` caught it.) Division
of ownership:
`dbt_project/seeds/metric_catalogue.csv` owns a metric's identity, direction and format; this document
owns its order, grouping and tier; the i18n layer owns its display string per locale.

⚠ **The `metric_id` column in the table above is NOT the catalogue's `metric_id`.** It is the DISPLAY
id, which for row 6 reads `shots_on_target_per_match` while the catalogue calls that metric
`shots_on_goal_per_match` — the internal id says "on goal", the user-facing term is "on target". The
catalogue reconciles them in its `label_i18n_key` column, which for that row is
`metrics.shots_on_target_per_match.label`. This mismatch caused a real defect during #370: the key was
read as a metric id, judged dangling, and replaced with one the catalogue declares nowhere. **Resolve
a label by reading the `label_i18n_key` column; never infer it from an id or a payload field.**

⚠ **Row 3 carries TWO metric ids, and that is the contract, not a typo.** A row of this table is a
display SLOT, and this slot measures different things on the two surfaces it appears on. A fixture
window is five matches, so the honest reading is the COUNT beside its denominator — `clean_sheets`,
`3/5`. A team season is ranked against a whole league, where matches played differ between teams, so
the honest reading is the PROPORTION — `clean_sheets_pct`, `21%`, labelled `% Clean sheets` under
the same `% ` prefix every other percent metric here carries. They are two catalogue metrics with one
formula between them, and the seed carries both. In `metricRows.ts` the row's own
`field`/`labelKey`/`format` are the FIXTURE binding and the team surface reads `teamBinding(row)`;
order, group and tier are shared and unchanged, so this table still locks sixteen rows.

Row 7's "relabeled" note is also load-bearing: this document rules that v2 ships
`% Goals per shot on target`, while the retired MVP corpus (`site/i18n/*.json`) says
`% Conversion rate`. #370 kept this document's version and left the divergence for the CPO.

**German and Finnish are CPO-approved** (2026-07-31); ten are carried forward from the validated MVP
corpus and are test-pinned to it so they cannot drift.

**Long compounds in those locales do not fit the layouts this document assumes, and the fix is part of
the display contract.** `Ø Torschussdifferenz` needs 89.1px; the hero tile label box was 71px and the
Performance row's is 77px, both measured at 375px.

- `system.css` gives both `overflow-wrap: anywhere`, which stops the clipping (worst case was +53.3px).
- That alone was NOT enough: it breaks a compound at an arbitrary letter with no hyphen, and it
  rendered `Ø` / `Torschussdiffe` / `renz` plus all three Finnish hero tiles the same way. `hyphens:
  auto` is inert — the rendering engine carries no de/fi dictionary.
- **The three hero tiles therefore STACK on phones** (CPO-approved 2026-08-01, shown the rendered line
  breaks), name left and value right. The tile becomes 301px wide and the label can take ~231px of it
  (the rest is the value and the gap), against the 89.1px the longest German name needs — measured, not
  assumed, after an earlier version of this line said "the full width" and meant the tile's.
  0 mid-word breaks in all three
  locales, at a cost of 53px of block height. ⚠ He ruled "on phones"; **the 560px threshold is the
  builder's**, picked because it collides with no existing breakpoint. Disclosed here because this is
  the document a cold reader takes the display contract from.
- **The Performance rows still break mid-word** — 3 in German, 9 in Finnish — because widening that
  column costs the comparison bar 115px → 80px. Open as **#876**; this document's row order and
  grouping are unaffected either way.

Any locale that compounds (Dutch is next) inherits all of this.

**Defined but not displayed** (stay in catalogue/marts, render nowhere in the
comparison): `shots_on_goal_pct` (% shots on target — superseded by the Ø-shots vs
Ø-on-target juxtaposition), `tackles_per_match` / `interceptions_per_match` /
`blocks_per_match` (sub-display of row 10 only), `dribbles_success_pct`
(dropped team-side; stays a player metric), `points_won` + `league_rank`
(window header / standing chip, not metric rows).

### The shooting funnel (rationale, ruled with fix "a")

Volume (Ø shots) → location quality (% from box) → on-target volume (Ø shots on
target) → finishing (% goals per shot on target). The finishing metric keeps its
formula (goals ÷ shots on goal, coverage-aligned) — the old label "% Conversion
rate" was the misnomer and is replaced. Glossary carries the caveat that finishing
can exceed 100% (penalties/own goals counted as goals but not always as shots);
the true value is always shown, never capped.

## Player rows — LOCKED (CPO, 2026-06-11)

The player display unit is the **bundled row** (1–3 related atomics per row with a
defined display string) — NOT one metric per row. That part stands.

⚠ **The "no tiers" half of this ruling was overridden on 2026-08-04.** It held that tiers are a
team-only concept because player importance is position-dependent and the provider's metric scope
cannot ground a per-position importance claim. Every player metric now carries a tier in
`metric_catalogue.csv`, on the CPO's reasoning that a tier is a judgement about what a fan wants
to see rather than a statistical claim. See the tier-semantics section above for the rubric.

Per-surface rules still apply where a surface needs an ordering the tier does not give (e.g. the
fixture top-players strip ranks goals → assists → key passes, GK variant saves + save %).

Changes vs the legacy player rows (definitions / formulas now live in the
`metric_catalogue.csv` seed; windows in `docs/metrics_context_model.md`): (1) rows
resequenced into the shared block order; (2) every
bundle carries the `metric_group` it inherits from its atomics — a bundle never
mixes groups; (3) ratio displays standardized to the full triple
`{num} of {den} · {pct}%`; (4) the GK row gains the triple (two new atomics).

| # | Row | Display string | Atomics | Group |
|---|---|---|---|---|
| 1 | Scorer points | `{goals} G · {assists} A` | goals, assists | Goals |
| 2 | Shots on target | `{shots_on}` | shots_on_target | Shooting |
| 3 | Duels won | `{won} of {total} · {pct}%` | duels_won, duels_total, duels_won_pct | Duels |
| 4 | Successful dribbles | `{success} of {attempts} · {pct}%` | dribbles_success, dribbles_attempts, dribbles_success_pct | Duels |
| 5 | Tackles + Interceptions + Blocks | `{T} T · {I} I · {B} B` | tackles_total, tackles_interceptions, tackles_blocks | Defending |
| 6 | Pass accuracy | `{accurate} of {total} · {pct}%` | passes_accurate, passes_total, pass_accuracy_pct | Passing |
| 7 | Key passes | `{count}` | passes_key | Passing |
| 8 | Cards | `{Y} Y · {R} R` | cards_yellow, cards_red | Discipline |
| 9 | Save percentage | `{saves} of {faced} · {pct}%` | **saves (new)**, **shots_on_target_faced (new)**, save_pct | Goalkeeping |

- Row 9 renders only for `position_code = 'G'`; whether a GK profile pulls the
  Goalkeeping block forward is a design call (#366).
- The **zero-denominator rule** is unchanged and now self-explanatory:
  `0 of 0 · —`.
- Atomics not in a bundle (offsides, dribbled past, penalties won/committed,
  goals conceded) stay defined in the catalogue but unrendered — same status as
  team `shots_on_goal_pct`.

## Data work implied (see 99_gaps_register.md)

- **GAP-09** — catalogue columns: `metric_group` (all atomics, team + player),
  `importance_tier` (**team-only** — null for player entries),
  `group_display_order` (this document is the source for the values).
- **GAP-10** — `wins`/`draws`/`losses` columns in `mart_team_season_record`
  (the W2 counts display).
- **GAP-11** — new team metrics (`clean_sheets` in both window marts,
  `duels_per_match`, `defensive_actions_per_match`, `shots_on_target_per_match`),
  the finishing relabel, catalogue description tightenings (coverage denominators,
  blocked-shots note, >100% finishing caveat).
- **GAP-12** — player additions: `saves` + `shots_on_target_faced` atomics (data
  exists as `goals_saves`/`goals_conceded`), display strings standardized to the
  full triple (duels, pass accuracy, saves), the legacy player display table
  superseded by this document.
- **GAP-13** — full-season variants of the five player-stat-derived team rows
  (shots on target, duels pair, defensive actions, key passes) in the season
  rollup + `mart_team_profile` (the team profile renders the same locked table).

## Rulings log

| Date | Ruling |
|---|---|
| 2026-06-11 | Groups = MVP blocks; MVP row order untouched; new metrics slot into blocks. |
| 2026-06-11 | Duels + Defending blocks placed before Passing. |
| 2026-06-11 | Clean sheets added (new metric); team dribbles dropped; T·I·B aggregated. |
| 2026-06-11 | Ø Duels added as context row before % Duels won; context pairs share a tier. |
| 2026-06-11 | Shooting block reshaped: Ø shots, % from box, Ø shots on target (new), finishing; `shots_on_goal_pct` unrendered; finishing relabeled (fix "a"). |
| 2026-06-11 | Tier 1 = goals, goals against, shots on target, finishing. Duels stay tier 2 (coverage + discrimination + compact-surface budget). |
| 2026-06-11 | W1 = form pills; W2 = W/D/L counts (GAP-10). |
| 2026-06-11 | Player display unit = the bundled rows (legacy player catalogue); resequenced into shared block order; groups inherited from atomics (no mixed bundles). |
| 2026-06-11 | **No tiers for players** — position-dependent importance can't be grounded in the provider's metric scope; compact surfaces use per-surface rules. |
| 2026-06-11 | No naked percentage: player ratio rows standardized to `{num} of {den} · {pct}%`; GK row gains the triple (`saves`, `shots_on_target_faced` atomics). Team comparisons keep single % values — adjacent count rows provide the volume. |
| 2026-06-11 | W2's user-facing name = "through matchday N" (mart name stays internal); the W1/W2 toggle states carry explicit scope labels (cross-comp vs within-comp) per the context matrix. |
| 2026-06-11 | Tournament window exception (cumulative + qualifier preview) confirmed as the matrix rule for display; found unimplemented in the new window marts → GAP-18, scheduled before WC 2026. |
