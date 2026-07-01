# Task contract — spec the Team → Squad screen (wireframe, doc-only)

> Written on a CLEAN tree (branch docs/391-squad-screen-spec off main @ dafd463).
> Doc-only wireframe spec — NO code/model/export change. The export wiring of mart_roster
> is a SEPARATE follow-up PR (gaps-register rule: "gap fixes never ship inside blueprint PRs").
> See docs/working_agreement.md §2 (contract), §10 (decision rights). Plan mode + ExitPlanMode required.

objective: >
  #391 track A (CPO-picked 2026-07-01): spec the Team → Squad surface so the already-built,
  orphan mart_roster (#503) can be wired next. Write the Squad wireframe following the
  docs/wireframes/00_overview.md §1–10 template, binding its blocks to mart_roster's columns as
  the PROPOSED payload; register the gap that mart_roster is not yet carried by the team export
  (a follow-up wiring PR fulfils it — the GAP-15 pattern); reconcile the now-stale "no squad
  mart / no squad surface yet" notes + the "Squad?" link in 02_team_profile.md; add the screen to
  the 00_overview.md inventory + component census. Doc-only; the export wiring is NOT in this PR.

refs: >
  mart_roster = dbt_project/models/5_marts/shared/mart_roster.sql — IDENTITY-ONLY, one row per
  (team_sk, league_code, season_api_year, player_sk), club competitions only: player_name,
  player_position, player_nationality, player_birth_date, player_photo_url (NO per-club stats /
  appearances — that is #480 / Phase C). content_architecture.md §3 (Squad block ↔ mart_roster,
  orphan) + §4 (Team page tabs incl. Squad) + §9 (build seq #3: leaderboards+roster, cheap, no
  governance). Established pattern: GAP-15 (02 §9 referenced fixtures ahead of the data PR #607).
  Export attach pattern: shape_team_payload seasons[] with per-season next_fixture/recent_results.

scope_paths:
  - docs/wireframes/**
  - .claude/task/**

decisions_taken: >
  Doc-only wireframe spec + a gaps-register entry (mart_roster not wired to the team export) +
  the 02_team_profile stale-note/link reconciliation + the 00_overview inventory/census addition.
  NO code/model/export/metric/catalogue change — the export wiring is a separate PR. Squad v1 scope
  = IDENTITY-ONLY (the roster list: name, listed position, nationality, age derived render-time from
  birth_date, photo, deep-link to the player profile), grouped by position, because mart_roster
  carries no stats. Arranges only existing roster fields; invents no metric.

decisions_reserved:  # §10 — surfaced to the CPO in plan mode, not pre-decided
  - IA STRUCTURE: where the Squad spec lives — a new dedicated wireframe file (Team→Squad sub-screen,
    added to the inventory) vs a new tabbed section inside 02_team_profile.md. Recommendation carried
    to the plan-back; the CPO rules. (Both options fall inside docs/wireframes/**, so scope is stable.)
  - The Squad EXPORT payload shape + attachment (per-season squad[] on the team payload vs a separate
    export target) — a follow-up wiring-PR decision; noted in the gap entry, not locked here.
  - Position grouping taxonomy (GK/DEF/MID/ATT vs flat) + within-group ordering — settled in the spec
    at build time against the actual player_position domain; flagged as a data check.

done_when:
  - A Squad wireframe (§1–10 per 00_overview) exists, every referenced field grounded in a real
    mart_roster column, with a registered gap for the unwired export and the interim/absent states.
  - 02_team_profile.md stale "no squad mart / no squad surface" notes + the Squad link reconciled;
    00_overview.md inventory + component census updated.
  - scope-auditor + bi-analyst-reviewer PASS (>=2 risks each); review.md diff_sha256 binds the staged
    diff; CPO merges. The export wiring is explicitly deferred to a follow-up PR.

amendments: (none)
