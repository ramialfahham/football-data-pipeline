# Task contract — metric labels come from the catalogue, per locale (#370 slice)

> Written on a clean tree before any file was touched. Branch `feat/370-metric-labels-from-catalogue`
> from `main` at `cc6cc45`. No protected path in scope, so no `protected_override`. `site_v2/` is the
> structural surface, so `impact_map` is required and present.

objective: >
  A stat's name is currently written down in FOUR places: the catalogue holds the i18n key but no
  translation, `metricRows.ts` hard-codes an English label, `strings.ts` hard-codes three more for the
  hero tiles, and the narrative sentence spells one out in prose. Nothing keeps them in step, and the
  German and Finnish pages show English stat names because the catalogue's keys resolve to nothing.

  This makes the catalogue's `label_i18n_key` real: one per-locale name per metric, read from one
  place by every page. It is the slice of #370 that unblocks composing narrative text from the
  semantic layer instead of hand-writing it per locale.

refs: >
  #370, the bullet "metric labels from `metric_catalogue` i18n keys (never hardcoded)" and only that
  bullet. The rest of #370 (hreflang, per-locale sitemaps, five new languages, locale-aware
  formatting, localised competition names) is explicitly NOT in this task.

scope_paths:
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/components/fixture/MetricRow.astro
  - site_v2/src/components/team/MetricLeagueRow.astro
  - site_v2/src/components/team/MetricSeasonRow.astro
  - site_v2/src/components/team/DeservedHero.astro
  - site_v2/src/styles/system.css
  - site_v2/src/specs/teams/team.spec.json
  - site_v2/src/specs/competition/matches/fixture.spec.json
  - site_v2/scripts/check-metric-labels.test.mjs
  - site_v2/scripts/check-page-specs.mjs
  - site_v2/scripts/check-page-specs.test.mjs
  - scripts/check_copy_gate.py
  - docs/wireframes/metrics_display.md
  - tests/test_governance_hooks.py
  - .claude/task/*.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/escalations.log
  - .claude/task/review_input.patch
  - .claude/active_work.md

acceptance_criteria:
  - Each stat name is written down once. `metricRows.ts` has no `label:` field, `heroSotFor`,
    `heroSotAgainst` and `heroSotDiff` are gone from `strings.ts`, and no stat name is spelled
    anywhere outside the one metric-label block.
  - A German reader sees German stat names. In the BUILT output the German hero tiles read
    `Ø Torschüsse`, `Ø Torschüsse gegen`, `Ø Torschussdifferenz`; the Finnish read
    `Ø Maalilaukaukset`, `Ø Maalilaukaukset vastaan`, `Ø Maalilaukauksien ero`; and the Performance
    rows differ per locale the same way.
  - If a name is ever missing, the page must not show gibberish. `t()` falls back to the key itself,
    so a gap would print the lookup code for a visitor to read. The built HTML contains zero
    occurrences of `metrics.`, and a test asserts every key resolves in all three locales.
  - Every name on the page belongs to a stat that really exists. A test cross-checks each key against
    `metric_catalogue.csv`, which is what catches the dangling `shots_on_target_per_match`.
    # Locked wording, kept verbatim. Its example is wrong — the catalogue DOES declare that key — and
    # only the CPO moves a locked criterion. He was asked and chose to leave it annotated.
  - The ten names the CPO already validated stay exactly as he wrote them. A test compares them
    against `site/i18n/*.json` so nothing approved is silently reworded while strings move.
  - The new names go through the same copy check as everything else. `scripts/check_copy_gate.py`
    reports a higher string count and applies its em dash, locale-completeness and terminology checks
    to the metric labels too.

impact_map: >
  writers: nothing writes these values at runtime. They are static per-locale strings in
    `site_v2/src/i18n/strings.ts`. The catalogue seed (`dbt_project/seeds/metric_catalogue.csv`)
    supplies `label_i18n_key`, `direction` and `format` and is NOT edited here. Every key the page
    uses is declared verbatim in the `label_i18n_key` COLUMN; none is invented.

  downstream: four render sites consume a metric name, enumerated from the tree rather than assumed —
    `components/fixture/MetricRow.astro`, `components/team/MetricLeagueRow.astro`,
    `MetricSeasonRow.astro`, and `components/team/DeservedHero.astro` (three `heroSot*` calls). All
    four already receive `lang` as a prop, so no prop threading is needed. `lib/metricRows.ts` is the
    LOCKED 16-row display contract read by `MetricComparison.astro` and `TeamPerformance.astro`; its
    `field`, `format`, `direction`, `group`, `tier`, `denom` and `sublabel` are untouched — only
    `label` leaves.

  layer_rules: no warehouse change, so `check_layer_contract.py` is unaffected. Selecting a string by
    key is selection, not derivation, so resolving a label per locale stays inside what the
    consumption layer may do. What it may NOT do is invent or restate a metric's meaning, which is
    exactly the duplication being removed.

  deploy_order: none. No warehouse, no migration, no export change; the payload is untouched. The
    build runs `npm test` via `prebuild`, so the new test gates the build itself rather than only CI.

  blast_radius: every metric name on the fixture page and both team-page tabs, in three locales — 18
    distinct keys across 19 render slots (`shots_on_target_per_match` is used twice: hero tile 1 and
    Performance row 6). Ten are CPO-validated strings that must not change and are test-pinned to
    `site/i18n/*.json`. What breaks if it is wrong: `t()` returns the KEY when a lookup misses, so a
    missed name renders `metrics.duels_per_match.label` as visible text on a public page. That failure
    is silent in review and loud to a reader, which is why criterion 3 greps the built HTML rather
    than trusting the diff.

decisions_taken: >
  CPO rulings on this task, one line each. **Full text with what was asked and what he answered is in
  `.claude/task/escalations.log`**, which survives this task; this contract does not.

  - The six acceptance criteria above: "All approved." Locked; only he moves them.
  - German metric names, supplied verbatim: `Torschüsse`, `Torschüsse gegen`, `Torschussdifferenz`.
  - Finnish, supplied verbatim: `maalilaukaukset`, `maalilaukaukset vastaan`, `maalilaukauksien ero`.
  - Eight further DE/FI names that were mine, plus two Finnish he had confirmed separately:
    "Approved, record it."
  - The overflow fix is styling, not shorter copy: "Change the styling."
  - `docs/wireframes/metrics_display.md` updated in this branch, not deferred: "Update it now."
  - Criterion 4's false example stays annotated rather than reworded: "Leave it, the note is enough."
  - The metric's name inside the hero prose sentences: "Yes, use my words."
  - The Finnish caption keeps its per-match basis and the `eron` inflection: "Put 'per match' back."
  - The two `axPlay` values and the German `heroCaption`: "Approve them."
  - The German rate word, chosen against my recommendation: `pro Spiel`.
  - Hero tiles stack on phones rather than breaking words mid-word: "Stack them on phones."
    The 560px threshold is a builder choice; he ruled the behaviour, not the number.
  - `.vs-row` mid-word breaks are filed, not fixed here: "Leave it filed, fix later" (#876).
  - Review rounds past the cap of 3, and finishing this branch: "yes and yes", then "finish 370".

  Builder judgement, recorded because it is visible in the design: the labels live in the i18n layer
  rather than a new seed, because the catalogue owns a metric's identity, direction and format while
  display copy does not belong in a warehouse seed. The structure is a dedicated per-metric map rather
  than flat dotted keys in the chrome dictionary, because a quoted dotted key is invisible to both
  `check_copy_gate.py`'s entry regex and `check-page-specs.mjs`'s key extraction — flat keys would
  have smuggled 54 strings past the copy check that criterion 6 requires.

decisions_reserved:
  - The narrative sentences themselves — shape, voice, rotation. This task is why #370 goes first:
    once labels resolve from the layer, a narrative can name a metric in any locale without a
    hand-written string. `heroVerdictUnder`/`Over` still hand-spell the name in all three locales and
    nothing mechanical keeps them in step with `METRIC_LABELS`.
  - `defensive_actions_per_match.sublabel` is still English in all three locales. It is a caption, not
    a name.
  - `YearOverYear.astro` renders three stat names from chrome strings and cannot be bound without a
    catalogue key that does not exist. Two of them are a second spelling of a name the new block owns.
  - Metric GROUP headings render in English on every DE/FI page that lists metrics, from two call
    sites. Where a group name should live is a schema question: **#875**, needs a CPO ruling.
  - Every other place a stat is named or abbreviated: **#877**, the single source for that set. Needs
    no ruling — it is ordinary display copy. Nothing in it was introduced by this branch.
  - The `-n` of `eron` in the Finnish `heroCaption` is a case ending I inferred, not the CPO's word.
    He approved it knowing that. Still unverified against a Finnish source.
  - EN `finishing_efficiency` has two approved names: v2's `% Goals per shot on target` and the MVP
    corpus's `% Conversion rate`. This task keeps v2's, which is why no English text changes.
  - Wiring `check_copy_gate.py` into CI: **#872**, blocked on the 16 copy findings, which are the CPO's.
  - Whether magnitude should change the narrative's wording, so 22 points reads differently from 4.
    Would need the tier to come from the mart; classifying the gap in the frontend is forbidden.

done_when:
  - `cd site_v2 && npm run build` passes, which runs `npm test` and `check-page-specs.mjs` via
    `prebuild`, so the new test gates the build.
  - Every acceptance criterion demonstrated in `.claude/task/acceptance_evidence.md`, read from
    `site_v2/dist/`, never from source and never from `outerHTML`.
  - `grep -rE "metrics\.[a-z_]+\.label" site_v2/dist` returns nothing.
  - `python scripts/check_copy_gate.py` reports a string count that includes the metric labels.
  - `python -m pytest tests/test_governance_hooks.py -q` green.

amendments:
  Scope additions, each with its authority. One line each.

  - `+ site_v2/scripts/check-page-specs.mjs`, `+ site_v2/src/specs/teams/team.spec.json` — the
    standing page-spec rule (#826/#844): a page declares its own surface. Found by the build gate,
    which refused the build because `team.spec.json` declared a key criterion 1 deletes.
  - `+ tests/test_governance_hooks.py`, `+ site_v2/scripts/check-page-specs.test.mjs` — the standing
    rule that new gate behaviour is pinned by a test that fails on revert.
  - `+ site_v2/src/styles/system.css`, `+ docs/wireframes/metrics_display.md` — CPO: "Change the
    styling" and "Update it now."
  - `+ site_v2/src/specs/competition/matches/fixture.spec.json` — same page-spec rule. `MetricRow`
    changed from `def.label` to `metricLabel()`, so the fixture page renders 16 names through the new
    key class and its spec declared none of them.
  - `+ .claude/task/escalations.log`, `+ .claude/task/review_input.patch` — both were already in the
    diff while excluded from declared scope. `escalations.log` is the durable record §11 requires;
    `.claude/task/*.md` does not match a `.patch` file.
  - Criterion 2 updated to the words the CPO chose after he revised all four himself, on his explicit
    yes. A later instruction supersedes an earlier one, but the record has to say so.
