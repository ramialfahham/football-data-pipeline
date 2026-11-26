# Task contract — an automatic context guard for Claude Code sessions

objective: >
  Issue 313. A new Stop hook, context_guard.py, reads the session transcript and, once per session,
  blocks the turn end when the context passes a named threshold, telling the session to hand off
  to a fresh one. No other behaviour changes.

refs: >
  Issue 313 (cap session context); the hook is approved in chat, 2026-11-23.

scope_paths:
  - .claude/hooks/context_guard.py
  - .claude/settings.json
  - tests/test_context_guard.py
  - docs/agent_guardrails.md
  - .claude/task/313-context-guard/contract.md
  - .claude/task/313-context-guard/review.md
  - .claude/task/313-context-guard/review_input.patch

protected_override: >
  .claude/hooks/context_guard.py and .claude/settings.json edits approved in chat, 2026-11-23, as
  issue 313; the MR head declares the locked files.

impact_map: >
  events: the hook is registered on the Stop event only, in .claude/settings.json beside
  stop_gate.py. Claude Code runs both on every turn end. Either can block. After any Stop block the
  next Stop event in that session carries stop_hook_active, and both hooks return at once on that
  flag (stop_gate.py lines 155 to 157, before its stash, contract and offline-gate checks). So once
  per session, past the threshold, the hand-off turn end is not checked by stop_gate.py. The block
  text therefore tells the session to edit nothing in the tree except the state file, and a test
  pins that text. A stop_gate.py block makes context_guard.py skip that continuation too; it
  checks again at the next turn end. The commit gate and CI check the tree as before. No other
  event, no matcher and no tool call is touched.
  fires: on every Stop event with a session_id and a transcript_path, once the event does not carry
  stop_hook_active. It reads only the tail of the transcript, takes the last assistant message
  that carries a usage block (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)
  and compares the sum with CONTEXT_TOKEN_THRESHOLD. Over it, it creates one marker file per
  session id under the system temp folder, atomically, and only then prints the block decision in
  the protocol stop_gate.py uses. Under it, nothing is written.
  readers: nothing imports context_guard.py, so no other hook, script or test depends on it. It
  imports read_event from .claude/hooks/_command_utils.py, as ten other hooks do
  (`grep -rln "from _command_utils import" .claude/hooks`), and relies on read_event returning {}
  on any error; a future change to read_event must list this hook. `grep -rn "stop_gate" tests scripts .gitlab-ci.yml` finds the
  readers of the neighbouring hook only: tests/test_governance_hooks.py and
  tests/test_hooks_resolve_worktree.py. docs/agent_guardrails.md gains one row.
  not_enforced_if_wrong: if the threshold is too high the session compacts at about 370,000 as it
  does today; if the hook never fires, nothing else loses a check, because it enforces no rule
  and guards no data. If it fires too early a session hands off sooner than needed, once.
  failure: a missing, empty or unreadable transcript, no assistant entry with usage, a malformed
  line, a usage value that is not a number, a missing session_id, a marker that cannot be created,
  or any exception, returns 0 and prints nothing: the turn ends. The hook fails open. The marker
  is created before the block is printed, so a failure to write it also ends in no block, and the
  session is never blocked twice.
  blast_radius: every session in this repo, once per session at most, with a block message and no
  change to files, the tree, git or the contract.

approved_design:
  - none: no page output changes

depends_on:
  - none: the change reads no open MR's code; settings.json and agent_guardrails.md are taken from gitlab/main

shared_files:
  - none: no design baseline, component registry, font coverage or chart screenshot changes

decisions_taken: >
  Issue 313's guard, approved in chat, 2026-11-23: a Stop hook that blocks once per session past
  300,000 tokens and tells the session to write a state file, message the coordinator and stop.
  Engineering calls: the marker is a file per session id in the system temp folder, created with
  exclusive create so two hooks running at once cannot both block; entries marked as sidechain or
  with the synthetic model, and entries whose usage sums to zero, are skipped so the last real
  assistant message counts; the transcript is read from its tail, in growing blocks, so a large
  file is not read whole; the state-file location named in the block reason is the shared notes
  folder the session was given, else its task folder, because no hook in the repo names a notes
  folder.
  The guard's block makes the following Stop event skip stop_gate.py once per session, because
  stop_gate.py ends at once on stop_hook_active. The issue's one-block design carries that, and the
  hand-off turn is told to write only the state file.
  Threshold declarations: no new dependency, no recurring cost; a new mechanism of the same class
  as stop_gate.py, named by the issue.

decisions_reserved:
  - none: the threshold, the block text and the location of the state file are as the issue states them

done_when:
  - tests/test_context_guard.py passes
  - the Stop block in .claude/settings.json lists context_guard.py beside stop_gate.py and the file parses as JSON
  - docs/agent_guardrails.md has one row for context_guard.py
  - tests/test_governance_doc_parity.py and tests/test_hooks_resolve_worktree.py still pass

amendments: (none)
