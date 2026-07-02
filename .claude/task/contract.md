# Task contract — Player → Career screen spec (wireframe 13) + GAP-22

> Written on a CLEAN tree (branch docs/391-career-screen-spec off main @ 65deea7).
> Doc/wireframe spec — went through plan mode; plan approved. Mirrors #625 (Stats 12) + #617 (Squad 11).
> No code/model/dbt/export change (docs/wireframes/** is NOT a structural surface → no impact_map).

objective: >
  Spec the Player → Career sub-screen (wireframe 13) against the merged per-club mart_player_career (#630,
  grain player×club×competition-season): a club-grouped season-by-season career log + a national-team caps
  section, honest counts only (apps/goals/assists), bound 1:1 to real mart columns. Register GAP-22 (the
  export-wiring gap — mart_player_career is not yet carried by shape_player_payload). Doc-only; the export
  wiring + the history backfill are separate follow-ups. Resolves the screen that opened the session.

scope_paths:
  - docs/wireframes/13_player_career.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/03_player_profile.md
  - .claude/task/**

decisions_taken: >
  Per the approved plan. NEW 13_player_career.md follows the 00_overview §1-10 template (mirrors 12/11):
  club-grouped season rows (Season · Competition · Apps · Goals · Assists) + per-club/career subtotals + a
  National-team caps section; counts-only (no per-90, CPO); §5 binds ONLY to mart_player_career columns
  (player/club identity, entity_type, appearances/goals/assists, national_appearances_total). Honest limits
  stated: national rows = appearances in COVERED competitions (NOT true caps) + the log is thin until the
  backfill runs. GAP-22 registered (export wiring, pending). Companion doc-syncs: 00 (screen inventory row 13
  + census), 99 (GAP-22), 03 (§7 ▸Career footer link + §10 reference). metrics_display.md NOT touched (plain
  integer counts, no new display idiom).

decisions_reserved:
  - Subtotal precompute (dbt) vs display-side grouping — the #630 decisions_reserved item; CPO at the GAP-22
    wiring PR. The spec presents subtotals as display grouping + flags this, does NOT pre-decide.
  - Export nesting shape of the career[] block — confirmed at the GAP-22 wiring PR (like Stats/Squad).
  - The export wiring PR itself + the history backfill (§10 cost) — separate follow-ups, not this PR.
  - All §10 (product/UX, metrics, naming, new mechanisms) — no new metric; labels from metric_catalogue only.

done_when:
  - docs/wireframes/13_player_career.md written §1-10; every §5 key is a real mart_player_career column;
    labels/formats reference metric_catalogue (goals/assists) / are facts (appearances); §6 covers thin +
    not-yet-wired + national-absent cases; §9 flags the new components.
  - 00_overview (inventory row 13 + census), 99_gaps_register (GAP-22), 03_player_profile (§7 link + §10 ref)
    synced; metrics_display untouched.
  - scope-auditor + bi-analyst-reviewer PASS (>=2 risks each); review.md diff_sha256 binds; CPO merges.

amendments: (none)
