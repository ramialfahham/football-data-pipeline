# Task contract — metric names on screen come only from the catalogue label

objective: >
  Every on-screen name of a catalogue metric comes from METRIC_LABELS through its label_i18n_key:
  column heads, tiles and axis titles take the label, and a sentence that names a metric in its
  base form fills it through a placeholder. The competition page's Deserved points table and
  explainer and the Team page's verdict, caption, axes and last-season heads name the metrics by
  the catalogue's names in EN, DE and FI. check-metric-labels.test.mjs fails on a page string that
  spells a catalogue name outside METRIC_LABELS, and on two metrics of one entity that share both
  name and second line.

refs: >
  #226 (the requirement; the names and sentences in EN, DE and FI researched by an independent
  football expert, approved in chat, 2026-10-27; the competition table mock and the DE and FI
  names of shots on target against, researched the same way, approved in chat, 2026-10-28); #134 (the English names of points_won, deserved_points and deserved_points_gap);
  #129 (the competition page, design approved).

scope_paths:
  - site_v2/src/i18n/strings.ts
  - site_v2/src/components/competition/DeservedTable.astro
  - site_v2/src/components/team/DeservedHero.astro
  - site_v2/src/components/team/YearOverYear.astro
  - site_v2/src/pages/[[]lang]/[[]competition]/[[]stats]/index.astro
  - site_v2/src/specs/competition/index.spec.json
  - site_v2/src/specs/competition/stats/index.spec.json
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/styles/system.css
  - site_v2/scripts/check-metric-labels.test.mjs
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: none; the export, the warehouse and the served data are unchanged. downstream: the
  competition page's Deserved points table (heads and explainer), the Rankings page's search
  description, the Team page's Deserved vs actual block (verdict, caption, axes, tiles) and its
  last-season heads, and every place that shows the shots on target names (Finnish: the Form
  comparison, the boards, the hero tiles). layer_rules: display only; names are looked up by the
  catalogue's label_i18n_key, no metric fact computed. deploy_order: none; deploy:site-v2 is
  manual. blast_radius: the strings.ts entries named above and the components that read them; the
  new METRIC_LABELS entries for points_won, deserved_points, deserved_points_gap, goals and
  goals_against, and the renamed shots on target, shots on target against and shots on target
  difference names; the label
  check, which can fail a build on any page string.

approved_design:
  - competition: #129
  - home: #127
  - match: #132

acceptance_criteria:
  - "The Deserved points table's heads and explainer, the Team page's verdict, caption, axes and last-season heads take every catalogue name in its base form from METRIC_LABELS; no page string repeats one."
  - "The rendered text is the approved wording in EN, DE and FI: shots on target difference reads Differenz der Schüsse aufs Tor (DE) and Laukausero maalia kohti (FI), shots on target reads Laukaukset maalia kohti (FI), shots on target against reads Zugelassene Schüsse aufs Tor (DE) and Vastustajan laukaukset maalia kohti (FI); Balance, shot balance, Schussbilanz and laukaustase are gone."
  - "check-metric-labels.test.mjs fails on a page string outside METRIC_LABELS that contains a catalogue name of two or more words or is exactly one, unless listed as not the metric, with its reason."
  - "check-metric-labels.test.mjs fails when two catalogue metrics of one entity share both name and second line in any locale."

decisions_taken: >
  The names and sentences as approved in chat, 2026-10-27; the competition table with the
  catalogue names as heads as mocked and approved in chat, 2026-10-28: four equal number columns
  that shrink on narrow screens, heads that wrap and hyphenate. The Team page has no approved
  design yet; its verdict, caption, axes, tiles and last-season heads ship the approved wording in
  their existing layout, approved in chat, 2026-10-28. Home and the match page change only through
  the renamed labels, in their approved layouts. Readings: a count of points takes the singular
  for one point; inside a sentence a
  name takes a small first letter in EN and FI and stays as written in DE; a one-word name inside
  a sentence is an ordinary word; the Finnish shots on target name is one name for the team and
  the player metric; a name inflected inside a German or Finnish sentence (Schüssen aufs Tor,
  laukauserolla maalia kohti) is written in that sentence, and the check cannot match it by
  spelling; the test's exceptions are exact matches that are not the metric (the standings Goals
  column, the match page's Goals section, the word after a goal count), each with its reason. The
  decision-history pin moves down by the comment lines this change removes. No new dependency and
  no recurring cost.

decisions_reserved:
  - Any metric name or sentence wording beyond the approved list; researched by the football expert before it is put to the CPO.

done_when:
  - The offline gates, check_copy_gate.py, check-page-specs, the site node tests and pytest pass.
  - A local build and the dev server show the approved wording in EN, DE and FI at 375px and 1010px.
  - check_design_inventory.py passes on the local build.
  - Reviewers per review_routing.json pass.

amendments:
  - "2026-10-28: the Team page, which has no approved design yet, ships the approved #226 wording in its verdict, caption, axes, tiles and last-season heads in its existing layout — authority: the CPO's ruling in chat, 2026-10-28, when asked whether the Team page's changed wording ships in this MR; content: decisions_taken records it, approved_design is unchanged."
