# Review — refactor/metric-rename-player-shooting — 2026-08-30

> **STEP 4 of the metric catalogue naming programme, MR 1 of seven.** The three player `shooting`
> metrics: `shots_total` → `shots_player`, `shots_on_goal` → `shots_on_goal_player`,
> `finishing_efficiency` → `finishing_efficiency_player_pct`, PLAYER entity only. Branched from main
> `1fa7e5f`.

diff_sha256: 97f964957e77e83c62bdf568dfa3f10a5c2e55d7a3614301af93dd1b919ca0e0

rounds: 3

⛔⛔ **THE FIRST TWO ROUNDS BOTH FAILED, ON ONE DEFECT, AND THE HISTORY IS RECORDED RATHER THAN
TIDIED.** Round 1 FAILED 4–1 and was fully reverted with nothing committed. Round 2 FAILED 5–0.
Every failure was the same mistake in a different shape: **for dotted reads I asked "did the source
relation rename this column?", and for bare reads I asked "does the alias match the inner name?"**
Those questions agree most of the time and disagree exactly where it matters. Corrected to one rule
applied uniformly across alias / dotted / bare / prose / seed. Round 3 is the cap and all five
reviewers PASS with no open findings.

⚠ **ONE IMPRECISION RAISED AT ROUND 3 AND NOT FIXED IN PLACE.** `platform-reviewer` noted that
`contract.md`'s "no gate in this repo resolves a column reference" overreaches —
`assert_metric_catalogue_expr_resolvable.sql` does, for the seed's formula fields, against a live
warehouse. It judged this an imprecision, not a defect, since the sentence is true inside the "nine
OFFLINE gates" framing its own paragraph opens with. Correcting `contract.md` would void all five
verdicts and force a round 4 past the cap, so **the correction is appended to `escalations.log`**
(hash-excluded) instead. Named here so no reader has to infer it.

## scope-auditor
VERDICT: PASS
risks_checked:
- The round-2 defect at `int_player_season__metrics.sql:45-46` now reads `sum(shots_player)` /
  `sum(shots_on_goal_player)` from `club_season = ref('int_player_club_season__metrics')`, which
  renames those same aliases at `:120-121`. Chain resolves; no dangling column.
- `docs/wireframes/03_player_profile.md` (bi-analyst's round-2 defect) is absent from the patch
  entirely and absent from `scope_paths` — the erroneous prose rename reverted and scope corrected.
- The seed's formula fields keep `sum(shots_total)` / `sum(shots_on)` against `int_legs__player_match`,
  a provider relation that does not rename — the round-1 defect class, still fixed.
- `core.yml` and `int_legs.yml` move only `doc()` references; the `name:` column fields stay
  `shots_total` / `shots_on_goal`, matching both CPO rulings.
- The `escalations.log` hunk is a pure addition — no line removed or edited — and the record
  correction's arithmetic (48 seed rows − 35 renamed = 13 unchanged = 12 `_per90` +
  `minutes_per_appearance`) checks out independently.
- `scope_paths` reconciled against every file in the patch, both directions.
- `decisions_reserved` honestly withholds the CI-gate call rather than taking it; no other §10-class
  decision appears without a quoted ruling. No credentials, no threshold crossings.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Traced the full composition chain that broke in both earlier rounds — `int_legs__player_match` →
  `int_player_club_season__metrics` → `int_player_season__metrics` → the marts — and it resolves at
  every hop. `finishing_efficiency_player_pct` and `shots_on_goal_per90` consistently reference the
  renamed column.
- Reads that must NOT move, verified unmoved: `int_player_club_season__metrics.sql:67-68` (`s.` =
  `fct_fixture_player_stats`), `int_player_momentum__metrics.sql:67-68` (`p.` =
  `int_legs__player_match`), `int_player_season_record.sql:50-51` (bare, from the legs).
- Reads that must move, verified moved: `mart_player_profile.sql:146,180-182,194` (`a.` = season,
  `y.` = yoy), `mart_leaderboards.sql` (`s.` = season), `int_player_profile__yoy.sql`'s four
  `shots_on_goal_player_*` write-columns.
- Seed rows: `metric_id` renamed, `base_relation` / `numerator_expr` / `denominator_expr` untouched.
- Doc blocks: no `doc('shots_total')` / `doc('shots_on_goal')` / `doc('finishing_efficiency')`
  reference remains anywhere; the three orphaned blocks removed with their owning TEAM columns left
  bare rather than dangling.
- The three PLAYER `accepted_values` lists moved; the three 22-name TEAM lists are byte-unchanged and
  absent from the diff. Repo-wide sweep found no half-renamed name.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Its round-1 finding (seed formula naming a nonexistent column) re-verified fixed: all three rows
  read the actual upstream leg columns, not the new metric ids.
- Its round-2 finding (bare read of a renamed relation) verified fixed at `:45-46`.
- Naming authority: all three renames verbatim in the log's "PLAYER, 35 REMAINING" table, with
  `_player` before the trailing `_pct` per RULING 5's quoted shape.
- Definitions byte-identical across every field of the three seed rows except `metric_id` —
  label keys, label_en, description, base relation, format, group, tier, direction, interpretation.
- `higher_better` is football-correct for all three; none is a conceded/cards class.
- **Meaning preserved at every grain it is computed**: season and position keep the identical
  NULL/zero-cap logic; club-season and momentum correctly do not compute the ratio at all, which is
  pre-existing design, so no coverage or NULL policy was silently introduced or dropped.
- No cross-entity leakage: the TEAM catalogue rows still read `int_legs__team_match` under the
  original column names.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Its round-2 headline defect verified fixed, and every dotted/bare read in every touched model
  traced against its actual source — not only the previously-broken one. No broken reference found.
- Provider / per-match surfaces genuinely untouched per the "yes" ruling, including
  `03_player_profile.md:126` now reading `shots_total` verbatim.
- ⭐ Found and named the contract imprecision recorded above — `assert_metric_catalogue_expr_resolvable.sql`
  already resolves the seed-formula surface against a live warehouse, so the categorical claim
  overreaches. Judged an imprecision, not a defect.
- The three claimed-orphaned doc blocks confirmed genuinely unreferenced tree-wide.
- Borrowed-doc-block re-pointing verified across five ymls: column names unchanged, only `doc()`
  moved — consistent with the 1604 description count being base-identical.
- `_LEADERBOARD_METRICS` / `_LB_KEEP` correctly updated with no stale sibling, and its round-2
  observation that these are pinned by no test is confirmed recorded in the log rather than lost.
- Nothing loosened: no hook, workflow, CI file, gate script, requirements or lockfile appears in the
  patch at all. No new LT05.
- Confirmed the log records both failed rounds plainly, including that the builder's own resolver
  repeated in miniature the mistake it was built to catch.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Its round-2 finding verified fixed: `03_player_profile.md:126` reads `shots_total`, the file is
  absent from the diff, and `scope_paths` no longer lists it.
- The remaining four wireframes checked occurrence by occurrence: every renamed mention binds to a
  surface that actually renamed (`mart_leaderboards`' board list, the benchmark chain); every
  remaining old-name mention binds to one that did not (the TEAM stems, and the distinct
  `shots_on_goal_against` goalkeeping metric).
- Binding rule: repo-wide grep shows none of the three old names or three new names anywhere in
  `site_v2/src` outside `src/data`. `TopPlayer.shots_on` traced through the untouched
  `mart_player_momentum` back to an unrenamed `sum(p.shots_on) as shots_on` — the field the frontend
  reads never moved.
- The rendered-page evidence is structural, not substring, and explicitly distinguishes "prediction
  confirmed" from "proof of work", pointing at the whole-token grep and gate results as the proof.
- No user-facing wording change: `label_i18n_key` and `label_en` byte-identical for all three rows;
  no `site/i18n/**` or `site_v2/src/i18n/**` file in the diff.

## escalations
(none)
