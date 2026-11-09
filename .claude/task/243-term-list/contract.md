# Task contract — one term list: one meaning, one key, one word

objective: >
  Issue #243: the site shows the approved term table. Each meaning has one key in
  site_v2/src/i18n/strings.ts, each component takes the full or the short form the registry names,
  and a test fails the build on a repeated meaning or a wrong form.

refs: >
  #243 notes 4179410849 (rules), 4179546416 (table), 4179559318 (the calls), 4179575490 (correction),
  approved in chat 2026-11-06; 4180302090 (acceptance criteria), approved in chat 2026-11-06;
  4185014476 (Versus in match titles and the Finnish match description), approved in chat 2026-11-07.

scope_paths:
  - .claude/task/243-term-list/
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - scripts/check_component_registry.py
  - tests/test_check_component_registry.py
  - tests/test_governance_hooks.py
  - scripts/check_copy_gate.py
  - site_v2/scripts/check-term-list.test.mjs
  - site_v2/scripts/check-metric-labels.test.mjs
  - site_v2/scripts/check-page-specs.mjs
  - site_v2/scripts/check-page-specs.test.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - site_v2/src/i18n/strings.ts
  - site_v2/src/i18n/strings.test.mjs
  - site_v2/src/components/*.astro
  - site_v2/src/pages/*.astro
  - site_v2/src/lib/*.ts
  - site_v2/src/lib/*.mjs
  - site_v2/src/specs/*.json
  - design-mocks/gen_top_players.py
  - design-mocks/gen_top_teams.py
  - tests/test_no_decision_history_in_code.py
  - design-mocks/gen_team_mock.py
  - site_v2/src/styles/system.css
  - docs/wireframes/09_chrome.md
  - docs/wireframes/02_team_profile.md
  - docs/wireframes/01_fixture_page.md
  - docs/metric_layer.md
  - docs/wireframes/metrics_display.md

protected_override: >
  docs/design/components.yml: #243 note 4179410849, approved in chat 2026-11-06, makes the full or
  short form a property of the component in this file.

impact_map: >
  writers: none; no ingestion, no dbt model, no seed, no export change. Keys the warehouse or the
  export serve keep their names: round_names, competition_types, confederations and the h2h keys.
  downstream: strings.ts feeds every page through t() and metricLabel(); the registry feeds
  scripts/check_component_registry.py, which generates docs/wireframes/block_standard.md from named
  fields only, and the new `short-forms` key is not one of them.
  layer_rules: scripts/check_copy_gate.py, site_v2/scripts/check-page-specs.mjs,
  site_v2/scripts/check-metric-labels.test.mjs and scripts/check_component_registry.py read the
  files changed here.
  deploy_order: none; no warehouse object changes.
  blast_radius: displayed words on every page in EN, DE and FI as the table lists them; no number
  and no metric definition changes.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - teams: #133
  - team: #134
  - player: #136

decisions_taken:
  - The term table, its calls and the correction on #243, approved in chat 2026-11-06.
  - Match titles take Versus in its short form, an en dash with spaces, and the Finnish upcoming match
    description opens with "Ottelu", #243 note 4185014476, approved in chat 2026-11-07.
  - NEW MECHANISM: scripts/check_copy_gate.py holds a list of texts the CPO approved as identical
    across languages, each with its locale, key, exact value and the #243 note that approved it;
    check 4 skips exactly that value and fails again when the text changes. Approved in chat,
    2026-11-09, starting with seoFixtureTitle in DE and FI and minutesShort in FI.
  - formIntro, formIntroPrev, playersIntro and playersIntroPrev read "jeder Mannschaft" in German,
    the article the table's word needs, approved in chat, 2026-11-09.
  - A warehouse-served key stays even where two now hold the same text (roundOf32, roundWcOf32):
    merging it needs a seed change and a fresh export, which this task does not make.

decisions_reserved:
  - none: the CPO approved the table and every open call on #243; a word not in the table goes to him.

acceptance_criteria:
  - The Standings head reads P, GD and Points in English, Sp., Diff. and Punkte in German, O, ME and Pisteet in Finnish.
  - The match header shows the points in full and the goal difference short in all three languages.
  - The line-up shows minutes as min, Min. and min.
  - A result row shows home or away as a full word in all three languages, and no row shows the letters H, A, K or V for it.
  - The German player row shows Vorlagen and Paraden, the Finnish player row shows Maalisyötöt.
  - The English menu shows Table, and the Finnish Team page shows Pelaajisto as the squad's name.
  - A player's position reads Forward, Midfielder, Defender or Goalkeeper, and its German and Finnish words, on every page.
  - No rendered page in any language shows a word the table retires.
  - The build fails when a text repeats a listed meaning with another word, or a component reads the wrong form.

done_when:
  - npm test in site_v2 passes, the new term test among them.
  - python scripts/check_component_registry.py passes.
  - python scripts/check_copy_gate.py passes.
  - pytest tests passes.
  - npm run build in site_v2 passes.

amendments:
  - Scope adds design-mocks/gen_top_players.py, design-mocks/gen_top_teams.py (they read the metric
    names) and tests/test_no_decision_history_in_code.py (its pin falls with the rewritten comments),
    approved in chat, 2026-11-09.
  - decisions_taken adds the copy gate's list of approved identical texts, approved in chat,
    2026-11-09.
  - Scope adds design-mocks/gen_team_mock.py (it reads the metric names),
    site_v2/src/styles/system.css (the table's Points column to 3rem) and
    docs/wireframes/09_chrome.md, docs/wireframes/02_team_profile.md,
    docs/wireframes/01_fixture_page.md, docs/metric_layer.md and docs/wireframes/metrics_display.md
    (their words and keys follow the term table), approved in chat, 2026-11-09.
