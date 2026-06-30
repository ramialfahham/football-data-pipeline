# Task contract — #391 GAP-14: surface player birth_date in the v2 player payload (+ doc sync)

> Written on a CLEAN tree (branch off main @ 557eb6d). Export change + the directly-coupled
> wireframe/gaps-register doc sync (folded in per CPO go 2026-06-30).
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (escalation), App. A.

objective: >
  Surface the player's birth_date at the top of the v2 player payload, and sync the player wireframe +
  gaps register so the spec reflects the now-closed gap. The column already exists on mart_player_profile
  and is already pulled by the player fetch (select *), but shape_player_payload never re-surfaces it and
  _strip_identity drops it from every season row, so it is currently lost from the payload. Adding the
  identity key closes GAP-14; the wireframe (03_player_profile.md) + gaps register (99_gaps_register.md)
  are updated in the same change so they no longer describe birth_date as missing.

refs: #391 (un-paused, data-first) · GAP-14 (Phase B; ruled approved CPO 2026-06-11; CPO-picked this session) · backlog in .claude/active_work.md

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/99_gaps_register.md
  - .claude/task/**

# Consumption surface (scripts/export_*.py) is in scope -> impact_map required.
# Leaf/additive/evidenced short-form:
impact_map: >
  writers: NONE — no dbt model changes. `mart_player_profile.player_birth_date` already exists
    (dbt_project/models/5_marts/shared/mart_player_profile.sql:75; lineage staging -> dim_player.sql:26
    -> mart, typed DATE) and is already queried by the player fetch `select * from mart_player_profile`
    (scripts/export_site_data.py:394). The export only reads an already-present column via latest.get();
    it derives nothing (consumption-layer contract honored).
  downstream: the v2 player payload is consumed only by `site_v2/` — an empty Astro scaffold (2 stubs:
    site_v2/src/pages/index.astro + [lang]/index.astro), NO player-page consumer yet. The payload SHAPE is
    documented in two spec files — docs/wireframes/03_player_profile.md (§3 enumeration, §5 identity
    binding, §10 gaps) and docs/wireframes/99_gaps_register.md (GAP-14 row) — BOTH updated in this PR so
    they stop describing birth_date as missing. (An earlier impact_map claimed "grep: only
    export_site_data.py + its test reference the shape" — that grep was incomplete; corrected here. A6.)
    No JSON schema enforces payload keys.
  layer_rules: consumption-layer contract (dbt_project/docs/layering.md §Consumption layer) — the export
    may select/rename, NEVER derive a fact. This surfaces an existing identity column with no transform;
    age stays a render concern (shared.yml:974). The doc edits are spec-only (no code/logic).
  deploy_order: NONE — `export_site_data.py` is wired into NO workflow yet (only `export_pages_data.py`,
    the SEPARATE live-MVP export, runs in pages-match-preview.yml + ci-ui.yml). No warehouse migration; no
    nightly interaction; additive JSON key cannot break a schema. Docs are not executed.
  blast_radius: one new additive key `birth_date` on the player payload JSON + a 4-spot wireframe sync +
    one gaps-register status line. No mart/number changes. The live MVP (`site/`, fed by export_pages_data.py
    + mart_matchday_insights) is untouched. RAW/dbt unaffected — `ci-data-build` skips (no dbt change); the
    export shape is python-unit-tested.

decisions_taken: >
  GAP-14 was ruled approved (CPO 2026-06-11, gaps register) and CPO-picked this session (export-only;
  simplest). The change is purely additive: surface the existing `mart_player_profile.player_birth_date` as
  a top-level identity key. The key NAME follows the established top-level bare-noun identity convention
  already locked in shape_player_payload — name / nationality / photo / position all strip the mart's
  `player_`/`_code` affix — so the column `player_birth_date` surfaces as `birth_date` (CPO confirmed the
  key name at plan approval). The value is the stored DATE verbatim (serialized by default=str); no age is
  derived here (render concern, shared.yml:974). The directly-coupled wireframe + gaps-register doc sync was
  folded into this PR per the CPO's explicit go ("fix that doc too, now, in the same change", 2026-06-30) —
  completing GAP-14 in code AND spec rather than shipping a spec that contradicts the code. No live-MVP
  impact (separate export).

decisions_reserved:
  - HOW birth date / age renders in the identity header (display treatment + position in the layout) — a
    frontend/UX (§10) call deferred to the v2 frontend (Phase E). The wireframe layout annotation stays
    illustrative, not prescriptive; this PR only makes the data available and records that availability.

done_when:
  - shape_player_payload returns `birth_date` from `latest.get("player_birth_date")`; no query, mart, or
    other-shaper change.
  - `pytest tests/test_export_site_data.py` passes, incl. a new assertion that the payload surfaces
    `birth_date`; full `tests/` suite green.
  - docs/wireframes/03_player_profile.md no longer lists birth_date as missing (§3 enumeration includes
    `birth_date`; §5 binding present-tense, key `birth_date`; §10 GAP-14 line removed); 99_gaps_register.md
    GAP-14 marked shipped.
  - Offline gates green (validate-local: python tests; no dbt/SQLFluff path touched). `ci-data-build` skips.
  - scope-auditor + analytics-engineer-reviewer + cto-reviewer + bi-analyst-reviewer PASS (>=2 risks each);
    review.md diff_sha256 binds the staged diff; CPO merges (never self-merge).

amendments:
  - 2026-06-30: + docs/wireframes/03_player_profile.md, + docs/wireframes/99_gaps_register.md,
    − .claude/active_work.md — authority: CPO explicit go this session ("Fix that doc too, now, in the same
    change"); content: fold the directly-coupled wireframe + gaps-register doc sync into this PR (resolves
    the scope-auditor doc-sync FAIL); drop active_work.md from scope (the handover refresh is a separate
    step, per the #607→#608 precedent). The impact_map grep claim was corrected (A6).
