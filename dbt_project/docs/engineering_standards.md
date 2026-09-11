# dbt Engineering Standards

This document defines practical standards for analytics engineering in this project.
Use it together with [`layering.md`](layering.md) (BigQuery dataset layout and layer rules).

## 0) Warehouse layout

- **Raw landing** lives in the BigQuery dataset named by dbt **`raw_schema`** (default `raw`). Ingestion must use the **same** dataset id (`API_FOOTBALL_BIGQUERY_DATASET` for API-Football).
- **Additional vendors:** prefer new `RAW_<VENDOR>_…` tables in the **same** `raw` dataset and a new folder `models/1_staging/<vendor>/` unless IAM forces a separate `raw_<vendor>` dataset.

## 1) Naming Conventions

- Model names use lowercase snake_case.
- Prefix by layer intent:
  - staging: `stg_<source>__<entity>`
  - base: `base_<domain>__<entity>`
  - core: `core_<entity>`
  - intermediate: `int_<domain>__<purpose>` — use **`int_matchday__*`** for matchday preview / form / fixture denorm spine, **`int_team_season__*`** for per-team-season preparation (e.g. standings dedupe), **`int_pipeline__*`** for ingestion or warehouse-operation helpers (for example raw load-time spread). Intermediate must not `ref()` any `mart_*` model.
  - marts: `mart_<consumer_or_domain>__<purpose>`
- Columns use lowercase snake_case.
- Boolean columns start with `is_` or `has_`.
- Timestamp columns end with `_at`, dates end with `_date`.

## 1.1) SQL Structure and Readability

- Every model starts with explicit import CTEs for each `ref()` / `source()` relation before transformation logic.
- Prefer named CTE chains over inline subqueries. Avoid `from ( ... )` when the same logic can be expressed as a named CTE.
- Keep each CTE single-purpose (import, explode/flatten, dedupe/rank, final projection) and use stable, descriptive CTE names.
- For BigQuery array expansion, prefer explicit `cross join unnest(...)` style over implicit comma joins where practical.

## 1.2) Code Comments (every language in the repo — Python, SQL, Astro, TypeScript, YAML)

Comments exist to convey **why**, not **what**. Well-named identifiers, CTEs, and functions already describe what the code does. A comment is warranted when the reader would otherwise be left wondering why a decision was made, what constraint is being respected, or what non-obvious behaviour to expect.

**Write a comment when:**
- A design decision has a non-obvious reason (e.g. why a coverage flag is overridden for finished fixtures)
- An invariant must hold for downstream code to be correct
- A workaround exists for a specific API quirk or external constraint
- The behaviour would surprise a competent reader unfamiliar with this domain

**Do not write a comment when:**
- The code already reads clearly from its identifiers and structure
- You would only be paraphrasing what the next line does
- The context is already captured in the PR description or a linked ticket

**Module / file level:** Every Python module and every dbt model should open with a one-sentence docstring or comment stating its purpose and its place in the pipeline (e.g. "Fetches qualifier fixtures per supporting league and merges into a single BQ payload."). This is the first thing a new engineer reads.

**Function / CTE level:** A short docstring on non-trivial functions. For SQL, a one-line comment before each CTE when its purpose is not obvious from its name.

**Inline:** Reserve for genuinely surprising logic. One line is almost always enough. Avoid multi-line comment blocks.

**Standard applied consistently across every language.** A senior engineer reading any file in this repo should be able to orient themselves within 30 seconds.

### Reasoning lives in git, not in the comment

A comment says **why**, in one line. **Who decided, when, which reviewer, which round, which MR or
issue — never in code.** That is history, and it has a home that survives the task without living
next to the line: the **commit message** carries the why and `Closes #N`; the **MR** carries the
review record (its head and its fold); the **issue** carries the exploration (its fold). Any line
reaches all three:

```bash
c=$(git blame -L 36,36 --porcelain CLAUDE.md | head -1 | cut -d' ' -f1)   # → the commit
git log -1 --format=%B "$c"                                               # → the why, "Closes #N"
git log --merges --ancestry-path --first-parent --reverse --format=%B "$c..gitlab/main" \
  | grep -m1 "See merge request"                                          # → "…!N", the MR
```

Run on 2026-09-11 against `CLAUDE.md` line 36: commit `82ddb9c5`, "Closes #117", "See merge
request rami.al-fahham/football-data-pipeline!175".

GitLab shows the MR for any commit directly. So a comment that reads "CPO ruled 2026-06-23",
"(cto-reviewer, round 3)" or "see !132" is a defect in three ways: it is not the why, it rots (the
GitHub-era numbers in this repo already point at nothing), and it argues with a reviewer in a place
the next reader has to carry forever. **Argue with a reviewer in the contract's `amendments`**,
which reviewers read and which the MR carries; it is the review's record, not the code's.

Why this section exists: the rule above it was ignored. On 2026-09-11 the code held **429**
comment lines carrying a date, "CPO", "reviewer" or "round N" (tests 99, `site_v2/src` 88, dbt
models 78, hooks 48, `scripts` 46, `ingestion` 35, dbt tests 19, `site_v2/scripts` 16 — the grep is
`(#|--|//|\*).*(20\d\d-\d\d-\d\d|CPO|reviewer|round \d)`). That number is the starting point of the
ratchet #115 step 8 adds as a hook; until then this paragraph is the rule and the count is the
measure.

## 1.3) Macros

Not a rulebook — a calibrated default. This project's habit has been reaching for a Jinja macro where plain SQL or a model would read better, so: **default to plain SQL.** A macro hides the real logic from the source files and surfaces errors in generated SQL, so it carries a readability/debuggability cost — spend it only when the macro buys something plain SQL or a model cannot.

**The trap we keep hitting — a shared list or formula held in a macro.** Build it once as a model (usually an `int_*`) and let the others read or aggregate it instead — the COMPOSE pattern (see §5). Same single source, no generated SQL.

**Where a macro genuinely earns it:**

- a dbt **override hook** (e.g. `generate_schema_name`, whose default would name datasets wrong);
- an **expression that must sit inside other queries** and would otherwise be copied across files (e.g. expanding a raw JSON payload inside the `from`/`unnest` of several staging models).

Beyond those there is no formula: an experienced analytics engineer weighs the readability cost against what the macro saves, and judges. This records the default and the trap — not a decision procedure.

## 2) Documentation Policy

### Who a description is for

**Someone about to use the data, who has never seen our code.** Not a reader tracking how we got
here. dbt states the same audience: *"Good documentation for your dbt models will help downstream
consumers discover and understand the datasets you curate for them."*
([dbt](https://docs.getdbt.com/docs/build/documentation))

The test for any description: **could a stranger querying this table in BigQuery use it correctly
from this text alone?**

### Coverage

- Every model must have a `description`.
- Business-facing columns in `core`, `intermediate`, and `marts` must have `description`.
- Every source table must have a short source description in `sources.yml`.
- Where coverage is partial, do marts and primary keys first — they are what a consumer touches.

### What a description contains

- **Business meaning**, in plain language.
- **Grain** — one row per what. Required on staging models by §3; expected on every model.
- **Where it comes from / how it is calculated** — the upstream input or the formula.
- **Known limits** — what NULL means, what is excluded, edge cases that will surprise someone.

### What a description must never contain

Two bans. Both come from real defects in this repo, not from theory.

**1. No downstream consumer claims.** Never write "the only reader is X", "no model reads this",
"its single consumer is Y", or a list of what depends on this. Upstream facts are fixed in the SQL
and change when the SQL changes; downstream facts change whenever anyone adds a model, and nobody
comes back to update the prose. Three descriptions carried false consumer claims simultaneously in
August 2026, and one of them stated that a column had no readers while a live mart filtered on it —
following it would have broken the competitions page. **dbt already computes this, correctly, on
demand: `dbt ls --select <model>+`.**

**2. No history.** No dates, no rulings, no issue or MR numbers, no "UPDATED", no "an earlier
version of this said X". Git holds all of it losslessly and cannot rot; a hand-copied version of it
starts rotting immediately. Rulings belong in `.claude/task/escalations.log`, open questions in the
tracker, design rationale in `layering.md`.

### Form

- Long text belongs in a **docs block**, not inline YAML — `{% docs name %}` in a `.md` file,
  referenced as `description: "{{ doc('name') }}"`. dbt: *"If you have a long description,
  especially if it contains markdown, it may make more sense to leverage a docs block."*
  ([dbt](https://docs.getdbt.com/reference/resource-properties/description))
- A column documented in more than one model gets **one** docs block, referenced from each. Do not
  restate it — restated definitions drift apart, which is how `league_code` came to be documented
  76 times in 22 different wordings.
- Keep YAML lines to **80 characters**
  ([dbt](https://docs.getdbt.com/best-practices/how-we-style/5-how-we-style-our-yaml)).
- Length is capped at BigQuery's own maxima — **1,024 for a column**, **16,384 for a model or
  seed** — measured on the RENDERED text and enforced by
  `scripts/check_description_hygiene.py`. That cap exists to stop `persist_docs` failing the
  build. It is not a brevity rule: **write less because nobody reads more, not because a number
  says so.**
- A docs block is **not** a length exemption: `persist_docs` renders the block into the description
  pushed to the warehouse, so the limit applies to the RESOLVED string — block plus qualifier, not
  what is written in the YAML.
- **A metric's definition is GENERATED, never written by hand.** The blocks in
  `models/docs/metric_columns.md` are produced from `seeds/metric_catalogue.csv`, which is already
  this project's only source of what a metric means. To change one, edit the seed's `description`
  and run `python scripts/sync_metric_docs_blocks.py`; `--check` fails on drift. Writing the
  definition into a model's YAML instead creates a second source, which is the drift this section
  exists to prevent — and the generated file is overwritten on the next run, so the edit is lost
  as well as wrong.
- **Where one name carries two meanings, there are two blocks and no default.** A metric defined
  differently for a team and a player gets `__team` and `__player` blocks, because a single block
  would be wrong at half its call sites. The generator refuses to pick a winner, and
  `check_description_hygiene.py` then stops policing that name and says so on every run rather than
  demanding a guess. Point each column at the meaning it actually carries. `league_code` is the
  worked example of getting this wrong: six columns were wired to the wrong one of its two
  meanings, found across three review rounds.

### Who reads these

Three consumers, all live. This is the part that used to be missing: for most of the project's life
nothing read a `description:` at all, which is why the field drifted into a decision log. A rule
about writing for a reader is unenforceable when there is no reader.

- **BigQuery itself.** `persist_docs` is on for every model and every seed, so a description is
  attached to the table and the column it describes. `bq show --schema <dataset>.<table>` prints it,
  and the console and any BI tool show it beside the data.
- **The dbt docs page.** `data:build:main` runs `dbt docs generate --static` after each merge to
  main and publishes `static_index.html` as a job artifact. Descriptions, lineage and column lists
  in one self-contained file.
- **`target/catalog.json`**, produced by the same step. It is the only place the warehouse's actual
  columns can be compared against what the `.yml` files declare.

The practical consequence when writing: assume a stranger reads your sentence in the BigQuery
console with none of this repo's context around it. That is now literally what happens.

### Worked example

Before — 1,080 characters, and the load-bearing sentence is false:

> Hybrid-IA nav group for this competition type (GAP-19 — the taxonomy that previously lived as the
> _GROUP_OF_TYPE dict in scripts/export_site_data.py). Empty (null) for types that never appear in
> the nav (friendlies). ⚠ SLATED FOR DELETION (CPO 2026-08-11, #57): … No dbt model reads it — all
> 35 downstream of this seed read entity_type only — so its single consumer is build_nav() … ⚠
> UPDATED 2026-08-19: …

After:

> Which navigation group a competition of this type belongs to: leagues, cups, continental-club or
> national-teams.
>
> Blank means the type is not browsable. Competitions of a blank type are excluded from
> mart_competition_index, and so from the competitions page. Only the friendly types are blank
> today, and no active competition uses one, so the exclusion currently removes no rows.

What changed: the deletion proposal moved to the tracker, the ruling and the dates to
`escalations.log`, the false consumer claim was deleted outright, and what remains is the one thing
a consumer needs — what the values mean and what blank does.

## 3) Testing Policy

**Hard rule: every model must have at least one schema test. A PR that adds or modifies a model without tests will not be merged.**

Per-layer minimums:

- `staging`: document the **grain** (one row per what) in the model `description`. Then:
  - `not_null` on every column required for that row to be valid (ids, dates, join keys).
  - `unique` or `dbt_utils.unique_combination_of_columns` on the column(s) that define the grain, so dupes and bad merges fail early. Use `severity: warn` (not error) only when the violation is a known, documented source data quality issue that cannot be corrected at this layer.
  - Constrained `accepted_values` (and other light tests) where they add signal.
  - Do **not** repeat the **same** uniqueness assertion downstream unless the **grain changes** (avoid redundant tests on the same keys in `base` / later layers).
- `base`: structural integrity when unions or reshaping apply—stronger `not_null`, key quality, `relationships`, and `unique` / composite tests where the grain is new or combined across sources (not a copy of staging’s uniqueness if nothing changed).
- `core`/`intermediate`: relationship and business-rule tests.
- `marts`: consumer-contract tests (required columns, accepted value ranges, metric consistency).

**Severity guideline:**

| Situation | Severity |
|---|---|
| Pipeline logic error (duplicate rows from ingest, bad join) | `error` — must fix before merge |
| Grain violation from source data quality issue (documented API bug, known ID collision) | `warn` — document the root cause in a YAML comment |
| "Nice to have" coverage on non-critical fields | `warn` |

## 4) Model Contracts and Metadata

- Use model contracts for stable `marts` outputs once schemas stabilize.
- Add `meta` fields for ownership:
  - `owner`
  - `domain`
  - `criticality` (`low|medium|high`)
- Use `tags` consistently (for example `daily`, `pre_match`, `api`).

## 5) Performance Standards (BigQuery)

- **Materialisation is a LAYER decision, never a per-model one.** It is set once in
  `dbt_project.yml` and enforced by `scripts/check_layer_contract.py`; a per-model
  `config(materialized=...)` is rejected in `1_staging` and `2_base` whatever its value.
- `staging` and `base` are **tables** (#547, and #33 items 9/10). "Prefer views for lightweight
  staging" was the rule here until 2026-08-12 and it was wrong for a measurable reason: a view
  stores nothing, so every test on it re-executes the parse of the raw JSON underneath. Testing
  cost more than building. See `dbt_project/docs/layering.md` §1_staging.
- Use tables for heavy transforms in `intermediate` and high-query `marts`.
- For large tables, apply partitioning and clustering (typically on date/time and league/team keys).
- Avoid repeated expensive expressions across layers; centralize once in `intermediate` if reused.

## 6) Environment and Promotion

- Keep `profiles.yml` out of git (already required in this repo).
- Use separate datasets/targets for `dev` and `prod`.
- Validate in `dev` before promotion.
- Do not introduce breaking mart schema changes without a migration plan.

## 7) CI/CD Minimum Gate

Every PR should pass:

1. `dbt deps --project-dir .\dbt_project`
2. `dbt parse --project-dir .\dbt_project`
3. `dbt build --project-dir .\dbt_project --selector staging`
4. `dbt build --project-dir .\dbt_project --selector base`

Before release to prod:

5. `dbt build --project-dir .\dbt_project`

## 8) Change Management

- Prefer additive changes over destructive renames/drops.
- If output schema must change, document:
  - what changes
  - why it changes
  - migration impact for downstream consumers
- Keep marts stable as product/API contracts.

## 9) Data Freshness and SLAs

- Define expected refresh cadence per source (for example daily pre-match refresh).
- Add source freshness checks when reliable load timestamps are available.
- Fail pipelines on stale critical sources once freshness is implemented.

## 10) Security and Secrets

- Never commit API keys, service account files, or secret env values.
- Use environment variables for external API authentication.
- Keep service roles least-privileged where possible.

## 11) GitHub Pages export contract

- **Source of league list:** `vars.active_competition_league_codes` in `dbt_project.yml`, domestic subset only (exclude `WC` and `WCQ*`).
- **Warehouse:** One `mart_matchday_insights` for all domestic leagues (`league_code` on every row); `mart_matchday_insights_bl1_relegation` only for BL1 play-offs; `mart_matchday_insights_wc` for WC fixture previews; one `mart_team_season_insights` table for all leagues. Do not add per-league filter views or codegen copies in `5_marts`.
- **Play-off windows:** Exclude play-off `round_name` values from the unified mart via dbt vars (`bl1_relegation_round_names`, `bl2_playoff_round_names`, `l1_relegation_round_names`). BL1 relegation legs use the dedicated mart + export fallback; BL2 promotion legs appear on the BL1 relegation path only. Policy and CPO checklist: [`docs/playoff_window_policy.md`](../../docs/playoff_window_policy.md).
- **Exporter:** `scripts/export_pages_data.py` queries unified marts with `WHERE league_code = @code`, writes `artifacts/data/{league_lower}/…`, and `artifacts/pages_export_manifest.json`. BL1 matchday falls back to the relegation mart when the domestic slice is empty. Each domestic entry includes `matchday_row_count`, `team_season_row_count`, and `matchday_source_mart` (warehouse table name used for matchday JSON).
- **UI routing vs labeling:** Landing phase is derived from manifest row counts (`matchday_row_count > 0` → fixture-list; else recap). `matchday_source_mart` drives relegation copy only (e.g. suffix when the source mart name contains `relegation`). Never hardcode per-league phase overrides in the UI for play-offs.
- **Site layout:** `_site/data/{league}/` plus manifest at `_site/pages_export_manifest.json`; `match-preview/matchday_insights.json` is optional BL1 compat copy until the UI reads the manifest.
