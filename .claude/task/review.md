# Review — feat/82-mr4c-write-plumbing-and-stats — 2026-08-25

diff_sha256: 71940ef320abd22e01f5015f40bc23989516ddb5592378bdd56b3df5bdf3ad4a

rounds: 2

⚠ THIS IS THE FIRST MERGE IN THE PROGRAMME THAT AUTHORS RATHER THAN MOVES TEXT. 56 new claims
about what a column holds, and nothing in the repo can check a claim about meaning: `dbt parse`,
the hygiene gate and the length cap all pass on a sentence that is confidently wrong. The machine
evidence proves the mechanics only. The sentences themselves needed a reader.

⚠ A THIRD READER WAS ADDED BEYOND ROUTING. `football-analytics-expert-reviewer` is routed only to
`metric_catalogue.csv`, which is untouched — but 22 of these sentences make football claims and no
routed reviewer is briefed for that. Routing is a minimum, not a ceiling.

## analytics-engineer-reviewer
VERDICT: PASS (round 1)
risks_checked:
- It hit the same stale `review_input.patch`, said so, and then reviewed the on-disk YAML and SQL
  directly rather than certifying the wrong diff. Every verdict below rests on that ground truth.
- ⛔ THE WIDEST-CALL-SITE CHECK, done independently for all 22 blocks. `fouls_committed` and
  `fouls_drawn` at five sites each: four player-grained from `stg_apif__fixture_players.sql:72-73`,
  plus `int_legs__team_from_players.sql:36-37` which sums them to TEAM grain — the block's caveat
  covers it, holds at all five.
- `upcoming_fixture_sk` at all 8: `int_team_momentum_window.sql:45`, `mart_team_season_record.sql:27`
  and `mart_player_season_record.sql:26` all filter `status_short in ('NS','TBD')` on `fct_fixture`;
  the momentum models inherit the same key. Holds at all eight.
- `starts` at three different grains — `countif(is_starter)`, `sum(starts)`, and a passthrough at
  `mart_player_profile.sql:140`. Text holds at all three.
- `goal_diff`: only `mart_team_season.sql:45` computes it; the other two select it. Compatible.
- `shots_blocked`'s direction corroborated from a second source I had not used — the catalogue's own
  `shots_per_match` and `shot_accuracy` rows state that team shots include blocked ones, so
  "Blocked Shots" is part of the team's own breakdown. Also confirmed it is a genuinely distinct
  concept from the `blocks_per_match` metric, and that the block's disambiguating sentence prevents
  the collision rather than creating one.
- NULL semantics for `minutes_played`, `is_substitute`, `is_captain`, `shirt_number` traced to
  `safe_cast(json_value(...))` in staging, which yields NULL on an absent field.
- `prompt_version`'s promotion: block body byte-identical to the replaced inline text.
- Multi-meaning exclusion spot-checked: `goals_for` confirmed still blank at all 12 sites across six
  files — declared as deferred and not quietly authored.
- Catalogue governance, layer contract, and competition-agnosticism all checked; no `.sql` touched.

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- ROUND 2: confirmed the regenerated patch carries exactly the 13 files in `scope_paths`, with no
  script, test, SQL or workflow file — consistent with the "no mechanism" claim.
- Re-derived both figures my own audit had fixed rather than taking them on trust: the arithmetic
  `77 − 13 − 7 − 1 = 56` / `183 − 71 − 11 − 2 = 99`, and the 102 description-adding lines, which it
  counted independently as 68 `{{ doc() }}` + 34 inline. That 68 is the 67 blank sites plus the
  seed's replaced line; 101 are net-new and the 102nd renders identically.
- ⛔ CHECKED THE NARROWING FOR COMPLETENESS, which is the thing I most wanted attacked: it grepped
  all 13 multi-meaning names, all 7 family names and `key_passes_prev_season_full` against the diff
  and confirmed NONE received a description. Nothing was declared deferred while being written.
- Swept every integer it could verify: 22 blocks added, 62 total, per-file wired/inline splits
  spot-checked against the raw diff for three files, and the deleted-line count of exactly 1.
- Established that `contract.md`'s own self-rewrite carrying deletions is the same convention the
  merged `!101` contract used, so "no other file carries a deletion" is precedent, not imprecision.
- Confirmed no metric-catalogue id collides with any of the 22 block names or the notable inline
  ones, so no sentence here defines a metric outside the seed.
- Swept the whole diff for credential-shaped strings: zero.
- Ruled the third, non-routed reviewer legitimate: routing is a floor, not a ceiling.
- ROUND 1 FINDINGS, kept because the cause is worth more than the fix:
- ROUND 1 FAIL: `review_input.patch` was still MR4b-2's, a different and already-merged task —
  17 files including `scripts/declare_missing_columns.py` and `tests/test_declare_missing_columns.py`,
  none of them in this contract's scope_paths, and `seeds/schema.yml` absent entirely. The auditor
  refused to certify anything from it and was right to: that patch is the channel the diff reaches
  reviewers through, so a stale one binds a verdict to the wrong work.
- ⛔ THE TRAP WAS ALREADY WRITTEN DOWN, in `active_work.md`'s own list: "`--review-patch` writes to
  STDOUT, so without redirect the patch is silently the PREVIOUS task's." Recorded, and not applied.
  Regenerated: 13 files, exactly this branch's set.
- It cross-checked the live tree rather than only the patch, and confirmed two load-bearing claims
  independently — 62 docs blocks in `shared_columns.md`, and `seeds/schema.yml:399-400` already
  pointing `prompt_version` at its block. That is why it reported a stale artifact rather than a
  fabricated MR.

## football-analytics-expert-reviewer
VERDICT: PASS (round 1)
risks_checked:
- `shots_blocked`'s DIRECTION confirmed against `base_apif__fixture_statistics.sql:24-35`: the
  pivot follows the provider's shot-breakdown block, so it is the team's own attempts that were
  blocked. It also noted the description correctly disambiguates from the player-grain
  `tackles_blocks`, whose existing doc reads "Shots blocked" and means the opposite direction.
- `red_cards`/`yellow_cards` — confirmed these come from the fixture-statistics endpoint and no
  code sums player cards into them, so "not a sum of its players' cards" is accurate.
- `is_substitute` — checked against `int_player_club_season__metrics.sql:103-115` including the
  382,942-row measurement; the bench-selection claim matches the code and its rationale.
- `starts` — confirmed the description states the computed rule (`is_starter = minutes > 0 and not
  is_substitute`) rather than the looser "named in the XI", and does not hide that a 0-minute
  starter is excluded.
- `home_away` — confirmed no venue-based override exists anywhere in the chain, so the
  neutral-venue claim holds for World Cup and cup finals.
- `is_knockout` — confirmed the caveat describes the real risk: an unrecognised round-name shape
  returns false by `coalesce` and would be treated as round-robin.
- Redefinition sweep over `metric_catalogue.csv` for every name discussed: no collisions.
- ⚠ ONE OPEN ITEM, honestly reported rather than resolved: whether the provider's per-player
  `$.penalty.*` fields fold in shoot-out kicks cannot be settled from this codebase. The
  descriptions do not claim either way, and the catalogue's penalty-goal metric is event-sourced,
  so no metric compounds the uncertainty. Not a defect; worth knowing.

## escalations
- none
