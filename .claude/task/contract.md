# Task contract — make the guardrails cover the surfaces that actually failed

> Written on a CLEAN tree (branch `chore/guardrails-cover-design-surface` off main @ 0cc2637).
> Part 1 of 2. Part 2 is the agent set (a `ui-expert` doer, a `ui-expert-reviewer`, two
> consultants, a fan probe) and it DEPENDS on this one: a doer that publishes mocks needs the
> artifact gate to exist first. See [[feedback-agent-guardrails]] [[feedback-design-off-the-cuff]].

protected_override: >
  `.claude/hooks/**` and `.claude/settings.json` are PROTECTED paths. The CPO approved this
  specific change via ExitPlanMode on 2026-07-22, against a plan naming every edit below. The
  retrospective that produced it was CPO-directed: *"what can I do better to move forward faster
  and how can we provide you with the prerequisites to work accurately and with high quality and
  as autonomously as possible."* Routes to cto-reviewer; the opus-on-guards rule applies.

objective: >
  Four verified holes in the guardrails, all of which let the 2026-07-21 failures happen.

  (1) PROTECTED PATHS DEMAND LESS EVIDENCE THAN A LEAF MART. `_is_structural` covers
      `ingestion/`, `dbt_project/models/`, `site*/` and `scripts/export_*.py`; the protected
      paths are a DISJOINT set. And the control flow is worse than the predicate: the protected
      branch RETURNS EARLY once `protected_override` is present, so the `impact_map` check below
      it is unreachable for those paths. Fix BOTH: add protected to `_is_structural`, and check
      `impact_map_present` INSIDE the protected branch before allowing the edit.

  (2) NO HOOK FIRES ON THE ARTIFACT TOOL. `PreToolUse` is wired to `Bash` and
      `Edit|Write|MultiEdit|NotebookEdit` only. The three rejected player-page mocks were
      artifacts, so no contract, no routing, no reviewer and no commit gate ever touched them.
      The one surface with no machinery is the one that failed three times in a day. Gate it:
      deny an `Artifact` call when no contract exists. Mocks are written to the scratchpad,
      OUTSIDE the repo, and `_gate_file_edit` returns early for anything outside the repo — so
      this needs its own branch, not a reuse of the path logic.

  (3) PLAIN LANGUAGE IS ENFORCED BY NOTHING. It failed inside the retrospective itself: file
      paths, section numbers and invented vocabulary throughout, while explaining why written
      rules do not change behaviour. New Stop hook, separate file, reads the turn's own final
      message and blocks on em dashes, section symbols, repo paths in prose, and length.

  (4) THE HANDOVER IS NOT DELIVERED. No `SessionStart` hook exists anywhere. The script exists
      and nothing runs it, while the handover file claimed it did. Wire it.

  Plus one prose correction: working agreement §11 bans a recommendation in escalations; the CPO
  wants one and practice is split (9 entries withhold, 8 give). Correct the rule.

refs: >
  Verified this session at source, not recalled:
  - `.claude/hooks/task_contract_gate.py`: `_STRUCTURAL_PREFIXES` (line ~87) vs
    `PROTECTED_PREFIXES` (line 66) are disjoint; `_gate_file_edit` returns at line 272 inside the
    protected branch, before the `_is_structural` check at line 281; line 248 returns for any
    path outside the repo.
  - `.claude/settings.json`: `PreToolUse` matchers are `Bash` and
    `Edit|Write|MultiEdit|NotebookEdit`. No `SessionStart` key. `.claude/settings.local.json` has
    a `permissions` key only. The user-level `~/.claude/settings.json` has NO `hooks` key at all.
  - `Artifact` is a valid `PreToolUse` matcher and such a hook can return a deny decision
    (Claude Code hooks documentation, confirmed via claude-code-guide).
  - The Stop payload carries `session_id`; the transcript is
    `~/.claude/projects/<slug>/<session_id>.jsonl` with assistant text in `message.content[]`
    blocks of `type: "text"`. CONFIRMED by reading this session's own transcript: 35 text blocks,
    the last matching the last message sent. Whether `transcript_path` is also in the payload is
    UNDOCUMENTED, so the hook uses it when offered and otherwise globs
    `~/.claude/projects/*/<session_id>.jsonl`. There is deliberately NO newest-by-mtime fallback:
    on a miss it would read a DIFFERENT session's transcript and block this turn over a message
    the CPO never saw. On a miss the gate fails open.
  - The `Artifact` tool name is CONFIRMED FROM REAL EVENTS, not from documentation: 71 `tool_use`
    records named exactly `Artifact` across this project's transcripts, each carrying `file_path`
    in its input. The cto-reviewer was right to refuse a third-party guide as evidence for a
    guard's trigger.
  - The 2,500-character cap is MEASURED, not guessed: across those 35 messages the median is 166,
    the top 30% run 1,682 to 3,343, and 4 exceed 3,000. Those 4 are the walls the CPO objected to.
  - `escalations.log`: 9 entries withhold a recommendation per §11, 8 give one.

impact_map: >
  writers: not a data change. Nothing writes a table. The artifacts changed are the hook scripts
    themselves and the settings that wire them.
  downstream: EVERY tool call in EVERY future session in this repo, for every agent (Claude Code
    and Cursor both read `.claude/`). `task_contract_gate.py` is wired to `PreToolUse` on Bash and
    the edit tools and to `PostToolUse` on Bash; `stop_gate.py` is wired to `Stop` and imports
    `_dirty_outside_task_dir`, `_is_protected`, `_matches_scope`, `_read_contract`, `_repo_root`
    from `task_contract_gate.py` — so a change to any of those five names breaks the stop gate
    too. Checked: this task changes `_is_structural` and `_gate_file_edit`, neither of which
    `stop_gate.py` imports, so the import surface is untouched.
  layer_rules: none apply. No dbt model, no seed, no CI workflow, no SQL. `check_layer_contract.py`
    is unaffected and still runs.
  deploy_order: none. No warehouse object, no shared dataset, nothing sequenced around the 04:00
    nightly. The change takes effect in the next session that loads `.claude/settings.json`.
  blast_radius: HIGH but bounded, and larger than most dbt models — which is precisely the
    argument for hole (1). A bug in a PreToolUse hook can deny every edit; a bug in a Stop hook can
    wedge the end of every turn. Mitigations, both required in `done_when`: every hook FAILS OPEN
    on any unexpected error (the existing house rule, stated in `_command_utils.py`), and each new
    or changed path is tested in BOTH directions plus with malformed input. Zero user-visible
    numbers change; no mart, no export, no page.
    RUNNING COST, which is not zero and was missing here until the round-2 cto review: the
    SessionStart injection adds roughly 13 KB of context to EVERY session start, including every
    resume and every compact, not just the first. And every plain-language block costs one extra
    assistant turn, on top of the message the CPO has already read — the gate cannot pre-empt a
    message, only follow it. Both are CPO-approved and provisional with a stated removal
    criterion (if the gate is still firing regularly after a handful of turns it is not working
    and comes out), but they belong in the blast radius rather than in a footnote.
    Also per turn: the plain-language gate reads up to 512 KB from the tail of the transcript and
    JSON-parses it, on top of the existing stop gate's `git status`. Bounded by construction (the
    tail is capped, so it does not grow with session length) but not free.
    AND THE COUPLING THAT MATTERS, missed in the first version of this map, which analysed only
    `stop_gate.py`'s IMPORT surface: the two Stop hooks share ONE `stop_hook_active` flag, because
    it is a property of the continuation, not of a hook. So a plain-language block stands the
    CONTRACT-VS-TREE check down for the remainder of that turn. Handled by forbidding file edits
    in the rewrite (the block message says so) and by stating it in `docs/agent_guardrails.md`, so
    it is a known limit rather than a discovered one.

scope_paths:
  - .claude/hooks/task_contract_gate.py
  - .claude/hooks/plain_language_gate.py
  - .claude/hooks/handover_in.py
  - .claude/settings.json
  - docs/working_agreement.md
  - docs/agent_guardrails.md
  - tests/test_governance_hooks.py
  - CLAUDE.md
  - .claude/task/TEMPLATE.md

decisions_taken: >
  (1) The artifact gate BLOCKS rather than warns. CPO 2026-07-22, when told it costs design speed
      in a two-week sprint: "I prioritize quality over speed. If me make it in 3 weeks it's ok as
      well. But 2 weeks remains our goal."
  (2) THE FOUR MECHANISMS THEMSELVES. `NEW mechanisms of any kind` is a §10 class, so the bare
      claim "approved via ExitPlanMode" that stood here was not good enough — the round-5
      scope-auditor applied this task's own §11 argument back to it, correctly. The authority is
      NOT plan-mode approval on its own; it is the CPO directing this work in conversation across
      the whole session and answering the specific questions each mechanism raised. Recorded
      VERBATIM in `.claude/task/escalations.log` (entry 2026-07-22, "the four guardrail
      mechanisms"), which is the durable record this rests on. NOT re-escalated, deliberately:
      re-asking a CPO who has already directed, chosen and ruled on this work would be the exact
      "bad question" failure the same session identified [[feedback-decide-dont-escalate]].
  (3) The 2,500-character cap is an engineering default derived from measurement, stated in the
      approved plan, and changeable by one constant. Not a §10 decision.

decisions_reserved:
  - Whether the 2,500 cap is the right number in practice. It is a measured default, not a ruling;
    if it blocks useful answers, the CPO decides the new number.
  - Whether main-session hooks fire for tool calls made INSIDE a subagent. UNDOCUMENTED and
    unresolved. It matters for PART 2, not for this task: if they do not fire, the `ui-expert`
    doer needs its own PreToolUse hook declared in its agent frontmatter (a documented mechanism).
    Do NOT guess in part 2 — test it.

done_when:
  - Protected hole tested BOTH ways: with `protected_override` and no `impact_map`, an edit to
    `.claude/hooks/` is DENIED; with the map present, ALLOWED. A one-sided test would pass while
    broken (the lesson from the lower_is_better guard).
  - Artifact gate tested BOTH ways: denied with no contract, allowed with one.
  - Plain-language gate tested non-vacuously: an em dash, a section symbol, a bare repo path and a
    3,000-character message each BLOCK; a clean short message PASSES.
  - Every touched hook fed malformed input and confirmed to exit 0 without blocking (fails open).
  - `handover_in.py` run against a stub event emits the handover text.
  - `python scripts/check_layer_contract.py` passes.
  - ONE commit, pushed with an explicit refspec, PR opened. The CPO merges.

amendments:
  # ORIGINAL scope, written on a clean tree BEFORE any implementation, four paths:
  #   .claude/hooks/task_contract_gate.py · .claude/hooks/plain_language_gate.py
  #   .claude/settings.json · docs/working_agreement.md
  # Stated explicitly because `contract.md` on main belongs to the PREVIOUS task, so the whole
  # file reads as new in the diff and a reviewer cannot otherwise tell original scope from
  # amended scope. A round-2 scope-auditor FAIL rested on exactly that ambiguity (it read
  # plain_language_gate.py as an undeclared extension; it was original). The arithmetic:
  # 4 original + 5 amended (3 below, then CLAUDE.md, then TEMPLATE.md) = the 9 in scope_paths.
  # This line said "4 + 3 = 7" for two rounds after the last two amendments were added beneath it,
  # miscounting by two in the one artifact that authorises scope, inside the task whose subject is
  # statements that stop being true (cto-reviewer, 2026-07-22). Update it with every amendment.
  - 2026-07-22: + `.claude/hooks/handover_in.py`, + `docs/agent_guardrails.md`,
    + `tests/test_governance_hooks.py`.
    AUTHORITY: the cto-reviewer FAIL at opus (round 1), plus the CPO's "yes" to keeping all four
    plain-language checks provisionally. Amendments are scope extensions forced by review
    findings, not new work chosen by the builder.
    CONTENT, and WHY each path is now needed:
    (1) `.claude/hooks/handover_in.py` — THE SERIOUS ONE. The first attempt wired `SessionStart`
        to `docs/portable_guardrails/hooks/handover_in.py`, which is NOT a PROTECTED prefix and
        has NO entry in `review_routing.json`. That would have made a script that auto-executes
        at every session start editable inside any ordinary task with no `protected_override`, no
        cto review and no opus floor — the exact class the CPO ruled on twice (`.claude/commands/`
        2026-06-14, `.mcp.json` 2026-06-18: "auto-launches a command every session ... an agent
        can never self-grant"). A guard-hardening change must not open a guard hole.
        `docs/agent_guardrails.md` already states the rule: project hooks live in
        `.claude/hooks/` and `docs/portable_guardrails/hooks/` is the copy-out ARCHIVE. The live
        copy moves to the protected directory and the setting points there.
    (2) `docs/agent_guardrails.md` — CLAUDE.md names it authoritative for "what fires, why". It
        does not describe the artifact gate, the plain-language gate or the SessionStart wiring.
        Shipping three new hook behaviours while the doc of record says otherwise is the
        stale-document failure this whole task exists to stop.
    (3) `tests/test_governance_hooks.py` — the reviewer found the trap this contract's own
        `done_when` names and then walked into: the committed suite covers only the ALLOW
        direction of the protected-path change, because its fixture already carries an impact
        block. Scratchpad verification proves it works today and stops nothing regressing
        tomorrow. That is precisely the lesson from the metric guards, which is the reason this
        session exists.
    NOT amended in: `docs/portable_guardrails/**` stays untouched — the archive is left as-is,
    and `docs/agent_guardrails.md` now says plainly that the archived copy is the PRE-fix one.
  - 2026-07-22 (round 3): + `CLAUDE.md`.
    AUTHORITY: the cto-reviewer FAIL at opus (round 3).
    CONTENT: `CLAUDE.md` line 19 summarises §11 as "premise check, two conflicting paths, no
    recommendation". This task reverses the no-recommendation half, so shipping without touching
    `CLAUDE.md` would leave the FIRST file read every session contradicting the rule it points at.
    That is the stale-document failure this task exists to stop, one file further upstream.
    ON THE AUTHORITY FOR THE §11 CHANGE ITSELF: **ESCALATED AND ANSWERED.** Both reviewers
    independently ruled that a rule extension is §10 and that "approved via ExitPlanMode" plus a
    memory file plus one in-session example is too thin for it, and they were right on process
    even though the answer was predictable. The question was put to the CPO in plain language with
    two paths (answer it now and record it, or cut the rule change out of this PR entirely) and a
    recommendation. **CPO ANSWER 2026-07-22: "go ahead as recommended"** — the escalation rule now
    requires a recommendation with its reasoning. Recorded verbatim in
    `.claude/task/escalations.log`, which is the durable authority this amendment rests on; the
    9-to-8 split in that log is evidence the WRITTEN rule was stale, never the reason to change it.
  - 2026-07-22 (round 4): + `.claude/task/TEMPLATE.md`.
    AUTHORITY: the cto-reviewer FAIL at opus (round 4).
    CONTENT: the template still tells authors the `impact_map` is required only on the raw /
    model / consumption surface and to "omit this key entirely when no structural path is in
    scope", and its `protected_override` comment says nothing about a map. This task makes a map
    mandatory on every protected path, and `_deny_no_contract` points authors at that file BY
    NAME. PART 2 (the `ui-expert` agent set) edits `.claude/agents/**`, so it would copy the
    template, follow it, omit the map and be denied by the gate this task just shipped. The file
    sits under `.claude/task/`, which the gate exempts unconditionally and which the routing
    lists as artifact-only, so there was no gate friction to notice it — which is precisely why
    it is declared here rather than edited quietly.
