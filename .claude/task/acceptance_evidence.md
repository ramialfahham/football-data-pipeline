# Acceptance evidence — #82 MR4c: writing the definitions that did not exist

Every number measured on this branch against merged main `bf0e23c`. Where a measurement
contradicted an expectation, the contradiction is what is recorded.

## The headline

| | |
|---|---|
| blank in-scope columns | **422 → 323** |
| names given a definition | **56** — 22 shared blocks, 34 written inline |
| sites filled | **99 in-scope**, plus 2 in base that the gate's rule reaches |
| docs blocks in `shared_columns.md` | 40 → 62 |
| deleted lines in the whole diff | **1**, in `seeds/schema.yml` |
| longest RENDERED column description | 936 chars, cap 1024 |
| suite | 1007 passed, 1 skipped, 14 subtests — measured on this branch |

## What is different about this MR, said before the evidence

The three merges before this one MOVED text whose truth had already been established somewhere:
generated from the metric seed, or promoted from a model that already carried the sentence. **This
one authors 56 new claims about what a column holds, and nothing in the repo can check a claim
about meaning.** `dbt parse`, the hygiene gate and the 1,024-character cap all pass on a sentence
that is confidently wrong.

So the machine evidence below proves the mechanics — that the right sites were filled, that
nothing was overwritten, that the endings and lengths are sound. It proves nothing about whether
the sentences are TRUE. That is the trace section, and it is the part worth a reviewer's time.

## The mechanics, measured

Blank-column counts read from the RAW YAML at the merge base and on the branch. Not from the
manifest, which stores the RESOLVED description and cannot tell a wired column from an inline one:

```
blank in-scope columns : 422  ->  323   (closed 99)
described in-scope     : 1277 -> 1376   (added 99)
blocks added: 22
  sites of those names: 67 referencing the block, 0 inline, 0 still blank
```

`git diff --numstat`, and the shape is the claim: **every model yml is additions only.**

```
  2  0  models/2_base/api_football/base.yml
 39  0  models/3_core/core.yml                       (20 wired + 19 inline)
  1  0  models/4_intermediate/.../int_team_season.yml
  8  0  models/4_intermediate/shared/int_legs.yml
  2  0  models/4_intermediate/shared/int_momentum.yml
  5  0  models/4_intermediate/shared/int_momentum_window.yml   (2 wired + 3 inline)
  1  0  models/4_intermediate/shared/int_player_club_season.yml
  1  0  models/4_intermediate/shared/team/int_team_market_value.yml
  3  0  models/5_marts/domestic_league/domestic_league.yml     (1 wired + 2 inline)
 39  0  models/5_marts/shared/shared.yml             (29 wired + 10 inline)
146  0  models/docs/shared_columns.md
  1  1  seeds/schema.yml                             <- the only deletion
```

101 added lines across the model ymls = 67 wired + 34 inline. The single deletion is
`prompt_version`, explained under "the one promotion" below.

⚠ **Line endings read as BYTES, because `git diff` normalises them** and this programme has
already hidden a whole-file rewrite behind a clean diff. All 13 files: **0 doubled CRs, every file
uniform.**

That check earned its place immediately. The first run of the block insertion wrote **110
`\r\r\n` sequences** — text built with `\r\n` and then converted again — and `git diff --numstat`
reported it as `400 added / 254 deleted`, a whole-file rewrite. Reverted and fixed before anything
else was done. **The numstat saw it; a review of the rendered diff would not have.**

⚠ **The checker's own first version was wrong too, and is worth saying so nobody rebuilds it.** It
compared the working copy against the stored blob and reported 12 files as "endings flipped". The
repo stores LF and this checkout is CRLF, so that comparison flags every file in the tree. What
matters is doubled CRs and per-file uniformity; that is what it checks now.

## No lineage change, proven rather than asserted

`git diff --name-only` filtered to anything that is not `.yml` or `.md`: **none**. `depends_on` is
built from `ref()` and `source()` in the SQL, so no SQL file changing is a stronger proof than
comparing two manifests, and it costs nothing.

`dbt parse` clean. Manifest: **1849 columns, 0 unrendered `{{ doc(` or `{%`** — every reference
resolves.

## The one promotion, and the one deleted line

`prompt_version` was **not authored**. Its definition already existed in `seeds/schema.yml` and
nowhere else, so the block's body is that sentence copied verbatim and the seed now references it.

```
before  description: "Version of the research prompt or ingest job (e.g. wc_squad_value_v1)."
after   description: "{{ doc('prompt_version') }}"
block   Version of the research prompt or ingest job (e.g. wc_squad_value_v1).
```

Rendered text identical. Leaving the seed's copy in place would have left the same words in two
files, which is the restatement the standard bans — so this costs one deleted line and removes a
future contradiction.

## The trace: what each sentence rests on

Every sentence was written from the SQL that produces the column, at **every** model the text
reaches. The previous merge lost a name to reading the sentence and finding it plausible while the
SQL said otherwise, so what is recorded here is the SQL, not a restatement of the description.

**The 22 shared blocks.** The claim that needed checking is in the right-hand column — the part
that could be true at one site and false at another.

| block | sites | traced to | the claim under it |
|---|---|---|---|
| `coach_api_id` | 2 | `dim_coach.sql:14`, `dim_coach_team_mapping.sql:19` — both `cast(coach_api_id as int64) as coach_sk` | that `coach_sk` IS this value cast, at both |
| `coach_sk` | 2 | same two lines | that it is `dim_coach`'s own key |
| `fouls` | 2 | `base_apif__fixture_statistics.sql:37` `stat_type = 'Fouls'` | NULL-not-zero: the pivot is `max(case when …)`, so a missing line yields NULL |
| `fouls_committed` | 5 | `stg_apif__fixture_players.sql:73` `$.fouls.committed`; `int_legs__team_from_players.sql:36` `sum(fouls_committed)` | **that one of the five sites is TEAM-grained.** The sentence says so rather than calling it a player's fouls |
| `fouls_drawn` | 5 | `stg…:72` `$.fouls.drawn`; `int_legs__team_from_players.sql:37` | same team-grained site |
| `goal_diff` | 3 | `mart_team_season.sql:45` `goals_for_sum_season - goals_against_sum_season`; the other two select it | that it is computed here, not read from a published table |
| `home_away` | 4 | `int_legs__team_match.sql:58,83` literals `'home'`/`'away'`; `int_legs__player_match.sql:100` `case when ps.team_sk = f.home_team_sk` | that it is always one of two, and follows the NOMINAL home side — so a neutral venue still has one |
| `is_captain` | 2 | `stg…:49` `$.games.captain` | NULL ≠ false: `safe_cast(json_value(…) as bool)` yields NULL when absent |
| `is_substitute` | 4 | `stg…:50` `$.games.substitute`; `fct_fixture_player_stats.sql:43` `is_starter = minutes > 0 and not is_substitute` | **bench selection, not appearance.** `int_player_club_season__metrics.sql:106-108` records 382,942 of 1,677,854 rows as 0-minute bench selections |
| `minutes_played` | 4 | `stg…:46` `$.games.minutes`; `coalesce(minutes_played, 0)` throughout the legs models | that NULL is real and distinct from 0 |
| `penalty_missed` | 2 | `stg…:79` `$.penalty.missed` | — |
| `penalty_saved` | 2 | `stg…:80` `$.penalty.saved` | that it is the KEEPER's side, not a miss |
| `penalty_scored` | 2 | `stg…:78` `$.penalty.scored` | that it is the statistics line, a different source from the event feed — see the finding below |
| `prompt_version` | 3 + seed | promoted, not authored | — |
| `red_cards` | 2 | `base_apif__fixture_statistics.sql:49` `stat_type = 'Red Cards'` | that it is the team's own line, NOT a sum of player cards — `cards_red` is a separate player metric |
| `shirt_number` | 2 | `stg…:47` `$.games.number`, at fixture grain | that it is per MATCH, not a squad registration |
| `shots_blocked` | 2 | `base_apif__fixture_statistics.sql:31` `stat_type = 'Blocked Shots'` | **direction.** It sits in the shots family beside on/off-goal, inside/outside-box, so it is the team's OWN attempts that were blocked, not blocks it made |
| `shots_off_goal` | 2 | `base…:27` `'Shots off Goal'` | NULL-not-zero |
| `shots_outside_box` | 2 | `base…:35` `'Shots outsidebox'` | NULL-not-zero |
| `starts` | 3 | `int_player_club_season__metrics.sql:111` `countif(is_starter)`; `int_player_season__metrics.sql:39` `sum(starts)` | that a start REQUIRES pitch time, via `is_starter`; and that club rows re-sum to season |
| `upcoming_fixture_sk` | 8 | `int_team_momentum_window.sql:45`, `mart_team_season_record.sql:27`, `mart_player_season_record.sql:26` — all `status_short in ('NS','TBD')` on `fct_fixture`; the other 5 inherit it | that all eight mean the same not-yet-played fixture. Checked at each, not assumed from the three |
| `yellow_cards` | 2 | `base…:47` `'Yellow Cards'` | as `red_cards` |

**The 34 inline sentences** are single-site by construction, so the widest-call-site problem cannot
arise. Each was still written from its own SQL; the ones carrying a claim beyond "what the provider
sent" are:

- `has_result` / `is_upcoming` — `mart_team_fixtures.sql:104-105`. `l.fixture_sk is not null` and
  `status_short in ('NS','TBD')`. **They are not complements**: a postponed or abandoned fixture is
  false on both. Both descriptions say so, because negating one to get the other is the natural
  mistake and it silently drops rows.
- `upcoming_rank` — `mart_team_fixtures.sql:136-140`. `is_upcoming` is IN the `partition by`, so
  the ranks run 1..n over upcoming fixtures with no gaps; and the partition includes
  `league_code, season_api_year`, so it is per competition-season, not per team overall.
- `is_knockout` — `macros/is_knockout_round.sql`. A regex over the provider's free-text round name,
  `coalesce(…, false)`. The description calls it a heuristic and says a false is not a promise,
  because the macro's own header says it may need per-competition tuning.
- `is_canonical` — `mart_head_to_head.sql:127` `a.team_sk < a.opponent_team_sk`. True on exactly
  one of the two directed rows.
- `top_player_rank` — `mart_player_momentum.sql:75-82`. `row_number()` over goals, assists, key
  passes, then `player_sk`. A selection order with no ties, not a rating.
- `team_name_snapshot` / `player_name_snapshot` — `fct_fixture_event.sql:85-86`, straight from the
  events feed. Described as a record of what the feed said and explicitly **not a name to
  display**, which matters while entity names are being corrected elsewhere.
- `team_in_sk` / `team_out_sk` — `fct_transfer.sql:34-35`. Described as a SOFT link, because
  `dim_coach_team_mapping`'s header states the same thing for the same reason: the career team set
  exceeds the tracked set.
- `end_date` — `stg_apif__coach_career.sql:31` `$.end`. NULL means current **or** omitted, so the
  description refuses to promise the coach is still in post.
- `leg_league_code` / `played_league_code` — `int_team_momentum_window.sql:109`,
  `mart_team_momentum_window.sql:64`. The window is cross-competition, so this can differ from the
  upcoming fixture's competition.
- `coach_age` — `stg_apif__coaches.sql:32` `$.coach.age`. A point-in-time value from the feed, so
  the description points at `coach_birth_date` for anything computed.

## What was planned and is NOT here, with the reason

The approved plan sized this at 77 names / 183 columns. **56 names / 99 columns shipped.** Nothing
was quietly dropped; two classes came out, both because the SQL says something the name does not.

**13 names mean different quantities at different sites.** Classified by machine — every site of
every candidate labelled by what its own model's SQL does with the column:

```
goals_for   (12 cols)  per-row int_legs__team_match / mart_team_season / mart_team_fixture_stats
                       AGGREGATE int_team_momentum__metrics, mart_head_to_head
                       WINDOW-CUMULATIVE int_team_season_record
```

`f.goals_home` in one model and `sum(goals_for) over w` in another. One block cannot be true at
both. The other twelve: `goals_total`, `goals_assists`, `shots_on`, `shots_inside_box`,
`corner_kicks`, `goalkeeper_saves`, `key_passes`, `tackles`, `blocks`, `interceptions`,
`clean_sheet_games`, `substitute_appearances`. They need either two blocks each or per-site text,
which is the grain question the next merge exists to settle — and writing one sentence for a name
that means two things is precisely what pulled six names from the previous MR.

**7 names belong to families the plan defers.** The plan's table counted them as plumbing because
they are key-shaped and date-shaped; they are head-to-head and opponent-mirror members and travel
with their family: `last_meeting_at`, `last_meeting_league_code`, `pair_key`,
`recent_meetings.kickoff_datetime`, `recent_meetings.league_code`, `opponent_name`,
`opponent_logo_url`.

## Two findings for the CPO, neither fixed here

**1. A column that is a catalogue metric under a different column name is invisible to the
generator.** `key_passes_prev_season_full` is the metric `passes_key` (entity=player) with the
`_prev_season_full` affix. Its four siblings — `goals_prev_season_full`,
`assists_prev_season_full`, `shots_on_goal_prev_season_full`, `defensive_actions_prev_season_full`
— all carry generated text and it is blank, because the generator matches metric ids and the
column is named the other way round. Writing it inline would define a catalogue metric outside the
catalogue, so it is left blank. The fix is a rename, which is a naming decision and needs
`--full-refresh` on an incremental model. `key_passes` and `blocks` at team level are the same
shape.

**2. The pipeline's penalty-goal figure does not come from the provider's penalty field.**
`int_legs__player_match.sql:46-52` derives `goals_penalty` by counting events
(`event_type = 'Goal' and event_detail = 'Penalty'`), while `penalty_scored` is
`$.penalty.scored` off the player statistics line. Two sources for one real-world quantity, and
they will not always agree. `penalty_scored`'s description says which source it is and stops
there; whether the two should be reconciled is not a description question.

## Not in this MR

The 13 multi-meaning names and the 48 derived families. The 31 names whose written sites disagree
with each other. The team columns waiting on the ruling about the seven player-only metrics. The 5
nested `recent_meetings.*` fields, which cannot be docs blocks at all. MR5, which switches the
presence rule on.
