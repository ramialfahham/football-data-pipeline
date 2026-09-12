# Review — feat/142-tracker-snapshot — 2026-09-12

diff_sha256: 4200afcea5f0ebd94be053b261abe3c4fcf57708ab32dcd0b6801d66c89fd046

rounds: 5

rounds_cap_override: round 4 was a delta re-bind on three standing PASSes after the second
  full-suite run found one more tree walker (`test_governance_doc_parity.py`) and the one-line
  exemption moved the hash; the cto-reviewer's round-4 FAIL was on the record itself — the
  amendment said the four-walker pattern "is named in the evidence" before the evidence said it —
  cured by writing it there (hash-excluded, so the binding did not move) and re-reviewed at
  round 5. The product owner did not rule on the cap; this note records the practice, not his
  decision.

cto-reviewer: FAIL at round 1 (`06c42946…`), PASS at round 2 (`88388724…`), PASS at round 3
  (`a63d5d17…`), FAIL at round 4 (`4200afce…`, the record, not the code), PASS at round 5
platform-reviewer: FAIL at round 1 (`06c42946…`), PASS at round 3 (`a63d5d17…`; it had no round
  2), PASS at round 4
scope-auditor: PASS at round 1 (`06c42946…`), PASS at round 2 (`88388724…`), PASS at round 3
  (`a63d5d17…`), PASS at round 4

Round 3 → 4. `tests/test_governance_doc_parity.py` requires every file mentioning a guard or
protected path to be in `COVERED_FILES` or `SWEEP_EXEMPT`; the snapshot quotes issue bodies that
name those paths. It joins `SWEEP_EXEMPT` beside `docs/audits/` with its own reason line; the test
file joins `scope_paths` (third amendment). No other change.

Round 2 → 3. platform-reviewer's round-1 finding: `is_governed` compared the path
case-sensitively, and on Windows `Docs/Tracker/gitlab_snapshot.md` is the same file — the hook
was a spelling away from silent. Now case-folded; three spellings pinned; the mutation (fold
removed) goes red on all three. And the first full-suite run found a third tree walker the
snapshot collides with: `test_materialisation_policy.py` read an old issue body quoted in the
snapshot as a live claim of the repo. The snapshot joins that test's existing "history, not a
live claim" exclusion, one line, and the test file joins `scope_paths` for it. Two amendments.

Round 1 → 2. cto-reviewer's finding: the checksum is computed by the same process that writes
the body, so it proves self-consistency, not provenance — a deliberate shell write that also
recomputes the header passes — and the guarantee had been represented as "fails any change the
script did not make". No code changed; the claim was corrected in the contract, the evidence,
the `CLAUDE.md` row, the guardrails row and both docstrings; provenance via CI re-reading GitLab
reserved as a token decision; the product owner told.

### cto-reviewer — round 4
Verdict then: FAIL (resolved at round 5)
- No widening: every file but the parity test and the contract byte-identical to round 3; the
  classification of the snapshot as a file that records, not governs, sound and the same as the
  precedent accepted at round 3; the address pin untouched.
- Finding 1: the round-4 amendment claimed "the pattern is named in the evidence" while the
  evidence still ended at the third walker — a record claim asserted before the record existed.
  → The evidence's SUITES bullet now records the fourth walker and states the pattern (a
  stale-CLAIM walker exempts the snapshot with its reason; a PROPERTY walker keeps scanning it).

### cto-reviewer — round 1
Verdict then: FAIL (resolved at round 2)
- §11 approval chain, routing of the three protected files, the hook's fail-open and scope, the
  read-only `glab` calls with no token, the cost, the "cannot be cited" row: all clean.
- Findings 1–3: the checksum is a tautology for a deliberate actor; the contract's `blast_radius`
  and the evidence overstated it as "no other writer"; the routing exemption rested on a stronger
  guarantee than was built. → Claim corrected everywhere; residual named; provenance reserved.

### platform-reviewer — round 1
Verdict then: FAIL (resolved at round 3)
- Pathspec and `fnmatch` parity for `docs/tracker/**` in both consumers, the artifact-only
  interaction, the script's byte decoding, pagination, `scope=all`, determinism (the test would
  fail without the explicit sorts), the header split and newline handling, fail-open, the wiring,
  `..` traversal, the test count, ruff, no credential: all clean.
- Finding 1: case-sensitive `startswith` on a case-insensitive filesystem → fixed and pinned.

## cto-reviewer
VERDICT: PASS (round 5)
risks_checked:
- Round 5 — the evidence's SUITES bullet now records the fourth walker and states the pattern in
  the form the round-4 finding asked for; the amendment's claim is true as written. The "three
  of the former, one of the latter" count checked (2 + 1 stale-claim checks closed by one
  reasoning across two files; one property check kept). The hash unchanged, so the code traced
  at rounds 2–4 needs no re-derivation; the `rounds_cap_override:` note accurate and attributes
  nothing to the product owner; no mechanism, dependency or routing change in the delta.
- Round 3 — the hook's only behavioural change is the case fold, which strictly narrows the
  bypass; `main`'s fail-open, the root resolution and the deny text untouched; the three-spelling
  test would fail without the fold. Script, wiring, routing entries, `protected_override`,
  `decisions_taken`, `decisions_reserved` byte-identical to round 2 — no authority change.
- Round 3 — `_is_bookkeeping` read in full: the snapshot fits the same test as its two existing
  precedents (a quotation of history, not an authority the repo cites); the walker still scans
  every source file where a live drift would appear; the other tree walker (the address pin)
  deliberately not exempted, so no general "invisible to every walker" precedent opened.
- Round 3 — both amendments match the diff exactly, including the 22 → 25 count.
- Round 2 — no code moved between rounds 1 and 2 — only docstrings, the test's message and one docstring
  comment; `is_governed`, `main`, the checksum computation and the routing entries byte-identical.
- The correction reaches every place the overstated claim was made: the contract's `blast_radius`,
  `decisions_taken` (1), the amendment; both evidence passages; the `CLAUDE.md` row; the
  guardrails row; both docstrings. No stale copy of "any change the script did not make" survives.
- The actual fix — CI re-reading GitLab — correctly reserved as a credential decision; nothing
  attempts to authorise it by naming it.
- Compared against `.claude/active_work.md`'s real protection (no hook at all): the tracker file's
  attack surface is narrower, not wider; the "no wider than the handover's" claim holds.
- One asymmetry recorded, not blocking: the sibling gates' CI backstops check writer-independent
  properties (an address, a character count); this one checks a checksum the same write controls
  — a strictly weaker backstop, now said plainly, so a disclosed residual rather than a live
  misrepresentation.
- The disclosure reaches the product owner through the report, the correct channel: his merge is
  the approval and he needs the accurate picture before giving it.
findings:
- none

## platform-reviewer
VERDICT: PASS (round 4)
risks_checked:
- Round 4 — the only hunk is the tuple entry plus three comment lines; its shape matches the
  neighbours (a `/`-terminated prefix consumed by `startswith`, so `docs/trackers/` is not
  swallowed); the walker's paths come from `git grep`, one canonical casing, so the Windows case
  class does not apply; the other six files carry identical blob hashes to round 3, so nothing
  from rounds 1 and 3 needs re-deriving.
- Round 3 — the case fold traced: `rel` is the side that carries the caller's casing past the shared
  prefix, so folding it is the correct fix; folding `GOVERNED` (already lowercase) would have been
  a no-op — that alternate mutation cannot pass silently. The three-spelling test builds paths as
  strings, never touching the filesystem, so it exercises the same code path on any OS.
- The Linux side-effect: a differently-cased sibling of `docs/tracker/` is a folder nothing names
  or reads, so the over-deny costs nothing; the alternative (leaving the Windows bypass) is worse
  on this repo's own platform. A disclosed trade-off, not a fail-open violation.
- The one-line exclusion in `test_materialisation_policy.py` matches its neighbours' shape
  (`startswith` because a folder is governed, with the literal `/`, so `docs/tracker_old/` is not
  swallowed); `rel` there comes from `git ls-files`, so the hook's case class does not apply;
  both failing tests share `_is_bookkeeping`, so one line closes both.
- Counts verified independently: 25 in the snapshot test (11 functions + 3 + 5 + 6 + 3), 8 in
  the materialisation test, 33 total as reported.
- The checksum correction prose-only and consistent across the hook, the script (whose docstring
  never over-claimed), the test, `CLAUDE.md`, the guardrails row and the contract.
- The script, the three routing entries and the wiring byte-identical to round 1 (same blob
  hashes), so the round-1 analysis of pathspec/`fnmatch` parity, byte decoding, pagination,
  `scope=all`, determinism and the header split stands on the current hash.
findings:
- none

## scope-auditor
VERDICT: PASS (round 4)
risks_checked:
- Round 4 — the third widening declared with its trigger and reason; the hunk is exactly the
  tuple entry plus its comment; all ten patch files in `scope_paths`. The `rounds_cap_override:`
  note matches the documented practice, distinguishes a re-bind on PASSes from a FAIL-clearing
  override, and attributes the practice to the builder's record, not to him. `decisions_taken`
  and `decisions_reserved` byte-identical to round 3; no secret or address in the delta; the
  exemption is a single reasoned addition beside `docs/audits/`, not a loosening.
- Round 3 — the scope widening (`tests/test_materialisation_policy.py`) declared in
  `amendments:` with its trigger and reason; the hunk is exactly one boolean arm plus a
  four-line comment; all nine patch files in `scope_paths`.
- Round 3 — the exclusion joins the same `_is_bookkeeping` arm as `product_direction_threads.md`
  with the same rationale; four specific exemptions, no wildcard; the address pin untouched and
  still scanning the snapshot — a narrow, single-purpose exclusion, not a loosening.
- Round 3 — both amendments match the diff; `decisions_taken` and `decisions_reserved`
  byte-identical to round 2; no address, token or credential in the delta; 22 → 25 verified.
- Round 2 — the eight patch files identical; the two JSON files and the script byte-identical
  to round 1; the hook and the test changed only in docstrings and message strings, every
  assertion and fixture unchanged. The correction confined to prose, as claimed.
- Round 2 — every place the overstated claim appeared now says "any change that did not also
  rewrite the header" and names the residual.
- Round 2 — his words reproduced verbatim; the correction framed as the builder's disclosure,
  not manufactured as his ruling. `decisions_reserved` grew by exactly the CI token item;
  nothing reserved was built — in particular no quiet upgrade to real provenance.
- Round 1 — scope: the eight patch files plus the hash-excluded ones named in the manifest all in
  `scope_paths`; `protected_override` names the three protected files; the routing exemption
  traced to the issue's own text, part of the ask before the "go"; `CLAUDE.md`'s four original
  rows byte-identical and the new row labelled backup-only; 142 headings and 22 tests counted;
  the patch without the snapshot and the manifest listing it; the session-end refresh honestly a
  routine; the existing `glab` login, no token; two loopback addresses in quoted issue bodies.
findings:
- none
