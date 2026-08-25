# Acceptance evidence — #82 MR4b: the derived metric columns

Every number measured on this branch, from the source the contract names. Where a measurement
contradicted an expectation, the contradiction is what is recorded.

## The headline, and it is smaller than the plan said twice over

| | |
|---|---|
| blank in-scope columns before | **635** |
| blank in-scope columns after | **508** |
| closed here | **127 wired + 3 that kept their sentence behind a reference** |
| generated blocks | 161 (80 metric + 81 derived) |
| files touched | 5 model ymls, 2 scripts, 2 test files, 1 generated `.md` |
| suite | 998 passed, 1 skipped — collection 977 stashed / 999 applied |
| review | **4 rounds, 6 real defects, 1 of them found by me** |

The plan said 251 columns. The figure moved four times and each move is a contract amendment:
251 → 214 (seven catalogue metrics are player-only, so 48 team columns have nothing to point at)
→ 110 (the promotion half needs a line-REPLACING mode this append-only tool does not have, and
moved to its own MR) → 132 (a decomposition fix found by mutation testing unblocked 22) → **130**
(totalling a rate is a different quantity, so one name gets no block).

⚠ **A SECOND EFFECT, outside the 130 columns.** Disabling hyphen-breaking in the wrapper corrects
the stored text of **3 blocks that shipped in `!98`** — `deserved_points`, `shots_per_match`,
`sot_points_gap`. Measured by rendering both versions and comparing whitespace-normalised, not
estimated; the same comparison proves no other block's text moves at all.

## ⛔ The finding: a fifth of the derived names would have carried the wrong definition

Composing the first blocks and READING them showed `goals_against_sum_season` — a column that
exists only on TEAM models — taking the catalogue's `goals_against`, which the catalogue defines
for a PLAYER: *"goals conceded by the team while the player was on the pitch (GK-relevant)"*.

**21 of 76 derived names had that shape.** Nothing automatic would have caught it: the block
resolves, the rendered length is fine, the YAML parses, `dbt parse` is clean, and
`check_description_hygiene` sees a description where it wants one. It reaches the warehouse and
reads as authoritative.

Verified at the source rather than inferred — seven metrics hold exactly one catalogue row,
`entity = player`, while team models use the same names:

`goals` · `goals_against` · `defensive_actions` · `shots_on_goal` · `shots_total` ·
`passes_accurate` · `passes_total`

**The obvious fix was the wrong one.** Teaching the generator which models are team-scoped is the
classifier this repo has already failed at three times. A fourth attempt, written only to measure
the damage, left 2 of 12 models unresolved.

**So the generator was made unable to be wrong rather than cleverer.** Every derived block is
emitted with an entity suffix, whether or not its metric is split. A metric the catalogue never
defined for a column's entity therefore has no block to point at, and the column stays blank and
visible instead of documented and wrong.

**Cost, stated not buried: 48 columns cannot be closed by anyone but the CPO.** They are listed by
the wiring tool on every run, and reserved in the contract. Writing team definitions into the
model YAML is the drift this programme exists to remove, and the catalogue is his.

## Mutation testing: 7 mutations, 4 killed, **3 survived — and each survivor was a real defect**

This is the part worth reading.

| mutation | result | what it exposed |
|---|---|---|
| drop the entity suffix | **killed** | — |
| reverse the affix order | **SURVIVED** | the test could not fail, AND the rule was wrong |
| delete the dotted-name filter | **SURVIVED** | the guard was unreachable |
| delete the emitted-name check (its replacement) | **killed** | — |
| disable the derived floor | **killed** | — |
| swallow a YAML parse error | **killed** | — |
| disable the clash guard | **killed** | — |
| delete the same-entity guard | **SURVIVED** | duplicated a guard that runs first |

**(a) The affix-order rule was wrong, not just untested.** `_decompose` tries every affix and only
accepts a stem that is a real metric, so order is irrelevant unless two decompositions are valid —
which made the "longest affix first" test unfailable. And where two ARE valid, longest-affix-first
picks the worse one: `goals_per_match_this_season` becomes `goals` + "divided by matches played"
instead of `goals_per_match` + "this season", silently dropping the null policy the catalogue
wrote for that rate. Changed to **longest stem wins**, i.e. the most specific metric.
⭐ **That fix closed 22 further columns**, because they now resolve to a team-scoped rate metric
rather than a player-only count — so the entity matches and a block exists.

**(b) The dotted-name filter was dead code.** A dotted name cannot decompose at all: the dot always
lands in the stem and no metric id contains one. Replaced with a check on the names actually
EMITTED, which is reachable the moment anyone adds an affix containing a dot — and which dies to
its own mutation.

**(c) The same-entity guard duplicated one that runs first.** Deleted, along with the test that was
unknowingly exercising the older one.

And a fourth defect, caught by a new test on its first run rather than by mutation: **four entries
in `MODEL_ENTITY` named models that do not exist**, carried from a scratch script without checking.

## The affix phrases are traced to the SQL, not inherited from a neighbour

MR1 of this programme shipped a description that was simply false because it compressed upstream
prose without reading the model underneath it. So each phrase cites where it comes from:

| affix | source read |
|---|---|
| `_this_season`, `_prev_season` | `int_team_profile__yoy.sql` — alignment by games played, prior season through its first N |
| `_prev_season_full` | `int_player_profile__yoy.sql` — complete total, no cutoff, *"never differenced"* |
| `_delta_yoy` | same files — this minus prev, NULL when either side is NULL |
| the NULL cases | `mart_team_profile.sql:14-18` — NULL for non-domestic competitions and where the prior season was never ingested |

⚠ **The phrases are deliberately neutral about what a "match" is.** Team models align by games
played and player models by appearances, and the same affix is used on both, so naming either one
would be false half the time. The precise rule belongs to the model description, which states it.

## The three columns that kept their own sentence

Reference in front, sentence kept — except where the sentence was a downstream-consumer claim,
which §2 bans outright.

| column | what was there | what it is now |
|---|---|---|
| `goals_delta_yoy` (`int_player_profile__yoy`) | "goals_this_season - goals_prev_season through N appearances. NULL when no prior season." | the block (which states the formula and a **wider** null policy) plus "here the alignment is by appearances" |
| `goals_prev_season_full` (`int_player_profile__yoy`) | full-season total, never differenced, plus a list of sibling columns | the block (same two facts) plus the sibling list |
| `points_won_sum_season` (`int_team_season__deserved_vs_actual`) | "the ACTUAL side of the comparison, carried here so the gap contract test can assert against it" | the block plus "in this model it is the ACTUAL side". **The clause about which test reads it was dropped deliberately** — §2 bans downstream consumer claims. |

## Verified by running

  - `git diff --numstat` over the model ymls: **129 added, 3 deleted**, the 3 being exactly the
    rewritten sites above. Nothing else moved.
  - Line endings checked as BYTES, because `git diff` normalises them and has hidden a whole-file
    rewrite in this programme: every touched file pure CRLF, 0 bare LF.
  - `sync_metric_docs_blocks.py --check` green; the generated file reproduces byte for byte.
  - `check_description_hygiene.py`: `ok: 1383 descriptions across 20 files, 171 docs blocks
    resolved, rendered lengths within 1024/16384`.
  - Six offline gates green plus `ruff --config .ruff-ci.toml`, which is a separate CI job and not
    one of the gates.

## What the gate CANNOT see here, said out loud

Every derived block is entity-suffixed, so `check_description_hygiene` treats all 82 names as
ambiguous and **stops policing them entirely**. Their coverage is asserted from the raw YAML
directly, name by name, and never from the gate's own output. This is the same blindness that let
three split-metric sites sit unwired in the previous MR, named here before it can bite rather than
after.

## Round 1: three FAILs, all real, none of them mine

**analytics-engineer-reviewer — a composed sentence that contradicted itself.** `clean_sheets` is
the catalogue's RATIO of clean-sheet games to games played, and its text carries that ratio's
display convention, *"shown as a count of games played (e.g. 3/5)"*. The column
`clean_sheets_sum_season` is the raw count. Composed, the block claimed in one breath that the
value is a small fraction **and** a season total. It read fluently, resolved, fitted the length cap
and parsed clean — the exact "true-sounding and wrong" shape the review brief named, found by a
reviewer reading the sentence and nothing else.

Fixed as a **class**: a totalling affix is refused on any metric with a `denominator_expr`, the
catalogue's own marker of a rate. Measured across all 76 derived names, that is exactly one name
today — every other rate metric takes `_this_season` / `_prev_season` / `_delta_yoy`, which are
sound on a rate — so the fix is a rule for the next one, not a patch for this one.

⚠ **A second defect inside the fix.** With no block at all, the wiring tool could not see the
column either: it reads "no candidate block" as "not a derived name". The refusal was silently
invisible, which is the coverage cut this programme keeps paying for. The generator now reports
its refusals on every run, `--check` included:

```
NO BLOCK GENERATED, 1 column name(s). ...
  clean_sheets_sum_season (totalling the rate metric clean_sheets)
```

**football-analytics-expert-reviewer — a false NULL claim on four player columns.** The
`_delta_yoy` phrase said NULL could arise from *"a gap in statistical coverage"*. That is a real
cause on the **team** side. It is **impossible** on the player side: a player's null per-match stat
means ZERO, not missing, so a running sum never goes null for coverage — and
`int_player_profile__yoy.sql` names only the absent prior season at that club. Four blocks carried
it into `goals_delta_yoy`, `assists_delta_yoy`, `shots_on_goal_delta_yoy` and
`defensive_actions_delta_yoy`. Fixed with entity-specific phrasing, plus a guard that refuses an
entity with no phrase rather than letting it silently take another's.

⚠ **That reviewer was routed by judgement, not by path.** Its trigger is the seed, which this MR
never touches. Inviting it anyway is the only reason this was caught.

**scope-auditor — the contract's own headline was stale.** `objective:` still described the
pre-amendment MR: 214 columns and 104 promoted, when nothing is promoted here at all. Corrected,
with all four moves of the figure now traceable through the amendments.

**platform-reviewer PASSed, and disclosed that it had no execution tools** and had traced the code
by hand instead of running it. It re-derived all three mutation claims independently and ran a
fourth of its own rather than believing the write-up.

## Three further mutations on the round-1 fixes, all killed

| mutation | aimed test |
|---|---|
| allow totalling a rate metric | `test_a_totalling_affix_on_a_rate_metric_gets_no_block` |
| stop reporting the refusal | same test's output assertion |
| accept an entity with no phrase | `test_an_entity_with_no_phrase_is_refused_rather_than_given_another_ones` |

And a narrowness test, because a rule that fires on everything is as useless as one that fires on
nothing: `test_a_rate_metric_still_takes_the_NON_totalling_affixes` proves "this season's
clean-sheet rate" still composes.

## Rounds 2 to 4: three more defects, and two of them were my own round-1 fixes

**Round 2, football-analytics-expert-reviewer — the fix to a false claim dropped a true one.** The
player year-on-year sentence I wrote in round 1 is complete inside `int_player_profile__yoy`, which
is domestic-league-only at the row level. But the block is REUSED at `mart_player_profile`, which
carries every competition-season a player has and left-joins the domestic-only rows onto it. A cup
or tournament row is NULL there for a reason the sentence no longer named. First a cause wrongly
added, then a cause wrongly removed, both because I read ONE model and wrote a sentence attached to
TWO. **The rule is now a standing comment in the script: a shared block is only as true as its
widest call site.**

**Round 3, found because a test failed for the wrong reason.** `textwrap` defaults to
`break_on_hyphens=True` and had been splitting "year-on-year" into "year-on-" / "year". The file is
not laid out for a reader of the file: `persist_docs` collapses the newline and the warehouse
renders a space inside the term. Three blocks were already live on main from `!98`. Fixed for all.
⚠ And my first test for it was VACUOUS — a natural sentence containing "year-on-year", which at
width 95 the wrapper never chose to break. Rewritten with a token longer than the wrap width.

**Rounds 1, 2 and 3, scope-auditor — the same class three times, and it was right every time.**
Each round it named a stale claim, each round I corrected exactly that sentence, and each round the
same claim was still elsewhere in the same document: the objective, then the blast radius and two
done_when bullets, then the blast radius again for a different reason. Its words: *"disclosed in an
amendment is not the same as reflected in the impact map that a reviewer is told to trust."*

⚠ The repo already carries the rule this violates — corrections replace, never accumulate, and
must replace EVERYWHERE — and reading it did not stop me doing it three times in one MR.

⭐ **What finally worked was measuring instead of describing.** Rendering both versions of the
generated file and comparing them named the 3 affected blocks exactly. It also corrected a number
I had given two reviewers: I said "five pre-existing breaks", counted from lines ending in a
hyphen. Three blocks are affected. A described blast radius is a claim; a measured one is a fact.

**Round 4 was over the cap of 3 and the CPO approved it**, asked as: a reviewer has caught the same
mistake in my paperwork three times, I have fixed the third one and nobody has checked it — one
more check, or ship? Answer, verbatim: *"run one more check"*. It PASSed, having re-swept the
contract with its own search rather than my list.

⭐ **Two non-blocking improvements taken rather than deferred.** football-analytics-expert-reviewer
PASSed round 3 while noting that "a cup or an international tournament" does not naturally describe
a QUALIFYING campaign, of which six are active; the wording now names one. And scope-auditor PASSed
round 4 while noting this evidence file was itself stale — which is the very class it had failed me
on three times, so it is corrected here rather than left because a reviewer declined to fail on it.

## Mutation testing, final tally: 12 run, 8 killed, 4 survived

Every survivor was a real defect, and four of my own tests could not fail:

| survived | what it exposed |
|---|---|
| reverse the affix order | the test could not fail, AND the rule was wrong — longest-affix-first picks the LESS specific metric. Changed to longest STEM wins, which closed 22 further columns |
| delete the dotted-name filter | the guard was unreachable; a dotted name cannot decompose at all |
| delete the same-entity guard | it duplicated one that runs first |
| restore hyphen breaking | the aimed test used a sentence the wrapper never broke at that width |

## Not in this MR

The 48 catalogue-blocked columns (the CPO's call). The promotion of 37 partially-covered names,
99 blank columns — its own MR, because it needs a replace mode. The 134 names no seed defines.
The 5 nested `recent_meetings.*` fields, which cannot be docs blocks at all. GitLab #88.
