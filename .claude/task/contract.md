# Task contract — AFCCL provider_league_id verification

> Audit F23 / issue #426: AFCCL carried provider_league_id 17 as `ingest_active: true`
> with a "legacy ID — spot-check" caveat (the four-wrong-IDs pattern). Verified id 17
> against the ingested RAW_APIF_LEAGUES data. See docs/working_agreement.md §5/§10.

objective: >
  Resolve issue #426 (audit F23). provider_league_id 17 for AFCCL was VERIFIED against
  RAW_APIF_LEAGUES (BigQuery): it returns "AFC Champions League Elite" (Cup), seasons
  2016–2025 incl. the current 2024/2025 — API-Football kept id 17 through the 2024/25
  "Elite" rebrand. The ID is CORRECT, so the issue's conservative "disable until
  verified" default does NOT apply; instead, keep ingest_active and record the
  verification evidence in the registry note (replacing the stale "legacy ID" caveat).
refs: #426 (audit F23); evidence: RAW_APIF_LEAGUES query 2026-06-12.

scope_paths:
  - docs/competition_registry.yml
  - .claude/active_work.md   # artifact-only: handover write-out at close

decisions_taken: >
  ID-17 verification result (RAW_APIF_LEAGUES, 2026-06-12) is the authority: id 17 =
  "AFC Champions League Elite", current seasons present → CORRECT. Action = record
  evidence + keep ingest_active: true. The "disable" branch of #426 is not taken
  because verification succeeded (data-quality favors keeping a confirmed-correct
  competition over a needless disable).

decisions_reserved:
  - No change to provider_league_id, ingest_active, history_seasons, or any cost knob —
    only the human-readable note is updated. If the verification were ambiguous, the
    disable decision would be CPO-class (§10) — it is not, the data is unambiguous.

done_when:
  - the AFCCL note records the id-17 verification (source: RAW_APIF_LEAGUES; name "AFC
    Champions League Elite"; seasons through 2025) and drops the stale "legacy ID" line.
  - ingest_active stays true; provider_league_id stays 17; no other field changes.
  - registry still parses: `python -c "import ingestion.api_football.registry as r;
    r._parse_competitions()"` succeeds; check_registry_var_sync + check_competition_type_seed pass.
  - reviewers: scope-auditor (always) + data-engineer-reviewer (competition_registry.yml) — PASS.

amendments: (none)
# On amendment (clean tree only):
#   - <date>: + <path> — authority: <CPO answer / standing rule>; content: <what>
