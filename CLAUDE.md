# Claude orientation — football-data-pipeline

Read this at the start of every session before doing anything else.

## Session start — branch hygiene (do this first, every session)

1. Run `git branch --show-current` via **Bash** to confirm the active branch.
2. If the branch doesn't match the task, switch now **before writing any files**: `git checkout <target-branch>` or `git checkout -b <new-branch>`.
3. **Use Bash for all commands** — git, bq, gh, python, curl, everything. Never use PowerShell; it runs commands as background tasks requiring file polling, which is slow and causes confusion.
4. If unsure which branch to use, ask the user before touching any file.
5. **Before creating a new branch**, run `gh pr list --state open` and ask two questions: (a) is this work a hard dependency for an open PR? (b) does separating it into its own PR buy anything — independent reviewability, an earlier merge path? If it's a hard dependency and separation buys nothing, commit to the existing branch. If it can stand alone and merge first, a new branch is fine. See `docs/working_agreement.md` section 3a.

## Working agreement

**Read [`docs/working_agreement.md`](docs/working_agreement.md) before doing anything.** It defines what you are and are not allowed to do, quality standards, branch discipline, layer rules, and communication style. Non-negotiable.

**Every unit of work runs Explore → Plan → Confirm → Implement → Verify** (§1). Four steps are machine-gated; **Confirm is the human checkpoint — WAIT for the user's explicit go before implementing.** Exploring options or thinking out loud is not a go. For any file-touching task, use **plan mode** so the harness enforces that wait (`EnterPlanMode` → plan-back → the user approves `ExitPlanMode`).

Pay particular attention to **§10 Decision rights** (the CPO-only decision classes — product/UX, metrics, naming, anything permanent, NEW mechanisms, rule extensions), **§11 Blinded escalation** (premise check, two conflicting paths, **and a recommendation with its reasoning** — §11 used to forbid one and was corrected 2026-07-22), and **Appendix A Historical anti-patterns** (the failure classes every reviewer hunts for). When a case doesn't clearly match a written rule, the classification itself is a CPO decision — never decide by analogy.

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
| Agent guardrails (hooks & skills — what fires, why, how to carry to a new project) | [docs/agent_guardrails.md](docs/agent_guardrails.md) |
| GitHub Pages match preview plan | `C:\Users\Rami\.cursor\plans\gh_pages_match_preview_bce3ad94.plan.md` |

## Architecture decisions (non-negotiable)

- **Layer contract**: staging = raw cleanup only; base = dedup + first logic; core = facts/dims; marts = consumption.
- **league_code** is the partition key on every model — never hardcode a competition identifier in business logic.
- **Raw table naming**: `RAW_APIF_{entity}` (e.g. `RAW_APIF_FIXTURES_NEXT`). All competitions share six unified raw tables, discriminated by a `league_code STRING` column. There are no per-competition raw tables. Staging models are generic — one file per entity, not per competition.
- **Form window**: domestic leagues use up to the last 5 matches in the current season; before matchday 1 they use the full previous season. WC uses qualifier matches through Group Stage Matchday 1, then cumulative finished WC tournament matches from Group Stage Matchday 2 onward (no 5-match cap). Never mix seasons.
- **Data quality is non-negotiable** — the user cannot manually verify numbers. Automated DQ tests are a hard requirement.
- **UI flow**: v2 website IA per `docs/site_architecture.md` (hybrid browse + fixtures-first home, epic #361). The legacy card MVP (Landing → fixture list → fixture detail carousel) stays live until cutover (#377).
- **History window is per-source** — how many seasons/years to backfill is a CPO decision made at onboarding time, stored in the registry. No global defaults.
- **Cost is non-negotiable** — every competition in `docs/competition_registry.yml` must have `ingest_active` set explicitly before any code is written. `history_seasons` cannot be increased without explicit CPO approval in the same conversation. The pipeline runs once daily at 04:00 UTC; do not add extra runs without approval.
- **Base models are views** — `2_base` models materialise as views by design. Never change this to table without a documented reason.

## Scalability rules — enforced by CI

These rules are machine-checked. If you are about to violate one, CI will catch it.
Do not work around the CI check — fix the approach instead.

| Rule | What it means | CI check |
|------|---------------|----------|
| **Zero-file rule** | Adding a league to `docs/competition_registry.yml` requires **zero file edits of any kind** — no SQL, no YAML, no Python. The registry entry is the only change. | `check_layer_contract.py` — fails if any per-competition staging subdirectory exists; dbt compilation catches any `ref()` pointing to a non-existent per-competition staging model |
| **Single-source rule** | The registry is the only place leagues are listed. `dbt_project.yml` is derived from it via `scripts/sync_dbt_vars.py` | `check_registry_var_sync.py` — fails if `active_competition_league_codes` doesn't match the registry |
| **CI ingest rule** | CI detects new leagues by querying `SELECT DISTINCT league_code FROM RAW_APIF_FIXTURES_NEXT` and ingests only those not yet present | `scripts/get_new_league_codes.py` + skip-if-exists logic in `ci-data-build.yml` |

### How to add a new league (the only correct procedure)

1. Add entry to `docs/competition_registry.yml`
2. Run `python scripts/sync_dbt_vars.py` (updates `dbt_project.yml`)
3. Push — CI ingests only the new league into the unified raw tables; all downstream models pick it up via the `league_code` column

**Do not create any new files in `dbt_project/models/` when adding a league.** If you find yourself doing that, stop — the approach is wrong. Generic staging models read `league_code` from the unified raw tables; no per-competition files are needed.

### The base model pattern (standard for all cross-league base models)

```sql
with src as (
    select * from {{ ref('stg_apif__entity') }}
)
```

Base models read directly from the generic staging model. The `league_code` column flows through from the raw table — no UNION ALL loop, no per-competition `ref()` calls.

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
