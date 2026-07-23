# Task contract — team page, Overview tab, from the approved mock

> Written on a CLEAN tree (branch `feat/team-page-overview` off main @ 3d6a31a).

objective: >
  Build the team page Overview tab (the next launch item, Pages group), from CPO-approved mock
  `f6348775`, as one data-backed increment like the fixture page (#672). Its signature block,
  deserved-vs-actual, is the corrected POINTS scatter: points won regressed on shots-on-target
  difference per match, the trend line is the model's `deserved_points`, a team's height off the line
  is `sot_points_gap`. The CPO approved this corrected hero as a rendered picture this session. The
  broken rank-space version (which the mock still drew) is replaced. Performance and Squad tabs are
  chrome + honest coming-state; their data binding is a follow-up.

refs: >
  Verified this session:
  - Fixture-page pattern: `site_v2/src/pages/[lang]/[competition]/matches/[fixture].astro` composes
    shared components, imports a committed sample JSON, holds no styling, derives no facts.
  - `scripts/export_site_data.py` `shape_team_payload` (line 163) already emits each season's
    `deserved_points`, `sot_points_gap`, `sot_difference_per_match`, `points`, `latest_rank`. It does
    NOT emit the league-level scatter context the hero needs.
  - `mart_team_profile` carries `deserved_points` (the fit) for every team in a domestic single-ladder
    league-season; the export only SELECTs and groups it (no derivation).
  - Preserved components on `origin/feat/site-v2-team-profile` (TeamHeader, RecordBlock, YearOverYear,
    TeamFixtures) — harvest material, reconciled to the mock.
  - The mock `f6348775` full HTML/CSS was fetched this session (tool-results dir) — the design source.

scope_paths:
  - scripts/export_site_data.py
  - site_v2/src/pages/[lang]/teams/
  - site_v2/src/components/team/
  - site_v2/src/styles/system.css
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - site_v2/src/data/teams/
  - site_v2/src/data/competitions.json
  - tests/test_export_site_data.py
  - .claude/active_work.md

impact_map: >
  writers: none in the warehouse. The export READS `mart_team_profile` (+ mart_team_fixtures for the
    fixtures block) and writes JSON; no dbt model, no table, no mart changes. The dbt layer is
    untouched.
  downstream: consumption + frontend only. `shape_team_payload` gains a `deserved_scatter` field per
    season; the committed sample and the built page consume it. No other export consumer reads teams
    yet (grep: only the team page). The site build is static (Astro getStaticPaths); nothing is
    deployed (no hosting chosen), so there is no runtime blast radius.
  layer_rules: the consumption-layer contract (Appendix A5) — the export may select/group/rename but
    NEVER derive a fact. `deserved_scatter` is a pure projection of mart rows the model already
    computed; the fitted line params come from the mart's own `deserved_points`, not re-fitted here.
    The frontend derives no facts (maps numbers to SVG coordinates only). `check_layer_contract.py`
    does not gate the export or site, but the reviewers do.
  deploy_order: none. No warehouse object; static site. Takes effect only when the page is built.
  blast_radius: bounded. The export change adds a field (additive, no existing consumer breaks). The
    site adds one new page + team components + team CSS blocks; the fixture page and shared system are
    untouched except APPENDING team blocks to system.css. The committed sample is one team, produced
    by the updated export, so the #805 binding rule (every rendered field exists in the export) is
    satisfied by construction — this page is that rule's first real test.

decisions_taken: >
  (1) BUILD THE APPROVED MOCK, Overview tab, points-scatter hero. CPO approved the plan
      (ExitPlanMode, 2026-07-22) and the corrected hero as a rendered picture the same session.
  (2) Overview tab only; Performance + Squad are honest coming-state, their data binding deferred.
      An increment sized like the fixture page, stated in the approved plan.
  (3) Add `deserved_scatter` to the team payload rather than a separate league file — the page is
      per-team and it keeps one import. Engineering call, not §10.

decisions_reserved:
  - The exact sample team is an implementation pick (a Premier League team with a visible gap so the
    hero demonstrates the block); not a product decision.
  - Whether to amend the wireframe spec `02_team_profile.md` (which still describes the OLD
    shot_share/points_capture hero) is a separate doc task, NOT in this scope. Noted so a reviewer
    does not read the stale spec as the contract.
  - The `metricRows.ts` 16-row Performance binding and the Squad roster binding are the next PRs.

done_when:
  - The export emits `deserved_scatter` per domestic single-ladder season; a test asserts its shape
    and that the self dot's `deserved_points` equals `intercept + slope*sotd`.
  - The committed sample `data/teams/{id}.json` is exactly what the updated export produces for that
    team (binding rule).
  - The team page renders in de/en/fi: identity + record + the points-scatter hero (trend line + self
    dot + gap) + vs-last-season + fixtures, with Performance/Squad as coming-state. Verified in the
    dev server with a screenshot.
  - The hero renders its absent state (never a broken scatter) when `deserved_points` is null.
  - `validate-local` passes (astro check + lint); `pytest tests/test_export_site_data.py` passes.
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments:
  - 2026-07-23 (glob-safe scope correction, no scope expansion): the contract gate
    matches scope_paths with `fnmatch`, which reads the bracketed Astro route
    `site_v2/src/pages/[lang]/teams/[team].astro` as glob character classes ([lang] =
    one of l/a/n/g), so the already-in-scope file never matched literally and its own
    page could not be written. Replaced that one file entry with the directory-prefix
    form `site_v2/src/pages/[lang]/teams/` (matched by literal `startswith`), which
    covers the same single route file and nothing more. The page was CPO-approved in
    the plan (ExitPlanMode 2026-07-22) and already listed in the original scope_paths;
    this only fixes how the matcher reads it.
