# Claude orientation — football-data-pipeline

Read this at the start of every session before doing anything else.

## Working agreement

**Read [`docs/working_agreement.md`](docs/working_agreement.md) before doing anything.** It defines what you are and are not allowed to do, quality standards, branch discipline, layer rules, and communication style. Non-negotiable.

## North star

**Read [`docs/north_star.md`](docs/north_star.md) first.** It defines the product vision, the user, the navigation flow, what makes it sticky, and the roles. Everything else flows from there.

## What this project is

A football data pipeline: Python ingestion from API-Football → BigQuery raw → dbt staging/base/core/marts → GitHub Pages match preview UI.

Current live competition: **German Bundesliga (BL1, API league id 78)**. `BL1` is the internal `league_code`; `D1` is the raw table prefix only (`RAW_D1_APIF_*`).
Roadmap: **WC 2026** (+ qualifiers as form fallback) → Premier League, La Liga, Serie A.

## Authoritative docs — read before making decisions

| Topic | File |
|-------|------|
| Project vision, UI, multi-competition roadmap | Claude memory files (see below) + this file |
| Agent role briefs | [docs/roles/](docs/roles/) — one file per role |
| Data contract (raw landing, merge model, endpoints) | [docs/data_contract.md](docs/data_contract.md) |
| dbt layer rules (what belongs where) | [dbt_project/docs/layering.md](dbt_project/docs/layering.md) |
| Engineering standards (naming, testing policy) | [dbt_project/docs/engineering_standards.md](dbt_project/docs/engineering_standards.md) |
| Operations runbook (env vars, ingest lock, backfill) | [docs/operations_guide.md](docs/operations_guide.md) |
| Development workflow (local validation, secrets) | [docs/development_workflow.md](docs/development_workflow.md) |
| GitHub Pages match preview plan | `C:\Users\Rami\.cursor\plans\gh_pages_match_preview_bce3ad94.plan.md` |

## Architecture decisions (non-negotiable)

- **Layer contract**: staging = raw cleanup only; base = UNION ALL + dedup + first logic; core = facts/dims; marts = consumption.
- **league_code** is the partition key on every model — never hardcode a competition identifier in business logic.
- **Form window**: last 5 matches, current season only. Before matchday 1 → fallback to qualifiers (for tournaments) or previous season (for leagues). Never mix seasons.
- **Data quality is non-negotiable** — the user cannot manually verify numbers. Automated DQ tests are a hard requirement.
- **UI flow**: Landing (competition cards) → Fixture list (next round only) → Fixture detail (carousel/deep dive).
- **History window is per-source** — how many seasons/years to backfill is a CPO decision made at onboarding time, stored in the registry. No global defaults.

## Memory files

Claude memory for this project lives at:
`C:\Users\Rami\.claude\projects\D--Projects-football-data-pipeline\memory\`

Read `MEMORY.md` there for the index. Key files:
- `project_vision.md` — product goals, UI, multi-competition roadmap
- `project_architecture.md` — layer design, CI order, form logic
- `feedback_engineering.md` — engineering principles and past corrections
- `user_profile.md` — who Rami is and how he works

## Cursor integration

This project uses Claude Code and Cursor interchangeably. Both tools follow the same rules. Cursor-facing rules live in `.cursor/rules/` and mirror `docs/working_agreement.md`. If you find a conflict between this file and a Cursor rule, `docs/working_agreement.md` is the authoritative source.

## Stack

- Python 3.11 ingestion (`ingestion/api_football/`)
- BigQuery (GCP project `football-data-pipeline-gcp`)
- dbt (project in `dbt_project/`)
- SQLFluff for SQL linting
- GitHub Actions for CI (`dbt-ci.yml`) and scheduled runs (`dbt-scheduled.yml`)
- GitHub Pages for the match preview UI (`pages-match-preview.yml`)
