# Task contract — chore: classify MCP config as PROTECTED + wire read-only dbt MCP server

> Governance + tooling. The CPO ruled this conversation (2026-06-18) that `.mcp.json` is a
> PROTECTED command-class file (it auto-launches `uvx dbt-mcp` every session — same class as
> `.claude/commands/`, ruled 2026-06-14) and chose Option 2: extend the guard list to cover MCP
> config AND wire the server. This is a PROTECTED governance task — it edits the gate + routing
> themselves, so the contract carries `protected_override`. Reviewers: cto-reviewer (guard +
> tooling, opus floor) + scope-auditor (always).

objective: >
  (1) Classify MCP-server config as PROTECTED command-class: add `.mcp.json` and `.cursor/mcp.json`
  to the task-contract gate's PROTECTED_FILES and route them to cto-reviewer, and document the rule
  in the authoritative guardrail docs — so no agent can self-grant an MCP server in an ordinary task.
  (2) Wire the read-only dbt MCP server via a committed `.mcp.json` (local-manifest lineage only:
  get_lineage_dev / get_node_details_dev / list / parse — no warehouse-touching tools, no dbt Cloud).

refs: >
  This conversation 2026-06-18. CPO ruling: Option 2 (PROTECTED). Probe facts: dbt-mcp shells out to
  our dbt 1.7.19 (no dbt-core dep, no forced upgrade); dbt-artifacts-parser 0.13.2 parses our v11
  manifest cleanly; dbt-mcp 1.20.4 needs Python >=3.12 (run via uv-managed interpreter; our venv stays
  3.11.9). Precedent: `.claude/commands/**` protected (CPO ruling 2026-06-14).

scope_paths:
  - .mcp.json
  - .claude/hooks/task_contract_gate.py
  - .claude/review_routing.json
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - .claude/task/contract.md
  - .claude/task/review.md

protected_override: >
  CPO ruling this conversation (2026-06-18): `.mcp.json` classified PROTECTED (command-class),
  Option 2 chosen. This authorizes the in-scope edits to .claude/hooks/task_contract_gate.py and
  .claude/review_routing.json (extending the guard list to cover MCP config). No other protected
  path is touched — `.claude/settings.json` is deliberately NOT edited (see decisions_taken).

decisions_taken: >
  - CPO chose Option 2 (2026-06-18): MCP config is PROTECTED; extend guards + wire the read-only
    server. The read-only env allowlist (DBT_MCP_ENABLE_TOOLS) is the safety mechanism — the server
    never exposes build/run/test/show/clone, so the redundant `mcp__dbt__*` denylist in the PROTECTED
    `.claude/settings.json` is NOT added (avoids a second, unnecessary protected edit; CPO concurred).
  - Protect BOTH `.mcp.json` (Claude Code) and `.cursor/mcp.json` (Cursor) on the same command-class
    rationale — protecting only the literal file would leave the Cursor entry point open and defeat
    the ruling's stated goal ("no agent self-grants an MCP server unreviewed"). This implements the
    objective fully, not by analogy. Narrow to only `.mcp.json` if the CPO intended the literal file.

decisions_reserved:
  - Warehouse-touching dbt tools (build/run/test/show/clone) and the dbt-Cloud Discovery / Semantic
    Layer / SQL tool groups are OUT. Enabling any is a separate, cost-gated CPO decision.
  - Column-level lineage (the Fusion/dbt-LSP server) is OUT — not wired here.
  - Whether to also CREATE `.cursor/mcp.json` (give Cursor the server too) is deferred: this PR
    PROTECTS that path but only creates the Claude Code `.mcp.json`. A Cursor config is a follow-up.
  - dbt stays 1.7.19. If a future dbt-mcp drops manifest-v11 support, revisit then — not now.
  - If wiring needs any file beyond scope_paths, STOP and escalate — do not widen scope silently.

done_when:
  - `.mcp.json` is valid JSON: launches `uvx --python 3.12.13 dbt-mcp` (EXACT patch pin — uv's
    minor-version link needs Windows admin/developer-mode, unavailable here, so a bare `3.12` fails to
    resolve while `3.12.13` resolves directly); env sets DBT_PROJECT_DIR, DBT_PATH (venv dbt.exe),
    DBT_PROFILES_DIR as ABSOLUTE paths, intentionally machine-local (single-operator repo; parametrizing
    is a deferred option); read-only allowlist is
    `DBT_MCP_ENABLE_TOOLS="get_lineage_dev,get_node_details_dev,list,parse"` ONLY — NO
    `DBT_MCP_ENABLE_DBT_CLI` (verification showed the group-enable + tool-allowlist combo exposes all 11
    CLI tools incl. build/run/test/clone; the tool-allowlist ALONE exposes exactly the 4).
  - task_contract_gate.py PROTECTED_FILES includes ".mcp.json" and ".cursor/mcp.json"; a gate self-test
    confirms a write to `.mcp.json` is denied without protected_override and allowed with it.
  - review_routing.json routes ".mcp.json" + ".cursor/mcp.json" -> cto-reviewer; _doc records the ruling.
  - working_agreement.md §2 + BOTH agent_guardrails.md enumerations (the gate-table row at line 54 + the
    opus-floor list at line 79) list MCP config among the protected paths.
  - uv installed locally; `uvx --python 3.12.13 dbt-mcp` launches and exposes ONLY the 4 allowlisted
    tools (live-verified: get_lineage_dev, get_node_details_dev, list, parse; zero warehouse tools;
    get_lineage_dev returns real lineage for dim_date).
  - review.md: cto-reviewer + scope-auditor VERDICT PASS (>=2 named risks each); no FAIL; any ESCALATE
    has a CPO ANSWER. diff_sha256 matches the staged hash.
  - Committed on chore/dbt-mcp-server; pushed with explicit refspec; PR opened. CPO merges.
  - Post-merge (Rami, manual): restart Claude Code/Cursor to load the server; confirm get_lineage_dev
    returns lineage against our manifest.

amendments:
  - 2026-06-18 (clean-tree, code stashed): done_when reconciled with the VERIFIED artifact after the
    iteration-1 cto-reviewer FAIL. Authority: review-cycle finding (no scope change, no new §10 — the
    build's live verification superseded the contract's planning-time config). Corrections: (1) env
    allowlist = `DBT_MCP_ENABLE_TOOLS` ONLY (dropped `DBT_MCP_ENABLE_DBT_CLI=true`, which leaked all 11
    CLI tools); (2) python pin 3.12 -> 3.12.13; (3) recorded the absolute DBT_* paths as intentionally
    machine-local. Also fixed the missed edit the reviewer caught: docs/agent_guardrails.md line 54
    (gate-table protected list) now includes the MCP paths, matching line 79 (opus floor).
