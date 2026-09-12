# Review — chore/115-step9-memory-budget — 2026-09-12

diff_sha256: 4aef0034fd17e6a743a1d559a030faba619ec0d8addb8e1d7dd46cd797c0954b

rounds: 2

cto-reviewer: FAIL at round 1 (`c93c245b…`), PASS at round 2
platform-reviewer: FAIL at round 1 (`c93c245b…`), PASS at round 2
scope-auditor: PASS at round 1 (`c93c245b…`), PASS at round 2

Round 1 → 2. cto-reviewer: the new operations-guide section published the CI runner's public
address, host size, city and firewall rule — a live host's fingerprint in a public repo, beside
the WIF description of the prod credential, never in the tracked tree before and not a disclosure
his "go" covered. Removed; the section now says the address is in the Hetzner account.
platform-reviewer: (1) the budget pin compared the three numbers as one tuple — lexicographic, so
a lowered first budget would hide a raised third — now three assertions; (2) the universal-newline
read had no test that could fail on Linux — a CRLF note written as bytes now pins it; (3)
`--report` crashed on a missing folder — now a message and exit 1, tested. Each fix proven by a
mutation that goes red. Two contract amendments record both. The memory folder itself, the hook's
gating path and its wiring are unchanged from round 1.

### cto-reviewer — round 1
Verdict then: FAIL (resolved at round 2)
- Approval form, the budgets as measurements (same class as the comment guard's pin), the guard
  invariants (fail open, path scope, shrink always passes), recurring cost, the routing: all clean.
- Finding 1: `docs/operations_guide.md` published the runner's IPv4, provider/city, OS stack, SSH
  policy and firewall rule into a public repo — a §10 "permanent once published" class the
  contract did not name. → Removed and declared (amendment 1).

### platform-reviewer — round 1
Verdict then: FAIL (resolved at round 2)
- `resulting_text` for Write/Edit/MultiEdit, the path test on both path styles, the cap
  arithmetic, the index exclusion, fail-open, the wiring, the slug derivation, the ops-guide
  section against `.gitlab-ci.yml` and the handover, ruff: all clean.
- Findings 1–3: the tuple-comparison pin; the untested CRLF branch; `--report` on a missing folder.
  → All three fixed, each with a mutation shown red (amendment 2).

## cto-reviewer
VERDICT: PASS (round 2)
risks_checked:
- The operations-guide section re-read in full: the public IPv4, host size, city and firewall rule
  are gone (a grep for the address → 0 hits in the doc and the patch). What remains — provider name, docker
  executor, `concurrent = 2`, SSH by key with the passphrase recovery fact, `GIT_STRATEGY=clone`,
  the IPv6 recipe, the console keyboard, per-project registration and why no group — is
  architecture and recovery knowledge, not a network fingerprint; nothing left says where the box
  is or what ports are open. The retained WIF attribute path is the repo's own path, public by the
  repo URL; the real WIF identifiers stay redacted placeholders in `.gitlab-ci.yml`. Nothing
  further to strike.
- The hook diffed function by function against round 1: `is_memory_path`, `note_count`, `measure`,
  `resulting_text`, `check`, `_default_folder` and `main`'s PreToolUse branch byte-identical;
  only `report()` gained the missing-folder guard. `protected_override`, `impact_map` and
  `decisions_taken` untouched — the round-1 authority clearance stands on the same text.
- Amendment 2's fixes touch `report()` (the human-facing CLI path, not the gating path) and the
  test file: no change to fail-open, path scope or the ratchet-only claim.
findings:
- none

## platform-reviewer
VERDICT: PASS (round 2)
risks_checked:
- Finding 1 re-read: three independent assertions with a docstring naming the lexicographic trap;
  the mutation (`MAX_FILES` 49, `FILE_MAX_CHARS` 999999) traced by hand — the third assertion
  fails. Closed.
- Finding 2 re-read: the CRLF note is built with `write_bytes` and a literal `b"\r\n"`, so it does
  not depend on `os.linesep`; the arithmetic hand-computed — 4,655 raw / 4,232 normalised chars —
  and the `newline=""` mutation traced: `measure()` reads 4,655 and the first assertion fails on
  its own (the same-length Edit would pass under both forms via the shrink rule and does not
  discriminate by itself; the test as a whole still goes red). Holds.
- Finding 3 re-read: `report()` checks `os.path.isdir` before `measure()` — ahead of any code that
  could raise — and the test pins exit 1, the message and no traceback.
- The gating path (`is_memory_path`, `resulting_text`, `check`, `main`'s PreToolUse branch)
  byte-for-byte identical to round 1; only `report()` changed.
- 20 test functions with the two parametrisations (×5, ×6) = 29 collected, matching the amended
  criterion 4.
- The operations-guide section after the redaction still agrees with the handover's
  passphrase-key note; no new contradiction.
- The contract's amendments record both reviewers' findings accurately, including the exact
  mutations, matching what was re-verified on disk.
findings:
- none

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- Round 2 — amendment 1 verified against the diff: the runner section holds no address, size, city
  or firewall rule (a grep for each of the five removed values → 0 hits in the patch); every
  item the amendment says was kept is present verbatim. (The auditor's grep pattern, which spelt
  the values out, was copied into this file at round 2 and pushed once; it was removed and the
  branch rewritten before merge so the pushed history does not carry it.)
- Round 2 — amendment 2 verified against the diff: three separate asserts; the CRLF test writes
  raw bytes; `report()` guards `isdir` and its test pins exit 1 and the message. 20 functions +
  (5 + 6 − 2) = 29 tests, matching the amended criterion 4.
- Round 2 — the changed-file set is the same seven repo files; nothing new in scope;
  `decisions_reserved` untouched by the delta.
- Round 2 — the redaction belongs in `amendments`, not `decisions_taken`: a reviewer-found
  correction in the safe direction, and amendment 1 states the disclosure was not something his
  "go" covered. No addition needed.
- Round 1 (the items below stand; the credential bullet's "public IPv4" is now moot, removed at
  round 2) — scope: every file in the patch (the hook, `settings.json`, the test, `agent_guardrails.md`,
  `operations_guide.md`, `CLAUDE.md`, `contract.md`) is in `scope_paths`; nothing outside it.
- §11 authority form: `protected_override` names the new hook and `settings.json`;
  `decisions_taken` quotes the dated "go" with the objection it answered, matching the plan file's
  "measured, not chosen" section in substance.
- Thresholds: NEW MECHANISM yes (approved), RECURRING COST none — the hook fires at edit time only,
  no scheduled job, no warehouse or API cost.
- `decisions_reserved` untouched: the matcher stays `Edit|Write|MultiEdit|NotebookEdit`
  (`settings.json:53-78`), the shell-write bypass is named open in the evidence, `_MEMORY_PATH`
  (`memory_budget_gate.py:51`) stays scoped to the folder's top-level `.md` files.
- Numbers against disk: the live folder holds exactly 50 notes + `MEMORY.md`; the index lists 50
  files with no dangling link; 18 `def test_` with two parametrisations (5 + 6) = 27; `CLAUDE.md`'s
  paragraph, the hook's constants and the test's pin agree (50 / 7,669 / 4,232).
- Doc sync: the guardrails row and the `CLAUDE.md` section present, as the criteria require.
- Credential sweep of the whole diff: a public IPv4, an SA name pattern and a WIF attribute path —
  infrastructure description, no key, token or password; `API_FOOTBALL_API_KEY` handling untouched.
- `operations_guide.md` placement: the GitLab section under the GitHub-era H2 is disclosed in the
  evidence as a separate un-fixed doc item — matches disk, not a dodge.
- `amendments: none yet` true for round 1.
findings:
- none
