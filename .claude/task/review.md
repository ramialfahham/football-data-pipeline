# Review — feat/metric-rename-catalogue-only — 2026-08-26

diff_sha256: 7bbe5787976d08f0a2709ded1bce7251676db410743769be6ea16433b7a89d96

rounds: 3

<!--
⚠ THIS IS THE ROUND CAP. Past three, the working agreement says STOP and bring the open findings to
the CPO rather than looping.

Required reviewer set computed from .claude/review_routing.json against the staged paths:
  scope-auditor                       always
  analytics-engineer-reviewer         dbt_project/**
  football-analytics-expert-reviewer  dbt_project/seeds/metric_catalogue.csv

HISTORY, so the standing PASSes are auditable rather than assumed.
  Round 1: three FAILs. (a) all three — the contract cited an escalations.log entry this branch did
    not contain, because the branch was cut from main before !111 merged. (b) analytics-engineer
    only — the impact_map per-file tally was wrong in five of nine files.
  Round 2: analytics-engineer PASS, football-analytics-expert PASS, scope-auditor FAIL. The log
    recorded the blanket approval "apply the suggested changes to ensure consistency" but never
    enumerated the six-item list it answered, so the contract's claim about what that list contained
    was unverifiable from the record. All three reviewers saw it; two declined to fail on it.
  Round 3 fix: the six are now ENUMERATED in the log entry, which also discloses that they were
    added late and that a reviewer's finding is why. `refs` points at that enumeration.

The RENAME has never changed across any round: the same two metric ids, the same 24 repoints, the
same grain classification, verified independently by analytics-engineer in rounds 1 and 2. Only the
authority record and one artifact tally moved. Only scope-auditor is re-spawned; the two round-2
PASSes stand, and both explicitly examined the gap this round fixes.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed file falls inside `scope_paths`; no file touched outside it.
- §10 naming decision: checked `escalations.log`'s new "THE SIX, ENUMERATED" block. It now lists
  both renames verbatim as items 4 and 5 of the table put to the CPO, and quotes his reply. This
  closes the round-2 gap scope-auditor previously failed on.
- Reference-count arithmetic, round 1's other defect: recounted the 24 repoints from the diff file
  by file — core 3, int_team_season 1, int_legs 3, int_momentum 3, int_momentum_window 2,
  int_player_club_season 1, int_player_season_position 1, int_season_record 3, shared 7 = 24.
  Matches the corrected tally exactly; no drift.
- Dangling-doc risk: grepped for the underlying column names behind the three dropped blocks and
  confirmed every model reference to them is a bare `- name:` entry with no description line, so no
  reference was orphaned.
- Frontend and doc-sync: the only site references are to `corner_kicks_per_match` and
  `corners_against_per_match`, untouched and deliberately deferred, not to the bare metric ids whose
  label keys changed. No frontend break, no undisclosed doc-sync gap.
- Impact map: no `.sql` file appears in the diff, consistent with "writers: NONE". The mutation
  test recorded in the evidence is concrete proof of the no-dangling claim rather than a bare
  assertion.
- Secrets, threshold crossings, and `decisions_reserved`: nothing credential-shaped; no new
  mechanism, cost or cadence; and none of the reserved items is actually touched in the diff.

## analytics-engineer-reviewer
VERDICT: PASS
<!-- Given in ROUND 2, against the same code. Round 3 changed only escalations.log and contract.md,
     and this reviewer explicitly examined that exact gap and declined to fail on it. -->
risks_checked:
- Re-derived the 24-reference tally directly from the diff rather than trusting it: core 3,
  int_legs 3, int_momentum 3, int_momentum_window 2, int_season_record 3, int_team_season 1,
  int_player_club_season 1, int_player_season_position 1, shared 7 = 24, split 6/6/12.
- Verified each repoint against the model it sits on rather than the column name, including mapping
  each of the 7 changed lines in `shared.yml` to its enclosing mart by header line number. Every one
  lands on the grain the new block name claims; no misclassification found.
- Tested the "no model column needs to move" claim: no `.sql` file is in the patch, and both raw
  column names still live unrenamed in every SQL model that owns them.
- Grepped the whole tree for all three old block names post-edit: zero hits, including outside
  `scope_paths`.
- The `*_sum_season` columns behind the dropped blocks carry no `description:` at all, so nothing
  dangles.
- Catalogue-row uniqueness holds against the pre-existing player `saves` row; each new label key
  occurs exactly once.
- Frontend exposure: only the untouched `corner_kicks_per_match`, consistent with the disclosed
  transient. Neither renamed metric is displayed, so no locale string is orphaned.
- The 22-metric benchmark `accepted_values` list contains only derivatives, none of which changed.
- ⚠ Saw the unenumerated-six gap and declined to make it a finding: "a citation-precision question
  ... no data/layer defect follows from it either way."

## football-analytics-expert-reviewer
VERDICT: PASS
<!-- Given in ROUND 2, against the same code, same reasoning as above. -->
risks_checked:
- Diffed the two changed catalogue rows field by field: only `metric_id` and `label_i18n_key`
  changed. Formula, description, direction, group, format and interpretation byte-identical. A pure
  rename, no redefinition.
- Direction correctness: both `higher_better`, correct for an attacking-pressure proxy and for
  shot-stopping volume.
- Edge-case honesty: both descriptions still disclose provider coverage gaps and the
  team-versus-summed-goalkeeper mismatch, and the saves interpretation still flags that a high count
  can mean strong goalkeeping OR a defence under pressure.
- No composite or fabricated score: both are single-column sums.
- Naming collision: no other team row labelled "Corners" or "Saves"; the player key namespace does
  not collide; `(metric_id, entity)` stays unique.
- Dangling fallout from the block merge: zero references to either deleted derived block anywhere.
- ⚠ Saw the same gap and judged it in-class: both renames are "a direct application of an approved
  general rule rather than an unapproved new naming decision", since `corners_against_per_match`
  already establishes the house noun and the player side is already `saves`.

## escalations
(none)
