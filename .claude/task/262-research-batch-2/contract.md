# Task contract — research batch 2 of the #262 provider-error backlog

objective: >
  Issue #262. Research the next 15 current-season matches of mart_competition_research_list
  that sit in a competition of the research skill's site table, after batch 1's, and add the
  agreed, sourced rows to the correction seeds, so the nightly can serve the values it withholds today.

refs: >
  #262 note, research backlog cleared as soon as possible (approved in chat, 2026-11-20);
  method .claude/skills/research-provider-errors/SKILL.md; row formats dbt_project/seeds/schema.yml.

scope_paths:
  - dbt_project/seeds/fixture_card_corrections.csv
  - dbt_project/seeds/fixture_goal_corrections.csv
  - .claude/task/262-research-batch-2/contract.md
  - .claude/task/262-research-batch-2/review.md
  - .claude/task/262-research-batch-2/review_input.patch

approved_design:
  - none: no page output changes

depends_on:
  - none: builds on merged seeds and mart_competition_research_list only
shared_files:
  - none: no design baseline, chart manifest or chart pin changes

decisions_taken: >
  The batch rule is the CPO's, approved in chat, 2026-11-20 (note on #262): clear the backlog
  current season first, in batches, each batch landing as an ordinary seed MR the CPO merges.
  Rows follow the skill's section 7 conventions. A match enters the seeds only when two blind
  reads agree and every name matches one player on the provider's sheet. No correction_no_longer_needed
  row is removed. No new mechanism, no new dependency, no recurring cost: reads only, plus
  BigQuery reads under 1 GB.

decisions_reserved:
  - which matches stay open when a read disagrees or a site cannot be read: reported, never guessed
  - removal of correction_no_longer_needed rows: undecided, untouched

done_when:
  - every added row's fixture_id is in the research list and its source is a host of the site table
  - dbt parse passes and the seed schema tests' accepted values hold for the added rows
  - the batch report lists matches researched, rows per seed, and every match stopped or left open

amendments: (none)
