# Task contract — Home rotation, part C: the fallback intro copy

objective: >
  Issue #101, third of three merge requests. When no slot is in season, Home's Top players and
  Top teams show the last completed season, and the intro says so by naming the season instead of
  saying "this season's rankings". The page reads one optional key of landing.json,
  fallback_season, which part B of the export will write; until then the key is absent and the
  page reads exactly as it does today.

refs: >
  #101 (decision 2026-09-03 and its 2026-09-13 amendment: the fallback shows elite's last
  completed season). The copy and the split into three merge requests are the coordinator's
  rulings, 2026-11-23 and 2026-11-25. The sentences are in the MR head under "Core text,
  approved by the merge".

scope_paths:
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/components/home/TopPlayers.astro
  - site_v2/src/components/home/TopTeams.astro
  - site_v2/src/pages/*/index.astro
  - site_v2/src/specs/index.spec.json
  - site_v2/src/data/landing.json
  - .claude/task/101-rotation-c-fallback-copy/contract.md
  - .claude/task/101-rotation-c-fallback-copy/acceptance_evidence.md
  - .claude/task/101-rotation-c-fallback-copy/review.md
  - .claude/task/101-rotation-c-fallback-copy/review_input.patch

impact_map: >
  writers: none; the three i18n keys and one optional payload key are new. landing.json is in
  scope only so the fallback render can be shown on the dev server with a temporary
  fallback_season; it is restored and is not part of the diff.
  downstream: the two components are leaves. `grep` over site_v2 finds homeTopPlayersIntro and
  homeTopTeamsIntro only in strings.ts, the page spec index.spec.json and the two components, and
  the components only in pages/[lang]/index.astro. Nothing else renders them.
  layer_rules: the page composes served values and derives nothing; the season label is a served
  string. check-page-specs.mjs, check_copy_gate.py and check_ui_i18n_metrics.py apply.
  deploy_order: independent of the export. With the key absent the intros are unchanged, so this
  can merge before or after part B.
  blast_radius: none while landing.json has no fallback_season; with it, only the two intro
  sentences of the home page change, in EN, DE and FI.

acceptance_criteria:
  - With the landing payload in fallback mode, Home's Top players intro names the season the board shows, in EN, DE and FI, in the rendered text of /en/, /de/ and /fi/.
  - With the landing payload in fallback mode, Home's Top teams intro names the season the board shows, in EN, DE and FI.
  - With the payload in season (no fallback key), both intros read exactly the sentence they read today, in all three locales.
  - Both intros still name the leagues on the boards, in the order shown, in fallback and in season.

approved_design:
  - home: #127

depends_on:
  - none: the key is optional, so this needs no other merge request

shared_files:
  - none: no design baseline, component registry or font coverage file changes

decisions_taken: >
  The fallback intro is a second sentence per block and locale, naming the season and the leagues,
  ruled by the coordinator on 2026-11-23 and shown to the CPO in the MR head under "Core text,
  approved by the merge". The copy says "last completed season" and not "last season", because
  an ingest gap can leave the fallback older than the season before the current one. No new
  component, no new style, no recurring cost.

decisions_reserved:
  - none: the copy is core text approved by the merge, and nothing else is open.

done_when:
  - python scripts/check_copy_gate.py, check_ui_i18n_metrics.py and node site_v2/scripts/check-page-specs.mjs pass.
  - node --test in site_v2 passes.
  - python scripts/ci_local.py --mr is green, including validate:ui, apart from the known line-ending failure of tests/test_ci_local.py.
  - acceptance_evidence.md shows the in-season and the fallback intros rendered in EN, DE and FI.

amendments: (none)
