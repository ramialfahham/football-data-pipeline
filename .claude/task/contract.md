# Task contract — #655: season-record "campaign is the season" (drop stale note)

> Written on a CLEAN tree (branch chore/655-campaign-is-season-note off main @ 81eb1ed).
> Comment/doc-only in model files — no logic, no compiled-SQL change. The CPO ruled the action in issue #655;
> contract + review + gate still run. (Redone in the primary tree after a concurrent session cleared.)

objective: >
  Remove the stale "multi-season national qualifier campaigns are a separate follow-up" deferral notes from the
  two season-record model docstrings. CPO ruling (#655, 2026-07-06): "the campaign is the season" — confirmed
  already true in the data (each WCQ campaign carries ONE season_api_year spanning its full 2–3-yr run, checked
  core.fct_fixture: WCQEU=2024 covers 2025-03→2026-03, etc.), so the (league_code, season_api_year) partition
  already cumulates the whole campaign as one unit. The notes describe a gap that does not exist. Replace them
  with a one-line statement of the correct behavior.
refs: #655; docs/metrics_context_model.md §4 (qualifying row) + §8.4; CPO ruling 2026-07-06.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - .claude/task/**

impact_map: >
  Trivial/cosmetic: docstring comment text only, in two 4_intermediate model files. No SELECT/CTE/logic/config
  change — the compiled SQL is byte-identical, so zero data/number/mart/export impact and no build risk. Evidence:
  the edits touch only the `{# ... #}` docstring blocks; the models' query bodies (the `with` CTEs, the `select`
  column lists, both `window` clauses) are untouched. No new model, no ref() change. `dbt ls` not needed (no
  lineage change); dbt CLI is broken locally regardless. The two files are unchanged by the just-merged
  81eb1ed/450c205 (ingestion + affiliation-mapping), so #655 applies cleanly on current main.

decisions_taken: >
  Rests on the CPO's #655 ruling ("campaign is the season") + the data check this session (each qualifying
  campaign = one season_api_year). No new decision — records a finding and removes a stale note. The corrected
  wording states the model already handles a qualifying campaign as one season (matching the momentum qualifiers
  window's OUTCOME — both cumulate the whole campaign, via different mechanisms), which the data + §4 matrix imply.

decisions_reserved:
  - The inconsistent season_api_year label ACROSS confederations (WCQAF=2023 vs WCQEU=2024 vs WCQSA=2026) is a
    SEPARATE observation — not touched here; linkage to the WC edition is via parent_competition, not the year.

done_when:
  - Both docstrings no longer claim multi-season qualifier campaigns are deferred; they state the campaign is one
    season (one season_api_year), already cumulated.
  - Compiled SQL unchanged (comment-only); `python scripts/check_layer_contract.py` passes.
  - scope-auditor + analytics-engineer-reviewer PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
