# NORTH STAR
**Version:** 1.0
**Last updated:** 2026-04-27
**Owner:** CPO

> Read this first. Then follow the links to authoritative sources.
> Never copy content from linked documents into this file — link, never duplicate.

---

## What we are building

A sticky Sports Analytics app for fans. Primary use case: open the app 30–60 minutes
before a match, compare both teams with meaningful metrics, discuss with friends.

Start: FIFA World Cup 2026. Then Big 5 European leagues. Eventually multi-sport.

---

## Current state

| Competition | Status | Branch |
|---|---|---|
| Bundesliga (BL1) | Active | main |
| FIFA World Cup 2026 (WC26) | In progress | feature/wm2026-infrastructure |
| Premier League, La Liga, Serie A, Ligue 1, BL2 | Planned | — |

---

## Where things live

| Topic | Authoritative source |
|---|---|
| Competition IDs, provider codes, onboarding rules | `docs/competition_registry.yml` |
| Layer contract (what goes where in dbt) | `dbt_project/docs/layering.md` |
| Naming conventions, testing policy | `dbt_project/docs/engineering_standards.md` |
| Field definitions | `docs/data_contract.md` |
| WC26 MVP scope and metric definitions | `docs/WM2026_MVP_SCOPE.md` |
| Daily operations, runbook, troubleshooting | `docs/operations_guide.md` |
| Branching, PR process | `docs/development_workflow.md` |
| Agent behavior rules | `.cursor/rules/agent-behavior.mdc` |

---

## Core architecture principle

Provider-specific logic lives in `staging` and below — never above.
`league_code` (BL1, WC26, PL, ...) is our internal identifier everywhere above staging.
Provider IDs and payload codes stay in ingestion scripts and staging models only.

Adding a new provider or switching providers never touches core or marts.

Full rules: `dbt_project/docs/layering.md`

---

## Anti-drift rules (mandatory for all agents)

1. Never invent fields — if not in `data_contract.md`, ask CPO first.
2. Never hardcode provider IDs — always read from `competition_registry.yml`.
3. Never expand scope without CPO approval — check the relevant scope document first.
4. Never modify existing competition models when onboarding a new one — additive only.
5. Always verify which branch you are on before making changes.
6. Flag any decision that affects BigQuery cost or API budget before implementing.

---

## Open questions (2026-04-27)

| Question | Priority |
|---|---|
| When will WC26 statistics_fixtures / statistics_players activate in api-football? | HIGH |
| Add source_system + source_entity_id to existing core dims? | MEDIUM |
| Define 2_base layer naming convention | MEDIUM |
