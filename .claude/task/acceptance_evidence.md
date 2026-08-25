# Acceptance evidence — #82 MR4b-2: promoting the definitions that already existed

Every number measured on this branch against merged main. Where a measurement contradicted an
expectation, the contradiction is what is recorded.

## The headline

| | |
|---|---|
| blank in-scope columns | **508 → 422** |
| names given one definition instead of many | **31** |
| sites | **123** — 92 blank, 31 already carrying the sentence |
| replacements whose resolved text DIFFERS from what it replaced | **0** |
| docs blocks in `shared_columns.md` | 9 → 40 |
| names PULLED during review | **6**, across two rounds |
| suite | 1007 passed, 1 skipped — collection 999 stashed / 1008 applied |

⚠ **Every figure here is the post-review one.** The MR was planned at 37 names and 146 sites. Six
were pulled, because a sentence true where it was written can be false at a blank site it is then
pointed at — and because reading the sentence is not enough to tell. The sections below name all
six.

## The one claim, and it is machine-checked rather than asserted

**Nothing was rewritten.** Every block's body is the sentence those columns already carried.

Proven by resolving the NEW description of every changed column through the docs blocks and
comparing it with the OLD one read from `git show main:<path>`, whitespace-normalised:

```
columns given a description that had none : 92
columns whose EXISTING text was replaced  : 31
replacements whose resolved text DIFFERS  : 0
references pointing at a missing block    : 0
```

That covers the folded scalar edited by hand as well as the 30 the script did, so the hand edit
gets the same proof as the machine ones rather than my word.

⚠ **AND THIS PROOF HAS A KNOWN LIMIT, which review found the hard way, twice.** It says the 31
replaced sites did not change. It says NOTHING about the 92 blanks, where pointing an existing
sentence at a column ASSUMES the sentence is true there. That assumption is checked by hand, per
name, **against the SQL of every model the block reaches** — not against the sentence, which is how
a sixth name survived my own sweep. See the review sections.

The script refuses to do this unsafely rather than relying on me to check afterwards: a site is
planned **only** when the block's body equals the description it would replace. A site whose text
differs is reported and skipped, because replacing it would be an edit dressed as a promotion.

## The guard that had to change, and how it was narrowed rather than loosened

`declare_missing_columns.py` is append-only by contract; `_verify` rejects any diff carrying a
non-insert opcode. A promotion is not an insert.

The rule is now: a `replace` is allowed **only** on a line this run planned to swap, carried from
the plan into the verifier. Every other opcode is still refused, and **an empty planned set — what
every other mode passes — restores the original rule exactly**. Both halves are pinned by
`test_verify_still_refuses_a_replace_the_run_did_not_plan`, which asserts the same edit is refused
with no plan, allowed with the right line planned, and refused again with a different line planned.

## Mutation testing: 5 run, 4 killed, 1 survived — and the survivor was a design error

| mutation | result |
|---|---|
| promote a site whose text differs from the block | killed |
| allow any `replace` opcode | killed |
| search the whole file instead of the model's block | killed |
| **skip the write-time check that the planned line is still there** | **SURVIVED** |
| skip it in the redesigned form | killed |

⭐ **The survivor was not a missing test, it was a wrong assumption.** The writer assumed a
description is always the line immediately after `- name:`. Nothing tested that — and chasing why
showed the assumption is false: `- name:` / `tests:` / `description:` is legal YAML and this repo
already uses that ordering, and the assuming version would have aborted the **whole file** for it.
Redesigned to search the column's own lines for the exact line the plan read, which cannot hit a
different line and no longer breaks on a legal ordering.

**Second time in two MRs that a surviving mutation meant the rule was wrong rather than the
assertion weak.** That is now the first question to ask when one survives.

## And one found by running it, not by a test

The plan searched the whole file for the description line, but a description is only unique
**within** its model: `is_home` carries the same sentence under five models of `shared.yml`. The
whole-file search returned five candidates and skipped all five as unidentifiable — honestly
reported, but five sites it should have promoted. Scoping the search to the model's block fixed it
and removed a duplicated copy of the block-range logic at the same time: `_model_block` is now one
function used by the planner and the writer alike. Promotable sites went 34 → 39, leaving exactly
the 2 folded scalars measured before planning.
⚠ **THOSE ARE THE FIGURES AS THEY STOOD BEFORE REVIEW**, and they are superseded twice over: six
names were pulled across two rounds, one of them a folded scalar. The final state is **30 script
promotions and 1 folded site** — see the headline table.

## The folded scalar, done by hand

It cannot be edited by line without mangling the file, so the script reports and skips it:

| site | before | after |
|---|---|---|
| `dim_team.team_slug` (`core.yml`) | a 9-line folded scalar in two paragraphs | `{{ doc('team_slug') }}` |

It is in the resolved-text comparison above and comes back identical. ⚠ The second folded site the
script reported, `int_team_season_record.opponent_shots_total`, is one of the five pulled in round
1 — its sentence says "cumulative" and one of its two models holds the per-match value.

## Verified by running

  - `git diff --numstat` over the model ymls: **319 added, 39 deleted**, and the 39 decompose by
    construction — 30 one-for-one swaps plus 9 from `team_slug`'s folded scalar. ⚠ The contract
    first said the deletions would equal the replaced-site count. That is only true of the swaps
    the script does; a folded scalar replaces many lines with one. Corrected by measuring.
  - Line endings checked as BYTES across every changed model yml and the block file: pure CRLF,
    0 bare LF.
  - `dbt parse` clean, and the parsed manifest carries **0 unrendered `{{ doc(`**.
  - `check_description_hygiene.py`: `ok: 1473 descriptions across 20 files, 201 docs blocks
    resolved, rendered lengths within 1024/16384`. It reported **146** findings the moment the
    original 37 blocks existed — the same number measured independently before any edit — and **0**
    once the wiring and promotion were done and the six names had been pulled. That the gate's
    count matched the pre-edit measurement exactly is what makes write-wire-promote-in-one-commit
    provable rather than asserted.
  - Six offline gates green plus `ruff --config .ruff-ci.toml` and the metric drift check.

## Round 1: three FAILs, and the first one is a lesson I had recorded an hour earlier

**analytics-engineer-reviewer — `is_home` is FALSE at four of the models it was newly wired to.**
Its sentence, *"true when team_sk is the home side of the **upcoming** fixture"*, is right at the
four momentum models where it was already written and grained on `upcoming_fixture_sk`. This MR
pointed it at `mart_team_fixture_stats`, `mart_player_fixture_stats`, `mart_player_match_log` and
`mart_team_fixtures` — every one grained on a finished or arbitrary fixture.

⛔ **The hole was in my proof, not just in that one name.** The machine check compares a block's
text against the text it REPLACED. That proves nothing was rewritten at the sites that already had
a sentence. It says nothing about whether the sentence is TRUE at the blank sites it is then
pointed at — and BUILDER'S CALL 3 measured only agreement among the written sites. *"A shared
definition is only as true as its widest call site"* is a rule from the previous MR that I did not
apply to this one.

**Swept as a class, and four more turned up that the reviewer had not named:**

| name | why it cannot be promoted as written |
|---|---|
| `is_home` | says "upcoming fixture"; reaches 4 models grained on a finished one |
| `opponent_shots_total` | says "cumulative … through this match", but `int_legs__team_match.sql:124` holds the per-match value; only `int_team_season_record.sql:134` sums it |
| `games_with_opp_stats` | says "window legs"; reaches `int_team_season_record` |
| `games_with_player_stats` | same |
| `goals_against_in_save_games` | says "keeps save_ratio same-window"; same model |

`int_team_season_record`'s own header calls it *"the complement to int_team_momentum__metrics (W1 =
last 5)"* — season-cumulative, not a window. All five need rewording, which is authoring, so they
go to MR4c.

## Round 2: a sixth, in a name my own sweep had marked safe

**`result` claims to come from a model that one of its sites never reads.** Its sentence is
*"W/D/L from `int_legs__team_match` for finished rows; null otherwise"* — a claim about
**provenance**. Four of its five sites trace there correctly. `mart_player_match_log` does not
reference that model at all and recomputes the value itself at `mart_player_match_log.sql:136-140`
with a `case when goals_for > goals_against` expression. Verified before acting:
`grep -c int_legs__team_match` on that model returns **0**.

⛔ **This is a finding about my round-1 fix, not the original defect.** I swept the class by
shortlisting blocks whose TEXT carried a scope word or named a model, then reading the sentence
against the model list. `result` survived because its sentence reads perfectly well at a match-log
model — only the SQL shows the provenance is wrong.

⭐ **A provenance claim is checkable only in the SQL. Reading the sentence is not the check.**
`team_slug`, the other block naming a source model, was then verified the same way: its claim is
about where the value is *derived*, which holds wherever it flows, so it stays.

Also from round 2: platform-reviewer PASSed and flagged a stale figure in a **code comment** as
non-blocking. Fixed rather than accepted — that is the exact class scope-auditor failed three
times, and it slipped through in the same round that recorded it.

**platform-reviewer — the `all()` in the replace guard was untested,** and it found that by
READING, having no execution tools. Every test replaced ONE isolated line, where `all` and `any`
are identical, so a mutation weakening it to "at least one planned line in the opcode" survived the
whole suite — and would let an unplanned line ride along inside a legitimate swap, invisible to the
structural check too, which compares parsed YAML and is blind to a reformat. Fixed with a test that
makes two adjacent lines change together so difflib emits one multi-line replace. It kills the
mutation, and the "both planned" case is asserted too so the test is not just refusing all
multi-line replaces.

**scope-auditor — the script's own docstring still said "APPEND-ONLY, AND THAT IS THE WHOLE
POINT … the acceptance test is simply that the diff has zero deleted lines",** in the MR that adds
a replacing mode. I had flagged the tension in the contract and fixed it only there, leaving the
artifact whose contract it is stating the old invariant. **Fourth instance of that class across two
MRs.** Fixed, and the rest of the file swept for the same claim rather than only the line named.

## Mutation testing: 6 run, 5 killed, 1 survived

| mutation | result |
|---|---|
| promote a site whose text differs from the block | killed |
| allow any `replace` opcode | killed |
| search the whole file instead of the model's block | killed |
| **skip the write-time check that the planned line is still there** | **SURVIVED** |
| skip it in the redesigned form | killed |
| `all` → `any` in the replace guard | killed (by the round-1 test) |

⭐ The survivor was a wrong assumption, not a missing test: the writer assumed a description is
always the line immediately after `- name:`. `- name:` / `tests:` / `description:` is legal YAML
and this repo already uses it, and the assuming version aborted the **whole file** for it.
Redesigned to search the column's own lines for the exact line the plan read.

**Third time in three MRs that a surviving mutation meant the rule was wrong rather than the
assertion weak.**

## Not in this MR

The 48 team columns waiting on the CPO's ruling about the seven player-only metrics. The 134 names
no seed defines, and the 26 partials whose sentences disagree with each other — both need
authoring. The 5 nested `recent_meetings.*` fields, which cannot be docs blocks at all. MR5.
