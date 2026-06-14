# Task contract — fix: transfers ingest fetched empty (paginate=False)

> Follow-up bugfix to PR-i (#467, merged). The dispatched pipeline run revealed that the
> transfers chain produced 0 rows: every team's `transfers_payload` came back empty. Cause:
> `transfers_response_for_team` uses `fetch_merged_paged` with default pagination, which sends
> `page=1` — and `/transfers` rejects the `page` param (like `/teams` and `/standings`,
> "The Page field do not exist.") and returns empty. The chain built GREEN on empty data,
> masking it. Verified fix: a single `team=` call (no `page`) returns the team's full move list
> (live curl `?team=157` → 289 results, paging total=1). See docs/data_contract.md §Pagination,
> docs/working_agreement.md §2/§7.

objective: >
  Switch `transfers_response_for_team` (ingestion/api_football/fixture_scheduling.py) from the
  default paginated fetch to `paginate=False` (single `{"team": team_id}` call, no `page` param),
  so /transfers returns real data instead of empty. Drop the now-unused
  `API_FOOTBALL_TRANSFERS_MAX_PAGE` lookup. Ingestion-only; no dbt/model change (the chain on
  main is correct — it was just fed empty raw data).

refs: #467 (merged PR-i); the empty-data finding (dispatched run 27506078487 → RAW_APIF_TRANSFERS
  team blocks all `transfers_payload: []`); verification curl `?team=157` → 289 (no page);
  docs/data_contract.md §Pagination ("/teams, /standings reject page").

scope_paths:
  - ingestion/api_football/fixture_scheduling.py
  - docs/data_contract.md
  - .claude/task/contract.md

decisions_taken: >
  paginate=False for /transfers is a fetch-correctness fix, not a §10 decision. PROOF is empirical
  (not an analogy): the live verification showed the paged call returns EMPTY while a single
  un-paged `team=` call returns the team's full move list (Bayern team=157 → 289 moves, paging
  total=1). Truncation risk is self-limiting — /transfers rejects the `page` param, so even if
  paging.total were >1 there is no retrievable page 2; a single call is the only correct fetch
  (see http_client.py paginate=False). This PR also DOCUMENTS /transfers in data_contract.md
  §Pagination (it previously listed only /fixtures, /teams, /standings). The by-team axis, cost,
  and dedup are unchanged (all CPO-approved in #467). The unused API_FOOTBALL_TRANSFERS_MAX_PAGE
  env is removed.

decisions_reserved:
  - If a reviewer finds evidence that /transfers DOES paginate for very large teams (so a single
    un-paged call would truncate), STOP and surface it — the verification (one page = 289, total=1)
    indicates a single call suffices, but flag any contrary signal.
  - Real-data validation (RAW_APIF_TRANSFERS populated + fct_transfer non-empty + DQ tests on real
    moves) happens on the next full pipeline run after this merges (scheduled 04:00 or a dispatch),
    NOT in this PR's CI — this PR's data-build builds the unchanged models against the (still
    empty) table and passes as before.

done_when:
  - `transfers_response_for_team` calls `fetch_merged_paged(..., paginate=False)` with no `page`
    param; `API_FOOTBALL_TRANSFERS_MAX_PAGE` removed; `python -m py_compile` clean.
  - docs/data_contract.md §Pagination lists /transfers among the page-rejecting endpoints.
  - reviewers: scope-auditor (always) + data-engineer-reviewer (ingestion/**) — PASS.

amendments:
  - 2026-06-14: + docs/data_contract.md to scope_paths. Authority: required doc-sync (iteration-1
    scope-auditor FAIL) — §Pagination listed only /fixtures/teams/standings as page-rejecting, not
    /transfers; the fix rests on the empirical verification, and this PR documents /transfers there
    rather than analogizing from a doc that omits it. Clean-tree amendment (code stashed). content:
    add /transfers to data_contract.md §Pagination; reframe decisions_taken to lead with the
    empirical proof + the self-limiting-truncation reasoning.
