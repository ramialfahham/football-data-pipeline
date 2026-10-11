# Task contract — one naming rule for core and mart models

objective: >
  The naming rule in engineering_standards.md section 1 states the names the core and mart models
  follow: fct_ and dim_ in core, mart_<entity>_<subject> in the marts, with a single match named
  fixture. The note in content_architecture.md that no document settles mart naming goes.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): its goals,
  line-ups and merged player-match mart add names. The rule text: approved in chat, 2026-10-11.

scope_paths:
  - dbt_project/docs/engineering_standards.md
  - docs/content_architecture.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: two documents; no model, test, script or page changes.
  downstream: none; no test, hook or script reads either line (grep for the old rule text finds
  only these two files).
  layer_rules: unchanged; layering.md keeps the tests a table must pass to earn fct_ or dim_.
  deploy_order: none.
  blast_radius: the rule new and renamed models follow. Seven marts do not follow it today
  (mart_leaderboards, mart_standings, mart_roster, mart_head_to_head, mart_match_days,
  mart_next_matchday, and mart_player_match_log, which #176 merges into
  mart_player_fixture_stats); no model is renamed here.

decisions_taken: >
  The rule text, and deleting the content_architecture.md bullet so the rule has one owner:
  approved in chat, 2026-10-11.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - The new names of the seven marts that do not follow the rule, and when they change.
  - The intermediate and staging rules, unchanged.

done_when:
  - The two lines in engineering_standards.md read as approved; the content_architecture.md bullet is gone.
  - pytest tests/ passes; the offline CI gates pass.

amendments: >
  none
