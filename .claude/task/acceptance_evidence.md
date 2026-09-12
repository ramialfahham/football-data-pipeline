# Acceptance evidence — no live host address in any committed file

criteria_demonstrated:
  - THE HOOK IS WIRED AND DENIES ON THE REAL REPO. `.claude/settings.json` carries the entry beside
    the other edit-time gates (parsed and counted: 1). Live in this session, a real `Write` of a
    runtime-shaped public IPv4 (the documentation range) into `.claude/task/acceptance_evidence.md`
    — a task artifact, the file class where the slip happened — was refused with the hook's own
    text ("puts a public network address into `.claude/task/acceptance_evidence.md` at line 3
    (IPv4) …"); the deny did not echo the value. Through the hook as the harness calls it (the
    test file's subprocess cases): denied into `docs/operations_guide.md`, `.claude/task/review.md`,
    `scripts/x.py` and `README.md`; an `Edit` and a `MultiEdit` denied on their `new_string`s;
    loopback and private addresses pass; a path outside the repo passes; six malformed inputs
    fail open.
  - THE PIN IS ZERO, MEASURED TWO-SIDED. `tests/test_no_host_fingerprint_in_tree.py` walks
    `git ls-files`, skips binaries, and applies the hook's own `flagged_lines`: **0 public
    literals**; the walk is proven to see files by the non-public IPv4 lines it passes over — **2
    lines, both in `design-mocks/README.md`, both the loopback preview address** — and the test
    asserts exactly that. The patterns proven both ways on runtime-built samples: five public
    shapes flagged (including one past the private block and the accepted bare-version false
    positive); the same public address flagged in eight surroundings — glued to a full stop, in
    parentheses, in backticks, with a port, inside a URL, bare, after `key=`, before a comma;
    nine non-public shapes seen by the pattern and passed by the range test; six number-shaped
    non-addresses ignored (a three-part version, a `v`-prefixed four-part version, a timestamp,
    an out-of-range octet, a five-part string); a global IPv6 flagged, a date-like colon run and
    a link-local address not. `test_definition_is_imported_not_copied` fails if this file ever
    compiles its own pattern or defines its own range test. **46 passed**; `ruff check --config
    .ruff-ci.toml` on the hook and the test → "All checks passed!"; `pytest tests/` →
    **1,132 passed, 1 skipped, 14 subtests passed** (28:58, run on the final code with nothing
    else touching the tree) — `main`'s 1,086 plus the 46 new.
  - FOUR MUTATIONS SHOWN RED. Private-range test widened (`172.16–31` block removed) → 2 of the
    non-public samples fail; IPv6 branch removed → the IPv6 sample test and the line-numbers test
    fail; a public address planted at the end of `docs/operations_guide.md` (by a shell write,
    which the hook cannot see) → `test_the_tracked_tree_holds_no_public_address` fails naming the
    file and line; the trailing lookahead reverted to the round-1 form that rejected any dot →
    the glued-to-a-full-stop case fails (1 failed, 7 passed of the surroundings). Each restored;
    46 passed after. And the guard's first catch was real: the contract's own first draft spelt
    the accepted-false-positive example out as four digits, and the pin test failed on
    `contract.md` line 62 before anything else ran — fixed by describing the shape instead of
    writing it.
  - THE DOCS AND THE HANDOVER ARE CURRENT. `docs/agent_guardrails.md` has the row; `CLAUDE.md`
    "Operational notes" has the line (the rule, the hook, the pin, the slip, and what no pattern
    can catch); `.claude/active_work.md` states #115 closed, #126 as its one follow-up, #118 next
    (15,999 chars, under the 16,000 budget).

## What is NOT demonstrated
- What the rule cannot recognise: a hostname, a provider, a city, a hardware size, a port list.
  Those remain judgment; the deny text and `CLAUDE.md` name them so the reminder lands at the
  moment of writing. Extending the pattern to hostnames is reserved.
- A shell write into a repo file bypasses the hook, like every edit-time gate; the pin catches
  it at CI (mutation 3 above is exactly that path).
- Git history is not scanned. The leaked commit on `!182` is unreachable from every branch after
  the rewrite; how long GitLab retains an unreachable object is the provider's, and the address
  itself remains valid until the host is given a new one — his call, stated on `!182`.
- `.gitleaks.toml` is untouched: a second rule set there would carry its own `useDefault`
  semantics, and one mechanism in the repo's own shape was the point.
