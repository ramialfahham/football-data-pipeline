# Review — governance/impact-map-518 — 2026-06-22

> Four-step review cycle (G3). Reviewers spawned cold on the cumulative branch
> diff (`review_input.patch`) + the contract. Required set for this diff
> (`.claude/hooks/**`, `.claude/agents/**`, `tests/**`, `docs/**`, `.claude/task/**`):
> scope-auditor (always) + cto-reviewer (guard paths, opus floor). analytics-engineer
> is NOT required — the bundled `dbt_project/docs/layering.md` codification was
> de-scoped to #539 mid-review, so no `dbt_project/**` path is in the diff.

diff_sha256: 1a022baba273f36ed64540980b4f57a44d6489acef750143ef4df4ce4851ce0b

## scope-auditor
VERDICT: PASS
risks_checked:
- Impact-map honesty / placeholder detection: `_impact_content()` rejects template
  placeholders (`<fill me in>`), comments, empty, and bare YAML block indicators on
  both the inline and indented-block paths; an embedded `writers: <…>` line is caught
  per-line. Verified by `test_placeholder_impact_map_does_not_satisfy`.
- Scope-check ordering: an out-of-scope structural path returns the OUTSIDE deny
  before the missing-map deny (scope is a precondition for the map requirement to be
  meaningful), verified by `test_out_of_scope_structural_edit_denied_for_scope_first`.
  Also confirmed: all scope_paths in the diff are in-scope; the contract's
  `impact_map: Not applicable` claim is honest (no scope path is structural); the
  `amendments:` block honestly records the layering.md de-scope to #539 with CPO
  authority; the NEW mechanism is CPO-approved via `protected_override`; the three
  reviewer specs, Appendix A6, §2, and agent_guardrails.md are all in doc-sync.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Hook parse correctness (`_read_contract` + `_impact_content`): all branches traced —
  inline real content accepted; block-scalar `>`/`|` rejected then indented content
  accepted; `<placeholder>` rejected by `^<.*>$`; `#` comments and `(none)`/empty
  rejected; a non-indented next top-level key terminates the block. The `# Known v1
  limits` comment block above `impact_map:` does not falsely trip presence.
- `_is_structural` boundary precision: `dbt_project/docs/` does NOT trip (prefix is
  `dbt_project/models/`) — load-bearing given the de-scope; `scripts/export_x.py`
  matches the anchored regex while `scripts/sync_dbt_vars.py` does not; `site/` +
  `site_v2/` covered. Surface matches the contract/working-agreement/guardrails wording.
- Deny placement order (protected → no-contract → out-of-scope → missing-map) and
  fail-open preserved (`main()` keeps the `try/except → return 0` envelope; new helpers
  add no I/O outside it).
- Test regression-safety: the `CONTRACT_NO_IMPACT` + injected `_IMPACT_BLOCK` rename
  keeps the pre-existing structural-path tests green; new cases cover
  present/absent/placeholder/non-structural/ingestion/out-of-scope-first.
- Guard integrity: `protected_override` quotes the CPO §10 sign-off for the PROTECTED
  `.claude/hooks/` + `.claude/agents/` edits; routing → cto at the opus floor; no
  dependency/secret/workflow-permission/cost change; the de-scope is recorded with #539.
- Reviewer-spec + doc coherence: the three sharpened specs are layer-coherent;
  agent_guardrails.md and §2/A6 are in sync with the hook's actual deny behavior.

Non-blocking observations (recorded, not findings): (1) documented v1 limit — the
shell-write path is not impact-gated (Edit/Write is the governed authoring path; shell
writes are best-effort and already heredoc/scope-gated; reviewers backstop at review).
If #518's pattern recurs via shell, the cheap follow-up is to call `_is_structural`
inside `_gate_bash_pre`. (2) A `impact_map: >` block-indicator with no following content
is handled correctly but not directly unit-tested — worth a one-line test in a future touch.

## escalations
(none)
