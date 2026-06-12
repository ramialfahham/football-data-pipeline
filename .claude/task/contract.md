# Task contract — doc-sync cleanup (audit F27–F37)

> Issue #419: the G4 audit's batched stale-doc cleanup. Low-risk doc/comment/docstring
> fixes only — no behavior change. See docs/working_agreement.md §2/§5/§10.

objective: >
  Fix the audit's stale-doc findings F27–F37 (issue #419): bring docs/comments/
  docstrings in line with reality. No code behavior changes — only documentation,
  comments, a registry section header, and a model docstring/yaml description.

refs: #419 (audit F27–F37). CPO ruling 2026-06-12: file as one batch; inventories exhaustive.

scope_paths:
  - dbt_project/docs/layering.md                         # F27 mart inventory exhaustive; F28 add fct_team_market_value_snapshot
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql  # F29 retired-consumer ref
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml              # F30 retired-consumer ref
  - docs/operations_guide.md                             # F31 scheduler cadence twice->once
  - ingestion/api_football/loads/catalog.py              # F32 WRITE_TRUNCATE comment -> WRITE_APPEND
  - ingestion/api_football/fixture_scheduling.py         # F33 predictions docstring -> 4 calls
  - docs/competition_registry.yml                        # F34 section header PLANNED -> IN PROGRESS
  - docs/agent_guardrails.md                             # F36 cto-reviewer "dormant" -> active
  - .claude/active_work.md                               # artifact-only: handover write-out at close

decisions_taken: >
  Pure doc-sync per the audit + CPO batch ruling (2026-06-12). F37 (working_agreement
  §2 protected-paths) is ALREADY fixed (`.claude/agents/` is listed) — no change.
  F35 (portable_guardrails) is VERIFIED correct (the dir exists with the 5 documented
  hooks) — no change. The mart inventory (F27) is made exhaustive: all 19 marts with
  grain + materialization from the model docstrings/configs.

decisions_reserved:
  - No code/behavior change. F29's int_player_season__metrics may be ORPHANED (no live
    consumer) — but REMOVING a model is out of scope here; only the stale docstring
    reference to the retired int_matchday__fixture_player_insights is corrected. If the
    orphan should be deleted, that is a separate task (note it, do not act).

done_when:
  - layering.md mart inventory lists all 19 marts (grain + materialization); fact
    inventory includes fct_team_market_value_snapshot.
  - the retired-consumer references (int_matchday__fixture_player_insights) are removed/
    corrected in both int_player_season__metrics.sql and int_team_season.yml.
  - operations_guide cadence reads once-daily 04:00 UTC; catalog.py comment reads
    WRITE_APPEND; fixture_scheduling docstring reads 4 calls (no predictions); the #262
    registry section header reads IN PROGRESS; agent_guardrails no longer calls
    cto-reviewer "dormant".
  - dbt parse passes; `python -c "import ingestion.api_football..."` imports succeed;
    validate-local offline gates green.
  - reviewers: scope-auditor (always) + analytics-engineer-reviewer (layering.md, int
    models) + data-engineer-reviewer (ingestion comments, registry) — PASS.

amendments: (none)
# On amendment (clean tree only):
#   - <date>: + <path> — authority: <CPO answer / standing rule>; content: <what>
