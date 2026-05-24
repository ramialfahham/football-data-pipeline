# Claude orientation — football-data-pipeline

Read this at the start of every session before doing anything else.

## Session start — branch hygiene (do this first, every session)

1. Run `git branch --show-current` via **PowerShell** to confirm the active branch.
2. If the branch doesn't match the task, switch now **before writing any files**: `git checkout <target-branch>` or `git checkout -b <new-branch>`.
3. **Never use the Bash tool for git commands on this repo** — use PowerShell only. Bash and PowerShell run in separate processes and see different working-directory state, causing branch confusion.
4. If unsure which branch to use, ask the user before touching any file.

## Working agreement

**Read [`docs/working_agreement.md`](docs/working_agreement.md) before doing anything.** It defines what you are and are not allowed to do, quality standards, branch discipline, layer rules, and communication style. Non-negotiable.

## North star

**Read [`docs/north_star.md`](docs/north_star.md) first.** It defines the product vision, the user, the navigation flow, what makes it sticky, and the roles. Everything else flows from there.

## What this project is

A football data pipeline: Python ingestion from API-Football → BigQuery raw → dbt staging/base/core/marts → GitHub Pages match preview UI.

Active competitions (see `docs/competition_registry.yml` for full list): BL1, BL2, PL, PD, SA, L1, VL, WC (2026), WCQ*, LMX, LP, MLS, SPL, ED.
Next: player insights chain (#153 → #156).

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
- **Form window**: domestic leagues use up to the last 5 matches in the current season; before matchday 1 they use the full previous season. WC uses qualifier matches through Group Stage Matchday 1, then cumulative finished WC tournament matches from Group Stage Matchday 2 onward (no 5-match cap). Never mix seasons.
- **Data quality is non-negotiable** — the user cannot manually verify numbers. Automated DQ tests are a hard requirement.
- **UI flow**: Landing (competition cards) → Fixture list (next round only) → Fixture detail (carousel/deep dive).
- **History window is per-source** — how many seasons/years to backfill is a CPO decision made at onboarding time, stored in the registry. No global defaults.
- **Cost is non-negotiable** — every competition in `docs/competition_registry.yml` must have `ingest_active` set explicitly before any code is written. `history_seasons` cannot be increased without explicit CPO approval in the same conversation. The pipeline runs once daily at 04:00 UTC; do not add extra runs without approval.
- **Base models are views** — `2_base` models materialise as views by design. Never change this to table without a documented reason; it would cause every base UNION ALL to be stored and rebuilt as a full table scan daily.

## Scalability rules — enforced by CI

These rules are machine-checked. If you are about to violate one, CI will catch it.
Do not work around the CI check — fix the approach instead.

| Rule | What it means | CI check |
|------|---------------|----------|
| **Zero-file rule** | Adding a league to `docs/competition_registry.yml` requires zero existing SQL file edits | `check_base_model_no_hardcoded_leagues.py` — fails if any cross-league base model contains a hardcoded `ref('stg_apif__XX_...')` |
| **Single-source rule** | The registry is the only place leagues are listed. `dbt_project.yml` is derived from it via `scripts/sync_dbt_vars.py` | `check_registry_var_sync.py` — fails if `active_competition_league_codes` doesn't match the registry |
| **CI ingest rule** | CI only ingests leagues whose raw BQ tables don't exist yet | `scripts/get_new_league_codes.py` + skip-if-exists logic in `ci-data-build.yml` |

### How to add a new league (the only correct procedure)

1. Add entry to `docs/competition_registry.yml`
2. Run `python scripts/sync_dbt_vars.py` (updates `dbt_project.yml`)
3. Scaffold 12 staging models + `sources.yml` entry (use the `onboard-competition` skill)
4. Push — CI ingests only the new league; base models auto-discover it via the Jinja loop

**Do not edit any file in `dbt_project/models/2_base/` when adding a league.** If you find yourself doing that, stop — the approach is wrong.

### The base model loop pattern (standard for all cross-league base models)

```sql
{% set league_codes = var('active_competition_league_codes') %}
with src as (
    {% for lc in league_codes %}
    {% if not loop.first %}union all{% endif %}
    select * from {{ ref('stg_apif__' ~ lc | lower ~ '_entity') }}
    {% endfor %}
)
```

Any base model that unions data across leagues must use this pattern. `check_base_model_no_hardcoded_leagues.py` enforces it permanently.

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
- GitHub Actions for CI (`ci-validate.yml`, `ci-data-build.yml`, `ci-ui.yml`) and scheduled runs (`dbt-scheduled.yml`)
- GitHub Pages for the match preview UI (`pages-match-preview.yml`)
