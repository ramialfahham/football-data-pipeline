# Retroactive alignment audit — 2026-06

> Governance program G4 (plan `fuzzy-launching-meadow.md` §5). A current-state audit
> of the codebase against its locked contracts. **Findings only.** Every disposition
> for a `violation` / `unapproved-decision` is a CPO ruling; the **CPO ruling** column
> is blank until ruled. Findings become GitHub issues **only after** the CPO rules.

## Scope (CPO kickoff rulings, 2026-06-12)

- **Depth:** current-state + per-finding provenance (the commit that introduced a
  finding is attached where "was this ever approved?" is the crux). No full
  commit-history walk.
- **Surfaces (7 passes):** dbt models · export scripts (consumption contract) ·
  seeds/macros · docs-vs-reality · metric values · **ingestion code** · **CI
  workflows**. The live MVP site is **excluded** (frozen / record-only; GAP-17).
- **Finding source:** four blinded read-only reviewer subagents generated the
  findings per domain; the builder compiled them verbatim and attached provenance.
  The builder did not re-judge its own past work.

## Method & caveats

- **Reviewers (cold, no conversation history, tools = Read/Grep/Glob only):**
  `analytics-engineer-reviewer` (sonnet) → dbt + seeds/macros + export consumption;
  `cto-reviewer` (sonnet) → scripts/tooling + CI workflows;
  `data-engineer-reviewer` (sonnet) → ingestion + registry;
  `scope-auditor` (haiku) → decisions/provenance + doc-vs-reality.
- **Provenance was attached by the builder** (reviewers have no git access). Provenance
  is a mechanical `git log -S` / add-commit lookup, not a judgement.
- **scope-auditor ran on its pinned `haiku`** (governance economy, CPO ruling
  2026-06-12). The depth of the decisions/provenance pass is bounded by that pin —
  see **F39** (a haiku false-finding caught by builder fact-check). Re-running that
  pass on a stronger model is a cheap CPO follow-up if the findings below look thin.
- **Classes:** `violation` (breaks a written contract) · `unapproved-decision` (a §10
  CPO-class choice with no recorded approval) · `stale-doc` (a contract doc that no
  longer matches reality) · `ok` (a place specifically checked and found aligned).
- Findings the two reviewers raised independently are merged and attributed to both.
  Genuine judgement-splits between reviewers are recorded as such (F3, F38).

---

## A. Warehouse / dbt + consumption layer

| # | class | evidence (file:line) | provenance | finding | proposed disposition | CPO ruling |
|---|-------|----------------------|------------|---------|----------------------|------------|
| F1 | violation | `dbt_project/models/2_base/api_football/base_apif__transfers.sql:3` | `7002643` 2026-05-29 (a *"purge dead bl1/d1 naming"* refactor that left the filter) | `where league_code = 'BL1'` in a `2_base` model — a hardcoded competition identifier above staging. Any new league's transfers silently produce zero rows, breaking downstream player-identity resolution. | File issue: replace with a data-presence guard, or escalate if BL1-only is intentional | |
| F2 | violation | `dbt_project/models/2_base/api_football/base_apif__players.sql:25` | (consequence of F1) | Comment *"BL1 only for now; extend this CTE…"* — an acknowledged scope restriction wired into a competition-agnostic layer; non-BL1 transfer-sourced player identities are omitted. | File issue: fix F1 first, then remove the BL1 reference | |
| F3 | violation→**escalate** | `dbt_project/models/5_marts/shared/mart_team_market_value.sql:14`; test `shared.yml:881` | `f421f93` 2026-05-26 (folder reorg) | `where league_code = 'WC'` hardcoded in a mart (and the `accepted_values: ["WC"]` test). May be an accepted WC-only scope rather than a defect. | Escalate to CPO: intended WC-only forever (document the exception + use a var) or make generic? | |
| F4 | violation | `scripts/export_site_data.py:191-209` (`shape_top_players`) | `ab46d5a` 2026-06-11 (#365) | Ranks players by goals/assists/key-passes in Python (A5). Leaderboard rank is a warehouse fact (`mart_top_scorers.scorer_rank` is the pattern). | File issue: add a mart/int rank column; delete the Python ranking. **(within GAP-19)** | |
| F5 | violation | `scripts/export_site_data.py:80-93,96-105,161` (`slugify`/`fixture_slug`) | `13c3b7c` 2026-06-10 (#365) | Generates URL slugs in Python via NFKD + ASCII-ignore. Slugs are published URL identity → must come from the warehouse. **Also** the transliteration choice (NFKD/ASCII-strip vs unidecode) is itself a §10 permanent-once-published decision — and is one of the two **parked slug rulings** (active_work.md). Raised by both analytics-engineer and scope-auditor. | File issue **(GAP-19)** for warehouse slug column; escalate the spelling/transliteration choice as the parked pilot ruling | |
| F6 | violation | `scripts/export_site_data.py:61-74` (`_GROUP_OF_TYPE`) | `ab46d5a` 2026-06-11 (#365) | A Python dict maps `competition_type` → nav group. Taxonomy mappings belong in seeds/registry; adding a competition_type needs a code edit. | File issue: add `nav_group` to `competition_types.csv`; read it in `build_nav()`. **(within GAP-19)** | |
| F7 | **escalate** | `scripts/export_site_data.py:373-463` (`fetch_fixture_payloads`) | `ab46d5a` 2026-06-11 (#365) | Assembles a per-fixture-side payload by joining 4 marts in Python (momentum, season-to-date, standing-context, h2h). Individual reads are select/filter, but the composition determines "what a fixture page shows" — the A4 borderline. | Escalate to CPO: are multi-mart payload joins in Python an accepted v2 pattern, or do they need a fixture-payload mart? | |
| F8 | violation | `dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__full_season_metrics.sql:125-128` | — | `save_ratio_season` = saves / (saves + goals_against). Numerator is stat-covered-games only; denominator sums all finished games — a same-window violation the W1/W2 marts avoid via `goals_against_in_save_games`. **Not** covered by the GAP-17 note. | File issue: coverage-restrict the denominator; add a `[0,1]` range test | |
| F9 | violation | `…/int_team_season__full_season_metrics.sql:116-120` | — | `finishing_efficiency_season` numerator (`goals_for`, all games) vs denominator (`shots_on_goal`, covered games) — same-window mismatch; W1/W2 use `goals_for_in_shot_games`. | File issue (GAP-17 sub-item or new): apply the coverage-restricted pattern; add range test | |

**Coverage (analytics-engineer):** read layering.md + engineering_standards.md (full),
working_agreement Appendix A, all 19 marts, 14 intermediates, 7 base, 6 core, 9 staging,
all mart/intermediate YAML, metric_catalogue.csv, 10 macros, 6 export/gen scripts.
**`ok` rows verified:** staging purity (no refs/group-by above staging); core has no
`stg_` refs; intermediates never ref marts; W1/W2 window marts respect same-window with
ratio bound tests; mart metrics trace to catalogue rows; legacy `export_pages_data.py`
does no metric math.

---

## B. Platform / scripts / CI workflows

| # | class | evidence (file:line) | provenance | finding | proposed disposition | CPO ruling |
|---|-------|----------------------|------------|---------|----------------------|------------|
| F10 | violation | `scripts/check_task_artifacts.py:79`; `.claude/review_routing.json:40-43` | `85340aa` 2026-06-12 (G3) | The `artifact_only` allowlist (`​.claude/task/**`) exempts `contract.md` — the document that authorizes all code edits — from review. A contract-only commit gets zero adversarial review. (Demonstrated live: PR #407 merged contract-only with no review.) | Escalate to CPO (guard-integrity change, protected path): narrow `artifact_only` to exclude `contract.md`, or add a contract-amendment CI validation | |
| F11 | violation | `scripts/check_task_artifacts.py:6-8` (design) | `85340aa` 2026-06-12 (G3) | CI cannot recompute a STAGED hash, so `review.md`'s `diff_sha256` is checked for well-formedness only — not bound to the PR diff. A code-commit-then-artifact-commit ordering false-greens on the prior task's review. **This is hardening candidate (c).** | Escalate to CPO: fix via branch-diff hash at review time, or require the artifact commit be the sole post-code commit. **(c) — scheduled as its own gate-lifted task)** | |
| F12 | violation | `scripts/check_task_artifacts.py:97-98` | `85340aa` 2026-06-12 (G3) | Global `count(ESCALATE) > count(CPO ANSWER)` check is redundant with — and weaker than — the per-section pairing below it; cross-section answers can mask an unanswered escalate at the global check (the per-section loop still catches it). | File issue: demote to a commented secondary backstop; document the dependency on the per-section loop | |
| F13 | violation | `.github/workflows/pages-match-preview.yml:17-22` | — | `push` path triggers list per-competition staging dirs (`…/pl/**`, `pd/**`, `bl2/**`, …) that the **zero-file rule forbids** and that don't exist. Dead triggers that also signal a forbidden architecture. | File issue: remove the per-competition path triggers | |
| F14 | violation | `scripts/scaffold_domestic_league_staging.py:1-34` | `64d7006` 2026-05-18 (pre-unified-raw onboarding) | Generates per-competition staging subdirs by copying BL1 files — its entire purpose is a CI-failing zero-file-rule violation; also hardcodes BL1. Obsolete relic with no deprecation guard. | File issue: delete the script; escalate only if a use is believed still-needed | |
| F15 | violation | `scripts/add_footer_i18n_keys.py:53-69` | `4ee6428` 2026-05-24 | One-time i18n migration left at module level — no `__main__` guard, not atomic (partial run truncates JSON), silently overwrites i18n values on re-run. | File issue: retire it (migration complete), or add a guard + dry-run | |
| F16 | unapproved-decision | `scripts/slack_bridge/*.py`; `.github/workflows/_paused/slack-executor-bridge.yml` | `5ec95aa` 2026-05-20 (automation wave) | A Slack-intake + executor-forwarding bridge **service** (new mechanism, A3) with no recorded CPO approval. Paused, but the scripts are committed and the workflow references live bridge secrets. | Escalate to CPO: produce the approval record or retire. Paused ≠ approved | |
| F17 | unapproved-decision | `scripts/squad_watch.py:1-45` | `3ee10a7` 2026-05-21 (#163) | A 390-line tool calling live `/players/squads` + `/players` for 48 WC teams — a new external-API-call-volume mechanism (§10 cost) with no documented budget approval. | Escalate to CPO: document approved API budget + use context | |
| F18 | unapproved-decision | `.github/workflows/board-request-sync.yml` | `8ca3da1` 2026-05-20 | A workflow making GitHub GraphQL **mutations** via a PAT on every PR/issue event (new mechanism + CI minutes on every PR + PAT of unstated scope). No approval cited. | Escalate to CPO: approve or retire; document PAT scope | |
| F19 | unapproved-decision | `.github/workflows/ci-failure-watchdog.yml:1,17-18` | `d746e71` 2026-05-20 | Auto-reruns failed CI jobs and opens/comments issues; holds `actions: write` + `issues: write` — the broadest permission widening in the active set. New lifecycle mechanism, no approval; watches `ci-ui` by display-name (renames silently drop the watch). | Escalate to CPO (security-class permission widening): approve or retire | |
| F20 | unapproved-decision | `requirements.txt:1-4` | — | `requests`, `functions-framework`, `beautifulsoup4`, `pandas` unpinned → supply-chain/reproducibility drift. `beautifulsoup4` appears unused; `functions-framework` likely belongs in `ingestion/…/requirements.txt`. | File issue: pin all; audit whether bs4/functions-framework belong at root | |

**Coverage (cto):** read cto.md, agent_guardrails.md, working_agreement §4/§10/Appendix A;
all 10 active + 4 paused workflows; both requirements.txt; all in-scope scripts (check_*,
sync, diagnostics, drop_*, slack_bridge, security); all 5 hooks; settings.json + routing.
**`ok` rows verified:** all 5 CI check scripts fail **closed**; all 5 project hooks fail
**open**; `restore_from_time_travel.py` defaults to dry-run and is re-run safe.

---

## C. Ingestion + registry

| # | class | evidence (file:line) | provenance | finding | proposed disposition | CPO ruling |
|---|-------|----------------------|------------|---------|----------------------|------------|
| F21 | violation | `tests/fixtures/apif/` (absent); `tests/test_batch_fixtures.py` etc. (mocks only) | — | The directory of committed sample payloads **does not exist**. Parser/merge logic in `batch_fixtures.py`, `coverage.py`, `completeness.py`, all loads has no fixture-backed offline tests — direct violation of the CPO rule (2026-06-12). | File issue: create `tests/fixtures/apif/` + rewrite parse/merge tests; must precede further parser changes | |
| F22 | violation | `ingestion/api_football/registry.py:133` | — | The `supporting_leagues` guard checks `competition_type == "international_tournament"`, a value **no** registry competition uses. Result: WC's 7-league supporting block parses to `()`, and COAM/AFCON/ACN/GCUP/UNL/EURO/CNL declare `form_source: supporting_leagues` with **no validation error** → form data silently missing at runtime. | File issue: fix the guard to the real `competition_type` values; add a WC supporting-leagues test. CPO to confirm whether form for those comps is intentionally deferred | |
| F23 | violation | `docs/competition_registry.yml:974-986` (AFCCL) | `aab550c` 2026-05-27 | `provider_league_id: 17` is `ingest_active: true` while the note itself says *"17 is the legacy ID — spot-check first ingest"* — the exact four-wrong-IDs failure pattern; an `api_coverage_verified` date is not discovery evidence. | File issue: set `ingest_active: false` until `discover_competition.py` confirms ID 17; add the evidence | |
| F24 | violation | `ingestion/api_football/loads/coaches.py:64`; `injuries.py:74`; `docs/data_contract.md` (absent) | — | `RAW_APIF_COACHES` and `RAW_APIF_INJURIES` are written every run but absent from the data contract's unified-raw-tables section — no contractual anchor for downstream consumers. | File issue: add both tables (write mode, partition, cluster, schema) to data_contract.md | |
| F25 | unapproved-decision | `docs/competition_registry.yml:57` (BL1 `history_seasons: 10`); `settings.py:38` | `6ee89b3` 2026-05-06 | BL1 carries `history_seasons: 10` (the max window) with no quoted CPO approval in its note; all other in-progress comps use `5` with approval quoted. CLAUDE.md requires explicit CPO approval for `history_seasons`. | Escalate to CPO: confirm + record approval for BL1=10, or treat as a cost finding | |
| F26 | unapproved-decision | `ingestion/api_football/registry.py:198-199` | — | `ingest_active` defaults to **`True`** when the field is absent. If the CI presence check ever regresses, a new comp ingests without cost approval. Fail-safe default should be `False`. | Escalate to CPO (onboarding cost behaviour): default to `False` or raise on absence | |

**Coverage (data-engineer):** read data_contract.md, operations_guide.md,
data_engineer.md, working_agreement, CLAUDE.md, competition_registry.yml + seed +
dbt_project.yml vars, dbt-scheduled.yml; all 27 `ingestion/api_football/**` files;
confirmed `tests/fixtures/apif/` absent. **`ok` rows verified:** FIXTURE_DETAILS
merge-on-write is idempotent (delete-before-reinsert); no WRITE_TRUNCATE on any data
table (only single-state operational tables); registry↔seed↔vars sync holds across all
45 comps; no API-predictions endpoint in live code paths.

---

## D. Decisions, provenance & stale docs

| # | class | evidence (file:line) | provenance | finding | proposed disposition | CPO ruling |
|---|-------|----------------------|------------|---------|----------------------|------------|
| F27 | stale-doc | `dbt_project/docs/layering.md:239-247` | — | Mart inventory lists **5** marts; **19** exist (14 undocumented: standings, market_value, form_window, momentum×2, season_to_date×2, fixture_stats×2, head_to_head, player_match_log, player_profile, team_profile, fixture_standing_context). Raised by analytics-engineer **and** scope-auditor. | Escalate to CPO: should the inventory be exhaustive? If yes, update with all 19 (grain/material/notes) | |
| F28 | stale-doc | `dbt_project/docs/layering.md:175-185` | — | Fact inventory lists **6**; **7** exist — `fct_team_market_value_snapshot` (seed-driven) is undocumented. | Escalate to CPO: first-class fact (add to inventory) or utility table (document the pattern)? | |
| F29 | stale-doc | `dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql:9` | — | Docstring lists a consumer (`int_matchday__fixture_player_insights`) retired in #321; no live model refs this intermediate — possibly orphaned. | File issue: identify the live consumer + fix docstring, or remove if orphaned | |
| F30 | stale-doc | `…/int_team_season.yml:68` | — | Same retired-consumer reference in the model description. | File issue: update to actual consumers | |
| F31 | stale-doc | `docs/operations_guide.md:223`; `dbt-scheduled.yml:5` | — | Doc says scheduler runs *"twice daily (04:00, 16:00 UTC)"*; the workflow has a single `0 4 * * *`. Doc overstates cadence 2× and conflicts with the cost rule. | File issue: correct to once-daily 04:00 UTC | |
| F32 | stale-doc | `ingestion/api_football/loads/catalog.py:32-34` | — | Comment claims `WRITE_TRUNCATE`; the call (line 37) passes `append=True` → WRITE_APPEND. Misleading about data safety. | File issue: correct the comment | |
| F33 | stale-doc | `ingestion/api_football/fixture_scheduling.py:388` | — | Docstring estimates 5 calls/fixture "incl. predictions"; predictions aren't ingested (project rule); function is dead code. | File issue: fix to 4 + drop "predictions"; consider deleting the dead fanout functions | |
| F34 | stale-doc | `docs/competition_registry.yml:924-925` | — | Section header reads `PLANNED — Continental club showpieces`; all 5 entries are `in_progress` + `ingest_active: true`. | File issue: update header to `IN PROGRESS` | |
| F35 | stale-doc | `docs/agent_guardrails.md:88-100` | — | Lists 5 global hooks "canonical copies in `docs/portable_guardrails/`"; if that dir is absent/out-of-sync the "version-controlled" claim is false (repo-only scope can't verify global hooks). | File issue: verify `docs/portable_guardrails/` exists + current; else fix the doc | |
| F36 | stale-doc | `docs/agent_guardrails.md:66-69` | — | Describes `cto-reviewer` as "dormant"; routing actively routes scripts/CI/etc. to it — it is active. | File issue: update to "active" | |
| F37 | stale-doc | `docs/working_agreement.md` §2 (lines 33-34) | — | §2's protected-paths list omits `.claude/agents/**` (now protected per the 2026-06-12 ruling, documented only in agent_guardrails.md) — a split that could mislead a §2-only reader. | Escalate to CPO: add `.claude/agents/**` to §2, or accept the documented split | |
| F38 | unapproved-decision | `dbt_project/models/4_intermediate/shared/int_team_profile__streaks.sql:1-83`; `mart_team_profile.sql:117-123` | — | Five streak metrics (unbeaten/win/winless/clean-sheet/scoring run) are modeled + surfaced on team profile but are **not** in the catalogue and have no wireframe/CPO product sign-off. **Judgement-split:** scope-auditor flagged this as an unapproved product feature; analytics-engineer classified the adjacent `performance_vs_results_gap` as `ok` (context signal, not a published metric). | Escalate to CPO: are streaks confirmed product features (→ catalogue) or modeled ahead of #391 wireframe sign-off? | |
| F39 | **reviewer error (no action)** | `docs/wireframes/metrics_display.md` | builder check: **PRESENT** | scope-auditor (haiku) reported this file **missing** and raised a critical stale-doc finding on it. Builder fact-check: the file **exists**. The finding is **false** — recorded to (a) not propagate it and (b) calibrate the haiku-pinned provenance pass depth. | No action. Calibration note re: scope-auditor model pin | |
| F40 | ok (assumption corrected) | `docs/roles/analytics_engineer.md` | — | The handover/plan assumed this role brief was **stale** (pre-refactor). scope-auditor checked: it correctly describes unified-raw + zero-file + league_code and is aligned with CLAUDE.md and layering.md. **The stale assumption, not the doc, was wrong** (G3 evidently refreshed it). | No action; correct the handover assumption | |

**Coverage (scope-auditor):** read working_agreement (§10/§11/Appendix A), layering.md,
site_architecture.md, north_star.md, wireframes 01-03 + 99_gaps_register, roles/
analytics_engineer.md, metric_catalogue.csv, export_site_data.py, escalations.log,
routing, active_work.md. Searched dbt/macros for UDFs / on-run-start / custom
materializations / per-competition dirs → **none found** (no new warehouse mechanisms).

---

## Cross-reference: already-logged gaps (do not double-file)

From `docs/wireframes/99_gaps_register.md`: **GAP-09/10/11** (metric display, approved
2026-06-11); **GAP-17** (season rollup denominator alignment — *pending*, shipped MVP
numbers **frozen**; F8/F9 are adjacent but reviewer states they are **not** covered by
the GAP-17 note); **GAP-18** (tournament form windows, before WC 2026); **GAP-19**
(consumption-layer audit — F4/F5/F6 are its line-item inventory, incl. the slug ruling).

## Known governance-hardening candidates surfaced here

- **(c)** F11 — CI cannot bind `review.md` to the PR diff (memory
  `governance_artifact_commit_ordering.md`). Scheduled as its own gate-lifted task this
  G4 phase.
- **(a-adjacent)** F10 — the `artifact_only` lane exempts the authorization contract
  from review (demonstrated by PR #407). New observation; belongs with the (a)/(c)
  hardening discussion.

## Disposition summary (counts, pre-ruling)

- `violation`: F1, F2, F4, F5, F6, F8, F9, F10, F11, F12, F13, F14, F15, F21, F22, F23, F24 (17)
- `unapproved-decision`: F16, F17, F18, F19, F20, F25, F26, F38 (8)
- `escalate` (ambiguous, reviewer would not classify): F3, F7, F27, F28, F37 (5)
- `stale-doc`: F29, F30, F31, F32, F33, F34, F35, F36 (8)
- `reviewer error / no action`: F39 (1)
- `ok / assumption corrected`: F40 (1)

**Next:** CPO rules each row (CPO-ruling column). Only then do approved findings become
issues. Nothing here is acted on — this document proposes; the CPO decides.
