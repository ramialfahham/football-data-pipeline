# Acceptance evidence — step 4, MR 2: the five player `discipline` metrics

Branch `refactor/metric-rename-player-discipline`, from main `3e5b25b`.

    cards_yellow       →  cards_yellow_player
    cards_red          →  cards_red_player
    cards_total        →  cards_player
    offsides           →  offsides_player
    penalty_committed  →  penalty_committed_player        (PLAYER entity only)

Every gate below was run **unpiped, with its exit code read bare**. No gate output was passed
through `head` or `tail`, and no closing banner was read as a verdict — `sqlfluff` prints
"All Finished!" on failure too.

criteria_demonstrated:
  - **Criterion 1 — no rendered name changed its words.** The site was built TWICE — once from the base content (stashed by explicit path) and once from the branch — and both were measured structurally from the markup, one `<div class="mrow">` per row and one `<div class="mgroup">` per heading, never by substring. Result: **12 metric rows and 7 group headings per comparison block in EN, DE and FI**, across **19 fixture pages** of a 66-page build; distinct-label sets equal element-for-element, **REMOVED none / ADDED none** in every locale. ⚠ This confirms a stated prediction; on its own it is NOT proof the rename happened — "no change" is also what doing nothing produces, the check the CPO rejected on `!114`. Criteria 2 and 4 are what prove the work.
  - **Criterion 2 — old names gone from every surface that moved, and nothing half-renamed.** Whole-token `git grep` over `site_v2/src` excluding `src/data`: **0 files**, before and after. The new names are present in **22** files (`cards_yellow_player`, `cards_red_player`), **18** (`offsides_player`, `penalty_committed_player`) and **9** (`cards_player`). Every one of the **48** yml column entries naming an old or new name was checked against its own model's `.sql`, both directions — all 48 resolve. The **16** surviving old names sit in exactly three partially-moving models, in the counts the classifier printed (8 / 4 / 4), and every one is an upstream READ of a provider relation.
  - **Criterion 3 — two guards passed AND each watched going RED.** `sync_metric_docs_blocks.py --check` (exit 0, 173 blocks) broken by mutating the seed's `offsides_player` `metric_id` → **RED, exit 1** ("missing block: offsides_player_MUTANT / block no longer in the seed: offsides_player"). `check_description_hygiene.py` (exit 0) broken by pointing `mart_leaderboards.cards_player` at a non-existent block → **RED, exit 1** ("unresolved docs block: 'cards_player_DANGLING'"). Both reverted, both green again, file count unchanged at 24.
  - ⭐ **Criterion 4 — every column reference resolves against the relation it reads.** The static resolver follows sources through CTE chains for **both dotted and bare** references: **42 references checked, 0 broken**, 2 unresolved and REPORTED (both in `mart_player_match_log.sql`, a provider surface this MR does not touch). Watched going RED **three times before it was trusted** — see below.

## Criterion 4 in full: the resolver was proven on BOTH shapes, and on the post-rename tree

A check that passes equally on the work and on its absence is not a check. So the resolver was
broken deliberately three times and each red was read for its diagnosis, not just its exit code:

| # | when | the break | what it said | exit |
|---|---|---|---|---|
| 1 | on the BASE tree, before applying | `mart_player_profile.sql:158` → `a.offsides_player` | "reads a.offsides_player where a = int_player_season__metrics, which does not emit 'offsides_player'" | 1 |
| 2 | on the BASE tree, before applying | `int_player_season__metrics.sql:58` → `sum(offsides_player)` | "bare read of 'offsides_player' inside CTE 'aggregated' whose source is int_player_club_season__metrics, which does not emit it" | 1 |
| 3 | on the POST-RENAME tree | `int_player_season__metrics.sql:58` reverted to `sum(offsides)` — an exact reproduction of the `!125` round-2 defect | "bare read of 'offsides' inside CTE 'aggregated' whose source is int_player_club_season__metrics, which does not emit it" | 1 |

Break 3 matters most: it is the defect that failed `!125` round 2, reproduced in THIS batch's own
code, and the resolver names the line and the reason. All three restored, all green.

⚠ **Two limits, stated rather than implied.** It can only check relations whose ymls declare their
columns (4_intermediate and 5_marts do; 1_staging / 2_base / 3_core under-declare), so the two
protected inner reads whose source is `fct_fixture_player_stats` are outside its reach — those rest
on the classifier's printed decision and on review. And it does not cover the prose or seed
surfaces, which have their own rules. `data:build:mr` remains the authority.

## The classification, printed in full before anything was written

216 tokens in sweep across 24 files, each decided once and its reason printed, grouped by
`(old, new)` pair so a protected first occurrence cannot hide real renames behind "(unchanged)":

    169 renamed  ·  47 protected  ·  1,039 tokens repo-wide
      785  untouched  (site_v2/src/data/**, .claude/**, site/**, docs/audits/**, metric_columns.md)
       38  provider .sql, excluded outright by the CPO's "yes" (9 files, none opened)

The 47 protected, by reason: 16 yml column entries on provider-surface models · 8 inner reads of a
self-aliasing aggregate over a provider relation · 8 dotted reads of a provider relation · 7 seed
reference fields · 5 prose/doc-file identifiers · 3 prose lines documenting a provider surface.

⭐ **The batch's defining hazard, and the classifier prints both answers side by side:** three
identically-shaped `sum(X) … as X` sites, two of which protect the inner read and one of which moves
it. The resulting code shows the difference plainly —

    int_player_club_season__metrics.sql:135   sum(coalesce(offsides, 0)) as offsides_player
    int_player_season_record.sql:63           sum(offsides) over w as offsides_player
    int_player_season__metrics.sql:58         sum(offsides_player) as offsides_player

## Gates, each unpiped with its exit code read bare

  - `python scripts/sync_metric_docs_blocks.py --check` → **0**. "173 metric docs blocks match" — 173 before and after, five blocks renamed in place, no orphan created and none lost.
  - `python scripts/check_description_hygiene.py` → **0**. **1604 descriptions**, 235 docs blocks resolved — *identical to the base*. That number is the CPO's "re-point them" ruling measured: blanking the 48 borrowed references instead would have given 1592.
  - `python scripts/check_layer_contract.py` → **0**.
  - `python scripts/check_ui_i18n_metrics.py` → **0**. 13 shown metrics resolve in 3 files; unaffected, because it reads the frozen `site/match-preview/` tree, which contains none of the five.
  - `dbt parse` (`.venv/Scripts/dbt.exe`, `DBT_PROFILES_DIR=C:/Users/Rami/.dbt`) → **0**, zero dangling `doc()`.
  - `python -m sqlfluff lint <the 8 changed models> --templater jinja --dialect bigquery` → **1**, and **proved pre-existing**: the same eight files were stashed by explicit path, re-linted at base content, and the two outputs are **BYTE-IDENTICAL**. **Zero LT05** on both sides. Every finding is the known `dbt_utils`-unresolvable TMP/PRS noise and the ST11 cascade behind it, which `CLAUDE.md` documents.
  - `python -m pytest -q` → **0**: **1009 passed, 1 skipped, 14 subtests** — the `3e5b25b` baseline, measured on the clean tree before any edit.
  - `npm test` (site_v2) → **0**: **76/76**.
  - `npm run build` → **0** on both base and branch: 66 pages, 57 fixture pages, `audit-seo` OK.

## #96 — all six `accepted_values` metric-key lists read by eye

No offline gate enforces these; six consecutive reproductions. Exactly one changes:

| list | names | changed? |
|---|---|---|
| `int_competition_benchmarks.yml:27` | 22 team | no |
| `int_competition_benchmarks.yml:66` | 22 team | no |
| `int_competition_benchmarks.yml:105` | 18 player benchmark | no |
| `shared.yml:2080` | 22 team | no |
| `shared.yml:2186` | 18 player benchmark | no |
| ⭐ `shared.yml:1756` | 14 leaderboard board keys | **yes — `cards_total` → `cards_player`** |

And the board key was checked for **three-way agreement**, mechanically, not by eye alone: the set
`mart_leaderboards.sql` emits, the `accepted_values` list, and the export's `_LEADERBOARD_METRICS`
all carry `cards_player`, none carries `cards_total`, and the emitted set equals the accepted set
exactly.

## The built-page prediction, made before any code — and it is not `!125`'s

`!125` could say its names never reached the payload. **Four of these five do.** The committed
fixture sample carries `offsides`, `penalty_committed`, `cards_yellow` and `cards_red` under
`top_players[]`, ten per fixture across 19 files, and that payload is built from
**`mart_player_momentum`** (`export_site_data.py:871`) — a player METRIC mart this MR renames — not
from `mart_player_fixture_stats`. `shape_top_players` filters with a DROP list naming none of the
five, so a renamed mart column flows straight into a payload key.

Predicted, then measured:

  - **The built pages do not change.** `site_v2/src/data/**` is the declared transient and is not swept, and no `.astro` / `.ts` / spec file references any of the five. Confirmed by the two-build comparison above, and more sharply: **whole-token grep over `site_v2/dist` finds all five names in ZERO built files** — Astro renders server-side, so the payload keys never reach the HTML at all.
  - **At the sample roll-forward those four payload keys change** to their `_player` forms. Nothing reads them, so nothing breaks. Declared here rather than discovered later.
  - `cards_player` reaches only the leaderboards payload, which is not committed under `site_v2/src/data/` and has no page today.

⭐ Because the payload's SOURCE renames, **`01_fixture_page.md:198-199` renames with it** — the prose
documenting that payload is a reference, and a reference follows its source. `!125` classified the
same file as team-side prose to protect and was right to: its only stem there was the TEAM
`shots_on_goal_pct` at line 151. Same file, different source, different answer.

## Three prose judgement calls, declared rather than buried

Each was printed by the classifier with its reason, and each is a one-line change if a reviewer
reads it the other way:

  - **`03_player_profile.md:119` does not move; `:100` and `:106` do.** Line 119 is a row of the MATCH LOG table, whose payload is `mart_player_match_log` — excluded by the "yes" ruling; its neighbours in that same table are `goals_total`, `goals_saves`, `minutes_played`, `is_substitute`. Lines 100 and 106 are the season-stats bundle and its unrendered atomics, a different surface nineteen lines above. ⚠ This is the same class as the prose defect `bi-analyst-reviewer` FAILed `!125` round 2 on, in the same file; it is keyed on LINE CONTENT, not a line number, so it cannot decay.
  - **`metrics_display.md:271` and `docs/ui_design_brief.md:98,166` do not move.** All three are English prose, not key lists — their siblings are deliberately non-identifiers ("dribbled past", "penalties won/committed", "goals conceded", "cards (Y/R)"). Renaming `offsides` alone would leave it the only identifier in a prose list. `metrics_display.md:264`, the metric-row contract's Atomics column, DOES move.
  - **`assert_metric_direction_lower_is_better_agree.sql:9` does not move.** Its `{# #}` comment records a DATED fact about the catalogue as it stood on 2026-07-21. Dated log → append, never rewrite. ⚠ The counter-argument is recorded rather than hidden: a reader grepping the live seed for `cards_yellow` will not find it.

⚠ `docs/ui_design_brief.md` is NEW to this sweep and was found by the classifier **aborting** on it,
not by a search — the abort-on-unlisted rule is why an ordinary English word colliding with a metric
id could not be swept silently.

## A verification bug of my own, recorded because the class matters

The post-transform verifier's "no half-rename" check first passed `HEAD` to `git grep`, so it read
the **committed base** instead of the working tree and reported 107 unexplained survivals on work
that was correct. It failed loudly rather than passing, which is the only reason it was harmless.
⭐ The rule it re-teaches: **name the tree a check reads.** A check pointed at the wrong tree gives
an answer that has nothing to do with the work — the same family as the vacuous `sed` intersection
and the empty flagged-file list already in the record.

Its second form asked a whole-file question of three models that PARTLY move, where a provider read
and a metric write sit on the same line. Replaced with an exact count per file (8 / 4 / 4), so a
read that wrongly moved — or a write that wrongly did not — changes the number.
