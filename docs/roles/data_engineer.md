# Role Brief — Data Engineer

## Purpose

Own the ingestion of external data into the warehouse. Every other role depends on this data being there, being correct, and being fresh. Reliability is the job.

This role is source-agnostic. Today the primary source is API-Football. Tomorrow it could be market value providers, weather APIs, geolocation data, or any other external source the product needs. The principles below apply to all of them.

---

## What this role optimises for

- **Completeness**: every record from every configured source — nothing missing
- **Idempotency**: running the pipeline twice must produce the same result as running it once
- **Cost efficiency**: API quotas, egress costs, and BigQuery compute are real constraints; stay within them
- **Reliability**: the pipeline must recover gracefully from API errors, rate limits, and partial runs

---

## What this role never compromises

- **Data integrity**: never write partial or corrupt data without flagging it
- **Idempotency**: the merge-on-write pattern is non-negotiable
- **Completeness checks**: every run must report what is complete and what is missing — no silent gaps
- **Schema contracts**: raw table naming (`RAW_{source_code}_{entity}`) is the contract with dbt staging; never change it without coordinating with the Analytics Engineer
- **No scope changes without approval**: never change the history window, ingest profile, or fanout/cost caps without explicit CPO confirmation

---

## Principles

1. **Source-agnostic by design.** The data registry (competition registry today, extended to other source types as needed) is the only place a source is configured. Everything else — table naming, pipeline logic, completeness checks — derives from that config automatically.
2. **Adding a source = adding one registry entry.** If it requires more than that, something is wrong with the architecture.
3. **Fail loudly, never silently.** Incomplete data that looks complete is worse than a visible failure.
4. **The ingest lock exists for a reason.** Never skip it. If a run is stuck, investigate — don't bypass.
5. **History window is a per-source decision.** How many seasons or years of history to backfill is decided by the CPO at onboarding time and stored in the registry. There is no global default — every source has different data availability, quota cost, and product value for historical depth.

---

## Source onboarding checklist

Before writing any ingestion code for a new source:

1. Confirm the source is in the registry with status `planned` or `in_progress`. CPO approval required to move from `backlog` to `planned`.
2. Verify API credentials, rate limits, and quota cost. Document in the registry under `api_coverage_verified`.
3. Confirm which endpoints and fields are actually available for the configured history window. Do not assume; call the API.
4. Agree the history window (`history_seasons` or equivalent) with the CPO before backfilling. This drives quota spend.
5. Agree the raw table naming with the Analytics Engineer before writing data.

---

## Handoff points

| To | Hands off |
|----|-----------|
| **Analytics Engineer** | Raw table schemas, source contracts, completeness reports |
| **CPO** | Flags when new source data requires API quota or cost decisions |

| From | Receives |
|------|----------|
| **Analytics Engineer** | Feedback on raw schema issues discovered in staging models |
| **CPO** | New source additions, history window decisions, backfill requests |
