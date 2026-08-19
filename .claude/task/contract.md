# Task contract — team_name_overrides batch 2 (BL1, ED, L1, LP)

objective: >
  Continues the same-day work on `fix/team-name-overrides-pool1` (MR !77): verify and correct
  Pool 1 team names against English Wikipedia, using the broadened (collision-OR-incompleteness)
  trigger the CPO ruled and that MR's review already accepted. This batch covers the remaining
  four Pool 1 leagues (Bundesliga, Eredivisie, Ligue 1, Liga Portugal).
refs: MR !77 (batch 1, PL/PD/SA, 61 rows, merged process — awaiting CPO merge); `.claude/task/
  escalations.log` 2026-08-19 entry, branch fix/team-name-overrides-pool1.

impact_map: >
  Same writer and downstream surface as MR !77 (batch 1) — same seed, same join in
  base_apif__teams_global.sql, so the lineage doesn't change between batches. Reusing that MR's
  real pasted `dbt ls --select base_apif__teams_global+ --resource-type model` evidence rather than
  re-running an identical query: 18 downstream models (16 marts + dim_team +
  dim_player_team_season_mapping) out of 97 in the project; 297 nodes total including tests when
  run unfiltered (`unique_dim_team_team_slug`, the seed's own
  `relationships_team_name_overrides_team_api_id__team_api_id__ref_dim_team_` FK test, included in
  that count). layer_rules / blast_radius: identical reasoning to MR !77 — correction stays in
  base per the 2026-07-27 CPO ruling; team_slug moves for every corrected team_api_id, acceptable
  pre-launch per site_architecture.md §3 (slugs not yet stable, nothing indexed).

scope_paths:
  - dbt_project/seeds/team_name_overrides.csv
  - dbt_project/seeds/schema.yml
  - .claude/task/escalations.log
  - .claude/active_work.md
  - CLAUDE.md
  - docs/wireframes/10_home.md
  - docs/wireframes/99_gaps_register.md

decisions_taken: >
  CPO, this session (quoted in full, self-contained, in THIS branch's own escalations.log entry —
  round-1 review correctly FAILed the previous version of this field for citing a quote that was
  only actually written into the log on the sibling branch, fix/team-name-overrides-pool1 / MR !77,
  which has not merged to main and so is not present in this branch's own history):

  "The name is Arsenal London and not Arsenal England. We have to fix and standardize these
  names... it's not Arsenal London. It's Arsenal FC. But it's Inter Milan... we have to define the
  name we use as the single source of truth for what we display."

  Applying that same standard to four more leagues; no new decision this batch.

  ⚠ STANDING EXCLUSION, recorded in dbt_project/seeds/schema.yml's team_name_overrides
  description (added to THIS branch by this same amendment, for the same reason above — the
  sibling branch's schema.yml fix has not merged either): "Bayern München is NOT corrected to
  Bayern Munich (CPO ruled one locale-independent slug)." Checked BL1 against this: Bayern München
  (team_api_id 157) is excluded from this batch for that reason — English Wikipedia's article
  title is "FC Bayern Munich", which is a LOCALE preference (München vs Munich), not a completeness
  defect, and this seed does not correct locale preference.

decisions_reserved:
  - ~15 teams across the four leagues could not be confidently verified this batch (Wikipedia's
    current-season club table didn't clearly cover them, likely relegated/promoted since the
    article was last edited, or the source's own summary was ambiguous) — left unchanged rather
    than guessed. Named in the escalations.log entry. Own follow-up if/when needed.

done_when:
  - Every new row cites its English Wikipedia source URL, matching the seed's existing convention.
  - No row corrects a locale/translation preference (only completeness/collision, per the
    standing exclusion above).
  - escalations.log's citation is self-contained and verifiable from THIS branch alone.
  - Committed on this branch; MR opened by the post-commit hook.

amendments:
  - 2026-08-19: + `dbt_project/seeds/schema.yml` — authority: analytics-engineer-reviewer round-1
    FAIL, same finding as batch 1's sibling branch (that branch's own fix has not merged to main,
    so this branch needs the identical fix independently until it does). Same two edits as the
    sibling branch: the model description states both triggers, the `note` column description
    covers both cases.
  - 2026-08-19: `decisions_taken` rewritten — scope-auditor + analytics-engineer-reviewer round-1
    FAIL, both citing the same defect: the CPO quote was attributed to "escalations.log,
    2026-08-19" but that entry only exists on the unmerged sibling branch, not in this branch's own
    log. Now quoted in full here, backed by a self-contained entry in this branch's own
    escalations.log (see done_when).
  - 2026-08-19: row count corrected 35 → 36 throughout — analytics-engineer-reviewer round-1 FAIL,
    a genuine arithmetic error (L1 was 13 rows, not 12; counted wrong when totaling).
  - 2026-08-19: + `CLAUDE.md`, `docs/wireframes/10_home.md`, `docs/wireframes/99_gaps_register.md`
    — authority: same standing instruction cited by the sibling branch's identical amendment.
    `main` moved a second time (MR !76, Top teams ruling, merged) while this MR sat open; merging
    `main` in to resolve the resulting conflict brings in !76's already-built, already-reviewed,
    already-merged content on these three files. None of it is authored, edited, or re-verified by
    this task.
