# Task contract — feat: GAP-18 live WC form LABEL (commit 2)

> Commit 2 of branch feat/gap-18-tournament-form-window (PR #485). Commit 1 landed the dbt mart
> LAYER — WC form NUMBERS are now tournament/qualifier-cumulative (window_type). This commit wires the
> live match-preview LABEL: the UI (site/match-preview/index.html `formContextLabel`) and i18n
> (`formContextWcQualifiers` / `formContextWcTournament`, already present in en/de/fi) switch on a
> boolean `form_from_qualifiers` flag that the retired `mart_matchday_insights_wc` used to provide and
> the current preview mart does not. Without it the live WC preview shows correct cumulative numbers
> but always the "all World Cup matches so far" label (wrong for qualifier-window teams). CPO approved
> this widening (this conversation). Pure dbt: one mart + its schema + the gaps-register marking. The
> live export (scripts/export_pages_data.py) is `SELECT *` passthrough writing full row dicts, so the
> new columns reach the JSON with NO export change. Reviewers: scope-auditor + analytics-engineer + bi-analyst.

objective: >
  (a) mart_matchday_insights (MODIFIED): surface two boolean columns derived from the momentum mart's
      window_type — home_form_from_qualifiers = coalesce(mh.window_type = 'qualifiers', false) and
      away_form_from_qualifiers = coalesce(ma.window_type = 'qualifiers', false). Additive only (no
      change to existing columns/grain/row-count). coalesce keeps them boolean (never null). The live
      `formContextLabel` UI reads exactly these field names; the export passes them through unchanged.
      Also de-stale the home/away_form_games_played descriptions ("last-5 window" → "form window;
      last-5 normally, cumulative for tournament fixtures").
  (b) domestic_league.yml (MODIFIED): document the two new boolean columns (not_null — coalesce makes
      them total) and update the two games_played descriptions.
  (c) 99_gaps_register.md (MODIFIED): update the GAP-18 row from "mart layer landed / label is the
      immediate follow-up" to "live preview fixed (numbers + label)"; the v2 blueprint drill-down
      (form_window[] cap, separate phase column) stays under #391.

refs: >
  GAP-18 live-label completion. Commit 1 = PR #485 mart layer. UI: site/match-preview/index.html
  formContextLabel() switches on home/away_form_from_qualifiers; i18n keys formContextWcQualifiers /
  formContextWcTournament already exist (en/de/fi). Live export scripts/export_pages_data.py is
  SELECT * → full-dict passthrough (no change needed). CPO approved widening 2026-06-16 (this conversation).

scope_paths:
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - docs/wireframes/99_gaps_register.md
  - .claude/task/contract.md

decisions_taken: >
  CPO 2026-06-16 (this conversation) approved widening the GAP-18 PR to wire the live WC form LABEL,
  after the reviewers + investigation showed the mart-numbers change alone reaches the live preview but
  leaves the label wrong (the live UI already has the labels + i18n; only the form_from_qualifiers flag
  is missing). Derive the flag from the existing window_type ('qualifiers') in dbt (consumption-layer
  contract: logic in dbt, the export only selects) — no export or UI/i18n change.

decisions_reserved:
  - The boolean field NAMES (home_form_from_qualifiers / away_form_from_qualifiers) are FIXED by the
    existing live UI (formContextLabel reads these exact keys) — match them, do not rename.
  - v2 blueprint drill-down (form_window[] ≤5 cap, separate `phase` column) stays under #391 — out of scope.
  - qualifying-type cumulative window #483, player strip #484 — still deferred.
  - Any §10 question -> escalate in plain language.

done_when:
  - dbt parse clean; sqlfluff lint passes on mart_matchday_insights.sql; validate-local clean.
  - mart_matchday_insights has home_form_from_qualifiers / away_form_from_qualifiers (boolean, never
    null); domestic_league.yml documents them with not_null; existing columns/grain/row-count unchanged.
  - Read-only BQ spot-check (or post-build): for live WC opener fixtures the flags are true; for MD2+
    WC fixtures false; for non-tournament fixtures false.
  - ci-data-build green (the mart builds + its tests pass); the live UI formContextLabel now switches
    "all qualifying matches" vs "all World Cup matches so far" correctly (the export passes the new
    columns through unchanged — SELECT *).
  - reviewers: scope-auditor + analytics-engineer-reviewer + bi-analyst-reviewer all PASS.

amendments: (none)
