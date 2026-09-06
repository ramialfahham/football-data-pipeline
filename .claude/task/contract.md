# Task contract — bound the deserved-points fit to the range it is allowed to occupy

objective: >
  `int_team_season_deserved_points_in_legal_range` is FAILING the prod build, and has been since
  !153 merged — one row, LP 2026, a fitted 12.0259 points against a ceiling of 12. It is an
  error-severity test inside `dbt build`, so everything below `int_team_season__deserved_vs_actual`
  is marked skipped and prod stops refreshing there. This caps the fitted points-per-match rate to
  the range the outcome can actually take, so the model cannot emit an impossible points total.

refs: >
  Not an issue — a live prod-build failure found on the !153 merge pipeline (job 16331792666).
  ⭐ **THE APPROACH IS THE CPO'S, AND HE OVERRULED MINE.** I recommended withholding the whole
  league-season's fit whenever any team left the legal range, arguing an out-of-range value is
  evidence of a degenerate fit. He rejected that and ruled for a mechanical cap:
  *"We could use methods that count for censoring of the dependent variable but to be pragmatic, we
  use OLS and cap mechanically at the possible max or mins."* Recorded in
  `.claude/task/escalations.log`, entry `2026-09-06 — fix/deserved-points-clamped-to-legal-range — DESERVED POINTS, CAP NOT WITHHOLD`.
  ⛔ **He was right and the measurement says so**, which is why this contract does not hedge: over
  1,125 fitted rows in prod, exactly ONE crosses a bound, by 0.0065 points per match, and no other
  row is within 0.1 of either bound. There is no degenerate-fit population for a cap to conceal, so
  my objection was a hypothesis the data does not contain.
  He then ruled the outcome's domain — *"Deserved points is always a positive integer incl zero"* —
  and, when I answered that the page already rounds it, overruled that too: *"Rounding is business
  logic."* ⛔ Both rulings stand; only the second one's CONSEQUENCE is out of scope here. The
  warehouse owes the integer, the page must not compute it, and `DeservedHero.astro:79` doing so is a
  defect — filed as **GitLab #108** with two siblings found in the same sweep. This MR keeps the
  stored value continuous for reasons that survive the correction (`decisions_taken`), and does not
  add the integer; #108 does.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md

impact_map: >
  writers: no ingestion, staging or base model touched. The change is inside one intermediate model.
  downstream: `int_team_season__deserved_vs_actual` is NOT a leaf. Its consumers, found by grep for
  `deserved_points`/`deserved_rank` across models, scripts and the site:
      dbt_project/models/5_marts/shared/mart_team_profile.sql
      scripts/export_site_data.py            (deserved_scatter_index, :208)
      site_v2/src/components/team/DeservedHero.astro
      site_v2/src/lib/types.ts
  None of them is EDITED here, and none needs to be: the column keeps its name, type and null
  semantics, and only its value moves — by at most the amount that made it illegal.
  ⛔ **THE ONE CONSUMER THAT CARES IS THE HERO'S TREND LINE, AND MY FIRST ASSESSMENT OF IT WAS
  WRONG.** `DeservedHero.astro:96-110` draws a straight segment between the two extreme-`sotd` dots'
  served `deserved` values, which are colinear in `sotd` only while nothing is capped. I wrote that
  "the component already tolerates a dot off the line (it plots dots and the trend independently)".
  The DOTS are independent; the SEGMENT ENDPOINTS are not — they ARE served `deserved` values. And
  the cap binds precisely at the extremes, because the capped team is by construction the one with
  the most extreme signal (LP's capped row carries `sotd` 6.5, its league's highest). So for a capped
  league-season the line is drawn through a capped endpoint and is no longer the model's line.
  Half right, and the wrong half is the one that matters. Found only by sweeping inverted while
  stopping at the round cap; no reviewer reached it. Filed as its own issue — see
  `decisions_reserved` — because `site_v2/**` is outside these `scope_paths` and the fix belongs with
  the rounding work, not here.
  layer_rules: `check_layer_contract.py`. The bound is a property of the METRIC — points per match
  cannot exceed 3 — so it belongs where the metric is computed, not in the mart or the export. The
  consumption layer may not derive; capping downstream would be exactly the forbidden derivation.
  deploy_order: none. The model rebuilds on the next `data:build:main` or nightly; no consumer
  changes, so nothing has to land in an order.
  blast_radius: one league-season's values move by <= 0.026 points TOTAL today (LP 2026, one team).
  Every other one of the 1,125 fitted rows is byte-identical — asserted by running the model both
  ways against prod and diffing, not by reading the SQL.

acceptance_criteria:
  - The compiled model run against LIVE PROD emits zero rows outside `[0, 3 * season_games_played]`,
    where it emits exactly one today.
  - Every other fitted row is UNCHANGED. Shown by a full row-by-row comparison of old against new
    over all 1,125 fitted rows, not by a row count.
  - `deserved_rank` and `deserved_points_gap` stay consistent with the capped `deserved_points`:
    the rank is computed FROM the capped value so a consumer sorting by the value cannot disagree
    with the served rank, and the gap arithmetic contract still holds exactly.
  - `deserved_points_was_capped` is true for exactly the rows the cap actually moved, and false
    (not null) for every other fitted row. Measured on prod.
  - `int_team_season_deserved_points_in_legal_range` passes on prod, and STILL FAILS when the cap
    is removed — so it pins that the cap is wired in, having lost the ability to discover the
    condition itself. Watched RED under that mutation.
  - The new warn-severity test reports the capped row rather than erroring, so a build is not
    skipped by it. Shown by the WARN line in the run output.
  - `dbt parse` exits 0 and SQLFluff passes under the templater CI uses, exit codes read BARE.
  - `check_description_hygiene.py` passes — the edited `deserved_points` doc block stays under
    BigQuery's 1,024-character column limit, measured as RENDERED text.

decisions_taken: >
  ⭐ **CAP THE RATE, NOT THE TOTAL.** `deserved_points <= 3 * games` is exactly
  `fitted_points_per_match <= 3`, and stating it on the rate makes the bound scale-free — it does
  not move when teams in one league-season have played different numbers of matches, which is
  already the awkward part of this model's mid-season arithmetic. The two are equivalent where games
  are equal; the rate form is the one that stays correct where they are not.
  ⭐ **RANK ON THE CAPPED VALUE.** If two teams ever both hit the ceiling they tie, and `rank()`
  handles that. Ranking on the pre-cap fit would preserve a strict ordering, but then
  `deserved_rank` disagrees with sorting by the served `deserved_points` — two served columns
  contradicting each other, which is worse than an honest tie. Nothing hits this today; it is a rule
  for when something does.
  ⛔ **THE STORED VALUE STAYS CONTINUOUS HERE — but the reason I first gave for that was WRONG and is
  struck.** This said "the integer domain is a display property, and stays one", on the grounds that
  `DeservedHero.astro:79` already renders `integer(...)`. The CPO overruled it: *"Rounding is
  business logic."* The page rounding a metric is the consumption layer deriving, which this repo
  forbids, so pointing at it was pointing at a defect and calling it a design.
  What survives is only the MEASUREMENT, and it argues about WHICH column, not about where rounding
  belongs: rounding the single served column would take rows tied on `deserved_points` from 75 of
  1,125 (6.7%) to 252 of 1,125 (22.4%), making a fifth of `deserved_rank` an artifact of rounding
  rather than of the fit, and would scatter the hero's dots off the trend line they are colinear
  with. So `deserved_points` keeps the continuous fit that the rank and the line need, and the
  warehouse owes an integer ALONGSIDE it — which is #108's, not this MR's. See
  `decisions_reserved`.
  ⛔ **The cap does NOT replace the `>= 3 finished games` gate**, and raising that threshold was
  rejected: it picks a new magic constant that will break again the first time a league carries an
  outlier at 6 or 8 games, where the cap needs no constant and is self-correcting as spread grows.
  THRESHOLD DECLARATIONS: no new mechanism, no new dependency, no recurring cost (two expressions in
  an existing table model). TWO guards are ADDED — `..._cap_did_not_bind` at warn and
  `..._capped_flag_matches_value` at error. ⛔ This line said "One guard is ADDED" and was WRONG;
  `scope-auditor` caught the miscount at round 2 and judged it concealed nothing, which it did not,
  but an unmeasured self-measurement in a contract that otherwise counts everything is exactly the
  habit worth not having. `int_team_season_deserved_points_in_legal_range` is
  NOT loosened — its predicate is unchanged and it stays severity=error; what changes is that the
  model now satisfies it by construction, which is why the new warn test exists to carry the
  detection the old test can no longer do.

decisions_reserved:
  - **The mid-season rendering questions.** Memory records two open CPO decisions on this read — how
    to render the fitted line mid-season, and from which matchday to show it at all. This touches
    NEITHER. It is a correctness bound, not a decision about when the read is worth showing, and it
    is deliberately built so that raising a matchday threshold later is still fully open.
  - **Whether a capped read should be suppressed at the page.** `deserved_points_was_capped` is
    emitted so that question CAN be answered later; it is not answered here, and no consumer reads
    it.
  - ⛔ **ROUNDING BELONGS IN THE WAREHOUSE, AND THE FRONTEND IS DOING IT — GitLab #108.**
    An earlier `decisions_taken` in this contract asserted the opposite: *"the integer domain is a
    display property, and stays one"*, on the grounds that `DeservedHero.astro:79` already renders
    `integer(...)`. **The CPO overruled that**: *"Rounding is business logic."* He is right, and the
    rule was already written — the consumption layer may select, filter and order, never derive. Two
    blinded reviewers passed my version, so this was a wrong decision that survived review.
    A sweep of `site_v2/src` found **three** places deriving a number the reader sees: the rounding
    here, `bars.ts`'s `displayRank` computing the direction-aware rank printed as "3rd of 18", and
    `TeamSquad.astro:58` defining "played" as `appearances >= 1` and printing the count. Two-sided:
    `barWidth`, `stackShares`, `rankFill` and `format.ts`'s percent conversion were checked and
    CLEARED — every call site traced, none produces a printed number.
    ⚠ Deliberately NOT fixed here. Serving the rounded integer changes what reaches the frontend, so
    it touches the mart, the export and `DeservedHero` — including the trend-line defect above. This
    MR's cap is correct either way and was already at the round cap. #108 carries it, with the
    ordering, and with the warning not to move any of it into `scripts/export_site_data.py`, which is
    consumption too.
  - **The freshness guard, and the nightly failing ~1 night in 3.** `assert_fct_fixture_no_stale_live`
    uses a 3-hour window against a once-daily ingest; its sibling `assert_fct_fixture_no_stale_ns`
    was already given a 30-hour cadence-aware window and says why in its own comment. Diagnosed in
    the same session, deliberately NOT in this MR — it widens a guard and deserves its own contract.
  - **The handover misattributes how `is_current_season` reached prod** (it says the nightly; it was
    `data:build:main` on the !153 merge). Left for the next handover MR rather than smuggled in here.

done_when:
  - `.venv/Scripts/dbt.exe parse` exits 0.
  - SQLFluff passes under the dbt templater from `dbt_project/`, exit code read bare.
  - The compiled model runs against prod read-only; old-vs-new compared row by row.
  - The legal-range test measured on prod: green with the cap, RED without it.
  - The new warn test measured on prod: reports the LP row, does not error.
  - `python -m pytest tests/ -q` passes as a regression check (nothing here touches Python).

amendments:
  - **2026-09-06, round 1 → 2: `dbt_project/seeds/metric_catalogue.csv` added to `scope_paths`.**
    NOT a scope expansion — a correction of where the SAME text had to be written.
    ⛔ **I hand-edited `dbt_project/models/docs/metric_columns.md`, which is a GENERATED FILE.** Its
    own first line says `GENERATED FILE - DO NOT EDIT BY HAND`, and
    `dbt_project/docs/engineering_standards.md:129-135` says the same as a project standard: a
    metric's definition is generated from the seed's `description` by
    `scripts/sync_metric_docs_blocks.py`. The seed row (`metric_catalogue.csv:78`,
    `deserved_points`) still carried the pre-cap text, so the seed and the generated file disagreed
    about what the metric means — the exact drift that rule exists to prevent — and the next run of
    the sync script would have silently overwritten my edit with the stale description.
    ⚠ **`.gitlab-ci.yml:411` runs `sync_metric_docs_blocks.py --check` in `validate:governance`**, so
    this was a live CI break, not a hypothetical one.
    ⭐ **Found by `tests/test_sync_metric_docs_blocks.py::test_the_real_seed_and_the_real_file_are_in_sync`
    AND, independently, by `analytics-engineer-reviewer`.** Neither `dbt parse`, SQLFluff,
    `check_description_hygiene.py`, `check_layer_contract.py` nor `check_registry_var_sync.py` saw
    it: all five went green over a hand-edited generated file. No CPO authority is cited because
    none is needed — the ruling is unchanged, only the file it had to be written into.
    The fix: revert the generated file, put the sentence in the seed's `description`, regenerate.
  - **2026-09-06, round 2 → 3: the sums-to-zero claim swept, not patched where it was named.**
    `football-analytics-expert-reviewer` FAILed round 2 because the round-2 fix corrected *"the gap
    sums to exactly 0 across a balanced season"* in the SQL comment and left the SAME claim standing
    in `metric_catalogue.csv:79` (`deserved_points_gap`) — which is the copy that actually reaches
    readers: `persist_docs` attaches it to the BigQuery column, `dbt docs generate --static`
    publishes it, and `scripts/export_site_data.py`'s `fetch_glossary` ships it into `metrics.json`.
    ⛔ That is `feedback_fix_the_class_not_the_instance` again, INSIDE the fix for a finding about a
    claim left standing in a sibling artifact. So the tree was swept rather than the named line
    patched. **Two-sided count: the claim had THREE live instances from TWO sources** — the SQL
    comment (already fixed at round 2), `metric_catalogue.csv:79`, and
    `int_team_season.yml:309`'s model description, **which the reviewer did NOT name**. The fourth
    copy, `metric_columns.md:306`, is generated from the seed and follows. Fixing only what was named
    would have shipped the third.
    ⭐ No scope change: both files were already in `scope_paths`. Recorded because an amendment block
    should carry what a later reader needs to know, not only what moved a path.
  - **2026-09-06, round 3 → 4: `severity: warn` is now the CPO's ruling, not my analogy.**
    ⛔ An earlier version of this entry kept `warn` and justified it in place, arguing §3 "carries the
    same principle". `scope-auditor` FAILed that and quoted the rule it broke:
    `docs/working_agreement.md:328` — *"when a new case does not clearly match a written rule, the
    classification itself is a CPO decision. 'It's analogous to X' is not a license."* It was right;
    :322 lists rule extension as CPO-only, and I had conceded the mismatch in writing before
    closing it myself.
    ⚠ The two reviewers had reached OPPOSITE conclusions — `analytics-engineer-reviewer` called warn
    "functionally sound independent of which §3 row it maps to" — which is itself the argument that
    the classification was not mine.
    Escalated, and ruled: **"warn"**. Recorded in `escalations.log`, entry
    `2026-09-06 — fix/deserved-points-clamped-to-legal-range — TEST SEVERITY: WARN`, with both options
    and their consequences as he was given them.
    ⚠ It rules on THIS test only. §3's table gains no fourth row, so the next computed-degradation
    test faces the same undecided classification; that was offered and not taken up.
  - **2026-09-06, round 3 → 4: the now-false formula sentence, and the `_was_capped` rename.**
    `analytics-engineer-reviewer` FAILed round 3 on `int_team_season.yml:305-307`, which still stated
    the PRE-CAP formula flatly — *"deserved_points is that rate times the team's games played"* —
    three lines above the sentence the round-3 sweep had just patched, in the same paragraph. False
    today for the LP 2026 row, where the served value is the capped rate times games.
    ⛔ That is the same class the round-3 amendment describes fixing, recurring one sentence away,
    inside the fix for it. The lesson, recorded because two sweeps have now missed by the same
    method: **grepping the phrase a reviewer named finds instances of that phrase. It does not find
    the other statements the change falsified.** Sweeping INVERTED — enumerate every claim about the
    quantity and ask whether each is still true — found this one AND a second outside these
    `scope_paths` (see `decisions_reserved`).
    Bundled with it, on the same authority: `deserved_points_was_clamped` → `deserved_points_was_capped`,
    so the column matches the word the CPO's own ruling used and the word all four prose copies use.
    `football-analytics-expert-reviewer` raised the inconsistency without failing it.
    ⛔ **AND THE RENAME BROKE BOTH CITATIONS TO THE ESCALATION LOG, which `scope-auditor` FAILed at
    round 4.** I aligned this file's wording with a blanket find-and-replace of "clamp" → "cap",
    which rewrote the branch name INSIDE the quoted entry titles — so the contract cited
    `fix/deserved-points-capped-to-legal-range`, a string that appears nowhere in the log, in the one
    artifact whose entire job is to make the CPO's authority independently checkable. A reader
    following the citation could not have found the ruling.
    Both are restored to the literal headers. The lesson, and it is the same one twice on this branch:
    **a blanket replace edits quoted strings too.** The first instance corrupted meaning I had to
    strike; this one corrupted a citation. `acceptance_evidence.md` had the branch name wrong from the
    same sed and is fixed with it.
