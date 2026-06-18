# Review — chore/dbt-mcp-server — 2026-06-18

> Classify MCP-server config as a PROTECTED command-class path (CPO ruling 2026-06-18) + wire a
> read-only dbt MCP server (.mcp.json: `uvx --python 3.12.13 dbt-mcp`, allowlist DBT_MCP_ENABLE_TOOLS
> = the 4 local-manifest tools). Guard-path diff → cto-reviewer on opus + scope-auditor. Iteration 1:
> cto-reviewer FAIL (done_when ↔ artifact mismatch on the safety flag + python pin + paths; a missed
> agent_guardrails.md line-54 enumeration). Fixed via a clean-tree contract amendment + the line-54
> edit; live-re-verified the 4-tool exposure. Iteration 2: both reviewers PASS.

diff_sha256: 97cccc4e9965e5fc67f57841f540b57c064f0732691a5b8922092fc480423462

## scope-auditor
VERDICT: PASS
risks_checked:
- Amendment legitimacy / scope-path authority: the iteration-2 amendment adds `docs/agent_guardrails.md`
  to scope_paths to legalise the line-54 fix. Verified it is a clean-tree amendment (code stashed), it
  changes no scope substance and makes no new §10 decision, and its authority chains to the recorded
  2026-06-18 CPO classification ruling (escalations.log) + the iteration-1 review finding — traceable.
- Live safety re-verification after the config amendment: `.mcp.json` was changed post-iteration-1
  (dropped DBT_MCP_ENABLE_DBT_CLI; pin 3.12→3.12.13). Verified done_when records the re-run live
  verification with the corrected config — exactly the 4 allowlisted tools, zero warehouse tools, and
  get_lineage_dev returning real lineage for dim_date — so the safety claim rests on observed evidence.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Iteration-1 finding 1 (safety flag) RESOLVED: `.mcp.json` sets `DBT_MCP_ENABLE_TOOLS` as the ONLY
  tool-governing var; `DBT_MCP_ENABLE_DBT_CLI` appears nowhere in the shipped config (only in contract
  prose explaining why it was dropped — the group-enable + allowlist combo exposed all 11 CLI tools incl.
  build/run/test/clone; the allowlist alone exposes exactly 4). Correct read-only posture; no
  warehouse-touching tool is reachable, so the absent `mcp__dbt__*` settings.json denylist is genuinely
  redundant. No run-frequency / API / BigQuery change (lineage reads the local manifest).
- Iteration-1 finding 3 (doc drift) RESOLVED, all FOUR enumerations checked to agree: agent_guardrails.md
  line 54 (gate-table) + line 79 (opus floor), working_agreement.md §2, and the live mechanisms
  task_contract_gate.py PROTECTED_FILES + review_routing.json paths all carry `.mcp.json` +
  `.cursor/mcp.json`. Prose, gate code, and routing are mutually consistent.
- Gate exact-match logic sound and not over-broad: `_is_protected` tests `rel in PROTECTED_FILES` on the
  repo-root-relative forward-slash path, so protection binds only repo-root `.mcp.json`/`.cursor/mcp.json`
  (the paths the tools auto-load) and would not fire on an unrelated `foo/.mcp.json`; routing keys are
  literal (no glob metachars); the allow path requires BOTH protected_override AND scope membership.
- Fail-open / opus-floor / scope all correct: the hook still fails OPEN (data-only tuple+comment change,
  no new exception surface); this is the opus-spawned guard-path review the override mandates; the diff is
  fully contained in scope_paths with protected_override naming the 2026-06-18 ruling; no
  secret/credential/permission-widening (the absolute paths are directory paths, not tokens).

## escalations
(none)
