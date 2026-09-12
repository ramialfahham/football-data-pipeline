# Review — feat/126-no-host-fingerprint-guard — 2026-09-12

diff_sha256: f7efa31ac26d8dff0aad592f656270d6aae34baeb85da06b6c591ffbc7c385e6

rounds: 2

cto-reviewer: PASS at round 1 (`f7d93749…`), PASS at round 2
platform-reviewer: FAIL at round 1 (`f7d93749…`), PASS at round 2
scope-auditor: FAIL at round 1 (`f7d93749…`), PASS at round 2

Round 1 → 2. platform-reviewer: (1) the IPv4 lookahead rejected any following dot, so an address
glued to a full stop — the ordinary prose case, the shape that leaked — passed both halves of the
guard; the lookarounds now reject a neighbouring dot only when a digit sits beyond it, eight
surroundings are pinned, and the mutation back goes red on the full-stop case. (2) The pin's
"walk sees files" half was coupled to one README's loopback lines; it now asserts only that at
least one non-public address line was seen. scope-auditor: the evidence carried the full-suite
placeholder while the suite ran — filled with the measured result. Two contract amendments record
all three. Tests 38 → 46; the wiring, the docs and the handover unchanged.

### platform-reviewer — round 1
Verdict then: FAIL (resolved at round 2)
- Reserved-range coverage, the documentation range as the public sample, the IPv6 pattern
  against a time, a link-local address, a hash and the compressed form, `flagged_lines`,
  `_written_texts`, fail-open, the wiring, the shallow-clone question, the import pin, secrets:
  all clean.
- Finding 1: an address followed directly by `.` is not matched (`(?![\w.])`), and the pin
  shares the blind spot → fixed, pinned, mutation shown red. Finding 2: the two-sided assertion
  coupled to `design-mocks/README.md` → relaxed to "at least one non-public sighting".

### scope-auditor — round 1
Verdict then: FAIL (resolved at round 2)
- Scope, the §11 quote, `decisions_reserved`, the patch and every task artifact grepped for both
  address shapes (zero; the one IPv6-shaped hit is a date in a test asserting it is NOT
  flagged), the README's two loopback lines, recurring cost: all clean.
- Finding 1: criterion 2's evidence line read `PYTEST_PLACEHOLDER` — asserted, not evidenced →
  filled with the measured full-suite result.

## cto-reviewer
VERDICT: PASS (round 2)
risks_checked:
- Round 2 — the delta is legitimate: `settings.json`, `CLAUDE.md` and `agent_guardrails.md`
  carry identical blob hashes in both patches; only the hook, the test and the contract moved.
- Round 2 — `main()`, `_written_texts()`, `_repo_root()` and the `emit_deny` call byte-identical
  to round 1: fail-open, no echo, only new text read, outside-repo paths pass, breadth unchanged.
- Round 2 — the new lookarounds hand-checked: a `v` prefix still blocks; a fifth dotted part still
  excludes; the only behavioural change is sentence-final position now matching — the documented
  fix, not a new false-positive class.
- Round 2 — the pin's load-bearing `public == []` untouched; the placeholder resolved with
  consistent arithmetic; the amendments cross-checked line by line against the diff and the
  evidence's mutation list; routing unchanged.
- Round 1 (the items below stand) — §11 form: `protected_override` names both protected files and points at `decisions_taken`,
  which quotes his words verbatim with the date; `impact_map` substantive (writers, firing
  conditions, what stops being enforced, blast radius with the named false positive).
- Breadth: his words were generic, so scope is the builder's; both leaks were tracked repo files,
  so "any file inside the repo" is the minimum that closes the hole, not a widening;
  `decisions_reserved` holds back the adjacent mechanisms rather than bundling them.
- Fails open (`main()` wraps the body; every early return is 0); never echoes the value (the deny
  interpolates only the path, line numbers and kind — pinned by the deny test); only `new_string`
  / `content` / `edits[].new_string` are read, so an Edit that REMOVES an address is never flagged.
- The version-string false positive verified against the regex: the lookbehind blocks a leading
  `v`, pinned by the sample test.
- Routing re-checked in `review_routing.json`: hooks → cto + platform, `settings.json` → cto.
- `settings.json` read live: the entry sits in the existing edit-time group; JSON intact.
- Recurring cost: one subprocess per edit-time call, same as the four gates in that group.
- Secrets: the patch grepped for dotted quads → zero; the docstring's range prose uses an `x`
  placeholder, not four-octet literals.
- "Zero public, one loopback" honest: the README's two `127.0.0.1` lines match the evidence's
  count; the pin asserts dynamically, so the load-bearing zero is real.
- `scope_paths` lists every touched protected file individually.
findings:
- none

## platform-reviewer
VERDICT: PASS (round 2)
risks_checked:
- The new lookarounds traced character by character: an address glued to a full stop matches; a
  five-part dotted number matches nowhere — the first offset fails the trailing lookahead, and
  the retry one octet later fails the leading lookbehind, so the fix does not merely shift the
  miss; a `v`-prefixed four-part version is blocked by `(?<!\w)`; a lone leading dot with no
  digit before it is flagged, which is correct by the rule's own definition; a CIDR `/24` suffix
  passes both lookarounds and matches.
- The eight-surrounding parametrisation traced case by case; all match; 38 + 8 = 46.
- The mutation claim reproduced by reasoning: reverting only the trailing lookahead fails exactly
  the full-stop case and leaves the other seven unaffected — "1 failed, 7 passed".
- The relaxed pin still proves the walk reads the tree: an empty walk leaves `seen` empty and the
  test fails with its message; a future permitted loopback elsewhere no longer breaks it.
- `ipv4_is_public`, `IPV6`, `flagged_lines`, `_written_texts`, `main`, the wiring and the doc
  rows byte-identical to round 1.
- The amendments and the evidence match the code on disk; no discrepancy.
findings:
- none

## scope-auditor
VERDICT: PASS (round 2)
risks_checked:
- The placeholder is gone (grep → 0); criterion 2 now reads a measured result.
- Test count: 14 functions, parametrisations 5 + 8 + 9 + 6 + 4 + 6 plus 8 single cases = 46,
  matching the evidence and the amendment.
- The full-suite total is internally consistent (1,084 at `!181` + 2 at `!182` + 46 = 1,132);
  the baseline rests on the evidence's own accounting, not an independent run.
- The two machinery fixes read against the diff: bug fixes to the approved mechanism, not a new
  mechanism or a widened deny — no fresh §10 exposure.
- No public address literal in `.claude/task/**` or the patch: the hits are a five-part dotted
  number in prose describing a non-match, the README's permitted loopback quoted in this file,
  and a date in a test asserting it is not flagged.
- Same six repo files; `decisions_taken`, `protected_override`, `decisions_reserved`
  byte-identical to round 1; the amendments name exactly the three findings.
findings:
- none
