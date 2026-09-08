# Review — fix/fixture-team-id-overrides-all-sources — 2026-09-08

diff_sha256: 1b2fe6e3a88697b435116b1754cf0761b39d2acdda9b0082698edf4ffb15594e

rounds: 3

⚠ **WHAT THE ROUNDS BOUGHT.** Two FAILs, three defects, all mine, and **both FAILs were claims I
wrote from memory instead of opening the file**:

    round 1  FAIL x2  the contract said fct_fixture_event was the only INCREMENTAL model in the
                      chain (false — both target facts are too, so the fix would never have
                      reached prod); and an acceptance criterion said only one team key was
                      removed (false — two are)
    round 2  FAIL     the contract claimed a `relationships` test on the seed that has never
                      existed under either name
    round 3  PASS x2

⭐ Every one of the three passed `dbt parse`, SQLFluff, four offline gates, `pytest` and a full
read-only verification against live prod. None of them is the kind of defect those instruments look
for: two were false sentences about code, and one was an asserted safety net.

## analytics-engineer-reviewer
VERDICT: PASS (round 3)
risks_checked:
- ⛔ **ROUND 1: it found that the fix could not reach prod at all.** `fct_fixture_player_stats` and
  `fct_fixture_team_stats` are both `materialized='incremental'` on a bare `raw_ingested_at`
  high-water mark that a finished fixture never advances, so the corrected rows are never
  re-processed on the nightly's bare `dbt build` — `base_apif__teams` would drop 22722 while the
  fact kept 21 rows carrying it, producing the exact orphan this MR exists to prevent, plus both new
  guards red in prod. My contract asserted the opposite.
- ⭐ And it closed the obvious escape before I could take it: copying the events self-heal does not
  work, because `fixture_player_stat_sk` hashes `(fixture_id, league_code, team_id, player_id)` and
  `fixture_team_stat_sk` hashes `(fixture_id, league_code, team_id)` — correcting `team_id` CHANGES
  the unique key, so a merge inserts the corrected row and strands the old one, which dbt never
  deletes. `event_sk` excludes `team_id`, which is the only reason its self-heal works. It then
  checked that a key REDEFINITION is not an escape either, since that itself forces a full refresh.
- **ROUND 2: it found a safety net that does not exist.** The contract claimed the seed carried a
  `relationships` test from `correct_team_api_id` to `dim_team.team_api_id`. It never did, under
  either name — I had misattributed a block belonging to `team_name_overrides`, the next seed in the
  same file. It argued the hole rather than just the wording: the value is hand typed, this seed is
  the registry for the NEXT mis-attribution, and a typo silently re-points a fixture's rows at
  whichever real team the mistyped id names — which neither participant guard can catch, because
  they only ask whether the team played the fixture.
- **ROUND 3** verified the added test is non-cyclic by finding the identical pattern already live on
  `team_name_overrides` in the same file, rather than reasoning about dbt's DAG; confirmed
  `team_api_id` is a real column on `dim_team`; and confirmed `wrong_team_api_id` correctly gets NO
  such test, because two of its four values are precisely the keys this MR retires — a test there
  would be red by design.
- It swept INVERTED as asked and reported two-sided: roughly a dozen statically checkable claims
  re-read against the tree, zero false this round. It was explicit that the prod row counts and the
  slug ladder are not independently re-runnable from its tool set, rather than implying it had
  checked them.
- Across the rounds it also verified: all four copies of the override join condition by condition
  with no drift; that the correction precedes each dedup and the collision guard reads post-override
  ids; that `base_apif__fixtures_next` carries a uniqueness test on `fixture_id` so the participant
  join cannot fan out; that adding `fixture_id` to `stg_fixture_level` is inert for
  `fixture_level_team_names`; and that base→base `ref()` is permitted by `layering.md:196`.
- ⚠ It named the key/name asymmetry under `alias` mode without failing on it — a folded key takes
  its name from the canonical id's sources, never the duplicate's. Written into the model as a
  comment rather than left implicit.

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- ⛔ **ROUND 1: it caught a false acceptance criterion and the undisclosed consequence behind it.**
  The contract said `base_apif__teams` "emits the same key set as main otherwise". It does not: the
  new key CTE applies the seed's pre-existing Riga FC `alias` row unconditionally, so `(UEL, 2263)`
  is removed too — a live team-identity change disclosed nowhere in `blast_radius`.
- **ROUND 2** it then RULED on the §10 question rather than deferring it: the `alias` semantics were
  CPO-approved under #526 and already documented in the seed's own `schema.yml` as "replace
  unconditionally", so wiring them to the key-minting logic completes an approved rule rather than
  taking a new decision — *"requiring approval for every consequence of a rule already approved in
  general form"* is what it declined to do. It required the disclosure AND the measurement, and got
  both.
- It swept every number in both artifacts INVERTED rather than grepping the phrase it had flagged,
  and reported them cross-consistent and arithmetically reconciling (1,875,217 + 21 = 1,875,238).
- Judged the new `deploy_order` legitimate: a one-off ~0.39 GiB command, disclosed with its reason
  and its safety measurement, presented as a recipe for the CPO to run rather than a decision taken
  on his behalf, and not crossing the recurring-cost line.
- Confirmed the seed rename is complete — no live `ref()` anywhere still names the old seed — that
  every diffed path is in `scope_paths`, that `decisions_reserved` still defers three genuinely
  unrelated items, that no guard was loosened or deleted, and no credentials.

## escalations
- **RULED: fix the nameless team, approach A** — *"go with A"*, `escalations.log:8098`.
  ⛔ A alone was then MEASURED insufficient and he was told before anything was built; the enlarged
  plan was approved in plan mode.
- **RULED: the seed's new name** — `fixture_team_id_overrides`, `escalations.log:8124`. The columns
  and the two modes were not put to him: those are form, and the transformation layer decides form.
- **OWED, and it is his to run:** one command at merge,
  `dbt build --full-refresh --select fct_fixture_player_stats fct_fixture_team_stats`. Not a
  decision — a step, with its reason and its safety measurement in `acceptance_evidence.md`.

## ⛔ WHAT THIS BRANCH SHOULD BE REMEMBERED FOR

**1. The bug report named one team; the guard found three.** Running the existing event guard's
predicate against the other two fanout facts BEFORE writing any code returned two offenders, not
one — and applying the seed uniformly retired a third id. The reported defect was the newest and
least interesting of them: Mação's team-statistics row had been wrong in prod since #53 diagnosed
and registered it, because the correction was wired to one feed of three.

**2. A correction that cannot reach the table it corrects is not a fix.** The whole verification
method here — compile the model, run it read-only against prod — measures what the LOGIC computes.
It is blind to what an incremental TABLE will contain, and both target facts are incremental. Every
number in the evidence was right and the change would still have broken the nightly.

**3. Three defects, three sentences I wrote from memory.** Which model is incremental, how many keys
move, which test exists. Each was checkable in seconds by opening the file, and each survived every
automated instrument the repo has, because none of them reads prose looking for a claim to falsify.

**4. The reviewer that found the §10 problem also ruled it discharged.** It did not escalate the
Riga FC key removal upward for a fresh ruling; it traced the `alias` semantics to their existing
CPO approval, demanded the disclosure and the slug measurement, and then decided. Escalating every
consequence of an approved rule is its own failure mode.
