# Task contract — refresh the committed export sample so it carries the four renamed columns

objective: >
  Regenerate `site_v2/src/data/**` from the PROD marts so the committed build sample serves the
  four column names that `!114` and `!116` renamed. Nothing else changes: no model, no script, no
  component, no label.

  ⭐ THIS WAS THE PROGRAMME'S CLOSING MR G AND THE CPO MOVED IT TO NOW. His words, verbatim:
  **"116 merged, do the refresh"**, and again when handing this task over: "the export-sample
  refresh, then batch C". It is done BEFORE batch C rather than after batch F.

  ⛔ WHY IT MOVED, and it is a measurement not an argument. A renamed FIXTURE field drops its row
  from the 16-row comparison on all 51 built fixture pages until the sample carries the new key:
  `MetricComparison.astro`'s `hasData()` omits a row where neither side has a value. `!116` measured
  **16 rendered metric names → 14**, and the whole **Goalkeeping** heading disappeared, because
  `saves_pct` is that group's only row. Batches C–F rename five more fixture payload fields, so
  refreshing now resets the baseline to a known-good 16 instead of letting the gap accumulate
  across four more MRs.

  ⭐ THE PRECONDITION IS MET, CHECKED TWO WAYS RATHER THAN ASSUMED FROM A GREEN TICK.
  (1) `data:build:main` succeeded on `4975934` — pipeline `#324` / `2797839942`, job
      `data:build:main: success`.
  (2) The PROD marts themselves were queried, because a green pipeline is not the same claim as a
      present column. `marts.INFORMATION_SCHEMA.COLUMNS` returns `corners_per_match` and `saves_pct`
      on `mart_team_momentum`, `mart_team_profile`, `mart_team_season_insights` and
      `mart_team_season_record`; `points_capture_pct` on `mart_team_profile` and
      `mart_team_season_insights`; and `clean_sheets_pct` as the three
      `_this_season` / `_prev_season` / `_delta_yoy` forms on `mart_team_profile`. `clean_sheets_pct`
      is additionally a `metric_key` VALUE on `mart_team_competition_benchmarks` (7,443 rows), which
      is why it has no bare column of its own. The four OLD names return **zero** rows from the
      same queries.

  MEASURED ON THIS BRANCH BEFORE ANY EDIT — the stale keys in the committed sample:
  **183 × `corner_kicks_per_match`, 181 × `save_ratio`, 97 × `clean_sheets_share`,
  25 × `points_capture`**.

  ⛔⛔ THE HANDOVER'S RECIPE IS WRONG, AND THE WORK CHANGED SHAPE BECAUSE OF IT. It says to run the
  export and the sample will carry the new keys. It will not, and no amount of re-running fixes it.
  `fetch_fixture_payloads` (`scripts/export_site_data.py:806`) selects
  `where status_short in ('NS', 'TBD') and fixture_date >= current_date()` — **upcoming fixtures
  only**. All 17 committed fixture payloads are from the 2026-08-18 matchday. The export ran
  cleanly (exit 0, 3,289 team + 5,066 fixture payloads) and did not touch one of them: their mtimes
  are unchanged and 5,083 files sit in `fixtures/` — the 5,066 new ones plus the 17 old.

  ⛔ AND THE ID SET CANNOT BE RE-EXPORTED, which is what rules out the obvious workaround.
  `mart_team_momentum` and `mart_team_season_record` are keyed on `upcoming_fixture_sk` and hold
  PRE-MATCH form; once a fixture kicks off its rows are gone. Queried against prod rather than
  assumed: fixtures `1492306` and `1622620` each return **0 rows from both marts**. There is no W1
  or W2 data to export for any committed fixture. Hand-editing is forbidden, so rolling the SET
  forward is the only remaining path.

  ⭐ THE MECHANISM ITSELF IS PROVEN SOUND, which is why the fix is a set swap and not a code change:
  of the 5,083 payloads now on disk, **exactly the 17 stale ones** contain `corner_kicks_per_match`
  and the **5,066 fresh ones carry `corners_per_match` and `saves_pct`**.
  ⚠ AND NOTHING IS WRONG IN PRODUCTION. `deploy:export` runs daily-fresh and always emits upcoming
  fixtures with whatever names prod holds, so the missing rows exist ONLY in the committed CI
  sample. This MR fixes a snapshot, not a defect.

refs: >
  **`.claude/task/escalations.log`, the block "THE METRIC CATALOGUE NAMING PROGRAMME"** — rulings
  dated 2026-08-26, complete tables appended 2026-08-27 — together with the two entries that follow
  it, `2026-08-27 STEP 3 STARTS` and `2026-08-27 STEP 3, MR B`.

  The transient this closes is declared in both of those entries. From `STEP 3 STARTS`: "the
  committed export sample under `site_v2/src/data/` can only be regenerated against the PROD marts,
  which do not carry the renamed columns until `data:build:main` runs on merge... Precedent for the
  sequencing is `!109`, 'refresh the committed export sample after #90'." From `STEP 3, MR B`,
  finding ONE: the 16→14 measurement and the vanished Goalkeeping heading, quoted in `objective`.

  The four renames whose keys this sample picks up are in the log's "⛔ TEAM, 12 REMAINING" table:
  `clean_sheets_share → clean_sheets_pct`, `points_capture → points_capture_pct` (`!114`), and
  `corner_kicks_per_match → corners_per_match`, `save_ratio → saves_pct` (`!116`).

  ⛔ NO PLAN FILE IS CITED. `feat/metric-rename-goals` and `feat/metric-rename-catalogue-only` were
  each FAILed for citing one; the tables live in the log itself.

  Branched from main **`b022909`**, clean tree. ⚠ The handover header says `4975934`; `b022909` is
  the handover's own merge commit on top of it and carries no code difference for this work.

scope_paths:
  - site_v2/src/data/**
  - .gitignore
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/acceptance_evidence.md
  - .claude/active_work.md

# ⚠ NOT IN SCOPE, each for a stated reason rather than by omission:
#  · dbt_project/** and scripts/** — nothing is renamed here. This MR runs the EXISTING export
#    unmodified; the four renames already merged in `!114` and `!116`.
#  · site/** — the retired MVP. Its sample is not this sample and no gate crosses.

protected_override: >
  none required. No file in scope_paths is protected.

impact_map: >
  ⭐ SHORT FORM, and evidenced rather than asserted: this touches NO dbt model, macro, seed, test or
  loader. `git grep -l` over `dbt_project/` for the four names returns nothing that this MR edits,
  because the renames already merged. The change is entirely in GENERATED consumption artifacts.

  writers: `scripts/export_site_data.py`, UNMODIFIED, is the only writer of these files. It is run
    exactly as `.gitlab-ci.yml`'s `deploy:export` runs it — the `--entities teams,fixtures` list is
    copied verbatim from that job, where a comment marks it load-bearing. The sample is never
    hand-edited.

  downstream: the Astro build reads `site_v2/src/data/**` at build time — `astro build` in
    `site_v2/`, and the `build:site-v2` CI job. Nothing else reads it. No BigQuery table is written:
    the export is read-only against `marts`.

  layer_rules: the consumption-layer contract — the export may select, group and rename but never
    derive a fact. Not at risk here, because no export CODE changes; only its output is refreshed.
    `check_layer_contract.py` governs `dbt_project/models/`, which is untouched.

  deploy_order: none. The precondition (`data:build:main` green on `4975934`) is already satisfied
    and confirmed above, so there is nothing to sequence around the nightly.

  blast_radius: the tracked sample under `site_v2/src/data/` plus the `.gitignore` allowlist. On
    the built site the effect is the reverse of the transient: the omitted fixture rows return and
    the Goalkeeping heading reappears.
    ⛔ THE SAMPLE'S FIXTURE SET IS REPLACED, not refreshed in place — the 17 committed payloads are
    past fixtures whose form rows no longer exist in prod (0 rows, queried). A fresh `landing.json`
    links **19 fixtures across 13 competitions**, all kicking off 2026-08-28; **17 of the 19 are
    fully populated** (29/29 non-null W1) and one (BL1 `1575140`) has a null W1 — pre-season, no
    form window — which exercises the absent path rather than weakening the sample. So the built
    fixture pages go from **51 to 57** (19 × 3 locales) at new URLs.
    ⚠ Values move too, and that is inherent to any refresh: fixture lists, form windows and roster
    rows carry today's data. Called out so a reviewer reads a changed number as a new snapshot and
    not as a rename defect.
    ⚠ The replacement set ages the same way — those 19 kick off today. But ageing moves the VALUES,
    never the KEYS: the payloads keep `corners_per_match` / `saves_pct` permanently, which is the
    only property this programme needs from them.
    Read cost, measured by `bq query --dry_run` rather than estimated: `mart_roster` 86.4 MB,
    `mart_player_career` 61.4 MB, `mart_team_fixtures` 8.7 MB, `mart_team_profile` 6.1 MB,
    `mart_team_competition_benchmarks` 2.7 MB, plus the fixture reads — well under a cent, and the
    identical shape CI already runs in `deploy:export`.

acceptance_criteria:
  - Every built fixture page renders 16 metric rows again, with a Goalkeeping group heading present, in all three locales — shown by counting `<div class="mrow">` and listing every `<div class="mgroup">` heading in the pages under `site_v2/dist/`, before and after the refresh, so the 14→16 recovery is visible as a pair of numbers.
  - The same 16 are confirmed by NAME and not only by count, using the substring-safe method: each metric label's occurrences on the built page minus the occurrences of any longer label that contains it. A plain substring test is not a presence test in a metric set full of `X` / `X against` pairs, and on `!116` it reported 16 when 14 was true.
  - No file under `site_v2/src/data/` contains `corner_kicks_per_match`, `save_ratio`, `clean_sheets_share` or `points_capture` — shown by a grep that returns zero against the 183 / 181 / 97 / 25 occurrences measured before the refresh.
  - The measurement is watched FAILING, because a check that passes equally on the work and on its absence is not a check: one refreshed fixture file has its `corners_per_match` key reverted, the site is rebuilt, the row count is seen to fall from 16 to 15, and the file is restored.
  - The sample's SET moves COHERENTLY: `landing.json`, the `.gitignore` allowlist and the committed fixture payloads all name the same fixture ids, shown by `audit-seo.mjs` passing in the build — it fails on any internal link that resolves to no emitted page, which is precisely the trap the sample's README warns a local build cannot catch. (This criterion REPLACES the one written before the roll-forward was authorised; see `amendments:`.)

decisions_taken: >
  Nothing is named, designed or decided here. The four names come from the record; the sequencing
  is the CPO's instruction quoted in `objective`; the `--entities` list is copied from
  `deploy:export`. The only builder judgement is the evidence METHOD, and it is the method the
  record already prescribes after `!116`'s substring failure.

  ⭐ THE STANDING FOUR ACCEPTANCE CRITERIA ARE NOT USED HERE, deliberately. The CPO approved them
  for "MRs B THROUGH F" — the rename batches — and their subject is a rename's invisibility. This
  MR is G pulled forward and its subject is the opposite: a rename becoming visible again. Its
  criteria are the ones he stated directly for it ("get that count back to 16 with Goalkeeping
  present"), expanded into commands above. Not a re-draft of the standing four, and not a request
  to re-approve them.

  ⛔ THE RESIDUAL, declared as it is created rather than discovered later. This closes the gap for
  `!114` + `!116` ONLY. Batches C–F rename more fixture PAYLOAD fields, so the count drops again on
  each of them and the original MR G — a final refresh after F — is still owed. Measured now so the
  next MR's expected number is known rather than guessed: of batch C's three names only
  `danger_zone_ratio` is one of the rendered 16; `shot_accuracy` is a payload field that the 16-row
  contract in `site_v2/src/lib/metricRows.ts` deliberately drops, and `shot_share` is not in the
  fixture payload at all. **C will take 16 → 15, and no heading is lost** — Shooting keeps 3 of 4.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none — no new script, macro, hook, test, generator or
  dependency; the export and every gate already exist and are re-run. RECURRING COST: none — no new
  CI job, no schedule, no extra build. The one BigQuery read is a single manual run of a job CI
  already defines, measured above at well under a cent, and it creates no recurring charge.

decisions_reserved:
  - Nothing in the DIFF decides a §10 item: no name, label, formula, URL or page structure is
    chosen here. The one thing a reviewer might read as a decision — running the refresh before
    batch C rather than after batch F — is the CPO's own instruction, quoted verbatim in
    `objective`.
  - ⛔ **BUT A §10 QUESTION WAS FOUND WHILE BUILDING, AND IT IS OPEN: the seven metric GROUP
    HEADINGS render in ENGLISH on the German and Finnish pages.** Filed as **GitLab #98**, and NOT
    fixed here. Found by `bi-analyst-reviewer` in round 1 of this MR's review; verified
    independently on the built site rather than taken on the reviewer's word — all three locales
    emit `['Goals', 'Shooting', 'Duels', 'Defending', 'Passing', 'Set pieces', 'Goalkeeping']`,
    while the metric names beside them translate correctly, so a DE page reads "Set pieces" above
    "Ø Ecken". Source: `MetricComparison.astro:40` and `TeamPerformance.astro:89`/`:110` interpolate
    the raw `MetricGroup` literal with no `t(lang, ...)` call, though both components already thread
    `lang` for everything else on the same lines.
    ⭐ ONE CORROBORATION THE REVIEWER DID NOT CITE, which is what settles it as an oversight rather
    than a deliberate residual: `TeamSquad.astro:99` already renders a group heading as
    `{t(lang, g.label)}`. The pattern exists in the codebase and these two components simply skip
    it.
    ⚠ IT IS THE CPO'S BECAUSE IT IS A NAME. The mechanism is the transformation layer's to pick;
    the seven German and seven Finnish words are a §10 naming decision. Fixing it here would have
    been both out of scope (this MR touches `site_v2/src/data/**` and `.gitignore` only) and a
    naming decision taken silently.
    ⚠ PRE-EXISTING, and this MR does not cause it — but it does multiply it, from 17 fixtures to 19,
    so 38 built DE/FI fixture pages now carry the English headings instead of 34. Disclosed rather
    than netted off.

done_when:
  - The export ran from the REPO ROOT as `PYTHONPATH=. python scripts/export_site_data.py --entities teams,fixtures --out site_v2/src/data`, then again with `--entities landing` to move the set's definition forward, with no hand-editing of any output file.
  - `git status --short` shows changes confined to `site_v2/src/data/**` and `.gitignore`, and the file set matches the roll-forward exactly: 17 fixture payloads removed, 19 added, `landing.json` / `competitions.json` / `teams/33.json` / `README.md` modified. ⚠ THIS BULLET WAS REWRITTEN. It previously read "confined to the 22 tracked files, with no new tracked file and no `.gitignore` edit" — written for the pre-roll-forward plan and falsified by the CPO decision recorded in `amendments:`. `scope-auditor` FAILed round 1 on exactly that contradiction and was right to: the amendment moved `acceptance_criteria` and `scope_paths` and left its neighbour asserting the opposite.
  - The ignored bulk was dropped before building, so the build sees only the tracked set — a full export leaves thousands of ignored payloads that make a local build resolve links CI cannot, and `astro build` OOMs at full scale. ⚠ NOT via `git clean -fX site_v2/src/data`, which this environment blocks: a scoped equivalent was used, taking its delete set from `git ls-files --others --ignored --exclude-standard site_v2/src/data` — git's own listing, the same one `git clean -X` consults — whose `--others` restriction makes it structurally incapable of selecting a tracked file. Verified by a dry run first: 8,337 to delete, 24 kept, and the 24 were enumerated and matched the intended set exactly.
  - `cd site_v2 && npm test && node scripts/check-page-specs.mjs` passes.
  - `python -m pytest -q` from the repo root passes with no new failures against the count on `b022909`.
  - The offline governance gates pass (`validate:governance`, `validate:secrets` equivalents).
  - Every acceptance criterion is demonstrated in `acceptance_evidence.md` under `criteria_demonstrated:`, read from the BUILT output under `site_v2/dist/`, never from source.

amendments:
  - 2026-08-28 (round 2, after `bi-analyst-reviewer` FAILed round 1): `decisions_reserved` no longer
    says "none". AUTHORITY: none needed — this DISCLOSES a §10 question rather than deciding one.
    CONTENT: the group-heading i18n gap, verified independently and filed as GitLab **#98**; and a
    stale sentence in `site_v2/src/data/README.md` claiming `landing.json` is "reduced by hand",
    which `shape_landing_payload` contradicts (it returns `{"type", "upcoming"}` and nothing else)
    and which the same README's own "never hand-edit a payload" rule contradicts again. The README
    line is corrected here because that file is in scope and this MR rewrites it; the i18n gap is
    NOT touched here because it is a §10 naming decision in components this MR does not own.
  - 2026-08-28 (round 2, after `scope-auditor` FAILed round 1): three `done_when` bullets rewritten
    to match the amendment below rather than the plan it replaced. AUTHORITY: none needed — this
    corrects the contract to describe what the CPO already authorised, and narrows nothing.
    ⛔ THE FINDING WAS EXACT AND THE FAIL WAS DESERVED: the round-1 amendment moved `scope_paths`
    and `acceptance_criteria` and left the neighbouring `done_when` bullet asserting "no new tracked
    file and no `.gitignore` edit" — the precise opposite of what it had just authorised, so the
    contract could not be trusted at face value. ⭐ Two MORE bullets in the same block were false for
    the same reason and are fixed here too, found by re-reading every claim in the block rather than
    only the one the reviewer named: the export bullet omitted the second `--entities landing` run,
    and the clean bullet named `git clean -fX`, which this environment blocks and which was not
    what ran.
  - 2026-08-28: + `.gitignore` to `scope_paths`, and acceptance criterion 5 REPLACED.
    AUTHORITY: the CPO, this conversation, choosing **"Roll the set forward"** from a blinded
    two-way fork after being shown (a) that the handover's recipe cannot work because the export
    emits upcoming fixtures only, (b) that the committed ids cannot be re-exported because their
    form rows return 0 from both marts, (c) the measured size of the replacement — 19 fixtures,
    13 competitions, 17 of 19 fully populated, built pages 51 → 57 at new URLs — and (d) the
    alternative of shipping `teams/33.json` alone, which would leave every fixture page at 14 rows
    with no Goalkeeping heading and fail the criterion he set.
    CONTENT: the `.gitignore` fixture allowlist is rewritten from the 17 stale ids to the 19 the
    fresh `landing.json` links, and `landing.json` itself is regenerated. Criterion 5 previously
    asserted the SET would NOT move and the allowlist needed no edit; that is falsified by this
    decision, so it is replaced by a criterion that the set moves COHERENTLY — which `audit-seo.mjs`
    settles, since it fails on a link to a page that was never emitted.
    ⚠ ALSO IN THE SAME `.gitignore` EDIT, declared rather than slipped in: `manifest.json` and
    `slug_map.json` are added to the ignore list. Both are byproducts every export run writes into
    the output directory, neither is part of the tracked sample, and both appeared as untracked
    strays the moment this MR's export ran. Ignoring them fixes the trap for the next refresh
    instead of deleting them and leaving it armed.
