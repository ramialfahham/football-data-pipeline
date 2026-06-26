# Task contract — name the five-step protocol + adopt plan mode as the Confirm gate

> Governance/docs task. Written on a clean tree BEFORE any edit. Non-structural
> (docs only) — no impact_map required. See docs/working_agreement.md §1, §2, §10.

objective: >
  Close the "Confirm" gap: of the five-step ladder Explore -> Plan -> Confirm ->
  Implement -> Verify, four steps are machine-gated and only "Confirm" (wait for the
  user's explicit go before implementing) is an unenforced behavioural rule. Per CPO
  decision 2026-06-26 ("Execute as recommended" -> option b + c1): (b) name the
  five-step protocol in the guard docs and designate working_agreement.md §1 as the
  Confirm step; (c1) adopt the harness's native plan mode (EnterPlanMode/ExitPlanMode)
  as the Confirm gate for any file-touching task. Hold option c2 (a self-attested
  `cpo_go` contract token + impact-map-gate extension) in RESERVE — do not build it.
refs: working_agreement.md §1; active_work.md "§1 lesson" 2026-06-25; CPO ruling 2026-06-26.

scope_paths:
  - docs/working_agreement.md
  - CLAUDE.md

decisions_taken: >
  CPO ruling 2026-06-26: "Execute as recommended" = options (b) + (c1) as presented this
  session. (b) = name "Explore -> Plan -> Confirm -> Implement -> Verify" in the guard docs,
  relabel working_agreement.md §1 as the Confirm gate, keep its three existing behavioural
  bullets. (c1) = adopt native plan mode as the Confirm mechanism for file-touching tasks;
  an already-given explicit go for a specific change IS the Confirm (plan mode then optional).
  (c2) self-attested `cpo_go` token = RESERVED, not built (a new gate must earn its place;
  no-over-engineering). Documentation only — NO hook/settings/workflow edit (plan mode is
  native), NO product/metric/§10 decision introduced.

decisions_reserved:
  - None new. This records a CPO decision already made; it does not introduce a product,
    metric, naming, or cost question. If wording drifts toward a NEW mechanism (e.g. actually
    wiring c2), stop and escalate — out of scope.

done_when:
  - docs/working_agreement.md §1 names the five-step protocol, marks Confirm as the human
    checkpoint, keeps the three existing bullets, and documents plan mode as the Confirm gate
    with c2 noted as reserved.
  - CLAUDE.md carries a concise named-protocol pointer (the five steps + Confirm = wait for
    explicit go + use plan mode for file-touching tasks).
  - No structural/code path touched; scope_paths limited to the two docs.
  - Routes to scope-auditor only (neither path is in review_routing paths); review cycle PASS;
    commit substantive (non-artifact) so scope-auditor must run; CPO merges.

amendments: (none)
