# Review — chore/wire-the-unwired-guards — 2026-08-06

branch: chore/wire-the-unwired-guards
diff_sha256: 5ad02d737544e88a0f2da6267415ffc47ef874193b2cdababc74cac4f4b74a2c

rounds: 3

> Connects the guards this repo already owned and did not run. Six items; the audit found three
> separately-built, correct guards invoked by nothing, and `inventory.py` reproduces the list
> mechanically.
>
> EIGHT FINDINGS ACROSS TWO REVIEWERS, NO FALSE POSITIVES. Two were real bugs in code written
> this task, two were tests weaker than the guarantee they advertised, one was a false cost
> declaration, one a false claim in the contract, one an unapproved new mechanism, one a pair of
> documents each naming the other as source of truth. Every one is fixed or withdrawn.

routing:
  - scope-auditor — `always`
  - cto-reviewer — `.gitlab-ci.yml`, `.claude/hooks/**`, `.claude/agents/**`,
    `.claude/review_routing.json` (four guard paths → OPUS floor)
  - platform-reviewer — `.gitlab-ci.yml`, `.claude/hooks/**` (→ OPUS floor), plus `scripts/**`
    and `tests/**`

## scope-auditor

VERDICT: PASS

rounds: PASS (1, full — 18 tool calls)

risks_checked:
- Scope — every file in the diff is listed in `scope_paths`; nothing outside it.
- `protected_override` — the six touched protected files checked against the working agreement's
  protected-path list; the claimed count and category coverage hold. The NARROWING claim (a
  planned push-to-main hook dropped because `~/.claude/hooks/branch_discipline.py` already
  implements it) is consistent with the diff.
- `review_summarise_paths` — read `escalations.log:1106-1154` directly. The entry exists, is
  dated, records `cto-reviewer` correctly refusing to rule on a §10 mechanism, carries the CPO's
  actual instruction, and bounds the approval to `site_v2/src/data/**`. Matches the contract's
  account exactly.
- Withdrawn mechanism cleanup — grepped `check_copy_gate.py`: only the comment explaining the
  removal remains; no orphaned parser or marker check.
- Recurring cost — confirmed `"always": ["scope-auditor"]` in the routing file, so the tier move
  is correctly declared as permanent per-commit spend.
- Doc-sync — both authoritative guardrail docs updated; no stale live assertion of haiku. The
  dated June audit record is correctly untouched.
- Credentials, `impact_map` evidence, and test-to-implementation correspondence all checked.

## cto-reviewer

VERDICT: PASS

rounds: FAIL (1, full) · PASS (2, full re-read) · PASS (3, delta)

Round 2 REFUSED the delta framing and re-read all 1,326 lines, correctly noting that a delta is
available only on top of an earlier PASS and its round-1 verdict was FAIL. Round 3 accepted a
delta because round 2 was a PASS on the same branch.

risks_checked:
- **R1 FINDING — `review_summarise_paths` had no CPO authority.** Correct and the most important
  finding of the task: the approved plan said "add a path to `review_exclude_paths`", what was
  built is a third routing key plus a manifest emitter, and the contract asked a REVIEWER to rule
  on it. §10 reserves new mechanisms to the CPO and §2 step 3 says a reviewer never approves a
  §10 decision. FIXED by taking it to the CPO in plain language; ruling recorded in
  `escalations.log`, bounded to `site_v2/src/data/**`, with any added path a fresh decision.
- **R1 FINDING — the `i18n:same-as-en` exemption marker.** WITHDRAWN, not approved. The reviewer
  showed the case it existed for is already exempt (check 4 skips values with no `[a-z]{3,}` word
  and single capitalised tokens), the repo has zero instances, and the one historical case was
  settled by the CPO TRANSLATING with no exemption available. A self-serve comment would have let
  a future agent green a §10 copy check on its own authority. Marker, parser and the dead
  `_dict_blocks` helper all deleted.
- **R1 FINDING — "RECURRING COST — NO" was false.** Moving `scope-auditor` haiku → sonnet is a
  permanent per-commit increase; the precedent is quoted inside the very file the task edits. The
  approval existed, the DECLARATION was wrong, and that field is the only place a cost crossing is
  visible because no gate parses it. Corrected to YES with the approval named.
- **R1 FINDING — a coverage claim overstated.** The working agreement said scope-auditor holds the
  sole enforcement for thresholds AND secrets; secrets are also hunted by cto-reviewer,
  platform-reviewer and `validate:secrets`. Rewritten to "the only reviewer on EVERY diff".
- Guard invariants — commit gate still returns 0 on the exception path and only emits;
  `hash_exclude_paths` byte-unchanged; `validate:governance` remains blocking. Hooks open, CI
  closed, both in the right direction.
- Its own brief (`.claude/agents/cto-reviewer.md`), the path where it is the only specialist —
  read line by line across two rounds. Two factual corrections, no hunt item, verdict rule or
  model pin weakened. In round 3 it verified the `validate:secrets` correction against
  `.gitlab-ci.yml:300-302` and noted that its OWN round-1 report had repeated the wording error
  being fixed.

## platform-reviewer

VERDICT: PASS

rounds: FAIL (1, full) · FAIL (2, full re-read) · PASS (3, delta)

Round 2 also declined to judge through a keyhole and re-read the full 1,325 lines rather than
refusing on the technicality.

risks_checked:
- **R1 FINDING — two files each named the other as source of truth, while disagreeing.**
  `validate-local` claimed "the first five" run at turn end, which INCLUDED
  `check_task_artifacts.py` (which must not — it needs a fetched `origin/main` and hard-fails on
  a missing or stale `review.md`, so it would block every turn during the build phase) and OMITTED
  `check_ui_i18n_metrics.py` (which does run). FIXED: `stop_gate.py`'s `FAST_GATES` is the single
  source of truth, the five are named explicitly, the exclusion is stated in both places with its
  reason, and a test pins them.
- **R1 FINDING — `test_manifest_failure_is_loud_not_silent` was VACUOUS.** It asserted
  `"raise" in inspect.getsource(...)`, and the word appears in the target function's own comment,
  so swapping the raise for `return b""` left it green; it never called the function at all.
  REWRITTEN to drive the real branch with a malformed pathspec under `pytest.raises`, and verified
  FAILING against the broken form before acceptance.
- **R1 FINDING — `docs/agent_guardrails.md` still asserted haiku.** It also exposed that the
  contract's claim of a "repo-wide" grep was FALSE — a three-file grep. A real `git grep` found a
  FOURTH site the reviewer had not flagged, `.claude/agents/cto-reviewer.md:81`. Both corrected;
  the false claim recorded in `amendments:` rather than quietly rewritten.
- **R2 FINDING — the parity test repeated the R1 defect class.** It asserted each name appeared
  *somewhere* in `SKILL.md`, where each appears three times over, so it stayed green when the
  turn-end list was deleted AND against the broken form it was written to catch. REWRITTEN to
  assert SET EQUALITY over an explicitly marked region. Round 3 re-derived the failure modes
  independently and confirmed a further direction the original never covered: removing a gate from
  `FAST_GATES` without touching the skill now fails too.
- Re-run safety and failure modes of the Stop hook — `stop_hook_active` bound intact; all five
  gates verified read-only, so a hook killed halfway leaves no partial state; `sys.executable`
  correct; output captured as bytes and decoded with `replace`, right on a cp1252 box;
  per-gate fail-open on timeout or spawn failure.
- Fail-open vs fail-closed traced per changed path — correct on every one, nothing inverted.
- The delta was verified by BLOB INDEX rather than memory, confirming the machinery cleared in
  earlier rounds was byte-identical and did not need re-auditing.
- `SKILL.md`'s CI mapping table spot-verified job-by-job against `.gitlab-ci.yml` line numbers.
- Credentials, permissions, dependencies, build health and hosting re-checked over each delta.

## escalations

none. No reviewer returned an ESCALATE in any round.

## Known and deliberately not fixed

1. **`test_fast_gates_and_validate_local_agree` takes the `repo` fixture and never uses it** —
   it reads the real tree. Costs one `shutil.copytree` per run and changes no assertion.
   `platform-reviewer` explicitly said to drop the parameter next time the file is open and NOT
   to open a round for it. Fixing it would void three PASS verdicts over a cosmetic.

2. **`protected_override` defines its own reach as "the paths in `scope_paths:`", which is
   self-referential** — an amendment can widen the override it is bounded by. Raised by
   `cto-reviewer`, which passed the specific case (a stale-fact correction with zero weakening)
   and flagged the general one. NOT fixed here: tightening the override mechanism under the
   authority it would constrain is the circularity itself. Filed as GitLab #18.

3. **`GATE_TIMEOUT_S = 90` is unreachable** — no `timeout` is set on the Stop hook, so the
   harness's 60s default bounds the whole hook first. Both fail open, so the outcome is identical.
   `platform-reviewer` noted that if a Stop-hook timeout is ever configured, 5 × 90s is 7.5
   minutes, past the "five minutes is unusable" line this hook draws for itself, and a total
   wall-clock budget is the shape that holds. Recorded, not acted on.

## Process note

Two reviewers were sent a delta brief after a FAIL and both refused the framing, re-reading the
full patch instead — the refusal condition their briefs carry, exercised correctly:

> a delta brief is a cost saving, never a way to move a change past you while you look through a
> keyhole.

Set against the same rule failing earlier in this session — a delta re-review on the previous
branch completed with ZERO tool calls and certified the builder's summary rather than the change —
this task's rounds used 5–24 tool calls each and verified claims by blob index, line number and
direct file read. `scope-auditor`'s own review here ran at sonnet (the change this task makes) and
used 18 tool calls against that earlier zero. One data point, not proof, and recorded on GitLab
#10 as such.
