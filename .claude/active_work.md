# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-13 (G4 audit-cleanup backlog COMPLETE + form-model naming refactor
#463 MERGED, old BQ tables dropped). **Website blueprint (#391) is PAUSED by CPO order.** The agent-governance system (plan
`C:\Users\Rami\.claude\plans\fuzzy-launching-meadow.md`) is fully LIVE: G1–G4 shipped.
Machinery: reviewer subagents in `.claude/agents/` (PROTECTED), routing in
`.claude/review_routing.json` (PROTECTED), the 4-step review cycle (Code Lock → cold
Blinding → Cross-Examination → SHA-256 Lock in `.claude/task/review.md`), the commit gate
(`git commit` DENIED without a matching review artifact; commit form = a SOLE plain
`git commit` — NO `cd … && git commit` prefix, NO chained `git add … && git commit`, NO
pipes), and the CI backstop `scripts/check_task_artifacts.py`. Gate integrity (#409/#421,
merged) closed: review `diff_sha256` covers code+contract EXCLUDING `hash_exclude_paths`
and CI RECOMPUTES it from `git diff base...HEAD --no-renames --no-abbrev`; contract.md is
NOT artifact-exempt and must be FINAL in the reviewed commit (no post-commit contract
amendments)._

## Standing authority (in force)
- **STANDING CPO GRANT (2026-06-13, `.claude/task/escalations.log`):** work the
  NON-protected, non-§10 audit-cleanup backlog autonomously (full review cycle → open PR;
  **CPO merges**). PLUS a BATCH protected_override for removing dead/stale
  `.github/workflows/` entries. Stop-conditions ALWAYS hold: never merge (CPO does);
  escalate §10 blinded; stop for cost/destructive.

## This session — G4 audit-cleanup backlog COMPLETE
- **#454 MERGED** — data_contract.md staleness follow-ups (MERGE vs RESHAPE landing-zone
  wording; coaches/injuries added to the append-only list).
- **#413 → PR #456 MERGED** — PAT scope audit. Documented the least-privilege
  `PROJECT_AUTOMATION_TOKEN` scope on docs/board_request_sync.md (read-only; no token touched).
- **#410/#411/#412 → PR #458 MERGED** — retired the Slack-to-Executor bridge (#410) +
  squad_watch.py (#411); declawed ci-failure-watchdog.yml (#412: removed the auto-rerun step
  + dropped `actions: write`, KEPT the [CI Failure] issue notification). Both protected-file
  edits done under explicit CPO protected_override (escalations.log 2026-06-13).
- **#430 → PR #460 MERGED** — removed the dead pages-match-preview trigger for the deleted
  `wc_supporting_league_codes.csv` seed, and corrected the retired
  `form_source`/`supporting_leagues` references in pipeline_architecture_plan.md to the
  competition_types taxonomy basis. **Product/form rules unchanged; CLAUDE.md unchanged.**

## After the backlog — form-model naming refactor (CPO request, COMPLETE)
- **PR #463 MERGED** — consistent naming for the form-window model family (CPO §10 ruling
  "Option 2", escalations.log 2026-06-13). PURE rename, no logic/grain/metric change. The
  NEW VOCABULARY (use these names):
  - live form: `int_momentum_window__team` (selection legs) + `int_momentum__{team,player}`
    (aggregate); marts `mart_momentum_window__team` + `mart_momentum__{team,player}`.
  - season record: `int_season_record__{team,player}`; marts `mart_season_record__{team,player}`.
  - OLD names (`int_form_window__team`, `int/mart_season_to_date__*`, `mart_form_window__team`)
    are GONE — renamed AND the orphaned BigQuery tables were DROPPED 2026-06-13 (CPO-approved,
    after the green ci-data-build built the new tables; 7-day BQ time-travel recovery exists).
  - KEPT deliberately: `window_type` VALUES (`last_5`/`season_to_date`/`prev_season` = the cut,
    not the model root) and the published JSON key `form_window` (UI contract). Authoritative
    window matrix = docs/metrics_context_model.md §4 (per competition_type × pre/during/post).

## PENDING CPO ACTIONS (outside the tree — only the CPO can do these; verify if done)
1. **Set `PROJECT_AUTOMATION_TOKEN`** to the fine-grained least-privilege scope (Projects
   RW, Issues R, Pull requests R, Metadata R, this-repo-only) per docs/board_request_sync.md
   (from #413, merged).
2. **Remove now-unused secrets** `CURSOR_EXECUTOR_BRIDGE_URL` + `CURSOR_EXECUTOR_BRIDGE_TOKEN`
   (from #458, merged — nothing in the tree references them anymore).

## Process lessons locked this session (do not repeat)
- **Write the handover ONLY at session END, in its own artifact-only branch/PR — NEVER
  inside a task PR.** A per-task handover commit raced the #454 merge by ~9s and got
  stranded on a dead branch; the handover must not chase a merge.
- **`git commit` must be the SOLE command** in the Bash call — no `cd … &&` prefix (the
  working dir already persists at repo root), no `git add … &&` chain, no pipes. Stage and
  commit as SEPARATE calls.
- **Don't over-read one model and manufacture a §10 question.** On #430 the builder read
  `int_form_window__team` in isolation and wrongly escalated that the WC form rule had
  changed; the CPO clarified the form rule is SETTLED (competition taxonomy + pre/during/post
  phase + last-5 / season-to-matchday windows). Verify the whole system before escalating.
- **Finalize the contract (full scope_paths + protected_override) on a CLEAN tree BEFORE
  any code edit.** Twice this session a missed scope file forced a restore-and-redo.
- **Editing `.claude/active_work.md` needs it in the contract's scope_paths** even though
  the commit is review-exempt (edit-gate vs commit-gate scope; see memory
  feedback_governance_edit_gate_scope).
- **A PR rebased past a sibling task that rewrote contract.md needs a review-hash re-lock.**
  When another task merges first, the shared `.claude/task/` artifacts conflict; rebase onto
  main, resolve those to YOURS, then RECOMPUTE the diff_sha256 (it changes because contract.md's
  diff base moved) and update review.md — content is identical, so the verdicts stand; note the
  re-lock. Then `--force-with-lease` the feature branch (never main). Rebase sidesteps the
  commit gate (git, not a Bash `git commit`); the post-commit auto-push fails mid-rebase
  harmlessly.
- **A model rename's old BQ tables are dropped AFTER the merge's ci-data-build is green** (so
  the new tables exist as the fallback) — never before. Destructive → needs explicit CPO approval.

## NEXT (CPO directs — none of these are auto-granted)
The G4 audit-cleanup backlog (issues #409–#430) is essentially done. Remaining larger work,
all needing CPO direction (NOT covered by the standing grant):
- **The Pilot** — rework the parked marts stash (`data/marts-gap15-16-19`, `stash@{0}`)
  under the full workflow, incl. the two BLINDED slug escalations (where slugs are produced;
  slug spelling/transliteration). Do NOT pre-decide either.
- **GAP-18 parent-child Core dim** — `parent_competition` (qualifier→tournament, cup→league)
  is in the registry but consumed by no model; this is the proper home for the WC↔qualifier
  form link. Also GAP-18 tournament form windows before WC 2026.
- **Player insights chain #153→#156** — the player-model redesign is COMPLETE (dim_player =
  pure global entity; affiliation = dim_player_team_season_mapping rostered + facts; see
  [[project-player-model-redesign]]).
- **GAP-17** (season-rollup denominator alignment, F8/F9) remains FROZEN — do NOT act.

## Why the pivot (do not re-litigate)
The CPO repeatedly caught agent drift by watching live (wrong-layer logic, unilateral
CPO-class decisions, rule over-extension — see working_agreement.md Appendix A). He
will not keep supervising. The governance machinery now enforces this in code.

## The governance program (approved 2026-06-11; G1–G4 all shipped)
1. **G1 — MERGED (#401)**: working_agreement.md §10 Decision rights (CPO-only classes +
   meta-rule: unclear classification is itself a CPO decision), §11 Blinded escalation
   (premise_check; ≥2 conflicting paths; NO recommendation), Appendix A anti-patterns (A1–A5).
2. **G2 — MERGED (#402)**: `task_contract_gate.py` (edit + shell + post-Bash check),
   `stop_gate.py`, git_discipline flag denies (`--amend`/`--no-verify`/`-n`/hooksPath),
   TEMPLATE.md, working_agreement §2 machine-gated. Write the contract FIRST (clean tree).
3. **G3 — MERGED (#403) + reviewer-model-pinning (#405)**: read-only reviewer subagents
   (praise banned; default FAIL; PASS requires ≥2 real risks; cross-reference Appendix A),
   the serialized 4-step cycle, the commit gate, the CI backstop + PR template block.
4. **G4 — COMPLETE**: `docs/audits/2026-06_alignment_audit.md` = 40 findings via 4 cold
   blinded passes; all ruled by CPO 2026-06-12; approved actions filed as #409–#430 and
   shipped (gate integrity #409/#421; #414 form_source #429; #426 AFCCL #432; #419 doc-sync
   #433/#434; #423/#424 dead scripts #436; #425 deps #438; #427 data-contract #439 + #454;
   player-model redesign #444/#446/#448; #420 closed by transfers deletion; #422 dead
   triggers #450; #413 #456; #410/#411/#412 #458; #430 #460). FROZEN: GAP-17 (F8/F9).
   PARKED to #391/Pilot: F5 slug-spelling, F7, F38.
5. **Pilot**: rework the parked marts branch under the full workflow (see NEXT).

## Parked state (do not touch until the pilot)
- Branch `data/marts-gap15-16-19`: GAP-15/16/19 mart work, built & verified, stashed as
  `stash@{0}` ("parked: marts-gap15-16-19 pilot work"). Contains the slug/UDF work that
  triggered the governance pivot — it gets REWORKED under the new workflow.
- Two CPO rulings pending, to be escalated BLINDED during the pilot: (1) where slugs are
  produced (frontend slug-map vs warehouse), (2) slug spelling (transliteration vs
  ASCII-strip). Do NOT pre-decide either.
- Blueprint resume-state (when CPO un-pauses): PR 3 = screens 04–07; slim export PR; GAP-18
  tournament windows before WC 2026; GAP-17 ruling pending.

## Do NOT
- **No blueprint/feature/data work while the website blueprint is PAUSED** unless the CPO
  directs it; the granted autonomous lane is the audit-cleanup backlog only.
- **Never decide CPO-class questions** (working_agreement §10); escalate blinded (§11) — no
  recommendations in escalations. Don't over-read one model and invent a §10 question.
- Do not compute anything in the frontend/export (layering.md §Consumption layer).
- Do not touch the live MVP; do not change shipped numbers (GAP-17 parked).
- File edits via Edit/Write tools only — never shell redirection/heredocs (A-pattern; G2
  enforces).
- Honor the task contract at `.claude/task/contract.md`: no edits outside scope_paths;
  protected paths need a `protected_override:` field naming the CPO authority; amendments
  only on a clean tree.
- Branch from main; never commit to main; the post-commit hook auto-pushes + opens PRs.
- **Never merge a PR — the CPO merges.**

## Environment notes
- dbt/sqlfluff from project `.venv`. BQ is a SHARED single environment (CI rebuilds from
  whichever branch built last — redeploy before BQ-based verification).
- sqlfluff 4.1.0 parse-depth cliff ≈ 7 nested calls (relevant to the parked slug work; the
  UDF approach in the stash was the unapproved workaround — see A3).
