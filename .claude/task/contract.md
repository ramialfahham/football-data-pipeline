# Task contract — #40 MR B: the Top players block on the Home page

objective: >
  Ship the Home page's Top players block (GitLab #40, MR B — the frontend half; the warehouse half
  shipped in !153). Four boards (Goals, Assists, Passes, Key passes), one player per league across
  the seven `elite` leagues, top 7, board names resolved from the metric catalogue, a board with no
  data omitted entirely. The work was written and parked in stash `TEMP-40-mrB`; this task pops it,
  fixes one defect found in it, wires it into `index.astro`, and builds the player page scaffold the
  block's row links require.
refs: >
  GitLab #40 (design authority; its issue body is STALE — the pooled ranking was withdrawn
  2026-08-18 for one player per league, and page length is not open).
  `docs/wireframes/10_home.md` §0 (the CPO's block composition), `docs/metric_layer.md` (read before
  touching a metric; the catalogue seed is the only source of a metric's label),
  `docs/site_architecture.md`:51 + :93-95 (the reserved `/{locale}/players/{slug}/` URL and the
  player slug rule). Precedent for the stub: `!151` (merge `448ef77`), the competition page shell.
  Approved plan: `C:\Users\Rami\.claude\plans\snoopy-rolling-penguin.md`.

scope_paths:
  - scripts/export_site_data.py
  - scripts/check_copy_gate.py
  - tests/test_export_landing.py
  - tests/test_governance_hooks.py
  - site_v2/src/components/home/TopPlayers.astro
  - site_v2/src/pages/*/index.astro
  - site_v2/src/pages/*/players/*.astro
  - site_v2/src/specs/index.spec.json
  - site_v2/src/specs/players/*.spec.json
  - site_v2/src/config/indexability.mjs
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/styles/system.css
  - site_v2/src/data/landing.json
  - site_v2/src/data/README.md
  - site_v2/scripts/check-metric-labels.test.mjs
  - site_v2/scripts/check-page-specs.mjs
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: NO dbt model, seed, macro or test is in scope. `mart_leaderboards` is READ by the export
    and is not modified; it is written only by the nightly `data:build:main` / `fdp-nightly` build
    from `int_player_season__metrics` + `dim_player` + `dim_team`.

  downstream: `mart_leaderboards` is a LEAF. Evidence, run in this session
    (`.venv/Scripts/dbt.exe ls --select mart_leaderboards+`, dbt 1.7.19 / bigquery 1.7.2,
    DBT_PROFILES_DIR pointed at a scratchpad profile with a `dev`/`dev_scratch` target only —
    `~/.dbt/profiles.yml` on this machine holds ANOTHER project's `dbt_analytics` profile and was
    not touched):
      `--resource-type model` -> football_data_pipeline.5_marts.shared.mart_leaderboards   (itself, only)
      `--resource-type all`   -> 27 nodes = the model + 26 tests, ZERO downstream models
    Among those tests: `assert_mart_leaderboards_every_home_board_has_a_leader` (the board-vanished
    guard this block depends on, shipped in !153), `assert_one_current_season_per_league`,
    `not_null_mart_leaderboards_is_current_season`, `mart_leaderboards_rank_in_range`.

  layer_rules: `check_layer_contract.py` is not engaged — no `dbt_project/models/**` path is in
    scope, so no staging/base materialisation or per-competition-subdirectory rule applies. The
    consumption-layer contract DOES apply: `scripts/export_site_data.py` may select, filter, group
    and rename, never derive a fact. The one behavioural change (per-league dedupe) is SELECTION
    among rows the mart already ranked — it computes no ranking and no metric.

  deploy_order: THIS BRANCH DEPENDS ON MR A AND THAT DEPENDENCY IS ALREADY SATISFIED. `!164` merged
    as `943c9f2`, `data:build:main` ran green (9m49s) and recreated the view, and the column was
    then confirmed live by querying prod: 28 rows carry `league_leader_order = 1` across the four
    Home boards and seven elite leagues, which is exactly one per league-board. Nothing else is
    owed: `mart_leaderboards` is a VIEW, so there was no table rebuild and none of the three
    incremental facts was touched. Nothing in the warehouse changes in THIS branch.
    `site_v2/src/data/landing.json` is a COMMITTED build input (`deploy:export` regenerates only
    `--entities teams,fixtures`), so the payload lands in this commit and the site build is
    self-contained.

  blast_radius: NO mart, model or number changes. What changes: (1) `landing.json` gains a
    `top_players` key; (2) the Home page gains a block; (3) a new stub route
    `/{locale}/players/{slug}/` emits at most 28 players x 3 locales; (4) three metric-label
    parsers widen to see a key namespace they were blind to, which can only make gates fire MORE.
    Gates newly engaged: `audit-seo.mjs` check 8 (dead internal link) — the reason the player
    scaffold exists at all, since no page in `site_v2` emits a player href today.

acceptance_criteria:
  - Each of the four boards renders at most one row per league_code, and every board that renders
    covers all seven elite leagues; shown from the committed landing.json.
  - The block's intro sentence names exactly the leagues that appear on the boards, with no league
    named that a board does not show.
  - Re-running the export twice over unchanged data produces a byte-identical landing.json.
  - Every board title renders a non-empty localised string in de, en and fi in the built HTML — no
    board title falls back to English and none is blank.
  - Every player href the built Home page emits resolves to a page the build emitted, in all three
    locales; astro build completes with audit-seo reporting no issues.
  - At 375px width every board row is a tap target of at least 44px, and a board stacks as a whole
    rather than row-by-row.
  - Deleting one Finnish board label makes check_copy_gate.py exit non-zero.

decisions_taken: >
  ONE PLAYER PER LEAGUE is the CPO's ruling of 2026-08-18 (pooled ranking withdrawn; the rule it
  justified — every row shows club AND league — stands). The parked shaper does NOT implement it:
  `mart_leaderboards` ranks with DENSE_RANK, so ties share rank 1, and filtering `rank == 1` yields
  several rows for one league. Measured against prod in this session: assists 24 rank-1 rows over 7
  leagues (top 7 covers 5 leagues, two of them twice), goals 14 (5 leagues, ED three times), key
  passes 12 (4 leagues), passes 7 (correct). This contract pre-approves the dedupe that makes the
  code match the ruling. It is implementation of an existing decision, not a new one.

  ⭐ THE TIE-BREAK IS RESOLVED, AND NOT THE WAY THIS CONTRACT FIRST CLAIMED. Round 1's
  `analytics-engineer-reviewer` FAIL was right: picking between joint leaders in Python is ranking
  in the consumption layer. It was escalated and the CPO ruled twice on 2026-09-09
  (`escalations.log`): (1) *"All ranking and ordering lives in the warehouse. The page renders the
  order it is served."* (2) a tie goes to FEWER MINUTES PLAYED, then to `player_sk` as a stable and
  explicitly meaningless last resort — GitLab #112 is filed to find a better final key.
  So the pick moved OUT of this branch entirely: `mart_leaderboards.league_leader_order` ships in
  MR A (`!164`, merged as `943c9f2`), and this export now filters `league_leader_order = 1` and
  computes nothing. The two things that forced the escalation are kept below, because they are the
  evidence the ruling rests on and both were quotable rather than argued:
    · `escalations.log`, 2026-08-18 `chore/record-top-players-ruling`, the same entry that rules one
      per league, ends: *"⚠ NOT DECIDED, do not assume either way: whether ordering the seven
      winners by value lives in the mart or the page. The 2026-08-16 Ruling 4 ('the mart carries
      facts, the spec declares the ORDER BY') points at the page, but it was ruled about
      competitions, not players."* So the mart-or-page question is EXPLICITLY reserved, and taking
      it silently is the drift this contract exists to stop.
    · That ruling's stated saving — *"NO new mart and NO new ranking. `mart_leaderboards` already
      ranks within (league_code, season_api_year), so each league's number one already exists"* —
      rests on a premise that is FALSE under ties: the mart uses DENSE_RANK, so a league can have
      several number ones. Measured 2026-09-08: 24 rank-1 rows on assists across 7 leagues.
  ⚠ SUPERSEDED, KEPT ONLY SO THE NEXT READER SEES WHAT WAS TRIED. The code took highest
  `sort_value` then lowest `player_id`, for determinism only —
  `landing.json` is committed and a stable sort would otherwise freeze BigQuery's row order. That is
  a candidate, not an authority. It is GONE from the code: `_board_order` is deleted, the shaper
  sorts nothing, and the query orders by the three ruled keys over served columns.

  BOARD LABELS, CPO-CONFIRMED IN THIS SESSION (2026-09-08): DE assists is **Torvorlagen** — his
  words, *"more precise than just Vorlagen"* — and DE key passes **Schlüsselpässe**. The stash
  carries `Vorlagen`; it is corrected. DE `Tore`/`Pässe` and FI `Maalit`/`Maalisyötöt`/`Syötöt`/
  `Avainsyötöt` stand as parked; `Tore`, `Pässe`, `Maalit` and `Syötöt` are additionally the stems
  of the CPO-validated legacy corpus in `site/i18n/`.

  THRESHOLD — NEW MECHANISM: the player route `/{locale}/players/{slug}/` is new SURFACE but not a
  new mechanism. The URL is already reserved in `docs/site_architecture.md`:51, and it ships as a
  STUB by the `!151` precedent: `stub: true` in its page spec, listed in `STUB_PAGES`, which the SEO
  audit uses to refuse `INDEXABLE = true` while it is non-empty. No new gate, no new build step, no
  new dependency, no new export entity. Its `getStaticPaths` iterates the committed `landing.json`
  rather than a new payload.

  THRESHOLD — RECURRING COST, two, both small and both stated rather than absorbed:
    (a) the export gains one BigQuery query, measured at 29.8 MB by dry run. The export runs once a
        night inside `fdp-nightly` (~129 GB/day today), so this is ~0.02% of the existing daily
        volume.
    (b) the site build gains at most 28 players x 3 locales = 84 pages against a ~15-20k-page
        corpus. `deploy:site-v2` already runs at `--max-old-space-size=8192`; 84 pages does not move
        that. If the CPO judges either unacceptable, the block cannot ship as designed and this is
        the place to say so.

  THE THREE LABEL PARSERS ARE WIDENED, NOT LOOSENED. `check_copy_gate.py`,
  `site_v2/scripts/check-metric-labels.test.mjs` and `site_v2/scripts/check-page-specs.mjs` each
  match only `"metrics.<ident>.label"`. The four board labels use the catalogue's `playerMetrics.*`
  namespace, so today they skip the em-dash, locale-completeness, terminology and untranslated
  checks entirely — a missing Finnish label would ship a blank board title (`metricLabel()` falls
  back to English, then to `""`) with nothing red. Widening each to a generic quoted dotted key can
  only make the gates cover MORE strings; no assertion is removed or narrowed.

  LANDING.JSON IS SPLICED, NOT WHOLESALE REFRESHED, AND THAT IS THE DELIBERATE CHOICE. Running
  `--entities landing` regenerates `upcoming` as well, which moves the committed sample's definition
  to whatever matchday is next. `site_v2/src/data/README.md` requires the sample to be refreshed AS
  A SET — every fixture `upcoming` links to needs a committed payload, or `audit-seo.mjs` check 8
  reddens CI. MEASURED on 2026-09-08: the committed set is **4 fixtures across 3 competitions**
  (CIT x2, DFBP, SPL — the 2026-09-01 matchday); today's next matchday is **49 fixtures across 7
  competitions** (KL1, ED, VL, SPL, UCL, FAC, LIBER). A wholesale refresh therefore multiplies the
  committed sample TWELVEFOLD, against a CPO ruling that the thin set is right — *"we're doing
  infrastructure work and don't show anything now"* — and it was measured for properties (both
  competition shapes, all three form paths, the row-omission path) that a new set would have to be
  re-measured for. That is a decision about the sample, not about #40, so this task does not take
  it: `upcoming` is left exactly as committed and only the new `top_players` key is added. BOTH
  HALVES ARE REAL EXPORT OUTPUT and are serialised by the export's own `_payload_bytes`; no value is
  hand-written, which is what `README.md`'s "never hand-edit a payload" forbids. The diff is
  334 insertions, 0 deletions. ⚠ The consequence is stated rather than hidden: the file now carries
  two snapshot dates, and README.md is amended to say so.

decisions_reserved:
  - What the player page actually SHOWS. Reserved and not answered here: this ships a stub whose
    body is the h1 only, exactly as `!151` shipped the competition shell. The real page is the
    Player Overview work (`project_player_page_design`, #845), whose five open CPO decisions are
    untouched by this task.
  - Whether the `elite` group stays the default. `competition_group = 'elite'` is a literal in the
    export and deliberately temporary — #101 decided the group is chosen per nightly build by
    weighted random over the in-season groups. Wiring that is its own MR and is not attempted here.
  - ⭐ RESOLVED, NOT RESERVED — AND THE RESERVATION ITSELF WAS THE DEFECT. This entry used to say the
    cross-league row order had to stay in the export because it is POOL-scoped and
    `mart_leaderboards` knows nothing about pools, so moving it into the warehouse would need a
    pool-aware mart. `analytics-engineer-reviewer` FAILed round 2 on exactly that, and was right
    twice over: it was the same ranking rule relocated from Python into SQL that still lives in the
    frontend, AND the reasoning was false. The ruled order is TOTAL, and restricting a total order to
    a subset keeps the relative sequence of what survives — so ranking every league leader globally
    lets any pool filter inherit the right order, and the pool never enters into it. MR C (`!165`,
    merged `7cac157`) added `board_leader_order` on that basis. This export now carries
    `order by l.board_leader_order` and compares nothing. Nothing is reserved here any more.
  - The last-resort tie-break itself. `player_sk` is stable and meaningless; GitLab #112 is filed at
    MINOR priority to find something that means anything. Nothing in this branch depends on the
    answer.
  - WHEN the committed sample set rolls forward, and to what. The `upcoming` half of landing.json
    now points at the 2026-09-01 matchday while `top_players` is 2026-09-08 — see decisions_taken.
    Rolling the set forward is periodic maintenance README.md already describes; choosing the new
    fixture set is the CPO's, because the current one was ruled thin on purpose and today's is 12x
    larger. Not attempted here and deliberately not answered.

done_when:
  - python -m pytest tests/test_export_landing.py — all pass, including a test that the shaper
    RENDERS THE ORDER IT WAS GIVEN rather than sorting, which is the ruling in unit-test form.
  - That is mutation-tested: putting a sort back into the shaper turns
    `test_top_players_does_not_reorder_what_it_is_given` RED.
  - The committed landing.json is produced by the shipped code against PROD, and two consecutive
    export runs over unchanged data are byte-identical.
  - python scripts/check_copy_gate.py exits 0, and exits non-zero with a Finnish board label removed.
  - cd site_v2 && npm test && npm run build — prebuild runs check-page-specs.mjs, the build runs
    audit-seo.mjs; dist/{de,en,fi}/index.html and the player stubs all emit.
  - Browser pane at 375px and at desktop: row tap-target height, the per-board stack, the value
    column alignment, and the focus ring not crossing a divider (!151 shipped a 21px target and a
    ring through a divider, both invisible at desktop width).

amendments:
  - 2026-09-08: + site_v2/src/data/README.md — authority: STANDING RULE, not a CPO answer, and it
    is named as such rather than dressed up as one. `docs/working_agreement.md` §4 and the repo's
    corrections-replace rule require a document that this change makes false to be corrected in the
    same change. That README states "landing.json today carries type/upcoming only" and describes
    the refresh recipe; adding `top_players`, and splicing rather than refreshing wholesale, makes
    both sentences wrong. Content: correct the key list, and record that the file now carries two
    snapshot dates and why. No other file in that directory is touched.
  - 2026-09-08: + tests/test_governance_hooks.py — authority: STANDING RULE (round-1 FAIL,
    platform-reviewer). Widening `check_copy_gate.py`'s `_METRIC_ENTRY_RE` fixed a real hole and
    NOTHING pinned it: reverting the regex to the old `metrics.` anchor leaves pytest green and the
    gate printing a clean pass over the four `playerMetrics.*` labels, because every fixture in
    `_strings_fixture()` emits only `metrics.mN.label` keys and `MIN_METRIC_KEYS` (15) still clears
    at 18. `feedback_never_loosen_a_guard` and the repo's own "a gate whose new behaviour no test
    pins" rule make the trip-wire mandatory, and this file is where the other two parsers' pins
    already live. Content: extend the parser-agreement test to the board label keys.
  - 2026-09-08: + .claude/task/rendered_page_evidence.md — authority: STANDING RULE (round-1 FAIL,
    bi-analyst-reviewer). The file on disk documents `feat/navigation-rules-competition-shell`, a
    different branch; its own header records that an artifact describing another change was FAILed
    once before for exactly this. This branch's rendered claims (44px tap target, per-board stack,
    the focus ring clearing the divider) are measured but were written only into
    `acceptance_evidence.md`, which is in `review_exclude_paths` and so invisible to reviewers.
    Content: replace it with this branch's measurements. It is in `hash_exclude_paths`, so this
    does not move the review hash.
  - 2026-09-09: rebased onto merged MR A (`943c9f2`) — authority: the CPO's two 2026-09-09 rulings
    in `escalations.log`, which this branch was escalated into and which he then answered, plus his
    instruction "merged A, continue with B". No path is ADDED or removed by this amendment; what
    changes is the CONTENT of `scripts/export_site_data.py` and `tests/test_export_landing.py`,
    which now filter a served column instead of ranking in Python. `_board_order` is deleted, the
    shaper sorts nothing, and two unit tests went to the warehouse with the behaviour they guarded
    (recorded in place in the test file, not silently dropped).
    ⚠ The three paperwork files collided on the rebase exactly as `docs/working_agreement.md` warns
    — `contract.md`, `acceptance_evidence.md` and `review_input.patch` came back UU while every code
    file merged clean. Resolved to THIS branch's versions; `escalations.log` was reverted before the
    rebase and taken from main, so the rulings are present once, not twice. All four conflict-marker
    kinds were grepped for afterwards, including `|||||||`: zero.
  - 2026-09-09: rebased onto merged MR C (`7cac157`) — authority: the CPO's 2026-09-09 Ruling 1,
    already recorded, plus his instruction "merged C, continue with B". No path is added or removed.
    What changes is ONE LINE of `scripts/export_site_data.py`: the three-key ORDER BY becomes
    `order by l.board_leader_order`, so the export compares nothing at all. The reserved item about
    the cross-league order is struck, because it is now answered rather than deferred — see
    `decisions_reserved`.
    ⚠ The same three paperwork files collided again on this rebase and were resolved the same way
    (this branch's versions; `escalations.log` reverted first and taken from main). All four
    conflict-marker kinds grepped for afterwards: zero.
    ⚠ ACCEPTANCE CRITERIA ARE UNCHANGED AND STILL BIND. In particular "re-running the export twice
    over unchanged data produces a byte-identical landing.json" now carries a second job: the
    payload must ALSO be byte-identical to the one produced before this change, because MR C's
    column was verified to reproduce the same order. If it differs, the column does not encode the
    rule the export was applying and that is a defect, not a surprise.
