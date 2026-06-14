# Review — feat/skill-onboard-endpoint — 2026-06-14

> CPO-directed (escalations.log 2026-06-14, "go ahead"): a new guide/checklist skill
> `.claude/skills/onboard-endpoint/SKILL.md` codifying the routine for evaluating + ingesting
> a NEW API endpoint — check-if-ingested -> throwaway verification calls -> cost estimate ->
> CPO cost-approval gate -> CPO history-depth -> build (raw -> staging -> base -> loads). A
> single new markdown file; not a protected path. Frontmatter validated (parses).
>
> Review cycle: FIVE cold iterations (reviewers: scope-auditor [gate-required for .claude/skills]
> + cto-reviewer [run voluntarily for the tooling change]). Findings caught and fixed across
> iterations: (1) Step 3 now ASKS the CPO directly + forbids self-grant + cites the §2/§11
> escalations-recording practice (scope-auditor F1/F2); (2) `set +x` now the first line of the
> key-load block (cto); (3) Step 0 checks code AND a populated raw table + resolves the
> configurable raw dataset from settings (cto + scope-auditor); (4) RapidAPI base URL +
> `x-rapidapi-host` value named; "Path B" defined; (5) coverage wiring names the real
> `ENDPOINT_REQUIRES_NONEMPTY`/`SHELL_KEY_TO_ENDPOINT` structures (cto); (6) a factual error
> (claiming entity-keyed endpoints don't carry `league_code`) corrected — the data contract
> requires `league_code` on all raw tables (cto). Iteration 5: both PASS against the hash below;
> cto verified every named fact against settings.py / coverage.py / data_contract.md / squads.py.
> Rejected (with reason): adding `.claude/skills/**` routing to review_routing.json — a protected
> change, out of this task's scope (cto run voluntarily satisfies the contract). Residual
> non-blocking notes: the curl+python heredoc quoting footgun (mitigated by an in-skill note),
> and an explicit multi-day-quota-feasibility check (partially covered by "how the backfill
> spreads across days").

diff_sha256: 410ef5ef8783e65297e5341275b3a105990401cbf8f5521cc7f3804b48099756

## scope-auditor
VERDICT: PASS
risks_checked:
- §10 routing + auto-grant: Step 3/Step 4 route cost approval and history depth to the CPO and
  forbid self-granting ("never infer or self-grant it"); recording an already-given approval in
  escalations.log is the documented §2/§11 builder practice, not a new mechanism. No §10 decision
  is embedded or presented as auto-grantable.
- Scope + guards: the diff touches only the two scope_paths (the new SKILL.md + contract.md);
  no protected guard (.claude/hooks, .claude/agents, settings.json, review_routing.json,
  .github/workflows) is touched; the skill name follows the `onboard-*` convention (not a new
  product-naming decision); no Appendix A pattern (A1 invented metrics — it forbids API
  predictions/leaderboards; A3 new mechanism — a precedented single markdown guide; A5 — it
  builds in dbt/raw/loads, not the export). Residual (non-blocking): cost step could require an
  explicit one-day-fit / multi-day-spread feasibility statement before the CPO gate.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Named-fact accuracy (verified against source): apisports base URL + `x-apisports-key`, RapidAPI
  base URL + `x-rapidapi-key`/`x-rapidapi-host: api-football-v1.p.rapidapi.com` all match
  settings.py (33-34, 86-90); `ENDPOINT_REQUIRES_NONEMPTY` + `SHELL_KEY_TO_ENDPOINT` exist in
  coverage.py (56-72); the configurable raw dataset matches settings.py:31; the corrected
  `league_code` statement matches data_contract.md (required on every raw table) + loads/squads.py
  (24, 64 stamp it). No remaining factual error.
- Key safety + cost gate: `set +x` is the first line of the key-load block and the key is only
  ever a shell var passed as a header (no print); the cost/history decisions route to the CPO and
  cannot be self-granted; the skill is a guide (no code, no auto-ingest) — no new mechanism (A3),
  no guard touched. Residual (non-blocking): the curl+python heredoc quoting is a footgun,
  mitigated by the in-skill note to avoid f-strings with escaped quotes.

## escalations
(none — five cold iterations; the gate-required scope-auditor and the voluntary cto-reviewer
both PASS against the locked hash. No reviewer raised a §10 question on this diff. Adding
`.claude/skills/**` to review_routing.json was deliberately NOT done — it is a protected change
out of this task's scope; running cto-reviewer voluntarily satisfies the contract.)
