# G4 audit — raw blinded reviewer outputs (fidelity trail)

> The four cold reviewer passes that generated the findings in
> `docs/audits/2026-06_alignment_audit.md`. Preserved verbatim (tables only;
> prose trimmed) so the scope-auditor faithfulness pass and the CPO can diff the
> compiled doc against source. Builder added provenance + dedup + the F39/F40
> corrections during compilation — those are the only builder edits.

agentIds (re-openable): analytics-engineer = a49937a964aaf31ef ·
cto = a0ade1dee09ec9a47 · data-engineer = a172531cdf2b89ff4 ·
scope-auditor (decisions/provenance pass) = acd84d3dac64b6ecd.

---

## analytics-engineer-reviewer (→ doc §A: F1–F9, F27, F29, F30)

- violation `base_apif__transfers.sql:3` — `where league_code = 'BL1'` in 2_base; new leagues silently zero rows. → F1
- violation `base_apif__players.sql:25` — "BL1 only for now" comment; non-BL1 transfer identities omitted. → F2
- violation `mart_team_market_value.sql:14` + `shared.yml:881` — `where league_code = 'WC'` hardcoded mart + accepted_values test. → F3
- violation `export_site_data.py:191-209` — `shape_top_players` ranks in Python (A5). → F4
- violation `export_site_data.py:86-93/96-105/161` — slug generation in Python (A5, GAP-19). → F5
- violation `export_site_data.py:61-74` — `_GROUP_OF_TYPE` taxonomy map in Python (A5). → F6
- violation `export_site_data.py:373-463` — multi-mart fixture payload assembly in Python (A4 borderline). → F7 (escalate)
- violation `int_team_season__full_season_metrics.sql:125-128` — `save_ratio_season` same-window mismatch; not covered by GAP-17. → F8
- violation `int_team_season__full_season_metrics.sql:116-120` — `finishing_efficiency_season` same-window mismatch. → F9
- stale-doc `layering.md:239-248` — mart inventory lists 5, 19 exist. → F27
- stale-doc `int_player_season__metrics.sql:9` — retired consumer `int_matchday__fixture_player_insights` (#321); possibly orphaned. → F29
- stale-doc `int_team_season.yml:68` — same stale consumer reference. → F30
- ok: staging purity; core no stg refs; intermediate no mart refs; catalogue trace; W1/W2 same-window respected; legacy export no metric math.

## cto-reviewer (→ doc §B: F10–F20; also confirmed F27)

- violation `check_task_artifacts.py:79` + routing `:40-43` — `artifact_only` exempts `contract.md` from review. → F10
- violation `check_task_artifacts.py:6-8` — CI cannot bind review.md to PR diff (hardening candidate c). → F11
- violation `check_task_artifacts.py:97-98` — global ESCALATE/ANSWER count redundant/weaker than per-section. → F12
- violation `pages-match-preview.yml:17-22` — dead per-competition staging path triggers (zero-file conflict). → F13
- violation `scaffold_domestic_league_staging.py:1-34` — generates per-competition staging; zero-file violation; obsolete. → F14
- violation `add_footer_i18n_keys.py:53-69` — one-time migration, no __main__ guard, not atomic. → F15
- unapproved-decision `slack_bridge/*.py` + `_paused/slack-executor-bridge.yml` — new bridge service (A3), no approval. → F16
- unapproved-decision `squad_watch.py:1-45` — new API-call-volume mechanism, no budget approval. → F17
- unapproved-decision `board-request-sync.yml` — GraphQL mutations via PAT on every PR/issue event. → F18
- unapproved-decision `ci-failure-watchdog.yml:1,17-18` — auto-rerun + `actions:write`/`issues:write` widening. → F19
- unapproved-decision `requirements.txt:1-4` — `requests`/`functions-framework`/`beautifulsoup4`/`pandas` unpinned. → F20
- stale-doc `agent_guardrails.md:88-100` — global-hooks/portable_guardrails inventory unverifiable. → F35
- stale-doc `agent_guardrails.md:66-69` — `cto-reviewer` called "dormant" but active. → F36
- ok: all 5 CI checks fail closed; all 5 hooks fail open; `restore_from_time_travel.py` dry-run-default re-run safe.

## data-engineer-reviewer (→ doc §C: F21–F26; F31–F34)

- violation `tests/fixtures/apif/` absent — no sample-based parser tests (CPO rule 2026-06-12). → F21
- violation `registry.py:133` — `supporting_leagues` guard checks an unused competition_type → silent form-data gap (WC + 7 comps). → F22
- violation `competition_registry.yml:974-986` — AFCCL `provider_league_id: 17` active but note says "legacy ID, spot-check". → F23
- violation `coaches.py:64`/`injuries.py:74` vs `data_contract.md` — `RAW_APIF_COACHES`/`_INJURIES` not in contract. → F24
- unapproved-decision `competition_registry.yml:57` + `settings.py:38` — BL1 `history_seasons: 10` (max), no quoted approval. → F25
- unapproved-decision `registry.py:198-199` — `ingest_active` defaults True (should fail-safe False). → F26
- stale-doc `operations_guide.md:223` vs `dbt-scheduled.yml:5` — "twice daily" vs single 04:00 cron. → F31
- stale-doc `catalog.py:32-34` — comment says WRITE_TRUNCATE; call is append=True. → F32
- stale-doc `fixture_scheduling.py:388` — docstring counts "predictions" (no-API-predictions); dead code. → F33
- stale-doc `competition_registry.yml:924-925` — header "PLANNED" but entries in_progress/active. → F34
- ok: FIXTURE_DETAILS merge-on-write idempotent; no WRITE_TRUNCATE on data tables; registry↔seed↔vars sync (45 comps); no API-predictions in live code.

## scope-auditor — decisions/provenance pass (→ doc §D: F27, F28, F37, F38; F39 corrected; F40 corrected)

- stale-doc `layering.md:239-247` — mart inventory 5 vs 19. → F27 (dup of analytics-engineer)
- stale-doc `layering.md:175-185` — fact inventory 6 vs 7; `fct_team_market_value_snapshot` undocumented. → F28
- unapproved-decision `export_site_data.py:80-93` — slug transliteration choice (NFKD/ASCII-strip) implemented ahead of parked CPO ruling. → folded into F5
- unapproved-decision `int_team_profile__streaks.sql:1-83` + `mart_team_profile.sql:117-123` — streak features not in catalogue / no wireframe sign-off. → F38
- stale-doc `01_fixture_page.md:139-156` — claimed `metrics_display.md` MISSING. **BUILDER CORRECTION: file is PRESENT** → F39 (reviewer error, no action).
- stale-doc `working_agreement.md §2 (33-34)` — protected-paths list omits `.claude/agents/**`. → F37
- ok `analytics_engineer.md` — found CURRENT (handover assumed stale). **BUILDER NOTE: corrects the stale assumption** → F40.
- ok: Appendix A current; metric_catalogue has no invented metrics; no UDFs/on-run-start/custom-materializations/per-competition dirs found.
- GAP register already logged: GAP-09/10/11 (approved 2026-06-11), GAP-17 (pending, MVP frozen), GAP-18 (before WC 2026), GAP-19 (consumption audit incl. slugs).
