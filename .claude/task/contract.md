# Task contract — data_contract.md doc-staleness follow-ups (#427 review)

> Two pre-existing data_contract.md inaccuracies surfaced by the #427 data-engineer review
> (out of #427's scope at the time, flagged as follow-up). Docs-only, non-protected — part
> of the CPO-granted autonomous non-protected backlog (2026-06-13, see escalations.log).
> See docs/working_agreement.md §2.

objective: >
  Fix two stale/inaccurate statements in docs/data_contract.md, verified against the
  ingestion loaders this session:
  1. The "Landing zone" section says the payload is the "verbatim"/"unchanged" API
     envelope. Not literally true: loaders that batch multiple calls don't keep each raw
     envelope as-is. Two shapes: the MERGE loaders (fixtures, standings, teams, injuries)
     concatenate the calls' `response` arrays into one standard envelope (recomputing
     results/paging); the per-team RESHAPE loaders players/squads (loads/squads.py) AND
     coaches (loads/coaches.py) store a `{league_code, response:[...]}` payload WITHOUT the
     envelope metadata (coaches items {team_id, coach}; squads items {team_id, season,
     players_payload}). Correct the "verbatim/unchanged" wording, AND scope line 23
     ("Nothing is discarded") to response DATA — the reshape loaders drop the per-call
     envelope metadata (get/parameters/errors/results/paging), keeping the response items.
  2. The "Append-only writes (reference tables)" prose lists "fixtures-next, standings,
     teams, players, leagues" but omits coaches + injuries (added as unified append tables
     in #427). Add them so the prose matches the unified-raw-tables table.
refs: #427 review follow-up (data-engineer pre-existing-staleness findings).

scope_paths:
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/active_work.md

decisions_taken: >
  Docs-only accuracy fixes within the CPO-granted autonomous non-protected backlog
  (2026-06-13). No code/behaviour change. Wording verified against the actual loaders
  (coaches.py reshapes; injuries.py merges seasons) — describing existing behaviour, not
  changing it.

decisions_reserved:
  - Keep it surgical: only the two flagged statements. Do NOT re-describe the merge model,
    the unified-tables table, or other sections. If a reviewer finds a deeper inaccuracy,
    STOP and surface it rather than expanding.

done_when:
  - Landing-zone "verbatim/unchanged" wording corrected to reflect the MERGE vs
    players/squads+coaches RESHAPE split; line 23 "Nothing is discarded" SCOPED to response
    data (no longer an absolute claim — reshape loaders drop envelope metadata, keep response items).
  - the append-only reference-tables prose lists coaches + injuries.
  - no other section changed; markdown renders (tables intact).
  - reviewers: scope-auditor (always) + data-engineer-reviewer (docs/data_contract.md) — PASS.

amendments: (none)
