# Review — feat/391-gap14-player-birth-date — 2026-06-30

> G3 Lock artifact. #391 GAP-14: surface player birth_date in the v2 player payload (export-only,
> additive) + the directly-coupled wireframe/gaps-register doc sync (folded in per CPO go this session).
> Required set (routing): scope-auditor (always) + analytics-engineer (scripts/export_*.py) + cto
> (scripts/export_*.py + tests/**) + bi-analyst (docs/wireframes/**). All four re-run FRESH at this hash
> after the doc sync was added (the first round, code-only, had scope-auditor FAIL on the missing doc sync;
> resolved by folding the wireframe/register sync in, correcting the impact_map A6, and dropping
> active_work.md from scope).

diff_sha256: 5577655cd82f246e5e920312d99f67d333b2f898440a9b3efd78d5511cac86c4

## scope-auditor
VERDICT: PASS
risks_checked:
- Doc-spec drift (App. A2): the wireframe edits (03_player_profile.md §4 annotation + §5 binding, 99_gaps_register.md GAP-14) stay descriptive — they record data availability + "age derived at render" intent but do NOT lock a §10 frontend/UX render decision (HOW age renders is reserved to Phase E in decisions_reserved). The scope amendment properly records the CPO authority; scope_paths match the diff (active_work.md intentionally not edited).
- Consumption-layer boundary (App. A5): top-level surfacing of birth_date via latest.get("player_birth_date") is pure selection (no derivation); _strip_identity drops it only from per-season rows (correct per wireframe §5.2 identity-only binding); the column exists in mart_player_profile.sql:75 (DATE, from dim_player). The impact_map A6 self-correction (earlier incomplete grep) verified honest.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- _strip_identity strip-path scope: applies only to the per-season rows (export_site_data.py:201), never the top-level identity dict; the new birth_date key cannot be double-stripped post-assembly.
- default=str DATE serialization: a BigQuery DATE arrives as datetime.date → ISO-8601 string via default=str (export_site_data.py:349); None → JSON null via the native json path (no raise). Both populated + null paths safe. Lineage staging → dim_player.sql:26 → mart_player_profile.sql:75 confirmed; no dbt/seed/.yml change in the diff → ci-data-build skips.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Test causally necessary: without export_site_data.py:198, latest.get("player_birth_date") returns None and the assertion at tests/test_export_site_data.py:250 fails; the fixture edit at :237 is the sole feeder — the test genuinely exercises the new behavior, would not silently pass pre-change.
- Zero regression surface: only one test uses shape_player_payload, via point assertions (no exact-dict/keys()/snapshot); no player-payload golden files exist; export_site_data.py is wired into NO workflow (pages-match-preview.yml + ci-ui.yml reference only export_pages_data.py) → live MVP isolated; python-ci runs the full tests/ suite. No new dependency, workflow, cost, or permission.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Field-binding accuracy: the mart column player_birth_date (mart_player_profile.sql:75, shared.yml:1024) surfaces as birth_date in the export (export_site_data.py:198) and the wireframe §3/§5 (03_player_profile.md:29,79) — identical spelling, same bare-noun identity convention as name/nationality/photo/position.
- Locked metric display contract untouched: metrics_display.md is not in the diff; the 9 locked player bundles (03_player_profile.md:94-100) are byte-identical; birth_date sits under the identity module, not the stat-bundle module; "age derived at render" is a frontend date-format op (consistent with shared.yml:974), not a modelled/per-90/composite metric. GAP-16 left intact; the register "shipped" annotation matches GAP-18's dual-annotation pattern.

## escalations
(none) — all four required reviewers PASS at this hash; no FAIL, no ESCALATE. The prior code-only round's scope-auditor FAIL (missing doc sync + impact_map A6 + active_work.md scope slip) was resolved by folding the wireframe/register sync into this PR (per CPO go), correcting the impact_map, and dropping active_work.md from scope.
