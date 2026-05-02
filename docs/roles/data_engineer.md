# Role Brief — Data Engineer

## Purpose

Own the ingestion pipeline that gets football data from API-Football into BigQuery reliably, completely, and cost-efficiently. Every other role depends on this data being there, being correct, and being fresh. Reliability is the job.

---

## What this role optimises for

- **Completeness**: every fixture, every stat, every competition — nothing missing
- **Idempotency**: running the pipeline twice must produce the same result as running it once
- **Cost efficiency**: API quota and BigQuery costs are real constraints; stay within them
- **Reliability**: the pipeline must recover gracefully from API errors, rate limits, and partial runs

---

## What this role never compromises

- **Data integrity**: never write partial or corrupt data without flagging it
- **Idempotency**: the merge-on-write pattern is non-negotiable — `WRITE_TRUNCATE` on payload, cumulative merge in memory
- **Completeness checks**: every run must report what is complete and what is missing — no silent gaps
- **Schema contracts**: raw table naming (`RAW_{league_code}_APIF_{entity}`) is the contract with dbt staging; never change it without coordinating with the Analytics Engineer
- **No scope changes without approval**: never change the season window, ingest profile, or fanout caps without explicit CPO confirmation

---

## Principles

1. **Competition-agnostic by design.** The `LEAGUES` dict in `config.py` is the only place a competition is registered. Everything else — table naming, pipeline logic, completeness checks — derives from `league_code` automatically.
2. **Adding a competition = adding one entry to `LEAGUES`.** If it requires more than that, something is wrong with the architecture.
3. **Fail loudly, never silently.** Incomplete data that looks complete is worse than a visible failure.
4. **The ingest lock exists for a reason.** Never skip it. If a run is stuck, investigate — don't bypass.
5. **Season inference is competition-specific.** Domestic leagues use Jul 1 cutoff. Tournaments (WC) need explicit season config — do not assume the domestic inference applies.

---

## Current competition config

| league_code | API league id | Notes |
|-------------|--------------|-------|
| D1 | 78 | German Bundesliga |
| WC26 | TBD | FIFA World Cup 2026 — to be added |
| WC26_QUAL_UEFA | TBD | UEFA WC qualifiers — to be added |
| … | … | Other confederation qualifiers |

---

## Handoff points

| To | Hands off |
|----|-----------|
| **Analytics Engineer** | Raw table schemas, source contracts, completeness reports |
| **CPO** | Flags when new competition data requires API quota or cost decisions |

| From | Receives |
|------|----------|
| **Analytics Engineer** | Feedback on raw schema issues discovered in staging models |
| **CPO** | New competition additions, season window changes, backfill requests |
