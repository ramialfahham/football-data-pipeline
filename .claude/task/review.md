# Review — refactor/materialisation-one-rule — one materialisation rule, written once, true in the code

diff_sha256: 91c599f3eda9a9c1b38a9c639bdfed9ed01c7e334f00b8c8483647acf0228c4d

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL: the impact_map asserted readers and blast radius without pasted lineage. Round 2: contract.md now gives the dbt ls downstream result for each of the 13 converted models, the outside-dbt reader grep (scripts, site_v2/src, site_v2/scripts, ingestion), and the row-content exceptions; the finding is addressed.
- Behaviour change disclosed: three models filter on current_date(); as tables the date is the build date, as for their table siblings; follows from the CPO-approved conversion and is disclosed to the CPO who merges.
- protected_override: quoted approval dated 2026-09-29, in chat through the plan; the MR head's Locked files line repeats the quote.
- Scope: every file in the diff is in scope_paths; docs/data_contract.md and test_no_decision_history_in_docs.py by a dated amendment citing the approved plan.
- Thresholds unchanged: NEW MECHANISM none, RECURRING COST down and measured; #183 tie-breaks stay reserved; no credentials or workflow changes.
- Doc sync: layering.md holds the rule; CLAUDE.md, AGENTS.md, engineering_standards.md, analytics_engineer.md, dbt.mdc, data_contract.md point to it; no stale view claims found.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Layer placement: the 65 model diffs remove only the first-line config() and the blank line after it; 52 table and 13 view removals; no SELECT, ref or join changed.
- The 13 views named in the contract match the 13 view removals; the layer defaults for core, intermediate and marts are table, so the 52 removals change nothing.
- The three incremental facts are untouched; materialized now appears under dbt_project/models only in those three; no yml sets a per-model materialisation.
- No grain, seed or catalogue change; no metric created or redefined; no league identifier added.
- Enforcement: check_upper_layer_materialisation exempts only a core fct_* file whose values are all incremental; dims, fct with view or table, and any override in intermediate or marts are rejected; tests cover each accept and reject case and the real tree.
- Rule stated once in layering.md §Materialisation with the incremental rationale preserved; other documents point to it.
- No consumer of the 13 depends on their being views.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Re-run safety: the only executable change is a stateless read-only scan wired into check_layer_contract.py main(); no state written.
- Test coverage: the probe test feeds a core dim view, a core dim incremental, an intermediate table and a marts view (all flagged) and a core fct incremental (allowed) through the real function; reverting the exception or the function fails it; a second test walks the real tree.
- Guard mechanics: the check fails closed and runs in CI (.gitlab-ci.yml) and via pytest; the layer hook is untouched and advisory.
- No dependency, credential, workflow, site or hosting change.
- Doc pins: decision-history counts recomputed from the gate's markers match the lowered pins (layering.md 14 to 9, engineering_standards.md 5 to 4, data_contract.md unchanged at 12); token pins match the files that quote the tokens.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Guard authority: the one guard path touched, .claude/agents/analytics-engineer-reviewer.md, carries protected_override quoting the CPO-approved plan line and a real impact_map; the single hunk removes the word "(views)"; no hunt item, verdict rule or output format changed.
- New mechanism: none; an existing check extended, reusing its helpers and wired into the existing main().
- Model diffs match the declaration: 13 view and 52 table config removals, no added lines in the model hunks; dbt_project.yml changes comments only.
- Guard invariant: the change only adds rejections for three layers that had none; the fct_* incremental exemption is narrow.
- Test changes tighten, not weaken: POLICY_SITES follows the documents that quote the token; decision-history pins go down.
- Recurring cost declared down with measured numbers; run frequency unchanged; storage for 13 tables is cents a month.
- Behaviour change noted: three current_date() filters become build-time, consistent with their table siblings.
- No dependencies, credentials or workflow permission changes.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- No ingestion file, registry, registry seed or scheduler workflow in the diff; parser, merge and onboarding classes not triggered.
- docs/data_contract.md: two prose edits replace the staging-materialisation history with a pointer to layering.md §Materialisation; raw naming, partitioning, merge/append model and endpoints untouched; the pointer target exists.
- dbt_project.yml: comments only; the five +materialized: table lines and registry-derived vars unchanged.
- No ingestion cost knob, run cadence or history window moves; nothing writes to raw.

## escalations
(none)
