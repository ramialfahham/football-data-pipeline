# Task contract — drop the home-page Browse section

objective: >
  Remove the home page's "Browse" block entirely (component, payload key, i18n, spec entry,
  export wiring) and correct every doc that describes it as current or shipping. Not a redesign,
  not a defer — a full drop, per CPO ruling this session.
refs: docs/wireframes/10_home.md §0/§5(2); .claude/active_work.md "⭐⭐ CURRENT" (Browse design
  history); GitLab issue #44 (the Browse redesign this decision supersedes/closes rather than
  implements); GAP-33 (Browse registry-direct-read gap — never filed, stays never-filed, see
  decisions_taken).

impact_map: >
  No dbt model/mart/seed DATA changes — zero warehouse blast radius, zero `dbt ls` needed. This
  is frontend + export-script + docs. Structural-surface trigger is `scripts/export_site_data.py`
  and `site_v2/**` in scope_paths, so this map is evidenced, not a placeholder:

  Consumers of the removed `browse` payload key / `BrowseGrid.astro`, verified by a full-repo
  grep sweep (36 files matched "browse", triaged individually): the ONLY runtime consumer is
  `site_v2/src/pages/[lang]/index.astro`'s `<BrowseGrid browse={data.browse} .../>`. No other
  page or component imports `BrowseGrid.astro` or reads `.browse` off the landing payload.
  `types.ts`'s `Landing.browse` field and the `BrowseCompetition`/`LandingBrowse` interfaces have
  zero other consumers (grep-confirmed).

  `shape_landing_payload(upcoming, browse)` is called from exactly one place,
  `fetch_landing_payload` (export_site_data.py:1248), itself invoked only from the
  `"landing" in entities` branch of `export_all`. `tests/test_export_landing.py` asserts the
  current 3-key shape (`type`/`upcoming`/`browse`) and constructs a `browse={...}` fixture — both
  need updating in lockstep or the suite goes red.

  `build_nav()`/`fetch_nav()` is NOT scoped for removal: confirmed it independently produces
  `nav.json` via its own `--entities nav` dispatch branch (export_site_data.py:1355-1359),
  unconnected to the landing entity. Zero site_v2 frontend file currently reads `nav.json` either
  way (grep-confirmed) — flagged in decisions_reserved rather than removed, since deleting a
  distinct export target is a bigger call than dropping one page's block.

  `dbt_project/seeds/schema.yml`'s `display_group` column docs its only consumer as `build_nav()`
  "feeding the home page's browse chips" (schema.yml:36). Since build_nav/nav.json stay,
  display_group keeps a real (reduced) consumer — only that doc's specific claim needs
  correcting, not the column's pre-existing SLATED FOR DELETION status (CPO 2026-08-11, #57),
  which stays open pending the nav.json question above.

  Grep triage result: 15 of the 36 matched files are genuinely about this block (in scope_paths
  below); the rest are the unrelated English word ("browser"), the still-live, separately-specced
  competitions-index page (`docs/wireframes/08_browse.md`'s own content, `/competitions/`), or
  pre-existing staleness in `docs/north_star.md` / `docs/ui_design_brief.md` /
  `docs/content_architecture.md` / `CLAUDE.md`'s "hybrid browse" IA line predating this change —
  deliberately left untouched (scope discipline), see decisions_reserved.

  Blast radius: zero BigQuery/warehouse impact. Site build output changes: home page loses one
  block; `landing.json` loses one top-level key. No other page's payload or component is affected.

scope_paths:
  - site_v2/src/components/home/BrowseGrid.astro
  - site_v2/src/pages/*/index.astro
  - site_v2/src/specs/index.spec.json
  - site_v2/src/lib/types.ts
  - site_v2/src/i18n/strings.ts
  - scripts/export_site_data.py
  - site_v2/src/data/landing.json
  - tests/test_export_landing.py
  - docs/wireframes/10_home.md
  - site_v2/src/specs/competitions/index.spec.json
  - site_v2/src/components/competitions/CompetitionIndexGrid.astro
  - dbt_project/seeds/schema.yml
  - docs/site_architecture.md
  - docs/wireframes/08_browse.md
  - .claude/active_work.md
  - .claude/task/escalations.log
  - .claude/task/rendered_page_evidence.md
  - site_v2/src/data/README.md
  - docs/wireframes/99_gaps_register.md
  - site_v2/src/config/indexability.mjs
  - site_v2/src/styles/system.css
  - site_v2/src/specs/page-spec.schema.json
  - site_v2/scripts/check-page-specs.mjs
  - site_v2/scripts/check-page-specs.test.mjs
  - CLAUDE.md
  - docs/north_star.md
  - docs/ui_design_brief.md
  - docs/content_architecture.md
  - dbt_project/models/5_marts/shared/mart_competition_index.sql

decisions_taken: >
  CPO, this session, in chat, verbatim: "stop" / "drop the browse section".

  Context immediately preceding that instruction, same session: Browse's previously-converged
  design (one mart unioning competitions+teams+players, chips on every page — active_work.md
  "⭐⭐ CURRENT", GAP-33 deliberately never filed because that redesign was to replace the block's
  data source entirely) was already blocked on the team-name and player-name data-quality work.
  When I narrowed scope to competitions-only (CPO: "let's skip teams as well", following "two
  different marts for browse is not smart"), checking the actual site IA (docs/site_architecture.md's
  nav line, `site_v2/src/pages` contents) showed the competitions pool is small enough that the
  existing competitions index page already fully covers it — Browse's only remaining justification
  (reachability into the long-tail team/player pages, ~9,669 teams / ~154,767 players) applies
  exactly to the two entity types already deferred. CPO agreed and ordered the block dropped
  outright rather than shipped competitions-only or left designed-but-unbuilt.

decisions_reserved:
  - Whether `build_nav()`/`fetch_nav()`/the standalone `nav.json` export target should also be
    removed, now that `landing.json` (its only current consumer) no longer uses it. Kept as-is
    this task — see impact_map. It is a distinct, independently-selectable export target, not
    literally "the browse section", and removing it risks breaking an invocation outside this
    task's visibility (CI/runbook). Flagged as a follow-up, not answered here.
  - ~~Whether to also correct the pre-existing Browse/composition staleness in
    `docs/north_star.md`, `docs/ui_design_brief.md`, `docs/content_architecture.md` and
    `CLAUDE.md`.~~ **ANSWERED by the CPO, in chat, 2026-08-19** (see the 5th amendment): "if there
    is no browse section anymore, we should not have any references to it as well nowhere." All
    four are now IN scope and corrected. No longer reserved.

acceptance_criteria:
  - `/{locale}/` (home page) renders Next matches only — no Browse block, no dead chips, no
    visual gap or layout regression in the space it occupied.
  - `landing.json` payload carries exactly `{type, upcoming}` — no `browse` key.
  - `astro build` (site_v2) succeeds with zero errors/warnings introduced by this change.
  - `pytest tests/test_export_landing.py` passes against the updated `shape_landing_payload`
    signature.
  - No remaining reference to the deleted `BrowseGrid.astro` anywhere in the repo (full grep
    sweep clean) — every mention either removed or rephrased to not cite a deleted file.
  - `nav.json` (`--entities nav`) still produces output, unaffected by this change — confirms
    `build_nav`/`fetch_nav` were left alone.
  - No surviving claim anywhere in the repo that Browse still exists, ships or feeds the home page,
    whether or not the passage uses the word "browse" (CPO ruling, 2026-08-19). The two kept
    categories are the struck-through record of the decision itself, and `08_browse.md`/the
    competitions index page, which are live and merely share the word.

  ⚠ FORMAT: these must be `- ` bullets. They were a NUMBERED list until the commit gate rejected
  the commit reading "the contract declares no acceptance_criteria" — `_bullets()` in
  git_discipline.py matches `^\s*-\s+` only, so a numbered list parses as ZERO criteria and the
  gate cannot tell that from an empty block. Same class as the already-recorded
  "acceptance_evidence.md bullets must be indented 2sp" trap in CLAUDE.md.

done_when:
  - Every file in scope_paths edited per the above; BrowseGrid.astro deleted.
  - Full-repo grep for "BrowseGrid" returns zero hits.
  - `pytest tests/test_export_landing.py -q` passes.
  - `npm run build` (or equivalent) in site_v2/ succeeds.
  - Dev-server preview confirms the rendered home page shows Next matches only.
  - Committed on this branch; MR opened by the post-commit hook.

amendments:
  - 2026-08-19: + `.claude/task/rendered_page_evidence.md`, `site_v2/src/data/README.md`,
    `docs/wireframes/99_gaps_register.md` — authority: bi-analyst-reviewer round-1 FAIL, three
    findings: (1) `rendered_page_evidence.md` on disk belonged to an unrelated prior branch, no
    real evidence for THIS diff's visual-regression claim (acceptance_criteria #1); (2)
    `site_v2/src/data/README.md`'s description of `landing.json` still claimed "the full registry
    browse axes", now false; (3) `docs/wireframes/99_gaps_register.md` GAP-04's withdrawal note
    still asserted the four-module composition in present tense — mis-triaged earlier this task as
    harmless historical record when it's actually a live, newly-false claim this task's own change
    caused, not pre-existing drift. All three now in scope_paths; fixes follow in this same round.
  - 2026-08-19: + `site_v2/src/config/indexability.mjs`, `site_v2/src/styles/system.css` —
    authority: bi-analyst-reviewer round-2 FAIL, two more files in the same defect class (a
    present-tense claim that Browse still exists, invalidated by this task's own change, missed by
    the round-1 triage despite `indexability.mjs` having been read in full during discovery).
    `indexability.mjs`'s `STUB_PAGES` comment claims "TWO content blocks — next matches and
    browse" and "the CPO's composition is ... browse" — both false. `system.css`'s `.subhead` rule
    is now dead CSS (zero consumers anywhere in `site_v2/src`, confirmed by grep — its only user
    was the deleted component) and its comment still justifies it by the deleted block;
    `.linkchip:hover`'s comment cites browse as one of three current inert-chip consumers, but
    `.linkchip` itself stays live for the team page and links footer — only the browse mention is
    wrong.
  - 2026-08-19: + `site_v2/src/specs/page-spec.schema.json`, `site_v2/scripts/check-page-specs.mjs`
    — authority: bi-analyst-reviewer round-3 FAIL, same defect class again. `page-spec.schema.json`'s
    `mart` property description asserts, present tense, "the home page's browse block reads the
    competition registry" as live justification for the `registry` source type — false now, and
    the reviewer confirmed the `registry` type has zero actual consumers left anywhere under
    `site_v2/src/specs/**`. `check-page-specs.mjs` carries near-identical wording for the same
    ruling (same CPO date, same "browse block reads the COMPETITION REGISTRY" claim) — not
    independently flagged by any reviewer yet, but the same present-tense defect, fixed
    proactively rather than waiting for a round-4 finding on the twin instance (the lesson
    `10_home.md`'s own header states: fixing one reported instance at a time instead of sweeping
    the class is what cost that document five review rounds).
  - 2026-08-19: + `site_v2/scripts/check-page-specs.test.mjs`, `CLAUDE.md`, `docs/north_star.md`,
    `docs/ui_design_brief.md`, `docs/content_architecture.md` — authority: CPO, in chat, ruling on
    the whole class rather than the next instance: *"if there is no browse section anymore, we
    should not have any references to it as well nowhere. right?"* That overturns this contract's
    own `decisions_reserved` entry (which had parked the four docs as pre-existing drift) and
    closes the bi-analyst-reviewer round-4 FAIL (`check-page-specs.test.mjs:194`) in the same
    sweep. The CPO's stated reason is the root cause, not the instance: *"there seems to be
    something wrong if 'browse' is spammed in multiple documents ... you spam things all around
    the repo and then forget to clean up. and then we have contradictions in our docs and files."*
    This session is a fresh instance of the duplication class GitLab **#71** already tracks — four
    review rounds, each finding one more copy of the same fact. Two categories stay, deliberately,
    and are NOT "references to Browse": (1) the struck-through RECORD that it was dropped and why
    (`10_home.md`, `escalations.log`, `active_work.md`) — deleting the decision trail is how the
    same idea gets re-proposed in six months; (2) `08_browse.md` and the competitions index page,
    which are live and unaffected and merely share the word.
  - 2026-08-19: + `dbt_project/models/5_marts/shared/mart_competition_index.sql` — authority:
    analytics-engineer-reviewer round-5 FAIL. Its header comment said `sort_order` "is still live
    on the home page", true until this branch removed the block that made it so. **This is the
    most important finding of the task and the reason the earlier sweeps kept missing things: it
    does not contain the word "browse" at all.** Every sweep up to round 4 grepped the literal
    word — exactly the paraphrase-evasion already on record in memory
    (`feedback_corrections_replace`: "a literal-phrase grep will not find the other copies").
    Round 5's sweep was therefore redone SEMANTICALLY: searching for CLAIMS about what feeds the
    home page (`still live|consumed by|feeds the|renders the` near `home|landing`) and for the
    machinery identifiers (`display_group`, `build_nav`, `nav.json`, `_GROUP_ORDER`,
    `_DOMESTIC_TYPES`, `linkchip`, `country hub`) rather than for the feature's name. That sweep
    also found, and this amendment covers, three more in files ALREADY in scope:
    `docs/site_architecture.md` §8's decisions-log row (still "locked"), `CLAUDE.md`'s
    `display_group` note (which owed its unblocking to #44, the now-moot browse redesign), and
    `.claude/active_work.md`'s "Verified state reference" bullet (asserted the built home page is
    "next matches → browse"; its component count was re-MEASURED at 28 rather than adjusted by
    arithmetic, per #904).
