# Task contract — the merge hook has an explicit timeout, and a stale reviewer sentence goes

objective: >
  Issue #262, follow-up to the agent-merge MR: `.claude/settings.json` sets `"timeout": 600` on the
  `git_discipline.py` hook, so the hook's own 480 s deadline and 500 s watchdog sit under a limit the
  repo states, not under the harness default. `.claude/agents/cto-reviewer.md` item 6 loses the
  sentence that calls the secret-scan config local-only, which `lint:python` makes false.

refs: >
  #262.

scope_paths:
  - .claude/task/262-hook-timeout/
  - .claude/settings.json
  - .claude/agents/cto-reviewer.md
  - tests/test_sentence_length_in_docs.py
  - tests/test_research_fix_merge_hook.py

protected_override: >
  The explicit hook timeout in .claude/settings.json and the cut in .claude/agents/cto-reviewer.md:
  approved in chat, 2026-11-20, as the follow-ups of the agent-merge MR.

impact_map: >
  writers: none; no table, model or page output changes.
  guard: the PreToolUse Bash entry for `.claude/hooks/git_discipline.py` in `.claude/settings.json`
  gains `"timeout": 600` (seconds). That hook is the merge guard, the commit gate and the branch
  nudge. The merge allowance in the hook stops its own work at 480 s and prints a deny at 500 s, so a
  harness limit of 600 s lets that deny arrive first. Every other event and hook entry is unchanged.
  readers: the harness reads `timeout` on a command hook; no repo script parses the key. The
  reviewer file is read by the cto-reviewer subagent at spawn.
  failure: if the key were ignored, the harness default applies, which is the state before this
  change. A timeout below 500 s would cancel the hook before its deny. 600 is the value of the
  default. The cut removes one sentence and leaves item 6 correct: the CI secret scan and pre-commit
  both run in CI.
  tests: tests/test_sentence_length_in_docs.py pins the count of long sentences per document, and the
  cut removes one from cto-reviewer.md, so its pin moves from 17 to 16 (the pin only moves down).
  tests: tests/test_research_fix_merge_hook.py gains one test that reads the merge hook's deadline
  and watchdog constants and the timeout in .claude/settings.json, and fails if the timeout is
  missing or not above deadline plus grace: a harness that cancels the hook first prints no deny.
  blast_radius: one hook setting, one sentence in a reviewer brief and the two tests that pin them.

approved_design:
  - none: no page output changes

depends_on:
  - !497

shared_files:
  - none: no design, registry, font or chart baseline changes

decisions_taken: >
  The timeout value and the cut are the follow-ups listed with the agent-merge MR, approved in chat,
  2026-11-20. No new dependency, no recurring cost.

decisions_reserved:
  - none: the value and the cut are the approved follow-ups.

done_when:
  - .claude/settings.json parses as JSON and the git_discipline.py entry carries "timeout": 600.
  - python scripts/ci_local.py --job test:python and --job lint:python are green.
  - the MR pipeline is green and python scripts/merge_ready.py <iid> says ready.

amendments: (none)
