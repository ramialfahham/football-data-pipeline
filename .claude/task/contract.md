# Task contract — feat: GAP-18 tournament form-window exception (W1, team)

> GAP-18 (CPO-approved 2026-06-11, "schedule before WC"; CPO go-ahead 2026-06-16 — this conversation —
> to change the live WC form numbers during the tournament). The shipped W1 momentum window
> (int_momentum_window__team) hard-caps at recency_rank <= 5 for EVERY competition, so live World Cup
> previews render a bare "last 5" — the matrix §4 tournament exception ("This tournament so far" /
> "Qualifiers") is unimplemented. This task implements that exception generically by competition_type,
> with a window_type descriptor, for the TEAM window. The parent→child link the qualifier window needs
> is NOT in the warehouse yet (only in the YAML registry), so it is synced into the registry seed via
> the existing single-source mechanism. Reviewers: scope-auditor + analytics-engineer + cto + data-engineer
> + bi-analyst (per .claude/review_routing.json for the staged paths).

objective: >
  Implement the matrix §4 W1 (live-form/momentum) tournament exception in the TEAM window, generic by
  competition_type — no league_code hardcoding:
  (a) Sync the parent link into the warehouse: scripts/sync_dbt_vars.py projects a third column
      `parent_competition` from docs/competition_registry.yml into seeds/competition_registry.csv;
      scripts/check_registry_var_sync.py validates the new column (triples) AND that every non-empty
      parent_competition references a known league_code. Regenerate the seed by RUNNING the script
      (it is generated, never hand-edited). Document the column in seeds/schema.yml.
  (b) int_momentum_window__team (MODIFIED): for an upcoming fixture side whose competition_type is
      world_championship or continental_championship, REPLACE the last-5 recency selection with —
      tournament_to_date: the team's finished legs in THIS competition (leg_league_code = the fixture's
      league_code) AND the fixture's season_api_year, before kickoff, cumulative (no 5-cap),
      window_type='tournament_to_date'; if the team has zero such legs (its opener / pre-MD1) fall back to
      qualifiers: finished legs in competitions whose registry parent_competition = the fixture's
      league_code, before kickoff, cumulative, window_type='qualifiers'. All OTHER types keep the existing
      last-5 recency selection (club season-capped, national uncapped), window_type='last_5'. Emit a
      window_type column (constant per upcoming_fixture_sk+team_sk); keep recency_rank (1=most recent) for
      drill-down ordering; OUTPUT SCHEMA = current columns + window_type only.
  (c) int_momentum__team (MODIFIED): carry window_type from the window legs instead of the hardcoded
      'last_5'. The aggregate is already a SUM over the window legs, so cumulative windows aggregate
      correctly; games_in_window becomes the cumulative count (may exceed 5).
  (d) mart_momentum_window__team (MODIFIED): carry window_type from the window legs instead of hardcoded
      'last_5'; emit ALL in-window legs (the invariant test requires list rows = games_in_window, so NO
      cap here — display truncation is a downstream/export concern, out of scope).
  (e) mart_momentum__team (MODIFIED): window_type flows through from the aggregate; verify it is selected
      (not re-hardcoded) and contributing_competitions stays correct.
  (f) Schema + tests: int_momentum_window.yml / int_momentum.yml / shared.yml — add 'tournament_to_date'
      and 'qualifiers' to window_type accepted_values ON THE TEAM PATH ONLY; relax the
      "recency_rank between 1 and 5" guard to "between 1 and 5 OR window_type in (tournament_to_date,
      qualifiers)"; fix descriptions that hardcode "1–5"/"last 5"/"the 5 legs" to the variable window;
      add a NEW DQ test assert_tournament_form_window.sql (tournament-type fixtures with >=1 prior
      same-edition leg => window_type='tournament_to_date' and games_in_window = that prior count, not
      capped at 5; openers => 'qualifiers' or empty). The existing
      assert_momentum_window_matches_momentum invariant must still pass.
  (g) Docs: update docs/competitions/wc26.md (the "form is recency-based / dim reserved for GAP-18" note
      is now implemented via the registry parent link) and mark GAP-18 implemented in
      docs/wireframes/99_gaps_register.md.

refs: >
  GAP-18 (docs/wireframes/99_gaps_register.md; metrics_display.md §4 + §5.3d; 01_fixture_page.md §5.3d;
  metrics_context_model.md §4 national-team matrix; docs/competitions/wc26.md "WC form window rules").
  CPO-approved 2026-06-11; CPO go-ahead 2026-06-16 (this conversation) to change live WC form numbers,
  with window_type values 'tournament_to_date' + 'qualifiers' confirmed and existing 'season_to_date'
  left untouched. Parent link source: docs/competition_registry.yml parent_competition (WCQ* -> WC).

scope_paths:
  - scripts/sync_dbt_vars.py
  - scripts/check_registry_var_sync.py
  - dbt_project/seeds/competition_registry.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/dbt_project.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window__team.sql
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_momentum__team.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/5_marts/shared/mart_momentum_window__team.sql
  - dbt_project/models/5_marts/shared/mart_momentum__team.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_tournament_form_window.sql
  - docs/competitions/wc26.md
  - docs/wireframes/99_gaps_register.md
  - .claude/task/contract.md

decisions_taken: >
  CPO 2026-06-11 approved GAP-18 (implement the matrix tournament exception + phase descriptor, schedule
  before WC). CPO 2026-06-16 (this conversation): rules are settled — opening-round (pre-MD1) form =
  qualifier matches; from MD2 = cumulative tournament-to-date; never "last 5"; explicit go-ahead to change
  the live WC form numbers now; window_type values 'tournament_to_date' + 'qualifiers'; existing
  'season_to_date' key left UNTOUCHED (published key, separate decision). Mechanism: sync the registry's
  existing parent_competition field into the registry seed (the sanctioned single-source path) and read it
  in the window model — no separate Core parent-child dim (single consumer; avoids a premature
  consumer-less model).

decisions_reserved:
  - SCOPE — this PR covers world_championship + continental_championship (the types the GAP-18 display
    entry names; the live-critical set). The matrix §4 ALSO gives `qualifying` a cumulative campaign window
    while running — NOT implemented here (not time-critical; the display GAP-18 entry names only
    championships). Filed as #483; do NOT silently extend or silently drop.
  - PLAYER-side window — int_momentum__player selects last-5 inline (no shared player window model); GAP-18
    names the TEAM model and the player top-strip is secondary. Player stays 'last_5' this PR; filed as
    #484 (immediate follow-up). Do not self-extend scope.
  - A new Core parent-child dim (the GAP-18 "Core dim" framing) — deferred; implemented via the seed.
    If a reviewer/CPO deems the core dim mandatory, escalate rather than self-decide.
  - Any other §10 question -> escalate in plain language; do not self-rule.

done_when:
  - `python scripts/sync_dbt_vars.py` regenerates competition_registry.csv with parent_competition;
    `python scripts/check_registry_var_sync.py` and `python scripts/check_competition_type_seed.py` pass.
  - dbt parse clean; sqlfluff lint passes on changed models; validate-local clean.
  - Read-only BQ spot-check on live WC ('WC') upcoming fixtures confirms: sides whose team has >=1 prior
    2026 WC leg show window_type='tournament_to_date' with games_in_window = that prior count (verified >5
    where applicable, i.e. the 5-cap is gone); opener sides show 'qualifiers' over WCQ* legs (or empty when
    no qualifier legs); non-tournament fixtures unchanged ('last_5', <=5 legs).
  - ci-data-build (full BQ build + DQ tests) green: assert_momentum_window_matches_momentum still passes;
    new assert_tournament_form_window passes; all window_type accepted_values updated so no test regresses.
  - int_momentum_window.yml / int_momentum.yml / shared.yml + seeds/schema.yml document the new values/column.
  - reviewers: scope-auditor + analytics-engineer-reviewer + cto-reviewer + data-engineer-reviewer +
    bi-analyst-reviewer all PASS (>=2 named risks each), no FAIL, every ESCALATE has a recorded CPO ANSWER.

amendments: (none)
