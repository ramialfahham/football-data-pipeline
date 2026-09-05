# Task contract — navigation rules, and Next matches applying them

objective: >
  Settle the site's navigation rule once — which element types are clickable and what each
  points at — write it into the authoritative IA doc as a PROVISIONAL standard, and apply it to
  the one block it was worked out against: Next matches. The competition heading becomes a real
  link, which requires a near-empty competition page for it to land on.
refs: >
  #52 (interaction standard — "which elements redirect where", open since 2026-08-10, never
  decided); #47 (the competition page's real content, NOT this task); plan
  C:/Users/Rami/.claude/plans/unified-seeking-waffle.md, CPO-approved 2026-09-04.

scope_paths:
  - docs/site_architecture.md
  - site_v2/src/specs/competition/index.spec.json
  - site_v2/src/pages/*/*/index.astro
  - site_v2/src/config/indexability.mjs
  - site_v2/src/i18n/strings.ts
  - site_v2/src/styles/system.css
  - site_v2/src/components/home/HeroFixtures.astro
  - site_v2/src/data/competition_index.json
  - .gitignore
  - site_v2/scripts/audit-seo.mjs
  - site_v2/scripts/audit-seo.test.mjs
  - .claude/task/escalations.log
  - .claude/task/rendered_page_evidence.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review_input.patch

impact_map: >
  writers: NONE. No dbt model, no ingestion loader and no export script is in scope.
    `grep -c "dbt_project/models" scope_paths` = 0. The warehouse is untouched, so there is no
    deploy ordering against the 04:00 nightly and no shared-warehouse migration.
  downstream: the EMITTED site only. `site_v2/src/pages/*/*/index.astro` adds a route; nothing
    imports a page. `system.css` is imported globally by `layouts/Layout.astro`, so a CSS change
    reaches every page — the addition is a NEW class selector (`.gh a` heading-link affordance),
    additive, and overrides nothing existing. `strings.ts` gains two keys per locale; every
    existing key is untouched. `indexability.mjs` has four readers (astro.config.mjs,
    Layout.astro, robots.txt.ts, audit-seo.mjs) and only `STUB_PAGES` changes, which is read by
    the audit alone.
  layer_rules: `check_layer_contract.py` governs dbt layers and is not engaged (no models).
    Consumption layer: select and filter served values, never derive facts. The shell derives
    nothing. Its source is a mart per `content_architecture.md` §2 rule 2 ("one block = one
    mart") — `competition_index.json`, from `mart_competition_index`, the same payload the
    competitions index page reads. ⚠ Route enumeration only: this shell has no blocks, and #47
    binds the hub's CONTENT to `competitions/{league_code}/{season}.json` per
    `site_architecture.md` §5.
  deploy_order: none. Frontend-only; `deploy:site-v2` is manual-only and unaffected.
  blast_radius: one newly emitted page per competition per locale, every one `noindex` while
    `INDEXABLE === false`, plus one changed element on the home page in 3 locales. No number on
    any page changes.
    ⚠ The count is a FORMULA, never a constant —
    `count(competition_index.json rows) x count(locales)`. Today that is 48 x 3 = 144
    (`python -c "import json;print(len(json.load(open('site_v2/src/data/competition_index.json'))['competitions']))"`),
    but the registry grows: a competition added to `docs/competition_registry.yml` must produce
    its page with NO code change, the frontend counterpart of the repo's no-new-model rule. The
    route therefore iterates the served map and never a literal list, and the spec's
    `page_count_driver` states the formula.

acceptance_criteria:
  - The navigation rule is written in `docs/site_architecture.md` and names all three families
    (chrome, content links, controls) and the four content-link shapes (row, heading, chip,
    prose), and states in the CPO's own terms that it is provisional. Shown by quoting the
    committed section.
  - The rule states the row half explicitly: a row links to its subject and nothing inside a row
    is separately clickable. Shown by quoting it.
  - On the built home page, the competition heading in Next matches is an `<a>` whose href is
    the competition's own URL, in all three locales. Shown from `dist/` html, not from source.
  - The heading link's affordance (a chevron) is present AT REST, not only on hover. Shown from
    the emitted markup plus the CSS rule that renders it.
  - A match row in Next matches remains a single link with no nested anchor inside it. Shown by
    counting `<a` inside one emitted `.fxrow`.
  - Every competition URL the home page links to is emitted by the build. Shown by a green
    `audit-seo.mjs`, whose check 8 fails the build on a link resolving to no emitted page.
  - The route is driven by the MART payload (`competition_index.json`, from
    `mart_competition_index`), not by a literal list and not by the registry map, so a competition
    added to the registry flows registry → mart → page with no code change. Shown by the spec's
    `page_count_driver` being a formula, by the page importing `competition_index.json`, and by
    `grep` finding no league_code or slug literal in the page source.
  - The three locales' competition pages emit non-identical `<title>` values. Shown by a green
    audit (check 6) plus the three emitted titles for one competition.
  - `STUB_PAGES` lists the competition page, and the audit still refuses `INDEXABLE === true`
    while it is non-empty. Shown by the committed array and the audit's own assertion.

decisions_taken: >
  ⭐ **THE RECORD IS `.claude/task/escalations.log`, entry `2026-09-04 —
  feat/navigation-rules-competition-shell — THE NAVIGATION RULE`.** Four rulings are there with the
  CPO's words verbatim and the consequence each one had on what was built:
  · **Ruling 1** — the navigation rule is PROVISIONAL ("the rules might be subject to change. We
    have not built every page yet"), and the header+row half is confirmed for Next matches and for
    any future header+row structure. Hence §3, not §2 where locked constraints live.
  · **Ruling 2** — a destination that does not exist yet is BUILT, not routed around. ⚠ Already
    written in `docs/wireframes/10_home.md` §0, which records that he had corrected me on it twice
    before; raising it a third time was the defect, not the question.
  · **Ruling 3** — the split. This branch is the rule + Next matches + the scaffold; #40 and #41
    need their own plan.
  · **Ruling 4** — deviating from dbt's structure is fine where the repo explains why, and
    otherwise stay close to dbt. A STANDING answer, not a one-branch one.
  ⛔ An earlier version of this block asserted those quotes here with NO log entry behind them, and
  `scope-auditor` failed round 1 for exactly that: unverifiable prose standing in for the record
  §11 requires. The quotes were real; the record was missing. Written now, and cited from here
  rather than restated.

  THRESHOLD DECLARATIONS: no new mechanism — `STUB_PAGES` already exists and this is its
  documented purpose ("Adding an entry here is how a future scaffold ships honestly"). No new
  dependency. No recurring cost: the build emits 144 more static pages, which is build-time only;
  nothing is scheduled, queried or billed. No guard is loosened — `STUB_PAGES` becoming non-empty
  TIGHTENS the go-live gate, since the audit refuses `INDEXABLE === true` while it holds entries.

decisions_reserved:
  - Whether the navigation rules graduate from provisional to locked, and when. The CPO said
    explicitly we do not know yet because not every page is built. Never decide this here.
  - Whether the competitions index page's 48 inert rows get wired to the new shell. It is the
    same rule applied to a second surface and it is now unblocked, but the CPO scoped this task
    to the rule plus Next matches. Raise it; do not fold it in.
  - The competition page's real content, tabs and blocks — #47. This task ships a shell with no
    content blocks and must not design one.
  - Whether a stub for EVERY competition in the registry is right, versus only those with enough
    data. §2's locked "no thin pages" constraint and #845's minimum-data gate both bear on it; a
    stub is a thin page by definition, which is why STUB_PAGES blocks go-live. ⚠ Whatever is
    decided must stay a RULE over the served registry, never a hand-kept list — the CPO,
    2026-09-04: "We have 48 competitions NOW. We will add more, so we should [have] something
    that is prepared for it anytime." Flagged, not decided.

done_when:
  - `python scripts/check_copy_gate.py` passes (no em dashes; no non-EN value byte-identical
    to EN) with the two new SEO keys present in all three locales.
  - `node site_v2/scripts/check-page-specs.mjs` passes: the new spec parses, its `stub: true`
    waives the blocks requirement, and every i18n key it names exists in the EN dict.
  - `npm run build` in `site_v2` succeeds after `git clean -fX site_v2/src/data`, and
    `audit-seo.mjs` reports zero issues — specifically no "dead internal link" (check 8) and no
    byte-identical title across locales (check 6).
  - `npm test` in `site_v2` passes.
  - The `validate-local` skill passes (governance, UI, secrets, python).
  - Browser pane at desktop and 375px: the accessibility tree shows the heading as a link with
    its chevron, and one `.fxrow` containing exactly one anchor.

amendments: >
  2026-09-04 — `site_v2/src/data/competition_index.json` and `.gitignore` ADDED to scope_paths.
  Authority: mine, on a mechanical dependency, not a design decision. This branch was blocked
  because two competitions rendered byte-identical titles; `!150` fixed that in the warehouse and
  is merged, and prod rebuilt (`data:build:main`, verified against `mart_competition_index` rather
  than trusted from the green job). The committed payload still holds the pre-fix names, so the
  branch cannot go green until it is re-exported — the file is a build INPUT this task must
  refresh, not a surface it redesigns. `.gitignore` rides along only if the tracked-file allowlist
  moves with it. No name, no design and no page behaviour is decided here; the export is rerun
  verbatim per `site_v2/src/data/README.md` and never hand-edited.

  2026-09-04 — `site_v2/scripts/audit-seo.mjs` and its test ADDED to scope_paths. Authority: mine,
  on a defect this task EXPOSED rather than caused. `audit-seo.mjs:438` picks a page's spec with
  `specs.find((s) => s.match.test(p))` — the FIRST match, with no specificity rule — and
  `specRouteRegex` turns every `[param]` segment into `[^/]+`. So `[lang]/[competition]/index.astro`
  matches `/en/competitions/` and the competitions INDEX gets judged against the competition HUB's
  spec, demanding `SportsOrganization` of a page that correctly emits `ItemList`. Astro itself
  routes correctly; only the audit is ambiguous.
  ⚠ This is not specific to my route: ANY top-level dynamic route collides with any sibling
  literal one, so the fix is a specificity rule (most literal segments wins), not an exemption for
  this page. Reported by the build, three violations, one per locale.
  ⚠ **Adds `platform-reviewer` to the required reviewer set** (`review_routing.json` maps
  `site_v2/scripts/**` to it), which is a consequence to declare rather than discover at commit.

  2026-09-04 — `.claude/task/escalations.log` ADDED to scope_paths, on `scope-auditor`'s round-1
  FAIL. Authority: `docs/working_agreement.md` §11, which the reviewer quoted — *"Every escalation
  is appended to `.claude/task/escalations.log` (committed with the branch)"*. `decisions_taken`
  cited three CPO chat quotes that appear nowhere in the log, so a reviewer had no way to check
  them and the working agreement's own record was simply missing. The rulings are real; the record
  was not written.
  ⚠ **This is NOT the same fix as the sibling branch's.** There, the principles I was citing him
  for were ALREADY documented (`layering.md`, the seed docs, #55), so the answer was to cite those
  and stop invoking him. Here the navigation standard is genuinely new — nothing in the repo
  states it — so the answer is the opposite: write the ruling into the log where §11 puts it.
  Distinguishing the two cases is the whole lesson: "cite the record" and "create the record" are
  different remedies for the same symptom.

  2026-09-04 — `.claude/task/rendered_page_evidence.md` ADDED to scope_paths, on
  `bi-analyst-reviewer`'s round-1 FAIL. Authority: mine, and the finding was plainly right. The
  file on disk documented a DIFFERENT branch (`chore/roll-forward-sample`, fixture-page metric
  labels) and said nothing about this diff — which its brief treats as equivalent to the artifact
  being absent, and absence on a rendering-affecting `site_v2/src/**` change is itself a FAIL.
  ⛔ It also caught that this contract's own `done_when` demanded a check "at desktop and 375px"
  and I had only ever looked at desktop. Doing it found a REAL defect the desktop pass could not:
  the heading link measured **100x21** at 375px, under the 24x24 CSS-px minimum target size and a
  third the height of the 81px match row beside it. Fixed in `system.css` with a padding /
  negative-margin pair (33px hit area, text position unchanged, verified by screenshot).
  ⭐ The mobile check was in `done_when` from the start. Skipping it and writing the evidence file
  anyway would have shipped a real accessibility defect behind a green build.

  2026-09-04 — `platform-reviewer` round-1 FAIL accepted; no scope change needed (both files were
  already in scope). It proved the tie branch of `specForPath` was untested — mutating `>` to `>=`
  turned ZERO tests red — and that the code silently resolved an equal-specificity overlap by
  walk order while its own comment called that "a spec-authoring bug, not something to paper
  over". A gate wired into `astro build` must fail CLOSED. `specTie()` added, reported as a build
  issue, with the reviewer's own counterexample (`[lang]/foo/[b]/[c]` vs `[lang]/[a]/bar/[c]`,
  both specificity 1, both matching `/en/foo/bar/x/`) kept verbatim as the test fixture.
  Mutation-tested: making `specTie` always return `[]` turns exactly that one test red.
