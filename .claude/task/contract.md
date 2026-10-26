# Task contract — the round in the competition header, in the page's language

objective: >
  The warehouse names every round of a competition's latest season by the competition's own name
  in EN, DE and FI: a seed of whole-round patterns, the competition's (and where its format
  changes yearly, the season's) own row before the general one, each giving a copy key and the
  number or group letter it shows; a test fails on a latest-season round text no pattern covers.
  The marts serve the key and values per fixture and the competition's current round; the export
  carries them; the competition header's round and the Matchdays picker render them, so no
  provider English reaches those places.

refs: >
  #148 (the requirement; the per-competition round names, researched by an independent football
  expert, approved in chat, 2026-10-26); #129 (the competition page, design approved); #229 (the
  season part of the same line).

scope_paths:
  - dbt_project/seeds/round_names.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/4_intermediate/shared/int_round_names.sql
  - dbt_project/models/4_intermediate/shared/int_round_names.yml
  - dbt_project/tests/assert_every_round_text_resolves.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_next_matchday.sql
  - dbt_project/models/5_marts/shared/mart_competition_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/export_site_data.py
  - scripts/check_copy_gate.py
  - tests/test_export_site_data.py
  - tests/test_governance_hooks.py
  - tests/test_no_decision_history_in_code.py
  - site_v2/src/lib/roundName.mjs
  - site_v2/src/lib/roundName.test.mjs
  - site_v2/src/lib/competitionPayload.mjs
  - site_v2/src/lib/competitionPayload.test.mjs
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/components/competition/CompetitionHeader.astro
  - site_v2/src/components/competition/MatchdaySchedule.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]matches]/index.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]stats]/index.astro
  - site_v2/src/specs/competition/index.spec.json
  - site_v2/src/specs/competition/matches/index.spec.json
  - site_v2/src/specs/competition/stats/index.spec.json
  - site_v2/src/data/competitions/BL1/2026.json
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: a new seed round_names and a new intermediate int_round_names (one row per distinct
  fct_fixture league_code, season and round text); mart_competition_fixtures and
  mart_next_matchday gain round_label_i18n_key, round_number and round_letter;
  mart_competition_index gains the current round's three; the export carries them in the
  competition payload (rounds and page meta) and in every file built from the competition fixture
  shape. downstream: the dbt ls lineage of the three marts is pasted in the evidence before
  review. The site: the competition header on the Overview, Matchdays and Rankings pages and the
  Matchdays picker; compFactMatchday's DE and FI text, which the match page also reads.
  layer_rules: the round text is read in intermediate, served by marts as a copy key and values,
  rendered by the site; no page reads a round text. deploy_order: the columns reach prod with the
  nightly after merge; the export carries them on the next deploy:export; deploy:site-v2 is manual.
  blast_radius: the header's round and the picker's titles; a latest-season round no pattern
  covers shows no name and is reported by a warn test with stored failures, without skipping the
  marts downstream.

approved_design:
  - competition: #129
  - match: #132

acceptance_criteria:
  - "Every round text of each competition's latest season in fct_fixture resolves through round_names to a copy key, with its number or letter where the name shows one; a singular warn test with stored failures reports any that does not."
  - "mart_competition_fixtures and mart_next_matchday serve round_label_i18n_key, round_number and round_letter per fixture; mart_competition_index serves the current round's three per competition."
  - "The competition header's round and the Matchdays picker render the approved per-competition names in EN, DE and FI from the served key and values; no provider round text is shown there."
  - "check_copy_gate.py requires every round_names copy key in EN, DE and FI."

decisions_taken: >
  The per-competition round names approved in chat, 2026-10-26, as researched; compFactMatchday
  becomes the Matchday name, so the match page reads the same form. Readings: one seed of
  whole-round patterns, because German and Finnish join a round's parts differently from English
  ("3. Gruppenspieltag", "Alkulohko, 3. kierros"); a cup's early rounds are named per season,
  matched to the organiser's rounds by the fixtures' dates, since the provider's "Round of 128"
  names different rounds in different seasons; the coverage test reads the latest season of each
  competition, the season the pages show; the season part stays the payload's served label from
  #229; the match page's cup rounds and the Team page's fixture rows keep the provider text, a
  follow-up. No new dependency; the recurring cost is a join of the distinct round texts on a
  small seed.

decisions_reserved: []

done_when:
  - dbt parse, SQLFluff, the offline gates, check_copy_gate.py, pytest and the site node tests pass.
  - A local build and the dev server show the approved names in the header and the picker in EN, DE and FI.
  - The MR data build passes, including the round coverage test.
  - Reviewers per review_routing.json pass.

amendments:
  - "2026-10-26: the parts seed round_parts became the whole-name seed round_names, per competition and season, after the CPO approved the per-competition names in chat; scope_paths, objective, criteria and readings follow."
  - "2026-10-26: tests/test_no_decision_history_in_code.py joins scope_paths, to lower its pin by the one flagged comment line this change removes from MatchdaySchedule.astro."
  - "2026-10-26: the match page (#132) joins approved_design, its matchday wording changing with compFactMatchday as the plan approved in chat; system.css joins scope_paths so a long round name wraps the picker's Next tag instead of overflowing at 375px; the coverage test is warn with stored failures, as engineering_standards.md §3.3/§3.4 prescribe for a check that shows no wrong number."
