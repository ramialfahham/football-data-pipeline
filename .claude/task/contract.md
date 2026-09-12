# Task contract — no live host address in any committed file: an edit-time guard and a pinned count

objective: >
  On `!182` the CI runner's public address went into a committed file twice — first into
  `docs/operations_guide.md` (caught by the cto-reviewer, removed), then as the grep pattern a
  reviewer used to prove it was gone, copied into `.claude/task/review.md`, which is committed and
  was pushed to the public repo before anyone noticed. The branch was rewritten. A review caught
  it once and not the second time, because the second copy sat inside the review's own record.
  This branch adds the guard: an edit-time hook that refuses writing a public network address into
  any file inside the repo, task artifacts included, and a CI test that pins the count of such
  literals in the tracked tree at zero — measured today: zero public, one loopback.

refs: >
  GitLab #126 (this task, `Task` template; the What/Why/How below are copied from it). The
  product owner's requirement, 2026-09-12, in chat, after the slip on `!182`: "So it actually
  slipped. We must not allow this in the future." The pattern the guard copies:
  `.claude/hooks/comment_history_gate.py` + `tests/test_no_decision_history_in_code.py` (`!177`).

protected_override: >
  `.claude/hooks/host_fingerprint_gate.py` (new) and `.claude/settings.json` (one hook
  registration). The product owner's words that require this mechanism are quoted in
  `decisions_taken` below, in the commit message and in the MR head; under working_agreement §11
  the durable approval is his merge of this MR.

scope_paths:
  - .claude/hooks/host_fingerprint_gate.py
  - .claude/settings.json
  - tests/test_no_host_fingerprint_in_tree.py
  - docs/agent_guardrails.md
  - CLAUDE.md
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: one new hook, one registration entry, one test file, one guardrails row, one line in
    `CLAUDE.md`, the handover.

  downstream (a guard's blast radius is every future edit): the hook fires on every `Edit`,
    `Write`, `MultiEdit` and `NotebookEdit` whose target is INSIDE the repo — any extension, any
    tree, `.claude/task/**` included, because that is where the slip happened. It reads only the
    written text (`content`, `new_string`, `edits[].new_string`) and denies when a line carries a
    public IPv4 literal (four bounded octets, not loopback, private, link-local, multicast, the
    unspecified or broadcast address) or a global-unicast IPv6 literal (a leading `2xxx`/`3xxx`
    group followed by at least three more colon groups). Paths outside the repo (memory, plans,
    scratchpad), and any text without such a literal, pass with no output. `NotebookEdit` writes
    `new_source`, never read here, so it passes. Any exception → return 0, no output: fails OPEN.
    The test imports the hook's patterns and its range test, walks `git ls-files`, and pins the
    tree at zero, so the CI count and the edit-time deny cannot drift apart. No other hook, the
    review hash, routing or CI job changes.

  what stops being enforced if it is wrong: nothing enforced today — no gate looked for this;
    gitleaks (`validate:secrets`) scans for credential shapes, not addresses. If the hook
    mis-denies, the message names the file and line and the way out (describe the host, keep the
    value in the provider's console).

  layer_rules: n/a. deploy_order: none.

  blast_radius: a NEW DENY on edits, bounded to lines carrying an address literal. Accepted false
    positive, named in the hook and the test: a bare four-part version string (four dotted
    numbers with nothing before them) reads as an IPv4 and is denied; none exists in the tree
    today, a `v` prefix is enough to pass, and the deny says what to do. The guard's first catch
    was this contract's own first draft, which spelt that example out as four digits.

acceptance_criteria:
  - `.claude/hooks/host_fingerprint_gate.py` is wired and denies, on the real repo, writing a
    runtime-built public IPv4 or IPv6 literal into a code file, a doc, and `.claude/task/review.md`;
    a loopback, private or link-local literal passes; the deny does not echo the value.
  - `tests/test_no_host_fingerprint_in_tree.py` pins the tracked tree at zero such literals
    (measured two-sided: 0 public, 1 loopback in `design-mocks/README.md`), proves the patterns
    both ways on runtime-built samples, and imports the hook's definition rather than copying it;
    `pytest tests/` green with `main`'s count plus the new tests; ruff clean.
  - Mutations shown red: widen the private-range test to admit a public address → the sample
    test fails; drop the IPv6 pattern → its sample fails; a scratch file with a public address in
    the tree → the pinned count fails.
  - `docs/agent_guardrails.md` has the row; `CLAUDE.md` "Operational notes" has the line; the
    handover states #126 done and #118 next.

decisions_taken: >
  CPO, 2026-09-12, in chat: "So it actually slipped. We must not allow this in the future." — the
  requirement. The shape is the builder's, in the repo's established form: an edit-time deny plus
  a pinned CI count, the two halves importing one definition.

  WHAT THE RULE CAN RECOGNISE: a network address literal. A hostname, a provider name, a city, a
  hardware size or a port list has no pattern; those remain judgment, and the guard's deny text
  names them so the moment of writing is the moment of the reminder.

  THRESHOLD — NEW MECHANISM: yes, required above. THRESHOLD — RECURRING COST: none (one more
  subprocess per edit, like the four gates already in that matcher group).

decisions_reserved:
  - Extending `.gitleaks.toml` with an address rule (a second rule set with `useDefault`
    semantics of its own); scanning git history; hostnames or provider names as a pattern.

done_when:
  - The four criteria proven; `pytest tests/` and ruff green; the three mutations shown red.

amendments:
  - After round 1 (platform-reviewer): (1) the IPv4 pattern's trailing lookahead rejected any
    following dot, so an address glued to a full stop — the ordinary prose case, and the shape
    that leaked — passed both the hook and the pin. The lookarounds now reject a neighbouring dot
    only when a digit sits on its other side (a longer dotted number), so `… is <address>.`
    matches and `1.2.3.4.5` still does not; a parametrised test pins eight surroundings (full
    stop, parentheses, backticks, a port, a URL, bare, `key=`, a comma), and the mutation back to
    the old lookahead goes red on the full-stop case. (2) The pin's "the walk sees files" half was
    asserted against one README's loopback lines — a coupling to content the guard itself permits
    to change; it now asserts only that at least one non-public address line was seen. Tests 38 →
    46; criterion 2's count updated.
  - After round 1 (scope-auditor): the evidence carried the full-suite placeholder while the
    suite ran — filled with the measured result before round 2, and the suite re-run after (1).
