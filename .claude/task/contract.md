# Task contract — no tracked file quotes the CPO's chat words

objective: >
  Replace every remaining quote of the CPO's chat words outside the core documents with the rule
  it carried, in plain words, as listed and approved in chat, 2026-10-06.

refs: >
  The cleanup of quoted chat words, approved in chat, 2026-10-06.

acceptance_criteria:
  - No tracked file outside the core documents quotes the CPO's chat words; a search for every removed phrase finds nothing
  - The site builds identically; with the same data, every page built from this branch matches the page built from main

scope_paths:
  - .claude/task/acceptance_evidence.md
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/agents/bi-analyst-reviewer.md
  - .claude/agents/cto-reviewer.md
  - .claude/agents/data-engineer-reviewer.md
  - .claude/agents/football-analytics-expert-reviewer.md
  - .claude/agents/platform-reviewer.md
  - .claude/agents/scope-auditor.md
  - .claude/agents/seo-expert-reviewer.md
  - .claude/review_routing.json
  - .claude/hooks/git_discipline.py
  - .gitlab-ci.yml
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/tests/assert_mart_team_leaderboards_every_board_has_a_leader.sql
  - dbt_project/tests/assert_mart_leaderboards_every_home_board_has_a_leader.sql
  - design-mocks/renders/*.html
  - design-mocks/gen_matches.py
  - design-mocks/gen_taxonomy.py
  - docs/competition_registry.yml
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md
  - ingestion/api_football/coverage.py
  - ingestion/api_football/loads/batch_fixtures.py
  - scripts/export_site_data.py
  - site_v2/scripts/check-metric-labels.test.mjs
  - site_v2/scripts/check-page-specs.mjs
  - site_v2/src/components/home/TopPlayers.astro
  - site_v2/src/data/README.md
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/competitionOrder.mjs
  - site_v2/src/lib/types.ts
  - site_v2/src/styles/system.css
  - tests/test_export_landing.py
  - tests/test_refetch_cadence.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

protected_override: >
  Approved by the CPO in chat, 2026-10-06: the quote removals in the eight reviewer briefs,
  git_discipline.py, review_routing.json and .gitlab-ci.yml, in the exact text listed, plus the
  routing note's wording "a cost approval quoted in" becoming "recorded in".

impact_map: >
  Comment, docstring and prose lines only. No executable line, string value the program uses,
  routing row, model column, export payload or page output changes, so no number on any page
  moves and no guard behaves differently. In the reviewer briefs only explanatory prose changes;
  every hunt item, verdict rule and output format stays. In review_routing.json only `_comment`
  strings change, which no code reads. In .gitlab-ci.yml only comment lines change.
  blast_radius: none beyond the text; dbt and ingestion files change comment lines only
  (`dbt ls` lineage unaffected, no SQL token changes).

decisions_taken: >
  The edits are the approved list, nothing else:
  - Each quote becomes the rule it carried in plain words, or is removed where the sentence
    already states the rule. The new text carries no date, issue or MR number, story or quote.
  - The seven quotes marked uncertain or unmarked are included, as approved.
  - Pins move down with them: the sentence-length and doc-history pins of the eight briefs and the
    data README, and the code-history line count.
  - The two acceptance criteria, approved in chat, 2026-10-06.
  Reading: criterion 1 covers the twelve design-mock renders, which inline the system.css comment;
  each changes that one CSS comment line the same way, so every render shows what it showed.

  Threshold declarations. NEW MECHANISM: none. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - Each OLD text is gone and each NEW text present, per the approved list.
  - pytest (whole suite), the offline gates, dbt parse and the CI lint pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
