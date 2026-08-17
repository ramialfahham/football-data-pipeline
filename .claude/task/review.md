# Review — feat/62-4-export-competition-index — 2026-08-17

diff_sha256: 9c94e26a611e26a65b2498fcdabe7e537e47bce3e210cb0f1fcf8d05228a6383

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: diffed files (contract.md, docs/site_architecture.md, scripts/export_site_data.py,
  tests/test_export_site_data.py, plus excluded .claude/active_work.md) all match contract's
  scope_paths exactly — no extra file touched.
- §10 silent decision: checked shape_competition_index/fetch_competition_index against the cited
  escalations.log 2026-08-16 entry ("feat/69-5-62-3-country-fk-and-mart", Ruling 4 — "THE MART
  CARRIES FACTS, THE SPEC DECLARES THE ORDER BY") — the code's `order by league_code` and its
  comment explicitly disclaiming it as display order match that ruling; no re-decision of sort
  order occurred here.
- Named-untouched functions: grepped _registry_competitions, fetch_nav/build_nav,
  _competitions_index, fetch_competition_payloads in the patch — all only appear as unmodified
  context lines, confirming the impact_map's "read-only reference points, NOT modified" claim.
- decisions_reserved (deferring CI --entities wiring to step 5): verified .gitlab-ci.yml/
  deploy-site-v2.yml invocations are unchanged in the diff and the new entity type stays dormant
  unless explicitly requested — an honest engineering deferral, not scope-dodging, since nothing
  downstream reads the file yet.
- Credentials/secrets: swept the full patch for key/token/secret/password/credential/permission
  patterns — only benign dict-key literals, nothing credential-shaped.
- Doc-sync: docs/site_architecture.md's competitions-index row is updated in this same branch to
  name competition_index.json/mart_competition_index, satisfying done_when.
- New mechanism / recurring cost: shape_competition_index is a pure keep-list projection, one more
  read-only SELECT in a script that already runs — no new warehouse object, library, service, or
  schedule introduced.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Keep-list column parity: _COMPETITION_INDEX_KEEP vs mart_competition_index.sql select list and
  shared.yml column docs — exact 14/14 match, no defect.
- shape_competition_index() computation check: dict-projection only, no rank/sort/filter/derive;
  unit test asserts order preservation and non-passthrough of unlisted columns.
- order by league_code in fetch_competition_index(): checked against escalations.log 2026-08-16
  CPO ruling on the approved display sort — confirmed this is a diff-determinism sort, not the
  real page order, documented as such in code.
- Claimed-untouched functions (_registry_competitions, fetch_nav, _competitions_index/
  competitions.json, fetch_competition_payloads/"competitions") — verified all sit outside the
  diff and are structurally unchanged.
- Downstream dormancy: grep site_v2/src for "competition_index" (zero hits) and CI entities lists
  in .gitlab-ci.yml:767 / deploy-site-v2.yml:65 (still teams,fixtures only) — confirmed new path
  is inert in deployed pipelines.
- Catalogue governance / hardcoded competition identifiers / same-window ratio rule — not
  applicable, no metric or ratio introduced.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round-1 gap (ambiguous fixture order in test_shape_competition_index_projects_the_keep_list_and_
  changes_nothing): re-derived both accidental-sort outcomes against the corrected fixture. Input
  order is [WC, PL]; alphabetical league_code sort and ascending region_rank sort both yield
  [PL, WC] — differing from the asserted ["WC", "PL"], so the assertion can only pass if the
  implementation preserves input order, which it does. Gap closed (also independently verified by
  the builder: temporarily sorting the function made the test go red, reverting made it green
  again).
- shape_competition_index implementation: confirmed select/project only, no sorted()/filter/
  derived field.
- Test also exercises null preservation, key-projection (unlisted column dropped), and both
  label-resolution branches — not happy-path-only coverage.
- CI/deploy wiring: grepped .gitlab-ci.yml and deploy-site-v2.yml for competition_index — zero
  hits in both, confirming dormancy.
- ENTITY_TYPES tuple change and the new export_all() block: additive only, follows the exact same
  write pattern as the immediately preceding landing block.
- Dependency/credential/build-health/hosting surfaces: no requirements/package/hook/workflow files
  in the diff; no secrets or permission widening.

## escalations
(none)
